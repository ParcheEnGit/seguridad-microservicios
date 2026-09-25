from datetime import UTC, datetime, timedelta

import jwt

from app.core.config import Settings
from app.db.models import User


class JwtValidationError(Exception):
    pass


def create_session_token(user: User, settings: Settings) -> str:
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "name": user.name,
        "google_id": user.google_id,
        "role": user.role,
        "exp": expires_at,
        "iat": datetime.now(UTC),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_session_token(token: str, settings: Settings) -> dict:
    try:
        return jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.PyJWTError as exc:
        raise JwtValidationError("Invalid or expired session token") from exc
