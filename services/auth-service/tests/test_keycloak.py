"""Pruebas unitarias del contrato OIDC, sin depender de un Keycloak en ejecución."""
import base64
import hashlib
import unittest
from urllib.parse import parse_qs, urlparse

from app.auth.keycloak import (
    KeycloakAuthenticationError,
    authorization_url,
    create_pkce_pair,
    profile_from_claims,
)
from app.core.config import Settings
from app.core.roles import ROLE_ADMIN, ROLE_USER


class KeycloakContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = Settings(
            google_client_id="test-google-client",
            jwt_secret="test-jwt-secret-at-least-thirty-two-characters",
            keycloak_url_public="http://localhost:8081",
            keycloak_realm="labsentinel",
            keycloak_client_id="labsentinel-web",
            keycloak_redirect_uri="http://localhost:8080/api/auth/keycloak/callback",
        )

    def test_authorization_request_uses_state_and_s256_pkce(self) -> None:
        verifier, challenge = create_pkce_pair()
        url = authorization_url(self.settings, state="state-for-test", challenge=challenge)
        query = parse_qs(urlparse(url).query)

        expected = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode("ascii")).digest()
        ).rstrip(b"=").decode("ascii")
        self.assertEqual(challenge, expected)
        self.assertEqual(query["state"], ["state-for-test"])
        self.assertEqual(query["prompt"], ["login"])
        self.assertEqual(query["code_challenge"], [challenge])
        self.assertEqual(query["code_challenge_method"], ["S256"])
        self.assertEqual(query["redirect_uri"], [self.settings.keycloak_redirect_uri])

    def test_realm_roles_are_mapped_to_labsentinel_roles(self) -> None:
        claims = {
            "sub": "keycloak-subject",
            "email": "ADMIN@labsentinel.bo",
            "name": "Administrador de prueba",
            "realm_access": {"roles": ["lector", "admin"]},
        }
        profile = profile_from_claims(claims)
        self.assertEqual(profile["role"], ROLE_ADMIN)
        self.assertEqual(profile["email"], "admin@labsentinel.bo")

        claims["realm_access"] = {"roles": ["lector"]}
        self.assertEqual(profile_from_claims(claims)["role"], ROLE_USER)

    def test_claims_without_authorized_role_are_rejected(self) -> None:
        with self.assertRaises(KeycloakAuthenticationError):
            profile_from_claims(
                {
                    "sub": "keycloak-subject",
                    "email": "lector@labsentinel.bo",
                    "realm_access": {"roles": ["offline_access"]},
                }
            )


if __name__ == "__main__":
    unittest.main()
