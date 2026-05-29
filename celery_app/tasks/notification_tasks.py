from celery import shared_task
import logging

logger = logging.getLogger("apps")


@shared_task
def send_broadcast_notifications(broadcast_id: str):
    """Create individual notifications for all targeted users."""
    from apps.notifications.models import BroadcastNotification, Notification
    from apps.users.models import User

    try:
        broadcast = BroadcastNotification.objects.get(id=broadcast_id)
    except BroadcastNotification.DoesNotExist:
        logger.error(f"Broadcast not found: {broadcast_id}")
        return

    if broadcast.target_role == "ALL":
        recipients = User.objects.filter(is_active=True)
    else:
        recipients = User.objects.filter(
            role=broadcast.target_role, is_active=True
        )

    notifications = [
        Notification(
            recipient   = user,
            notif_type  = Notification.NotifType.BROADCAST,
            priority    = broadcast.priority,
            title       = broadcast.title,
            message     = broadcast.message,
        )
        for user in recipients
    ]
    Notification.objects.bulk_create(notifications, batch_size=500)

    broadcast.sent_count = len(notifications)
    broadcast.is_sent    = True
    broadcast.save(update_fields=["sent_count", "is_sent"])

    logger.info(f"Broadcast sent to {len(notifications)} users.")

@shared_task
def handle_whatsapp_message(phone: str, message: str, wa_msg_id: str = ""):
    """Background mein WhatsApp message handle karo."""
    from apps.whatsapp.conversation import handle_incoming
    handle_incoming(phone, message, wa_msg_id)


@shared_task
def notify_shopkeeper_whatsapp(order_id: str):
    """
    Order place hone pe shopkeeper ko WhatsApp alert bhejo.
    Orders view mein call hoga.
    """
    from apps.orders.models import Order
    from apps.whatsapp.wa_client import send_order_alert_to_shopkeeper
    from apps.whatsapp.models import WhatsAppSession

    try:
        order = Order.objects.select_related(
            "shop__owner", "buyer"
        ).prefetch_related("items").get(id=order_id)

        shopkeeper = order.shop.owner

        # Shopkeeper ka WhatsApp session hai?
        try:
            session = WhatsAppSession.objects.get(user=shopkeeper)
        except WhatsAppSession.DoesNotExist:
            logger.warning(
                f"Shopkeeper {shopkeeper.email} ka WhatsApp number nahi hai"
            )
            return

        items_summary = "\n".join(
            f"• {i.product_name} x{i.quantity} = ₹{i.line_total}"
            for i in order.items.all()
        )

        # Shopkeeper ko alert bhejo
        send_order_alert_to_shopkeeper(
            shopkeeper_phone = session.phone,
            order_number     = order.order_number,
            buyer_name       = order.buyer.full_name,
            total            = float(order.total_amount),
            payment_method   = order.payment_method,
            items_summary    = items_summary,
        )

        # Session ko ORDER_MENU state mein daalo
        session.state = "ORDER_MENU"
        session.temp_data["pending_order"] = order.order_number
        session.save()

        logger.info(f"WhatsApp order alert sent for #{order.order_number}")

    except Exception as e:
        logger.error(f"WhatsApp shopkeeper notify failed: {e}")

@shared_task
def trigger_payment_split(order_id: str):
    """Called after DELIVERED — split payment to wallets."""
    from django.conf import settings
    from django.utils import timezone
    from apps.orders.models import Order
    from apps.payments.models import Payment, PaymentSplit
    from apps.wallet.models import Wallet

    try:
        order   = Order.objects.get(id=order_id)
        payment = order.payment
    except Exception as e:
        logger.error(f"Payment split failed: {order_id} — {e}")
        return

    if payment.status != Payment.Status.PAID:
        logger.warning(f"Payment not paid, skipping split: {order_id}")
        return

    total = float(payment.amount)

    # Shopkeeper split
    shopkeeper_amount = round(total * settings.SHOPKEEPER_PERCENT / 100, 2)
    shop_wallet, _    = Wallet.objects.get_or_create(user=order.shop.owner)
    shop_wallet.credit(
        amount      = shopkeeper_amount,
        description = f"Order #{order.order_number} earnings",
        reference   = order.order_number,
    )
    PaymentSplit.objects.create(
        payment   = payment,
        recipient = order.shop.owner,
        role      = "SHOPKEEPER",
        amount    = shopkeeper_amount,
        percent   = settings.SHOPKEEPER_PERCENT,
        is_credited = True,
        credited_at = timezone.now(),
    )

    # Delivery boy split
    try:
        from apps.delivery.models import DeliveryAssignment
        assignment      = DeliveryAssignment.objects.get(order=order)
        delivery_boy    = assignment.delivery_boy
        delivery_amount = round(total * settings.DELIVERY_BOY_PERCENT / 100, 2)

        db_wallet, _ = Wallet.objects.get_or_create(user=delivery_boy)
        db_wallet.credit(
            amount      = delivery_amount,
            description = f"Delivery earning — Order #{order.order_number}",
            reference   = order.order_number,
        )
        PaymentSplit.objects.create(
            payment   = payment,
            recipient = delivery_boy,
            role      = "DELIVERY_BOY",
            amount    = delivery_amount,
            percent   = settings.DELIVERY_BOY_PERCENT,
            is_credited = True,
            credited_at = timezone.now(),
        )

        # Update delivery boy stats
        profile = delivery_boy.delivery_profile
        profile.total_deliveries += 1
        profile.total_earnings   += delivery_amount
        profile.availability = profile.AvailabilityStatus.AVAILABLE
        profile.save(update_fields=[
            "total_deliveries", "total_earnings", "availability"
        ])

        assignment.is_earning_credited = True
        assignment.save(update_fields=["is_earning_credited"])

    except Exception as e:
        logger.warning(f"Delivery boy split skipped: {e}")

    # Update shop earnings
    order.shop.total_earnings += shopkeeper_amount
    order.shop.save(update_fields=["total_earnings"])

    logger.info(f"Payment split complete — Order #{order.order_number}")


@shared_task
def purge_old_location_logs():
    """Daily task — delete GPS logs older than 24 hours."""
    from django.utils import timezone
    from datetime import timedelta
    from apps.delivery.models import LocationLog

    cutoff = timezone.now() - timedelta(hours=24)
    count, _ = LocationLog.objects.filter(recorded_at__lt=cutoff).delete()
    logger.info(f"Purged {count} old location logs.")
