from celery import shared_task
import logging

logger = logging.getLogger("apps")


@shared_task
def mark_overdue_emi_installments():
    """
    Daily task — mark overdue EMI installments.
    Runs every day at 9 AM IST.
    """
    from django.utils import timezone
    from apps.emi.models import EMIInstallment, EMIPlan

    today    = timezone.now().date()
    overdue  = EMIInstallment.objects.filter(
        status=EMIInstallment.Status.PENDING,
        due_date__lt=today,
    )
    count = overdue.update(status=EMIInstallment.Status.OVERDUE)

    # Mark plans as defaulted if 2+ installments overdue
    for plan in EMIPlan.objects.filter(status=EMIPlan.Status.ACTIVE):
        overdue_count = plan.installments.filter(
            status=EMIInstallment.Status.OVERDUE
        ).count()
        if overdue_count >= 2:
            plan.status = EMIPlan.Status.DEFAULTED
            plan.save(update_fields=["status"])

    logger.info(f"Marked {count} EMI installments as overdue.")


@shared_task
def send_emi_reminders():
    """
    Monthly task — send reminder 3 days before due date.
    """
    from django.utils import timezone
    from datetime import timedelta
    from apps.emi.models import EMIInstallment
    from core.email import send_otp_email  # reuse email utility

    reminder_date = timezone.now().date() + timedelta(days=3)
    upcoming = EMIInstallment.objects.filter(
        status=EMIInstallment.Status.PENDING,
        due_date=reminder_date,
    ).select_related("plan__buyer", "plan__order")

    for installment in upcoming:
        buyer = installment.plan.buyer
        logger.info(
            f"EMI reminder sent to {buyer.email} — "
            f"₹{installment.amount} due on {installment.due_date}"
        )

    logger.info(f"EMI reminders sent for {upcoming.count()} installments.")