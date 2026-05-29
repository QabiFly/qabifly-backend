from pymongo import MongoClient
from django.conf import settings

_client = None


def get_mongo_client() -> MongoClient:
    """Return a singleton MongoClient instance."""
    global _client
    if _client is None:
        mongo_cfg = settings.MONGODB
        uri = (
            f"mongodb://{mongo_cfg['USER']}:{mongo_cfg['PASSWORD']}"
            f"@{mongo_cfg['HOST']}:{mongo_cfg['PORT']}/{mongo_cfg['DB_NAME']}"
            f"?authSource=admin"
        )
        _client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    return _client


def get_mongo_db():
    """Return the primary QabiFly MongoDB database."""
    client = get_mongo_client()
    return client[settings.MONGODB["DB_NAME"]]