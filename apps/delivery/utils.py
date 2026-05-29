from apps.shops.utils import haversine_distance_km


def find_nearest_delivery_boy(shop_lat: float, shop_lon: float):
    """
    Find nearest available delivery boy to the shop.
    Returns User instance or None.
    """
    from apps.users.models import User
    from .models import DeliveryBoyProfile

    available = DeliveryBoyProfile.objects.filter(
        availability=DeliveryBoyProfile.AvailabilityStatus.AVAILABLE,
        is_verified=True,
        current_lat__isnull=False,
        current_lon__isnull=False,
    ).select_related("user")

    if not available.exists():
        return None

    nearest      = None
    min_distance = float("inf")

    for profile in available:
        dist = haversine_distance_km(
            shop_lat, shop_lon,
            float(profile.current_lat),
            float(profile.current_lon),
        )
        if dist < min_distance:
            min_distance = dist
            nearest      = profile.user

    return nearest