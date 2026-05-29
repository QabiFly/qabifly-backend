import json
import logging
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsAdminUser
from core.responses import success_response, error_response
from .models import WhatsAppSession, WhatsAppMessage
from .conversation import handle_incoming
from .wa_client import (
    send_text,
    send_order_alert_to_shopkeeper,
    send_order_status_to_buyer,
    send_udhaar_reminder,
)

logger = logging.getLogger("apps")


@csrf_exempt
@require_http_methods(["GET", "POST"])
def webhook(request):
    """
    Meta WhatsApp Webhook.
    GET  = verification challenge (ek baar hota hai setup mein)
    POST = incoming messages
    """
    if request.method == "GET":
        # Meta webhook verification
        mode      = request.GET.get("hub.mode")
        token     = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")

        if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
            logger.info("WhatsApp webhook verified successfully")
            return HttpResponse(challenge, content_type="text/plain")
        else:
            return HttpResponse("Forbidden", status=403)

    elif request.method == "POST":
        try:
            body = json.loads(request.body)
            logger.info(f"WhatsApp webhook received: {body}")

            # Meta ka webhook format parse karo
            entry = body.get("entry", [])
            if not entry:
                return JsonResponse({"status": "ok"})

            changes = entry[0].get("changes", [])
            if not changes:
                return JsonResponse({"status": "ok"})

            value = changes[0].get("value", {})

            # Incoming messages
            messages = value.get("messages", [])
            for msg in messages:
                phone      = msg.get("from")          # e.g. "916387403745"
                msg_type   = msg.get("type")
                wa_msg_id  = msg.get("id", "")

                if msg_type == "text":
                    text = msg["text"]["body"]
                    # Background mein handle karo
                    from celery_app.tasks.notification_tasks import (
                        handle_whatsapp_message,
                    )
                    handle_whatsapp_message.delay(phone, text, wa_msg_id)

                elif msg_type == "interactive":
                    # Button replies
                    interactive = msg.get("interactive", {})
                    if interactive.get("type") == "button_reply":
                        btn_id = interactive["button_reply"]["id"]
                        from celery_app.tasks.notification_tasks import (
                            handle_whatsapp_message,
                        )
                        handle_whatsapp_message.delay(phone, btn_id, wa_msg_id)

            return JsonResponse({"status": "ok"})

        except Exception as e:
            logger.error(f"WhatsApp webhook error: {e}")
            return JsonResponse({"status": "ok"})  # Always 200 to Meta


class AdminWhatsAppStatsView(APIView):
    """GET /api/v1/whatsapp/admin/stats/"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        total_sessions = WhatsAppSession.objects.count()
        authenticated  = WhatsAppSession.objects.filter(
            state="AUTHENTICATED"
        ).count()
        total_messages = WhatsAppMessage.objects.count()

        return success_response(data={
            "total_sessions":     total_sessions,
            "authenticated_users": authenticated,
            "total_messages":     total_messages,
        })


class AdminSendBroadcastView(APIView):
    """
    POST /api/v1/whatsapp/admin/broadcast/
    Sabhi WhatsApp users ko message bhejo.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        message = request.data.get("message")
        if not message:
            return error_response(message="Message required.", status_code=400)

        sessions = WhatsAppSession.objects.filter(
            user__isnull=False
        ).select_related("user")

        count = 0
        for session in sessions:
            if send_text(session.phone, message):
                count += 1

        return success_response(
            message=f"Broadcast sent to {count} WhatsApp users."
        )
