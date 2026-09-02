# Plan de pruebas experimentales

Los resultados se completarán después de implementar. Registrar fecha, versión/commit, entorno, datos de entrada, resultado esperado, resultado obtenido y evidencia.

| Categoría | Caso mínimo | Resultado esperado | Métrica/evidencia |
| --- | --- | --- | --- |
| Funcional | Inicio de sesión con usuario válido | Se obtiene credencial válida | Código HTTP, respuesta y captura/log |
| Seguridad | Credencial ausente, alterada o vencida | Acceso rechazado | Código HTTP y registro sin secretos |
| Seguridad | Usuario sin rol/permiso suficiente | Acceso denegado | Código HTTP y política aplicada |
| Seguridad | Usuario autorizado | Acceso permitido solo al recurso asignado | Respuesta y trazabilidad |
| Rendimiento | Carga gradual de solicitudes autenticadas | Medir degradación controlada | Latencia, throughput, errores, CPU y RAM |
| Escalabilidad | Incrementar usuarios virtuales (10 → 50 → 100 → 500, si el entorno lo permite) | Identificar límite y comportamiento | Tabla, gráfico e interpretación |
| Comunicación | Indisponibilidad simulada de identidad o recurso | Fallo controlado sin fuga de acceso | Código de error, tiempo y logs |

No presentar solo tablas: el informe debe interpretar los datos, condiciones de prueba y limitaciones del entorno.
