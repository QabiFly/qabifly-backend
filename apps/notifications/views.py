import logging
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from core.responses import success_response, error_response
from core.permissions import IsAdminUser
from apps.users.models import User
from .models import Notification
from .serializers import NotificationSerializer, BroadcastSerializer
from .utils import create_notification, broadcast_to_role

logger = logging.getLogger("apps")


class MyNotificationsView(generics.ListAPIView):
    """GET /api/v1/notifications/"""
    permission_classes = [IsAuthenticated]
    serializer_class   = NotificationSerializer

    def get_queryset(self):
        qs = Notification.objects.filter(recipient=self.request.user)
        notif_type = self.request.query_params.get("type")
        is_read    = self.request.query_params.get("read")
        if notif_type:
            qs = qs.filter(notif_type=notif_type.upper())
        if is_read is not None:
            qs = qs.filter(is_read=is_read.lower() == "true")
        return qs

    def list(self, request, *args, **kwargs):
        queryset   = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        unread     = queryset.filter(is_read=False).count()
        return success_response(data={
            "unread_count":  unread,
            "notifications": serializer.data,
        })


class UnreadCountView(APIView):
    """GET /api/v1/notifications/unread-count/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).count()
        return success_response(data={"unread_count": count})


class MarkReadView(APIView):
    """POST /api/v1/notifications/<uuid:notif_id>/read/"""
    permission_classes = [IsAuthenticated]

    def post(self, request, notif_id):
        try:
            notif = Notification.objects.get(id=notif_id, recipient=request.user)
        except Notification.DoesNotExist:
            return error_response(message="Notification not found.", status_code=404)
        notif.mark_read()
        return success_response(message="Marked as read.")


class MarkAllReadView(APIView):
    """POST /api/v1/notifications/mark-all-read/"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        count = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).update(is_read=True, read_at=timezone.now())
        return success_response(message=f"{count} notifications marked as read.")


class AdminBroadcastView(APIView):
    """
    POST /api/v1/notifications/admin/broadcast/
    Admin sends notification to specific role or ALL users.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        serializer = BroadcastSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data        = serializer.validated_data
        target_role = data["target_role"]
        title       = data["title"]
        body        = data["body"]

        if target_role == "ALL":
            roles = ["BUYER", "SHOPKEEPER", "DELIVERY_BOY", "ADMIN"]
            total = 0
            for role in roles:
                total += broadcast_to_role(role, title, body, request.user)
        else:
            total = broadcast_to_role(target_role, title, body, request.user)

        logger.info(
            f"Broadcast sent by {request.user.email} to {target_role} — {total} recipients"
        )
        return success_response(message=f"Broadcast sent to {total} users.")