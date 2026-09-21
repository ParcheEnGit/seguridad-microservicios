from google.auth.exceptions import TransportError
from google.auth.transport import requests
from google.oauth2 import id_token

from app.core.config import Settings


class GoogleTokenVerificationError(Exception):
    pass


def verify_google_id_token(token: str, settings: Settings) -> dict:
    """Cryptographically verify a Google ID token against the configured client ID."""
    try:
        id_info = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            settings.google_client_id,
        )
    except TransportError as exc:
        raise GoogleTokenVerificationError(
            "Cannot reach Google to verify the token"
        ) from exc
    except ValueError as exc:
        raise GoogleTokenVerificationError("Invalid Google token") from exc

    if id_info.get("iss") not in {"accounts.google.com", "https://accounts.google.com"}:
        raise GoogleTokenVerificationError("Unexpected token issuer")

    if id_info.get("email_verified") is not True:
        raise GoogleTokenVerificationError("Google token email is not verified")

    google_id = id_info.get("sub")
    email = id_info.get("email")
    name = id_info.get("name") or email

    if not google_id or not email:
        raise GoogleTokenVerificationError("Google token is missing required claims")

    return {
        "google_id": google_id,
        "email": email,
        "name": name,
        "picture_url": id_info.get("picture"),
    }
