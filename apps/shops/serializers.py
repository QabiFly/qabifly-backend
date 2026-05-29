from rest_framework import serializers
from django.utils.text import slugify
from apps.users.serializers import PublicUserSerializer
from .models import Shop, ShopCategory, ShopDocument
from .utils import generate_shop_slug


class ShopCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model  = ShopCategory
        fields = ("id", "name", "slug", "icon", "description", "sort_order")


class ShopDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ShopDocument
        fields = ("id", "doc_type", "file", "is_verified", "uploaded_at")
        read_only_fields = ("id", "is_verified", "uploaded_at")


class ShopCreateSerializer(serializers.ModelSerializer):
    documents = ShopDocumentSerializer(many=True, read_only=True)

    class Meta:
        model  = Shop
        fields = (
            "name", "category", "description", "logo", "banner",
            "address", "village", "block", "district", "state",
            "pincode", "latitude", "longitude",
            "gstin", "opening_time", "closing_time",
            "documents",
        )

    def validate(self, attrs):
        request = self.context["request"]
        # One shop per shopkeeper
        if Shop.objects.filter(owner=request.user).exists():
            raise serializers.ValidationError(
                "You already have a registered shop."
            )
        return attrs

    def create(self, validated_data):
        request  = self.context["request"]
        owner    = request.user
        name     = validated_data["name"]
        slug     = generate_shop_slug(name, str(owner.id))
        return Shop.objects.create(
            owner=owner,
            slug=slug,
            **validated_data,
        )


class ShopPublicSerializer(serializers.ModelSerializer):
    """For buyers — limited info."""
    category     = ShopCategorySerializer(read_only=True)
    owner_name   = serializers.CharField(source="owner.full_name", read_only=True)

    class Meta:
        model  = Shop
        fields = (
            "id", "name", "slug", "category", "owner_name",
            "description", "logo", "banner",
            "address", "village", "latitude", "longitude",
            "is_open", "average_rating", "total_reviews",
            "opening_time", "closing_time",
        )


class ShopOwnerSerializer(serializers.ModelSerializer):
    """For shopkeeper — full info about their own shop."""
    category  = ShopCategorySerializer(read_only=True)
    documents = ShopDocumentSerializer(many=True, read_only=True)

    class Meta:
        model  = Shop
        fields = (
            "id", "name", "slug", "category", "description",
            "logo", "banner", "address", "village", "block",
            "district", "state", "pincode", "latitude", "longitude",
            "status", "rejection_reason", "is_open",
            "gstin", "opening_time", "closing_time",
            "total_orders", "total_earnings",
            "average_rating", "total_reviews",
            "approved_at", "created_at", "documents",
        )
        read_only_fields = (
            "id", "slug", "status", "rejection_reason",
            "total_orders", "total_earnings",
            "average_rating", "total_reviews",
            "approved_at", "created_at",
        )


class ShopUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Shop
        fields = (
            "description", "logo", "banner",
            "address", "latitude", "longitude",
            "gstin", "opening_time", "closing_time", "is_open",
        )


class ShopAdminSerializer(serializers.ModelSerializer):
    """For admin — everything."""
    owner    = PublicUserSerializer(read_only=True)
    category = ShopCategorySerializer(read_only=True)

    class Meta:
        model  = Shop
        fields = "__all__"


class ShopApproveSerializer(serializers.Serializer):
    action           = serializers.ChoiceField(choices=["approve", "reject"])
    rejection_reason = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        if attrs["action"] == "reject" and not attrs.get("rejection_reason"):
            raise serializers.ValidationError(
                {"rejection_reason": "Rejection reason is required when rejecting a shop."}
            )
        return attrs