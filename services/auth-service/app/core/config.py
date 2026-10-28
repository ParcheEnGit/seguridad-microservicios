from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    service_name: str = "auth-service"

    database_url: str = "postgresql+psycopg2://labsentinel:labsentinel@postgres:5432/labsentinel"

    google_client_id: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7

    cors_origins: str = "https://localhost:8080"

    cookie_name: str = "labsentinel_session"
    cookie_secure: bool = False
    cookie_samesite: str = "lax"
    # Solo permite inicializar el primer administrador si public.users está vacía.
    # No concede acceso automático cuando ya existen usuarios autorizados.
    admin_emails: str = ""
    local_password_login_enabled: bool = False

    # Keycloak permanece opcional para no interrumpir los accesos existentes de
    # Google ni el login local de desarrollo. El flujo usa Authorization Code
    # con PKCE; un cliente público no requiere ni debe exponer un secreto.
    keycloak_enabled: bool = False
    keycloak_url_internal: str = "http://keycloak:8080"
    keycloak_url_public: str = "https://localhost:8081"
    keycloak_realm: str = "labsentinel"
    keycloak_client_id: str = "labsentinel-web"
    keycloak_redirect_uri: str = "https://localhost:8080/api/auth/keycloak/callback"
    keycloak_frontend_url: str = "https://localhost:8080/"
    keycloak_state_cookie_name: str = "labsentinel_keycloak_state"
    keycloak_verifier_cookie_name: str = "labsentinel_keycloak_verifier"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def admin_email_set(self) -> set[str]:
        return {
            email.strip().lower()
            for email in self.admin_emails.split(",")
            if email.strip()
        }

    @property
    def keycloak_issuer(self) -> str:
        return f"{self.keycloak_url_public.rstrip('/')}/realms/{self.keycloak_realm}"

    @property
    def keycloak_internal_realm_url(self) -> str:
        return f"{self.keycloak_url_internal.rstrip('/')}/realms/{self.keycloak_realm}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
