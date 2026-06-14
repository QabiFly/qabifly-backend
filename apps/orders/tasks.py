# apps/orders/tasks.py
import logging
import random
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger("apps")


@shared_task
def auto_assign_delivery_boy():
    """
    Har 2 minute mein run hoga.
    Jo orders READY hain aur 5 minute se kisi ne pick nahi kiya
    unhe nearby delivery boy ko auto-assign karega.
    """
    from apps.orders.models import Order
    from apps.users.models import User
    from apps.notifications.models import Notification

    cutoff = timezone.now() - timedelta(minutes=5)

    # Orders jo READY hain aur kisi ne accept nahi kiya
    pending_orders = Order.objects.filter(
        status="READY",
        delivery_boy__isnull=True,
        updated_at__lte=cutoff,
    ).select_related("shop", "buyer")

    for order in pending_orders:
        # Shop ke paas ke delivery boys
        available_boys = User.objects.filter(
            role="DELIVERY_BOY",
            is_active=True,
            is_available_for_delivery=True,
        ).exclude(
            # Jo already busy hain unhe exclude karo
            assigned_orders__status__in=["OUT_FOR_DELIVERY"]
        )

        if not available_boys.exists():
            logger.warning(f"No delivery boys for order {order.order_number}")
            continue

        # Random ek select karo
        boy = random.choice(list(available_boys))

        # Assign karo
        order.delivery_boy = boy
        order.status = "OUT_FOR_DELIVERY"
        order.save(update_fields=["delivery_boy", "status"])

        # Delivery boy ko notification
        Notification.objects.create(
            user=boy,
            title="🚴 Naya Delivery Assignment!",
            message=f"Order #{order.order_number} aapko assign hua hai. "
                    f"Address: {order.delivery_address}",
            notification_type="DELIVERY",
        )

        # Buyer ko notification
        Notification.objects.create(
            user=order.buyer,
            title="📦 Delivery On The Way!",
            message=f"Aapka order #{order.order_number} delivery ke liye "
                    f"pick ho gaya hai.",
            notification_type="ORDER",
        )

        logger.info(f"Auto-assigned order {order.order_number} to {boy.email}")


@shared_task
def notify_delivery_boys_new_order(order_id):
    """
    Jab order CONFIRMED ho — sab delivery boys ko notify karo.
    """
    from apps.orders.models import Order
    from apps.users.models import User
    from apps.notifications.models import Notification

    try:
        order = Order.objects.select_related("shop").get(id=order_id)
    except Order.DoesNotExist:
        return

    boys = User.objects.filter(
        role="DELIVERY_BOY",
        is_active=True,
    )

    notifications = [
        Notification(
            user=boy,
            title="📦 New Delivery Available!",
            message=f"Order #{order.order_number} pickup ke liye ready hai. "
                    f"Shop: {order.shop.name}. "
                    f"Address: {order.delivery_address}",
            notification_type="DELIVERY",
        )
        for boy in boys
    ]

    Notification.objects.bulk_create(notifications)
    logger.info(f"Notified {len(notifications)} delivery boys for order {order.order_number}")
