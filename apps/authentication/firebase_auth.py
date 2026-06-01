import logging
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
from django.conf import settings

logger = logging.getLogger("apps")

# Firebase app initialize — sirf ek baar
_firebase_app = None


def get_firebase_app():
    global _firebase_app
    if _firebase_app is None:
        try:
            cred = credentials.Certificate(
                settings.FIREBASE_CREDENTIALS_PATH
            )
            _firebase_app = firebase_admin.initialize_app(cred)
            logger.info("Firebase initialized successfully")
        except Exception as e:
            logger.error(f"Firebase init failed: {e}")
            return None
    return _firebase_app


def verify_firebase_phone_token(id_token: str) -> dict | None:
    """
    Firebase ID Token verify karo.
    Returns phone number ya None.
    """
    try:
        get_firebase_app()
        decoded = firebase_auth.verify_id_token(id_token)

        phone = decoded.get("phone_number")
        uid   = decoded.get("uid")

        if not phone:
            logger.warning("Firebase token mein phone number nahi hai")
            return None

        return {
            "phone":    phone,
            "uid":      uid,
            "firebase_uid": uid,
        }

    except firebase_auth.ExpiredIdTokenError:
        logger.warning("Firebase token expired")
        return None
    except firebase_auth.InvalidIdTokenError:
        logger.warning("Firebase token invalid")
        return None
    except Exception as e:
        logger.error(f"Firebase verify failed: {e}")
        return None
