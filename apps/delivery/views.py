import logging
from django.utils import timezone
from django.db import transaction
from django.conf import settings as django_settings
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from core.responses import success_response, error_response
from core.permissions import IsDeliveryBoy, IsAdminUser
from apps.users.models import User
from apps.orders.models import Order, OrderStatusLog
from apps.wallet.models import Wallet
from .models import DeliveryBoyProfile, DeliveryAssignment, LocationLog, DeliveryRating
from .serializers import (
    DeliveryBoyProfileSerializer,
    UpdateAvailabilitySerializer,
    UpdateLocationSerializer,
    DeliveryAssignmentSerializer,
    AdminAssignDeliverySerializer,
    DeliveryRatingSerializer,
)
from .utils import find_nearest_delivery_boy

logger = logging.getLogger("apps")


# ── Profile ───────────────────────────────────────────────────────────────────

class MyDeliveryProfileView(APIView):
    """GET /api/v1/delivery/profile/"""
    permission_classes = [IsAuthenticated, IsDeliveryBoy]

    def get(self, request):
        profile, _ = DeliveryBoyProfile.objects.get_or_create(user=request.user)
        return success_response(data=DeliveryBoyProfileSerializer(profile).data)

    def patch(self, request):
        profile, _ = DeliveryBoyProfile.objects.get_or_create(user=request.user)
        serializer = DeliveryBoyProfileSerializer(
            profile, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(
            data=DeliveryBoyProfileSerializer(profile).data,
            message="Profile updated.",
        )


class UpdateAvailabilityView(APIView):
    """POST /api/v1/delivery/availability/"""
    permission_classes = [IsAuthenticated, IsDeliveryBoy]

    def post(self, request):
        serializer = UpdateAvailabilitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        profile, _ = DeliveryBoyProfile.objects.get_or_create(user=request.user)
        profile.availability = serializer.validated_data["availability"]
        profile.save(update_fields=["availability", "updated_at"])

        return success_response(
            message=f"Availability updated to {profile.availability}."
        )


class UpdateLocationView(APIView):
    """
    POST /api/v1/delivery/location/
    Flutter app calls this every 30 seconds while on delivery.
    """
    permission_classes = [IsAuthenticated, IsDeliveryBoy]

    def post(self, request):
        serializer = UpdateLocationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        lat = serializer.validated_data["latitude"]
        lon = serializer.validated_data["longitude"]

        profile, _ = DeliveryBoyProfile.objects.get_or_create(user=request.user)
        profile.current_lat          = lat
        profile.current_lon          = lon
        profile.last_location_update = timezone.now()
        profile.save(update_fields=["current_lat", "current_lon", "last_location_update"])

        # Log location if on active delivery
        active_assignment = DeliveryAssignment.objects.filter(
            delivery_boy=request.user,
            status__in=[
                DeliveryAssignment.Status.ACCEPTED,
                DeliveryAssignment.Status.PICKED,
            ]
        ).first()

        if active_assignment:
            LocationLog.objects.create(
                delivery_boy = request.user,
                assignment   = active_assignment,
                latitude     = lat,
                longitude    = lon,
            )

        return success_response(message="Location updated.")


# ── Assignments ───────────────────────────────────────────────────────────────

class MyAssignmentsView(generics.ListAPIView):
    """GET /api/v1/delivery/assignments/"""
    permission_classes = [IsAuthenticated, IsDeliveryBoy]
    serializer_class   = DeliveryAssignmentSerializer

    def get_queryset(self):
        qs = DeliveryAssignment.objects.filter(
            delivery_boy=self.request.user
        ).select_related("order__shop", "order__buyer")

        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter.upper())
        return qs

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return success_response(data=serializer.data)


class ActiveAssignmentView(APIView):
    """GET /api/v1/delivery/assignments/active/"""
    permission_classes = [IsAuthenticated, IsDeliveryBoy]

    def get(self, request):
        assignment = DeliveryAssignment.objects.filter(
            delivery_boy=request.user,
            status__in=[
                DeliveryAssignment.Status.ASSIGNED,
                DeliveryAssignment.Status.ACCEPTED,
                DeliveryAssignment.Status.PICKED,
            ]
        ).select_related("order__shop", "order__buyer").first()

        if not assignment:
            return success_response(data=None, message="No active assignment.")

        return success_response(data=DeliveryAssignmentSerializer(assignment).data)


class AcceptAssignmentView(APIView):
    """POST /api/v1/delivery/assignments/<uuid:assignment_id>/accept/"""
    permission_classes = [IsAuthenticated, IsDeliveryBoy]

    def post(self, request, assignment_id):
        try:
            assignment = DeliveryAssignment.objects.select_related(
                "order"
            ).get(
                id=assignment_id,
                delivery_boy=request.user,
                status=DeliveryAssignment.Status.ASSIGNED,
            )
        except DeliveryAssignment.DoesNotExist:
            return error_response(message="Assignment not found.", status_code=404)

        # Check no other active delivery
        other_active = DeliveryAssignment.objects.filter(
            delivery_boy=request.user,
            status__in=[
                DeliveryAssignment.Status.ACCEPTED,
                DeliveryAssignment.Status.PICKED,
            ]
        ).exists()

        if other_active:
            return error_response(
                message="Complete your current delivery before accepting a new one.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        assignment.status      = DeliveryAssignment.Status.ACCEPTED
        assignment.accepted_at = timezone.now()
        assignment.save(update_fields=["status", "accepted_at"])

        # Update delivery boy availability
        profile, _ = DeliveryBoyProfile.objects.get_or_create(user=request.user)
        profile.availability = DeliveryBoyProfile.AvailabilityStatus.ON_DELIVERY
        profile.save(update_fields=["availability"])

        return success_response(message="Assignment accepted. Go pick up the order.")


class MarkPickedView(APIView):
    """POST /api/v1/delivery/assignments/<uuid:assignment_id>/picked/"""
    permission_classes = [IsAuthenticated, IsDeliveryBoy]

    @transaction.atomic
    def post(self, request, assignment_id):
        try:
            assignment = DeliveryAssignment.objects.select_related(
                "order"
            ).get(
                id=assignment_id,
                delivery_boy=request.user,
                status=DeliveryAssignment.Status.ACCEPTED,
            )
        except DeliveryAssignment.DoesNotExist:
            return error_response(message="Assignment not found.", status_code=404)

        assignment.status   = DeliveryAssignment.Status.PICKED
        assignment.picked_at = timezone.now()
        assignment.save(update_fields=["status", "picked_at"])

        # Update order status
        order = assignment.order
        prev  = order.status
        order.status = Order.Status.PICKED
        order.save(update_fields=["status"])

        OrderStatusLog.objects.create(
            order=order, from_status=prev,
            to_status=Order.Status.PICKED,
            changed_by=request.user,
            note="Picked up by delivery boy",
        )

        return success_response(message="Order picked up. Proceed to delivery address.")


class VerifyAndDeliverView(APIView):
    """
    POST /api/v1/delivery/assignments/<uuid:assignment_id>/deliver/
    OTP verify karo → DELIVERED mark karo → earnings credit karo.
    """
    permission_classes = [IsAuthenticated, IsDeliveryBoy]

    @transaction.atomic
    def post(self, request, assignment_id):
        try:
            assignment = DeliveryAssignment.objects.select_related(
                "order__buyer", "order__shop__owner"
            ).get(
                id=assignment_id,
                delivery_boy=request.user,
                status=DeliveryAssignment.Status.PICKED,
            )
        except DeliveryAssignment.DoesNotExist:
            return error_response(message="Assignment not found.", status_code=404)

        otp_code = request.data.get("otp_code", "")
        if not otp_code:
            return error_response(message="OTP code is required.", status_code=400)

        order = assignment.order
        if order.delivery_otp != otp_code:
            return error_response(
                message="Incorrect OTP. Please ask the buyer for the correct code.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Mark order delivered
        prev_status = order.status
        order.status               = Order.Status.DELIVERED
        order.delivery_otp_verified = True
        order.delivered_at          = timezone.now()
        order.save(update_fields=["status", "delivery_otp_verified", "delivered_at"])

        OrderStatusLog.objects.create(
            order=order, from_status=prev_status,
            to_status=Order.Status.DELIVERED,
            changed_by=request.user,
            note="Delivered — OTP verified",
        )

        # Mark assignment delivered
        assignment.status       = DeliveryAssignment.Status.DELIVERED
        assignment.delivered_at = timezone.now()
        assignment.save(update_fields=["status", "delivered_at"])

        # Delivery boy availability reset
        profile, _ = DeliveryBoyProfile.objects.get_or_create(user=request.user)
        profile.availability          = DeliveryBoyProfile.AvailabilityStatus.AVAILABLE
        profile.total_deliveries     += 1
        profile.successful_deliveries += 1
        profile.save(update_fields=["availability", "total_deliveries",
                                    "successful_deliveries", "updated_at"])

        # Trigger payment split via Celery
        from celery_app.tasks.notification_tasks import trigger_payment_split
        trigger_payment_split.delay(str(order.id))

        logger.info(f"Order #{order.order_number} delivered by {request.user.email}")
        return success_response(message="Order delivered successfully. Earnings will be credited shortly.")


# ── Admin ─────────────────────────────────────────────────────────────────────

class AdminAssignDeliveryView(APIView):
    """
    POST /api/v1/delivery/admin/assign/
    Admin manually assign karta hai delivery boy ko.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    @transaction.atomic
    def post(self, request):
        serializer = AdminAssignDeliverySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            order = Order.objects.get(
                order_number=serializer.validated_data["order_number"],
                status=Order.Status.READY,
            )
        except Order.DoesNotExist:
            return error_response(
                message="Order not found or not in READY state.", status_code=404
            )

        try:
            delivery_boy = User.objects.get(
                id=serializer.validated_data["delivery_boy_id"],
                role="DELIVERY_BOY",
            )
        except User.DoesNotExist:
            return error_response(message="Delivery boy not found.", status_code=404)

        # Check existing assignment
        if DeliveryAssignment.objects.filter(
            order=order,
            status__in=[
                DeliveryAssignment.Status.ASSIGNED,
                DeliveryAssignment.Status.ACCEPTED,
                DeliveryAssignment.Status.PICKED,
            ]
        ).exists():
            return error_response(
                message="This order already has an active delivery assignment.",
                status_code=400,
            )

        # Calculate earning (3% of order total)
        earning = round(float(order.total_amount) * django_settings.DELIVERY_BOY_PERCENT / 100, 2)

        assignment = DeliveryAssignment.objects.create(
            order             = order,
            delivery_boy      = delivery_boy,
            earning           = earning,
            assigned_by_admin = True,
        )

        return success_response(
            data=DeliveryAssignmentSerializer(assignment).data,
            message=f"Order assigned to {delivery_boy.full_name}.",
            status_code=status.HTTP_201_CREATED,
        )


class AdminAutoAssignView(APIView):
    """
    POST /api/v1/delivery/admin/auto-assign/
    System nearest available delivery boy dhundta hai.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    @transaction.atomic
    def post(self, request):
        order_number = request.data.get("order_number")
        try:
            order = Order.objects.select_related("shop").get(
                order_number=order_number, status=Order.Status.READY
            )
        except Order.DoesNotExist:
            return error_response(
                message="Order not found or not in READY state.", status_code=404
            )

        if not order.shop.latitude or not order.shop.longitude:
            return error_response(
                message="Shop location not set. Cannot auto-assign.", status_code=400
            )

        nearest = find_nearest_delivery_boy(
            float(order.shop.latitude), float(order.shop.longitude)
        )

        if not nearest:
            return error_response(
                message="No available delivery boys found nearby.",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        earning = round(float(order.total_amount) * django_settings.DELIVERY_BOY_PERCENT / 100, 2)

        assignment = DeliveryAssignment.objects.create(
            order        = order,
            delivery_boy = nearest,
            earning      = earning,
        )

        return success_response(
            data=DeliveryAssignmentSerializer(assignment).data,
            message=f"Auto-assigned to {nearest.full_name}.",
            status_code=status.HTTP_201_CREATED,
        )


class AdminDeliveryListView(generics.ListAPIView):
    """GET /api/v1/delivery/admin/list/"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class   = DeliveryAssignmentSerializer

    def get_queryset(self):
        qs = DeliveryAssignment.objects.select_related(
            "order__shop", "order__buyer", "delivery_boy"
        )
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter.upper())
        return qs

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return success_response(data=serializer.data)


class AdminDeliveryBoysView(generics.ListAPIView):
    """GET /api/v1/delivery/admin/boys/ — all delivery boys with status"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class   = DeliveryBoyProfileSerializer

    def get_queryset(self):
        qs = DeliveryBoyProfile.objects.select_related("user")
        availability = self.request.query_params.get("availability")
        if availability:
            qs = qs.filter(availability=availability.upper())
        return qs

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return success_response(data=serializer.data)


# ── Rating ────────────────────────────────────────────────────────────────────

class RateDeliveryView(APIView):
    """POST /api/v1/delivery/assignments/<uuid:assignment_id>/rate/"""
    permission_classes = [IsAuthenticated]

    def post(self, request, assignment_id):
        try:
            assignment = DeliveryAssignment.objects.select_related(
                "delivery_boy"
            ).get(
                id=assignment_id,
                order__buyer=request.user,
                status=DeliveryAssignment.Status.DELIVERED,
            )
        except DeliveryAssignment.DoesNotExist:
            return error_response(message="Assignment not found.", status_code=404)

        if hasattr(assignment, "rating"):
            return error_response(
                message="You have already rated this delivery.", status_code=400
            )

        serializer = DeliveryRatingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(assignment=assignment, rated_by=request.user)

        # Update delivery boy average rating
        profile = assignment.delivery_boy.delivery_profile
        all_ratings = DeliveryRating.objects.filter(
            assignment__delivery_boy=assignment.delivery_boy
        )
        profile.average_rating = round(
            sum(r.rating for r in all_ratings) / all_ratings.count(), 2
        )
        profile.total_ratings = all_ratings.count()
        profile.save(update_fields=["average_rating", "total_ratings"])

        return success_response(message="Thank you for rating your delivery.")