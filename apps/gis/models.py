import uuid
from django.db import models
from django.conf import settings


class Landmark(models.Model):

    class LandmarkType(models.TextChoices):
        SCHOOL     = "SCHOOL",     "School"
        HOSPITAL   = "HOSPITAL",   "Hospital"
        MASJID     = "MASJID",     "Masjid"
        MANDIR     = "MANDIR",     "Mandir"
        BAZAAR     = "BAZAAR",     "Bazaar"
        BUS_STOP   = "BUS_STOP",   "Bus Stop"
        PANCHAYAT  = "PANCHAYAT",  "Panchayat Office"
        BANK       = "BANK",       "Bank / ATM"
        SHOP       = "SHOP",       "Shop"
        OTHER      = "OTHER",      "Other"

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name         = models.CharField(max_length=200)
    landmark_type = models.CharField(max_length=20, choices=LandmarkType.choices)
    latitude     = models.DecimalField(max_digits=9, decimal_places=6)
    longitude    = models.DecimalField(max_digits=9, decimal_places=6)
    description  = models.TextField(blank=True)
    village      = models.CharField(max_length=100, default="Reoti")
    is_active    = models.BooleanField(default=True)
    added_by     = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name="landmarks_added"
    )
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "landmarks"
        ordering = ["landmark_type", "name"]

    def __str__(self):
        return f"{self.name} ({self.landmark_type})"


class DeliveryZone(models.Model):
    """
    Circular delivery zones defined by center + radius.
    Shops aur delivery routes iske against check honge.
    """
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name        = models.CharField(max_length=100)
    center_lat  = models.DecimalField(max_digits=9, decimal_places=6)
    center_lon  = models.DecimalField(max_digits=9, decimal_places=6)
    radius_km   = models.DecimalField(max_digits=4, decimal_places=2, default=2.0)
    is_active   = models.BooleanField(default=True)
    color_hex   = models.CharField(max_length=7, default="#3B82F6")  # for map display
    description = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "delivery_zones"

    def __str__(self):
        return f"{self.name} ({self.radius_km}km)"

    def contains_point(self, lat: float, lon: float) -> bool:
        from apps.shops.utils import haversine_distance_km
        dist = haversine_distance_km(
            float(self.center_lat), float(self.center_lon), lat, lon
        )
        return dist <= float(self.radius_km)