import math


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two GPS coordinates in kilometers.
    Used for 2km radius shop filtering.
    """
    R = 6371  # Earth radius in km
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )
    return R * 2 * math.asin(math.sqrt(a))


def generate_shop_slug(name: str, owner_id: str) -> str:
    """Generate a unique slug from shop name + partial owner UUID."""
    import re
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    suffix = str(owner_id)[:8]
    return f"{base}-{suffix}"