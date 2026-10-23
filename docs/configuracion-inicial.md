# Configuración inicial y guía de arranque

## Prerrequisitos

- Git.
- Docker Desktop con Compose v2.
- (Opcional) Node.js 22+ si ejecuta el frontend fuera de Docker.
- (Opcional) k6 si va a correr el escenario de carga: https://k6.io/docs/get-started/installation/
- Cuenta Google Cloud con un OAuth Client ID de tipo “Web application” y orígenes autorizados:
  - `http://localhost:8080`
  - `http://localhost:5173`

## Preparación

```powershell
cd ruta\al\seguridad-microservicios
Copy-Item .env.example .env
```

Edite `.env` y defina al menos:

| Variable | Ejemplo / nota |
|---|---|
| `POSTGRES_PASSWORD` | Contraseña local (debe coincidir con el volumen de Postgres; si cambia tras el primer arranque, use `docker compose down -v`) |
| `KEYCLOAK_DB_PASSWORD` | Misma contraseña de Postgres si Keycloak usa el mismo usuario |
| `GOOGLE_CLIENT_ID` | Client ID de Google |
| `VITE_GOOGLE_CLIENT_ID` | El mismo Client ID |
| `JWT_SECRET` | Cadena ≥ 32 caracteres |
| `ADMIN_EMAILS` | Su correo de Google (solo primer alta) |
| `SIMULATOR_API_KEY` | Clave larga aleatoria |
| `SIMULATOR_ENABLED` | `true` para alimentar dashboards |
| `CORS_ORIGINS` | `http://localhost:8080,http://localhost:5173` |

## Inicio de sesión opcional con Keycloak

Google y el login local continúan funcionando sin cambios cuando `KEYCLOAK_ENABLED=false`.
Para habilitar Keycloak en desarrollo, configure en `.env`:

```dotenv
KEYCLOAK_ENABLED=true
VITE_KEYCLOAK_ENABLED=true
KEYCLOAK_URL_PUBLIC=http://localhost:8081
KEYCLOAK_URL_INTERNAL=http://keycloak:8080
KEYCLOAK_REALM=labsentinel
KEYCLOAK_CLIENT_ID=labsentinel-web
KEYCLOAK_REDIRECT_URI=http://localhost:8080/api/auth/keycloak/callback
KEYCLOAK_FRONTEND_URL=http://localhost:8080/
```

El realm incluido usa un cliente **público** con Authorization Code + PKCE S256:
no configure ni suba un `client_secret` para el frontend. Cree los usuarios desde la
consola de Keycloak y asígneles el rol de realm `admin` o `lector`; el callback valida
firma RS256, emisor, audiencia, expiración y rol antes de crear la sesión HttpOnly de
LabSentinel. La identidad se enlaza por el `sub` de Keycloak y por correo solo en el
primer vínculo, evitando sustituir identidades existentes.

`start-dev --import-realm` importa el archivo únicamente cuando el realm no existe.
Si Keycloak ya se inició antes, replique los cambios del cliente en la consola (redirect
URI exacta, PKCE S256 y Direct Access Grants deshabilitado) o recree solamente el entorno
local según el procedimiento acordado por el equipo. Nunca use `down -v` en un entorno
con datos que deban conservarse.

## Arranque

```powershell
docker compose up --build
```

En segundo plano: `docker compose up --build -d`.

Espere a que `postgres`, `auth-service` y `telemetry-service` estén healthy. El primer inicio puede tardar varios minutos.

## URLs

| Recurso | URL |
| --- | --- |
| LabSentinel (gateway) | `http://localhost:8080` |
| Frontend Vite directo | `http://localhost:5173` |
| Keycloak (opcional) | `http://localhost:8081` |
| Postgres en el host | `localhost:5433` (usuario/DB `labsentinel`) |
| Device health | `http://localhost:8080/api/devices/health` |
| Telemetry health | `http://localhost:8080/api/telemetry/health` |
| Alert/ticket health | `http://localhost:8080/api/alerts-tickets/health` |
| Report health | `http://localhost:8080/api/reports/health` |
| Sesión actual | `http://localhost:8080/api/auth/me` |
| OpenAPI telemetría | `http://localhost:8080/api/telemetry/docs` |

## Roles

| Valor en BD / JWT | Rol |
|---|---|
| `0` | Administrador |
| `1` | Lector |

Tras el primer login, el rol se conserva en BD. Para promover un usuario ya creado:

```powershell
docker compose exec postgres psql -U labsentinel -d labsentinel -c "UPDATE users SET role = 0 WHERE email = 'tu-correo@gmail.com';"
```

Cierre sesión y vuelva a entrar para renovar la cookie.

## Simulador

Con `SIMULATOR_ENABLED=true`, el servicio `simulator-device` envía lecturas a dispositivos `activo` cada `SIMULATOR_INTERVAL_SECONDS` (mínimo 5).

```powershell
docker compose logs -f simulator-device
```

Picos de demostración (solo admin): `http://localhost:8080/peak`.

## Comandos útiles

```powershell
docker compose ps
docker compose logs -f gateway
docker compose logs -f auth-service
docker compose down
docker compose down -v
```

`down -v` borra el volumen de Postgres (datos locales).

## Pruebas y carga

Ver [tests/README.md](../tests/README.md), [plan-pruebas.md](plan-pruebas.md) y [checklist-demostracion.md](checklist-demostracion.md).
