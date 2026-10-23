# Evidencias de la demostración final

Completar en la sesión de demo. No pegar secretos, cookies ni tokens completos.

## Metadatos

| Campo | Valor |
|---|---|
| Fecha | |
| Entorno | Docker Compose local / Windows |
| Commit / rama | |
| Participantes | Grupo 36 |
| URL base | `http://localhost:8080` |

## Resultados pytest (pegar salida `pytest -q`)

Ejecución local (Python 3.11) en preparación de la HU12:

```text
device-service          10 passed
report-service           4 passed
alert-ticket-service    38 passed
telemetry-service       49 passed
Total                  101 passed
```

| Servicio | Resultado | Notas |
|---|---|---|
| telemetry-service | 49 passed | lecturas, historial, alertas por umbral |
| alert-ticket-service | 38 passed | alertas + tickets + trazabilidad |
| device-service | 10 passed | permisos admin/lector |
| report-service | 4 passed | admin-summary 401/403 |

## Resultados k6

Comando:

```powershell
k6 run tests/performance/labsentinel-smoke.js
```

| Métrica | Valor observado | Umbral del script |
|---|---|---|
| http_req_failed | | &lt; 1% |
| http_req_duration (p95) | | &lt; 800 ms |
| checks | | 100% |

Pegar extracto del resumen de k6:

```text

```

## Capturas / observaciones

1. Login admin — descripción:
2. Dashboard Admin — descripción:
3. Alertas (revisar/cerrar) — descripción:
4. Login lector + ticket — descripción:
5. 401/403 demostrado — descripción:

## Limitaciones

- 
-
