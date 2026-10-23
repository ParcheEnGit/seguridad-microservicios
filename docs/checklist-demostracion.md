# Checklist de demostración final — HU12

Usar este checklist en la presentación. Marcar cada ítem al verificarlo y adjuntar evidencias en [evidencias-demostracion.md](evidencias-demostracion.md).

## A. Arranque reproducible

- [ ] `.env` creado desde `.env.example` (sin secretos reales en el repositorio).
- [ ] `docker compose up --build` completa sin errores de migraciones.
- [ ] `docker compose ps` muestra `postgres`, `auth-service`, `telemetry-service`, `gateway`, `frontend` en estado Up/healthy.
- [ ] `http://localhost:8080` carga el login.
- [ ] Health checks: devices, telemetry, alerts-tickets, reports → `200`.

## B. Dashboard Admin (rol 0)

- [ ] Login con cuenta admin (Google).
- [ ] Sidebar muestra opciones de admin (reportes/usuarios/configuración según menú).
- [ ] Inicio / resumen admin con datos o estado vacío coherente.
- [ ] Registrar o editar un dispositivo y umbrales.
- [ ] Ver telemetría / historial de un dispositivo.
- [ ] En Alertas: filtrar, ver detalle, Revisar y Cerrar (flujo abierta → revisada → cerrada).
- [ ] (Opcional) Forzar pico en `/peak` y observar alerta nueva o escalada.

## C. Dashboard Lector (rol 1)

- [ ] Login con cuenta lector (o misma cuenta con `role = 1`).
- [ ] Puede consultar dispositivos, telemetría y alertas (sin botones de escritura de alertas).
- [ ] Crear ticket en Tickets (campos obligatorios + confirmación).
- [ ] Ver “Mis tickets”; no ve tickets ajenos (404 si se fuerza URL de otro id).
- [ ] Intento de acción admin (p. ej. crear dispositivo o cerrar alerta) → 403 o UI sin acción.

## D. Microservicios protegidos

- [ ] Petición sin cookie a `/api/devices` o `/api/auth/me` → 401.
- [ ] Cookie inválida → 401.
- [ ] Simulador con `X-Simulator-Key` incorrecta en `POST /api/telemetry/readings` → 401.
- [ ] pytest de permisos (device, alertas, tickets, reportes, telemetría) en verde.

## E. Carga k6

- [ ] k6 instalado (`k6 version`).
- [ ] `k6 run tests/performance/labsentinel-smoke.js` con el stack arriba.
- [ ] Umbrales del script cumplidos (o desviación documentada).
- [ ] Resumen de métricas pegado en evidencias.

## F. Cierre

- [ ] Capturas o logs con fecha, URL y rol usado.
- [ ] Limitaciones del entorno anotadas (puerto Postgres, Keycloak opcional, SMTP desactivado, etc.).
- [ ] Commit/tag o SHA del código demostrado registrado en evidencias.
