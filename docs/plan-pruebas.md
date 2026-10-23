# Plan de pruebas experimentales

Registrar fecha, commit, entorno, entrada, esperado, obtenido y evidencia en [evidencias-demostracion.md](evidencias-demostracion.md).

## Cómo ejecutar

| Tipo | Comando |
|---|---|
| Unitarias / API (pytest + HTTPX) | Ver [tests/README.md](../tests/README.md) — un contenedor por servicio |
| Carga (k6) | `k6 run tests/performance/labsentinel-smoke.js` con Compose arriba |
| Manual / demo | [checklist-demostracion.md](checklist-demostracion.md) |

## Matriz mínima

| Categoría | Caso mínimo | Resultado esperado | Evidencia |
| --- | --- | --- | --- |
| Funcional | Login Google como admin o lector | Cookie de sesión y UI según rol | Captura + `/api/auth/me` |
| Seguridad | Credencial ausente, alterada o vencida | 401 | pytest + curl sin cookie |
| Seguridad | Lector crea dispositivo / cierra alerta / admin-summary | 403 | pytest device, alerts, reports |
| Seguridad | Lector consulta inventario e historial | 200 | pytest |
| Funcional | Lectura fuera de umbral genera alerta sin duplicar | Alerta activa única | pytest telemetry + UI Alertas |
| Funcional | Ticket del lector con trazabilidad | 201 + historial “abierto” | pytest tickets |
| Rendimiento | k6 smoke 5 VUs / 30 s sobre `/health` | Fallos &lt; 1%, p95 &lt; 800 ms | salida k6 |
| Escalabilidad | Subir `VUS` a 10–50 si el equipo lo permite | Degradación documentada | tabla en evidencias |

## Interpretación

No presentar solo tablas: indicar condiciones (Docker Desktop, CPU disponible, SMTP desactivado) y si algún umbral de k6 se incumplió por el entorno local.
