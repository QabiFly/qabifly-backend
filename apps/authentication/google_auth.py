import logging
import httpx
from django.conf import settings

logger = logging.getLogger("apps")


def verify_google_token(token: str) -> dict | None:
    """
    Google token verify karo.
    Dono formats handle karta hai:
    1. ID Token (Flutter/Android se)
    2. Access Token (NextJS Web se)
    """
    # Pehle Access Token try karo (NextJS web se aata hai)
    result = _verify_access_token(token)
    if result:
        return result

    # Phir ID Token try karo (Flutter se aata hai)
    result = _verify_id_token(token)
    return result


def _verify_access_token(access_token: str) -> dict | None:
    """
    Google UserInfo endpoint se verify karo.
    NextJS web app yeh use karta hai.
    """
    try:
        response = httpx.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        if response.status_code != 200:
            return None

        data = response.json()

        if "sub" not in data:
            return None

        return {
            "google_id": data["sub"],
            "email":     data.get("email", ""),
            "name":      data.get("name", ""),
            "picture":   data.get("picture", ""),
            "verified":  data.get("email_verified", False),
        }
    except Exception as e:
        logger.error(f"Google access token verify failed: {e}")
        return None


def _verify_id_token(id_token: str) -> dict | None:
    """
    Google ID Token verify karo.
    Flutter/Android app yeh use karta hai.
    """
    try:
        from google.oauth2 import id_token as google_id_token
        from google.auth.transport import requests as google_requests

        idinfo = google_id_token.verify_oauth2_token(
            id_token,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )

        if idinfo["iss"] not in (
            "accounts.google.com",
            "https://accounts.google.com",
        ):
            return None

        return {
            "google_id": idinfo["sub"],
            "email":     idinfo.get("email", ""),
            "name":      idinfo.get("name", ""),
            "picture":   idinfo.get("picture", ""),
            "verified":  idinfo.get("email_verified", False),
        }
    except Exception as e:
        logger.error(f"Google ID token verify failed: {e}")
        return None