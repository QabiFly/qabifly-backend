import logging
from django.utils import timezone
from django.db import transaction
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from core.responses import success_response, error_response
from core.permissions import IsAdminUser
from apps.users.models import User
from apps.orders.models import Order
from .models import SupportTicket, SupportMessage
from .serializers import (
    SupportTicketListSerializer,
    SupportTicketDetailSerializer,
    CreateTicketSerializer,
    ReplyTicketSerializer,
    RateTicketSerializer,
    AdminAssignTicketSerializer,
    generate_ticket_number,
)
from .ai_responses import get_auto_response

logger = logging.getLogger("apps")


class CreateTicketView(APIView):
    """
    POST /api/v1/support/tickets/create/
    Creates ticket → AI auto-response pehle aata hai.
    Agar AI handle nahi kar paya → PENDING state mein jata hai.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = CreateTicketSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        related_order = None
        if data.get("related_order"):
            try:
                related_order = Order.objects.get(
                    order_number=data["related_order"], buyer=request.user
                )
            except Order.DoesNotExist:
                pass

        ticket = SupportTicket.objects.create(
            ticket_number = generate_ticket_number(),
            raised_by     = request.user,
            category      = data["category"],
            subject       = data["subject"],
            priority      = data["priority"],
            related_order = related_order,
        )

        # User's first message
        SupportMessage.objects.create(
            ticket      = ticket,
            sender      = request.user,
            sender_type = SupportMessage.SenderType.USER,
            body        = data["message"],
        )

        # AI auto-response
        ai_reply = get_auto_response(data["subject"], data["message"])
        if ai_reply:
            SupportMessage.objects.create(
                ticket      = ticket,
                sender      = None,
                sender_type = SupportMessage.SenderType.AI,
                body        = ai_reply,
            )
            ticket.status = SupportTicket.Status.AI_HANDLED
        else:
            ticket.status = SupportTicket.Status.PENDING

        ticket.save(update_fields=["status"])

        logger.info(f"Support ticket created: #{ticket.ticket_number} by {request.user.email}")
        return success_response(
            data=SupportTicketDetailSerializer(ticket).data,
            message="Ticket created. Our assistant has responded. If unresolved, an agent will assist shortly.",
            status_code=status.HTTP_201_CREATED,
        )


class MyTicketsView(generics.ListAPIView):
    """GET /api/v1/support/tickets/mine/"""
    permission_classes = [IsAuthenticated]
    serializer_class   = SupportTicketListSerializer

    def get_queryset(self):
        return SupportTicket.objects.filter(
            raised_by=self.request.user
        ).prefetch_related("messages")

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return success_response(data=serializer.data)


class TicketDetailView(APIView):
    """GET /api/v1/support/tickets/<ticket_number>/"""
    permission_classes = [IsAuthenticated]

    def get(self, request, ticket_number):
        try:
            ticket = SupportTicket.objects.prefetch_related(
                "messages__sender"
            ).get(ticket_number=ticket_number)
        except SupportTicket.DoesNotExist:
            return error_response(message="Ticket not found.", status_code=404)

        if ticket.raised_by != request.user and request.user.role != "ADMIN":
            return error_response(message="Access denied.", status_code=403)

        return success_response(data=SupportTicketDetailSerializer(ticket).data)


class ReplyToTicketView(APIView):
    """POST /api/v1/support/tickets/<ticket_number>/reply/"""
    permission_classes = [IsAuthenticated]

    def post(self, request, ticket_number):
        try:
            ticket = SupportTicket.objects.get(ticket_number=ticket_number)
        except SupportTicket.DoesNotExist:
            return error_response(message="Ticket not found.", status_code=404)

        if ticket.status == SupportTicket.Status.CLOSED:
            return error_response(message="Cannot reply to a closed ticket.", status_code=400)

        if ticket.raised_by != request.user and request.user.role != "ADMIN":
            return error_response(message="Access denied.", status_code=403)

        serializer = ReplyTicketSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        sender_type = (
            SupportMessage.SenderType.AGENT
            if request.user.role == "ADMIN"
            else SupportMessage.SenderType.USER
        )

        SupportMessage.objects.create(
            ticket      = ticket,
            sender      = request.user,
            sender_type = sender_type,
            body        = serializer.validated_data["message"],
        )

        if sender_type == SupportMessage.SenderType.AGENT:
            ticket.status = SupportTicket.Status.IN_PROGRESS
            ticket.save(update_fields=["status"])

        return success_response(message="Reply sent.")


class RateTicketView(APIView):
    """POST /api/v1/support/tickets/<ticket_number>/rate/"""
    permission_classes = [IsAuthenticated]

    def post(self, request, ticket_number):
        try:
            ticket = SupportTicket.objects.get(
                ticket_number=ticket_number,
                raised_by=request.user,
            )
        except SupportTicket.DoesNotExist:
            return error_response(message="Ticket not found.", status_code=404)

        if ticket.status not in (
            SupportTicket.Status.RESOLVED, SupportTicket.Status.CLOSED
        ):
            return error_response(
                message="You can only rate resolved or closed tickets.", status_code=400
            )

        if ticket.rating:
            return error_response(message="Already rated.", status_code=400)

        serializer = RateTicketSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ticket.rating         = serializer.validated_data["rating"]
        ticket.rating_comment = serializer.validated_data.get("comment", "")
        ticket.save(update_fields=["rating", "rating_comment"])

        return success_response(message="Thank you for your feedback.")


class AdminTicketsView(generics.ListAPIView):
    """GET /api/v1/support/admin/tickets/?status=PENDING"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class   = SupportTicketListSerializer

    def get_queryset(self):
        qs = SupportTicket.objects.select_related(
            "raised_by", "assigned_to"
        ).prefetch_related("messages")
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter.upper())
        return qs

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return success_response(data=serializer.data)


class AdminAssignTicketView(APIView):
    """POST /api/v1/support/admin/tickets/<ticket_number>/assign/"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, ticket_number):
        try:
            ticket = SupportTicket.objects.get(ticket_number=ticket_number)
        except SupportTicket.DoesNotExist:
            return error_response(message="Ticket not found.", status_code=404)

        serializer = AdminAssignTicketSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            agent = User.objects.get(id=serializer.validated_data["agent_id"], role="ADMIN")
        except User.DoesNotExist:
            return error_response(message="Agent not found.", status_code=404)

        ticket.assigned_to = agent
        ticket.status      = SupportTicket.Status.IN_PROGRESS
        ticket.save(update_fields=["assigned_to", "status"])

        return success_response(message=f"Ticket assigned to {agent.full_name}.")


class AdminResolveTicketView(APIView):
    """POST /api/v1/support/admin/tickets/<ticket_number>/resolve/"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, ticket_number):
        try:
            ticket = SupportTicket.objects.get(ticket_number=ticket_number)
        except SupportTicket.DoesNotExist:
            return error_response(message="Ticket not found.", status_code=404)

        ticket.status      = SupportTicket.Status.RESOLVED
        ticket.resolved_at = timezone.now()
        ticket.save(update_fields=["status", "resolved_at"])

        return success_response(message="Ticket marked as resolved.")