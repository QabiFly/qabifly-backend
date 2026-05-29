from core.mongo import get_mongo_db
from datetime import datetime, timezone


COLLECTION = "iot_readings"


def save_reading(node_id: str, data: dict) -> str:
    """Save a sensor reading to MongoDB. Returns inserted ID."""
    db  = get_mongo_db()
    doc = {
        "node_id":      node_id,
        "temperature":  data.get("temperature"),   # Celsius
        "humidity":     data.get("humidity"),       # %
        "soil_moisture": data.get("soil_moisture"), # %
        "rainfall":     data.get("rainfall"),       # mm
        "wind_speed":   data.get("wind_speed"),     # km/h
        "uv_index":     data.get("uv_index"),
        "recorded_at":  datetime.now(timezone.utc),
    }
    result = db[COLLECTION].insert_one(doc)
    return str(result.inserted_id)


def get_latest_reading(node_id: str) -> dict | None:
    """Get the most recent reading for a node."""
    db  = get_mongo_db()
    doc = db[COLLECTION].find_one(
        {"node_id": node_id},
        sort=[("recorded_at", -1)],
    )
    if doc:
        doc["_id"] = str(doc["_id"])
        doc["recorded_at"] = doc["recorded_at"].isoformat()
    return doc


def get_readings_last_n_hours(node_id: str, hours: int = 24) -> list:
    """Get readings from last N hours for a node."""
    from datetime import timedelta
    db       = get_mongo_db()
    since    = datetime.now(timezone.utc) - timedelta(hours=hours)
    cursor   = db[COLLECTION].find(
        {"node_id": node_id, "recorded_at": {"$gte": since}},
        sort=[("recorded_at", -1)],
    )
    results = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        doc["recorded_at"] = doc["recorded_at"].isoformat()
        results.append(doc)
    return results