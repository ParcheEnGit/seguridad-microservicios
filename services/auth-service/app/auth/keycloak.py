"""Cliente OIDC de Keycloak para el flujo Authorization Code con PKCE."""
import base64
import hashlib
import secrets
from urllib.parse import urlencode

import jwt
import requests

from app.core.config import Settings
from app.core.roles import ROLE_ADMIN, ROLE_USER


class KeycloakAuthenticationError(Exception):
    """Error seguro para presentar al usuario sin filtrar detalles del proveedor."""


def create_pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


def create_state() -> str:
    return secrets.token_urlsafe(32)


def authorization_url(settings: Settings, *, state: str, challenge: str) -> str:
    query = urlencode({
        "client_id": settings.keycloak_client_id,
        "redirect_uri": settings.keycloak_redirect_uri,
        "response_type": "code",
        "scope": "openid profile email",
        # Evita reutilizar de forma silenciosa una sesión SSO de Keycloak que
        # podría pertenecer a una cuenta sin rol en LabSentinel. El usuario
        # puede escoger explícitamente la identidad autorizada.
        "prompt": "login",
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    })
    return f"{settings.keycloak_issuer}/protocol/openid-connect/auth?{query}"


def exchange_code(settings: Settings, *, code: str, verifier: str) -> dict:
    try:
        response = requests.post(
            f"{settings.keycloak_internal_realm_url}/protocol/openid-connect/token",
            data={
                "grant_type": "authorization_code",
                "client_id": settings.keycloak_client_id,
                "code": code,
                "redirect_uri": settings.keycloak_redirect_uri,
                "code_verifier": verifier,
            },
            timeout=10,
        )
    except requests.RequestException as exc:
        raise KeycloakAuthenticationError("No se pudo conectar con Keycloak") from exc
    if not response.ok:
        raise KeycloakAuthenticationError("Keycloak no aceptó el inicio de sesión")
    token_set = response.json()
    if not isinstance(token_set.get("id_token"), str):
        raise KeycloakAuthenticationError("Keycloak no devolvió una identidad válida")
    return token_set


def verify_id_token(settings: Settings, id_token: str) -> dict:
    try:
        jwk_client = jwt.PyJWKClient(f"{settings.keycloak_internal_realm_url}/protocol/openid-connect/certs")
        signing_key = jwk_client.get_signing_key_from_jwt(id_token)
        return jwt.decode(
            id_token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.keycloak_client_id,
            issuer=settings.keycloak_issuer,
            options={"require": ["exp", "iat", "sub"]},
        )
    except jwt.PyJWTError as exc:
        raise KeycloakAuthenticationError("La identidad de Keycloak no es válida") from exc


def profile_from_claims(claims: dict) -> dict:
    subject = claims.get("sub")
    email = claims.get("email")
    roles = set((claims.get("realm_access") or {}).get("roles") or [])
    if not subject or not isinstance(email, str) or not email.strip():
        raise KeycloakAuthenticationError("Keycloak no proporcionó el correo requerido")
    if "admin" in roles:
        role = ROLE_ADMIN
    elif "lector" in roles:
        role = ROLE_USER
    else:
        raise KeycloakAuthenticationError("La cuenta no tiene un rol autorizado en Keycloak")
    return {
        "keycloak_id": str(subject),
        "email": email.strip().lower(),
        "name": str(claims.get("name") or claims.get("preferred_username") or email).strip(),
        "role": role,
        "picture_url": None,
    }


def logout_url(settings: Settings) -> str:
    query = urlencode({
        "client_id": settings.keycloak_client_id,
        "post_logout_redirect_uri": settings.keycloak_frontend_url,
    })
    return f"{settings.keycloak_issuer}/protocol/openid-connect/logout?{query}"
