
"""Consultas de solo lectura para los reportes administrativos de LabSentinel."""

from sqlalchemy import text



# Indicadores generales de dispositivos registrados en el período.
DEVICE_REPORT_SUMMARY_SQL = text("""
    SELECT
        COUNT(*) AS total,
        COUNT(*) FILTER (WHERE status = 'activo') AS activos,
        COUNT(*) FILTER (WHERE status = 'inactivo') AS inactivos,
        COUNT(*) FILTER (WHERE status = 'mantenimiento') AS mantenimiento
    FROM device_service.devices
    WHERE created_at >= :start_date
      AND created_at < :end_date
      AND (:device_id IS NULL OR id = CAST(:device_id AS uuid))
      AND (:device_status IS NULL OR status = :device_status)
""")


# Información detallada de los dispositivos.
DEVICE_REPORT_DETAILS_SQL = text("""
    SELECT
        id,
        device_code,
        name,
        device_type,
        location,
        status,
        created_at
    FROM device_service.devices
    WHERE created_at >= :start_date
      AND created_at < :end_date
      AND (:device_id IS NULL OR id = CAST(:device_id AS uuid))
      AND (:device_status IS NULL OR status = :device_status)
    ORDER BY created_at DESC, id
""")


# Cantidad de dispositivos registrados por día.
DEVICE_REPORT_TIMELINE_SQL = text("""
    SELECT
        DATE(created_at AT TIME ZONE 'UTC') AS day,
        COUNT(*) AS total
    FROM device_service.devices
    WHERE created_at >= :start_date
      AND created_at < :end_date
      AND (:device_id IS NULL OR id = CAST(:device_id AS uuid))
      AND (:device_status IS NULL OR status = :device_status)
    GROUP BY 1
    ORDER BY 1
""")

# HU11: Indicadores generales de alertas por período.
ALERT_REPORT_SUMMARY_SQL = text("""
    SELECT
        COUNT(*) AS total,
        COUNT(*) FILTER (WHERE severity = 'critica') AS criticas,
        COUNT(*) FILTER (WHERE severity = 'advertencia') AS advertencias,
        COUNT(*) FILTER (WHERE status = 'abierta') AS abiertas,
        COUNT(*) FILTER (WHERE status = 'revisada') AS revisadas,
        COUNT(*) FILTER (WHERE status = 'cerrada') AS cerradas
    FROM alert_ticket_service.alerts
    WHERE created_at >= :start_date
      AND created_at < :end_date
      AND (:device_id IS NULL OR device_id = CAST(:device_id AS uuid))
      AND (:severity IS NULL OR severity = :severity)
      AND (:alert_status IS NULL OR status = :alert_status)
""")


# HU11: Tabla detallada de alertas.
ALERT_REPORT_DETAILS_SQL = text("""
    SELECT
        a.id,
        a.device_id,
        d.device_code,
        d.name AS device_name,
        a.metric_code,
        a.value,
        a.unit,
        a.severity,
        a.status,
        a.created_at,
        a.reviewed_at,
        a.resolved_at
    FROM alert_ticket_service.alerts AS a
    LEFT JOIN device_service.devices AS d
        ON d.id = a.device_id
    WHERE a.created_at >= :start_date
      AND a.created_at < :end_date
      AND (:device_id IS NULL OR a.device_id = CAST(:device_id AS uuid))
      AND (:severity IS NULL OR a.severity = :severity)
      AND (:alert_status IS NULL OR a.status = :alert_status)
    ORDER BY a.created_at DESC, a.id
""")


# HU11: Evolución diaria de alertas por severidad.
ALERT_REPORT_TIMELINE_SQL = text("""
    SELECT
        DATE(created_at AT TIME ZONE 'UTC') AS day,
        COUNT(*) AS total,
        COUNT(*) FILTER (WHERE severity = 'critica') AS criticas,
        COUNT(*) FILTER (WHERE severity = 'advertencia') AS advertencias
    FROM alert_ticket_service.alerts
    WHERE created_at >= :start_date
      AND created_at < :end_date
      AND (:device_id IS NULL OR device_id = CAST(:device_id AS uuid))
      AND (:severity IS NULL OR severity = :severity)
      AND (:alert_status IS NULL OR status = :alert_status)
    GROUP BY 1
    ORDER BY 1
""")
