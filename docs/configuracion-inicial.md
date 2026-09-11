# Configuración inicial

## Prerrequisitos

- Git.
- Docker Desktop con Compose v2.
- Node.js 22 LTS o superior para ejecutar React fuera de Docker.
- Python 3.11+ solo si se ejecutarán los servicios fuera de Docker.

## Preparación local

```powershell
Copy-Item .env.example .env
docker compose up --build
```

El primer inicio descarga imágenes y puede tardar varios minutos. PostgreSQL crea las bases `labsentinel` y `keycloak` solo al inicializar un volumen vacío. Si se cambia `KEYCLOAK_DB` después del primer arranque, habrá que recrear deliberadamente el volumen de desarrollo. PostgreSQL 18 usa el volumen en `/var/lib/postgresql`, configuración ya aplicada en `compose.yaml`.

## URLs iniciales

| Recurso | URL |
| --- | --- |
| LabSentinel mediante gateway | `http://localhost:8080` |
| Frontend Vite directo | `http://localhost:5173` |
| Keycloak | `http://localhost:8081` |
| Device health | `http://localhost:8080/api/devices/health` |
| Telemetry health | `http://localhost:8080/api/telemetry/health` |
| Alert/ticket health | `http://localhost:8080/api/alerts-tickets/health` |
| Report health | `http://localhost:8080/api/reports/health` |

## Realm y roles

El realm `labsentinel` se importa automáticamente al iniciar Keycloak. Ingrese con `KEYCLOAK_ADMIN` y la contraseña de `.env`; después cree los usuarios de prueba. A cada usuario humano asígnele exactamente uno de los roles de realm: `admin` o `lector`.

El cliente `labsentinel-web` está preparado para el frontend local. El cliente `labsentinel-simulator` queda creado para la futura identidad técnica del simulador. Genere y guarde su secreto exclusivamente en `.env` cuando se implemente el envío de lecturas.

## Comandos útiles

```powershell
docker compose ps
docker compose logs -f gateway
docker compose logs -f keycloak
docker compose down
docker compose --profile simulator up --build
```

## Estado de la base

Los cuatro servicios FastAPI responden `/health`; aún no implementan endpoints de dominio ni persistencia. Esta decisión evita introducir datos, permisos o contratos incoherentes antes de acordarlos en el sprint. El orden recomendado es: contratos OpenAPI, autenticación por API, migraciones, endpoints, interfaz y pruebas.
