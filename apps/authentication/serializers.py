from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from apps.users.models import User


# ── Registration ──────────────────────────────────────────────────────────────

class RegisterSerializer(serializers.Serializer):
    email     = serializers.EmailField()
    password  = serializers.CharField(write_only=True, min_length=8)
    full_name = serializers.CharField(max_length=150)
    role      = serializers.ChoiceField(
        choices=["BUYER", "SHOPKEEPER", "DELIVERY_BOY"],
        default="BUYER",
    )

    def validate_email(self, value):
        value = value.lower().strip()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        return User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            full_name=validated_data.get("full_name", ""),
            role=validated_data.get("role", "BUYER"),
            is_verified=False,
        )


# ── OTP ───────────────────────────────────────────────────────────────────────

class SendEmailOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()


class VerifyEmailOTPSerializer(serializers.Serializer):
    email    = serializers.EmailField()
    otp_code = serializers.CharField(min_length=4, max_length=10)


class SendPhoneOTPSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)


class VerifyPhoneOTPSerializer(serializers.Serializer):
    phone    = serializers.CharField(max_length=15)
    otp_code = serializers.CharField(min_length=4, max_length=10)


# ── Login ─────────────────────────────────────────────────────────────────────

class EmailPasswordLoginSerializer(serializers.Serializer):
    email    = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class EmailOTPLoginSerializer(serializers.Serializer):
    """Login via OTP sent to email — no password needed."""
    email = serializers.EmailField()


# ── Password ──────────────────────────────────────────────────────────────────

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_new_password(self, value):
        validate_password(value)
        return value


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    email        = serializers.EmailField()
    otp_code     = serializers.CharField(min_length=4, max_length=10)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_new_password(self, value):
        validate_password(value)
        return value


# ── Token ─────────────────────────────────────────────────────────────────────

class TokenRefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()