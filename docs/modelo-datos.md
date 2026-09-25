# Modelo de datos de LabSentinel

La base utiliza PostgreSQL con un esquema por servicio dentro de la misma instancia local. Es una solución que facilita la ejecución con Docker Compose y mantiene delimitada la propiedad de datos:

| Esquema | Propietario | Datos |
|---|---|---|
| `public` | `auth-service` actual | Tabla existente `users`; no se modifica por la migración de dominio. |
| `device_service` | `device-service` | Dispositivos y umbrales. |
| `telemetry_service` | `telemetry-service` | Lecturas inmutables de métricas. |
| `alert_ticket_service` | `alert-ticket-service` | Alertas, tickets, comentarios e historial de estados. |
| `report_service` | `report-service` | Snapshots de reportes y eventos de auditoría. |

## Decisiones de diseño

- `public.users` se conserva por compatibilidad con el login que existe en la rama. Los campos `*_user_id` son referencias lógicas a `public.users.id`; no tienen una FK física porque la identidad es propiedad de `auth-service`.
- Las relaciones entre servicios, como una lectura y un dispositivo, se guardan como UUID sin FK entre esquemas. Cada servicio valida la existencia mediante API o contrato, evitando acoplar la disponibilidad de una base de otro servicio.
- La telemetría usa `metric_code`, `value` y `unit` en lugar de columnas fijas de temperatura/humedad. Esto permite ampliar métricas sin migrar la tabla.
- Las alertas conservan una copia de los umbrales que las generaron y evitan duplicar alertas activas por dispositivo y métrica.
- Tickets y alertas no se eliminan al desactivar un dispositivo; son evidencia histórica.
- `ticket_status_history` satisface la trazabilidad solicitada en HU-10: conserva estado anterior, nuevo estado, autor, nota y fecha de cada transición.

## Aplicación de la migración

`infra/postgres/migrations/001_labsentinel_domain_schema.sql` es idempotente: puede ejecutarse más de una vez sin borrar tablas ni datos. Docker Compose ejecuta el contenedor `database-migrations` después de que PostgreSQL está saludable.

Para comprobar las tablas:

```powershell
docker compose exec postgres psql -U labsentinel -d labsentinel -c "\\dn"
docker compose exec postgres psql -U labsentinel -d labsentinel -c "\\dt device_service.*"
```

No se debe editar una migración ya aplicada en un entorno compartido. Las evoluciones posteriores se agregan como archivos numerados nuevos.

## Implementación de HU5

`device-service` es propietario del CRUD de `device_service.devices` y `device_service.thresholds`. Sus endpoints se exponen mediante el gateway bajo `/api/devices`:

| Método | Ruta | Acceso | Finalidad |
|---|---|---|---|
| `GET` | `/devices` | Admin y lector | Lista con filtros, paginación y umbrales. |
| `GET` | `/devices/{id}` | Admin y lector | Detalle y umbrales de un dispositivo. |
| `POST` | `/devices` | Admin | Registro con umbrales iniciales. |
| `PATCH` | `/devices/{id}` | Admin | Edición de datos del inventario. |
| `PATCH` | `/devices/{id}/deactivate` | Admin | Desactivación lógica; no elimina historial. |
| `PUT` | `/devices/{id}/thresholds` | Admin | Reemplazo validado de los umbrales. |

El servicio valida la misma cookie de sesión JWT emitida por `auth-service`. Las operaciones de escritura requieren el claim de rol `admin`; las consultas son accesibles al lector para su Dashboard Lector.
