
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
