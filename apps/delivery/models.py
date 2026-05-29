import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.orders.models import Order
from apps.shops.models import Shop


class DeliveryBoyProfile(models.Model):

    class AvailabilityStatus(models.TextChoices):
        AVAILABLE   = "AVAILABLE",   "Available"
        ON_DELIVERY = "ON_DELIVERY", "On Delivery"
        OFFLINE     = "OFFLINE",     "Offline"

    class VehicleType(models.TextChoices):
        BICYCLE    = "BICYCLE",    "Bicycle"
        MOTORCYCLE = "MOTORCYCLE", "Motorcycle"
        SCOOTER    = "SCOOTER",    "Scooter"
        ON_FOOT    = "ON_FOOT",    "On Foot"

    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user             = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="delivery_profile",
        limit_choices_to={"role": "DELIVERY_BOY"},
    )
    vehicle_type     = models.CharField(
        max_length=20, choices=VehicleType.choices, default=VehicleType.MOTORCYCLE
    )
    vehicle_number   = models.CharField(max_length=20, blank=True)
    availability     = models.CharField(
        max_length=20,
        choices=AvailabilityStatus.choices,
        default=AvailabilityStatus.OFFLINE,
    )

    # Current GPS location
    current_lat      = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    current_lon      = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    last_location_update = models.DateTimeField(null=True, blank=True)

    # Stats
    total_deliveries    = models.IntegerField(default=0)
    successful_deliveries = models.IntegerField(default=0)
    total_earned        = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    average_rating      = models.DecimalField(
        max_digits=3, decimal_places=2, default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    total_ratings       = models.IntegerField(default=0)

    is_verified         = models.BooleanField(default=False)
    created_at          = models.DateTimeField(auto_now_add=True)
    updated_at          = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "delivery_boy_profiles"

    def __str__(self):
        return f"{self.user.full_name} — {self.availability}"

    @property
    def success_rate(self):
        if self.total_deliveries == 0:
            return 0
        return round((self.successful_deliveries / self.total_deliveries) * 100, 1)


class DeliveryAssignment(models.Model):

    class Status(models.TextChoices):
        ASSIGNED  = "ASSIGNED",  "Assigned"
        ACCEPTED  = "ACCEPTED",  "Accepted"
        PICKED    = "PICKED",    "Picked Up"
        DELIVERED = "DELIVERED", "Delivered"
        FAILED    = "FAILED",    "Failed"
        REASSIGNED = "REASSIGNED", "Reassigned"

    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order         = models.OneToOneField(
        Order, on_delete=models.CASCADE, related_name="delivery_assignment"
    )
    delivery_boy  = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True,
        related_name="assignments",
        limit_choices_to={"role": "DELIVERY_BOY"},
    )
    status        = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ASSIGNED
    )

    # Distance & Earning
    distance_km   = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    earning       = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)

    # Timestamps
    assigned_at   = models.DateTimeField(auto_now_add=True)
    accepted_at   = models.DateTimeField(null=True, blank=True)
    picked_at     = models.DateTimeField(null=True, blank=True)
    delivered_at  = models.DateTimeField(null=True, blank=True)

    # Failure
    failure_reason = models.TextField(blank=True)

    # Admin override
    assigned_by_admin = models.BooleanField(default=False)

    class Meta:
        db_table = "delivery_assignments"
        ordering = ["-assigned_at"]

    def __str__(self):
        return f"Assignment #{self.order.order_number} → {self.delivery_boy}"


class LocationLog(models.Model):
    """GPS location history — stored in PostgreSQL for audit."""
    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    delivery_boy  = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="location_logs",
    )
    assignment    = models.ForeignKey(
        DeliveryAssignment, on_delete=models.CASCADE,
        related_name="location_logs",
        null=True, blank=True,
    )
    latitude      = models.DecimalField(max_digits=9, decimal_places=6)
    longitude     = models.DecimalField(max_digits=9, decimal_places=6)
    recorded_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "location_logs"
        ordering = ["-recorded_at"]

    def __str__(self):
        return f"{self.delivery_boy.full_name} @ {self.latitude},{self.longitude}"


class DeliveryRating(models.Model):
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assignment   = models.OneToOneField(
        DeliveryAssignment, on_delete=models.CASCADE, related_name="rating"
    )
    rated_by     = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="delivery_ratings_given"
    )
    rating       = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment      = models.TextField(blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "delivery_ratings"

    def __str__(self):
        return f"Rating {self.rating}★ for {self.assignment}"