from celery import shared_task
import logging

logger = logging.getLogger("apps")


@shared_task
def mark_overdue_udhaar():
    """Daily task — auto-mark overdue udhaar records."""
    from django.utils import timezone
    from apps.udhaar.models import UdhaarRecord

    today   = timezone.now().date()
    overdue = UdhaarRecord.objects.filter(
        is_settled=False,
        status=UdhaarRecord.Status.ACTIVE,
        due_date__lt=today,
    )
    count = overdue.update(status=UdhaarRecord.Status.OVERDUE)
    logger.info(f"Marked {count} udhaar records as overdue.")


@shared_task
def send_udhaar_reminders():
    """Daily task — send reminder 2 days before due date."""
    from django.utils import timezone
    from datetime import timedelta
    from apps.udhaar.models import UdhaarRecord

    reminder_date = timezone.now().date() + timedelta(days=2)
    upcoming = UdhaarRecord.objects.filter(
        is_settled=False,
        due_date=reminder_date,
    ).select_related("buyer", "shop")

    for record in upcoming:
        logger.info(
            f"Udhaar reminder: {record.buyer.email} owes "
            f"₹{record.amount_remaining} to {record.shop.name} "
            f"due {record.due_date}"
        )

    logger.info(f"Udhaar reminders processed for {upcoming.count()} records.")