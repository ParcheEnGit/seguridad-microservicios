# Casos de seguridad (índice HU12)

Los casos automatizados viven en cada servicio. Esta tabla resume qué verificar en demo o CI.

| Caso | Esperado | Dónde se prueba |
|---|---|---|
| Sin cookie de sesión | 401 | device, telemetry history, alerts, tickets, reports |
| Cookie alterada / otra clave | 401 | mismos servicios |
| Lector crea dispositivo / cierra alerta / admin-summary | 403 | `device-service`, `alert-ticket-service`, `report-service` |
| Lector lista dispositivos / historial / alertas | 200 | device list, telemetry history, alerts list |
| Lector crea ticket propio; no ve ajenos | 201 / 404 | `test_ticket_traceability.py` |
| Simulador sin `X-Simulator-Key` | 401 | `test_reading_validation.py` |
| Transición ilegal de alerta | 409 | `test_alert_management.py` |
