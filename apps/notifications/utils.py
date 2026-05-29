import logging
from .models import Notification

logger = logging.getLogger("apps")


def create_notification(
    recipient,
    notif_type: str,
    title: str,
    body: str,
    priority: str = "NORMAL",
    data: dict = None,
):
    """
    Central utility — always use this to create notifications.
    Also pushes to WebSocket channel.
    """
    notif = Notification.objects.create(
        recipient  = recipient,
        notif_type = notif_type,
        priority   = priority,
        title      = title,
        body       = body,
        data       = data or {},
    )

    # Push via WebSocket
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
        group_name    = f"notifications_{recipient.id}"
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type":       "send_notification",
                "id":         str(notif.id),
                "notif_type": notif_type,
                "title":      title,
                "body":       body,
                "priority":   priority,
                "data":       data or {},
                "created_at": str(notif.created_at),
            }
        )
    except Exception as e:
        logger.warning(f"WebSocket push failed for notification {notif.id}: {e}")

    return notif


def notify_order_update(order, title: str, body: str):
    """Notify buyer about order status change."""
    create_notification(
        recipient  = order.buyer,
        notif_type = Notification.NotifType.ORDER_UPDATE,
        title      = title,
        body       = body,
        priority   = "HIGH",
        data       = {"order_number": order.order_number, "status": order.status},
    )


def notify_payment(user, title: str, body: str, amount: float):
    create_notification(
        recipient  = user,
        notif_type = Notification.NotifType.PAYMENT,
        title      = title,
        body       = body,
        priority   = "HIGH",
        data       = {"amount": amount},
    )


def broadcast_to_role(role: str, title: str, body: str, sender=None):
    """Admin broadcast — send to all users of a specific role."""
    from apps.users.models import User
    recipients = User.objects.filter(role=role, is_active=True)
    count = 0
    for user in recipients:
        create_notification(
            recipient  = user,
            notif_type = Notification.NotifType.BROADCAST,
            title      = title,
            body       = body,
            priority   = "NORMAL",
            data       = {"sent_by": sender.email if sender else "system"},
        )
        count += 1
    return count