from rest_framework import serializers
from .models import User


class UserProfileSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(read_only=True)

    class Meta:
        model  = User
        fields = (
            "id", "email", "phone",
            "virtual_number", "station_code",
            "virtual_name", "virtual_photo",
            "display_name", "full_name", "role",
            "auth_provider",
            "is_verified", "is_phone_verified",
            "onboarding_complete",
            "profile_photo",
            "village", "district", "state", "pincode",
            "created_at",
        )
        read_only_fields = (
            "id", "email", "role",
            "virtual_number",
            "auth_provider",
            "is_verified", "is_phone_verified",
            "created_at",
        )


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = (
            "full_name", "phone", "profile_photo",
            "village", "district", "state", "pincode",
        )

    def validate_phone(self, value):
        if value:
            value = value.replace(" ", "").replace("-", "")
            if not value.startswith("+91"):
                value = "+91" + value.lstrip("0")
            if len(value) != 13:
                raise serializers.ValidationError(
                    "Valid 10-digit Indian number daalen."
                )
            qs = User.objects.filter(phone=value).exclude(
                pk=self.instance.pk if self.instance else None
            )
            if qs.exists():
                raise serializers.ValidationError(
                    "Yeh number already registered hai."
                )
        return value


class PublicUserSerializer(serializers.ModelSerializer):
    """Safe to expose — sirf public info."""
    display_name   = serializers.CharField(read_only=True)
    virtual_number = serializers.CharField(read_only=True)

    class Meta:
        model  = User
        fields = (
            "id", "display_name",
            "virtual_number", "virtual_photo",
            "village", "district",
        )