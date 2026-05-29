import uuid
import random
import string
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


def generate_otp():
    """Generate a numeric OTP of configured length."""
    length = getattr(settings, "OTP_LENGTH", 6)
    return "".join(random.choices(string.digits, k=length))


class OTPRecord(models.Model):

    class OTPType(models.TextChoices):
        EMAIL_VERIFICATION  = "EMAIL_VERIFICATION",  "Email Verification"
        EMAIL_LOGIN         = "EMAIL_LOGIN",          "Email Login"
        PHONE_VERIFICATION  = "PHONE_VERIFICATION",  "Phone Verification"
        PASSWORD_RESET      = "PASSWORD_RESET",       "Password Reset"

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Store email or phone as identifier — no FK to user (user may not exist yet during signup)
    identifier = models.CharField(max_length=255)   # email or phone number
    otp_type   = models.CharField(max_length=30, choices=OTPType.choices)
    otp_code   = models.CharField(max_length=10, default=generate_otp)
    is_used    = models.BooleanField(default=False)
    attempts   = models.IntegerField(default=0)      # wrong attempts counter
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = "otp_records"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["identifier", "otp_type"]),
        ]

    def save(self, *args, **kwargs):
        if not self.expires_at:
            if self.otp_type == self.OTPType.PHONE_VERIFICATION:
                minutes = getattr(settings, "PHONE_OTP_EXPIRY_MINUTES", 5)
            else:
                minutes = getattr(settings, "EMAIL_OTP_EXPIRY_MINUTES", 10)
            self.expires_at = timezone.now() + timedelta(minutes=minutes)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        return not self.is_used and not self.is_expired and self.attempts < 5

    def __str__(self):
        return f"{self.identifier} — {self.otp_type} — {'used' if self.is_used else 'active'}"


class RefreshTokenRecord(models.Model):
    """
    Track issued refresh tokens for blacklisting on logout.
    SimpleJWT ka built-in blacklist bhi use hoga — yeh extra audit trail ke liye hai.
    """
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user       = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="refresh_tokens",
    )
    token_jti  = models.CharField(max_length=255, unique=True)   # JWT ID claim
    is_revoked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = "refresh_token_records"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} — {'revoked' if self.is_revoked else 'active'}"