# Selección de tecnologías y protocolos

No seleccionar una tecnología por popularidad. La decisión debe comparar alternativas según seguridad, compatibilidad, facilidad de implementación, reproducibilidad, observabilidad y adecuación al alcance académico.

| Componente | Alternativas a evaluar | Selección | Justificación y evidencia |
| --- | --- | --- | --- |
| Backend de servicios | Node.js, Python/Flask-FastAPI, Java/Spring | Pendiente | Pendiente |
| API Gateway | Framework propio, Nginx, Kong, Spring Cloud Gateway | Pendiente | Pendiente |
| Identidad | JWT propio, OAuth 2.0/OIDC con proveedor, alternativa documentada | Pendiente | Pendiente |
| Autorización | RBAC, permisos/scopes, ABAC simplificado | Pendiente | Pendiente |
| Comunicación | HTTP/REST sobre TLS, otra opción justificada | Pendiente | Pendiente |
| Datos de prueba | En memoria, PostgreSQL, MySQL u otra | Pendiente | Pendiente |
| Contenerización | Docker Compose, ejecución local, otra | Pendiente | Pendiente |
| Pruebas de carga | k6, JMeter, Locust u otra | Pendiente | Pendiente |
| Métricas y logs | Docker stats, Prometheus/Grafana, otra | Pendiente | Pendiente |

## Criterio sugerido para la decisión

Para el alcance actual, prioricen una solución que permita demostrar de manera clara y reproducible autenticación, autorización, rechazo de accesos no válidos y medición de tiempos/recursos. Añadan complejidad (por ejemplo, Kubernetes o un proveedor cloud) únicamente si pueden documentarla y probarla de forma fiable.
