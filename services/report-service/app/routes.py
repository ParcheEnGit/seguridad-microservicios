"""Endpoints del report-service para el Dashboard Admin (HU4).

El report-service es el servicio de CONSULTA de LabSentinel: consolida información
de los demás servicios para mostrarla. Por eso solo ejecuta SELECT de solo lectura
sobre los esquemas device_service, telemetry_service y alert_ticket_service.
Nunca inserta, actualiza ni borra datos que pertenecen a otros servicios.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import AdminSummary
from app.security import require_admin

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

RECENT_ALERTS_LIMIT = 3

DEVICE_COUNTS_SQL = text("""
    SELECT COUNT(*)                                         AS total,
           COUNT(*) FILTER (WHERE status = 'activo')        AS activo,
           COUNT(*) FILTER (WHERE status = 'inactivo')      AS inactivo,
           COUNT(*) FILTER (WHERE status = 'mantenimiento') AS mantenimiento
    FROM device_service.devices
""")

ALERT_COUNTS_SQL = text("""
    SELECT COUNT(*) FILTER (WHERE status IN ('abierta', 'revisada'))                         AS active,
           COUNT(*) FILTER (WHERE status = 'abierta')                                        AS pending_review,
           COUNT(*) FILTER (WHERE status IN ('abierta', 'revisada') AND severity = 'critica') AS critical
    FROM alert_ticket_service.alerts
""")

TICKET_COUNTS_SQL = text("""
    SELECT COUNT(*) FILTER (WHERE status IN ('abierto', 'en_revision'))         AS open,
           COUNT(*) FILTER (WHERE created_at >= date_trunc('day', NOW()))       AS created_today
    FROM alert_ticket_service.tickets
""")

READING_STATS_SQL = text("""
    SELECT COUNT(*) FILTER (WHERE recorded_at >= date_trunc('day', NOW())) AS today,
           MAX(received_at)                                                AS last_received_at
    FROM telemetry_service.readings
""")

RECENT_ALERTS_SQL = text("""
    SELECT a.id, d.name AS device_name, d.device_code, a.metric_code, a.value, a.unit,
           a.threshold_min, a.threshold_max, a.severity, a.status, a.created_at
    FROM alert_ticket_service.alerts a
    LEFT JOIN device_service.devices d ON d.id = a.device_id
    WHERE a.status IN ('abierta', 'revisada')
    ORDER BY a.created_at DESC
    LIMIT :limit
""")

CHART_24H_SQL = text("""
    SELECT date_trunc('hour', recorded_at)                                    AS hour,
           AVG(value) FILTER (WHERE metric_code = 'temperatura')::float       AS temperatura,
           AVG(value) FILTER (WHERE metric_code = 'humedad')::float           AS humedad
    FROM telemetry_service.readings
    WHERE recorded_at >= NOW() - INTERVAL '24 hours'
      AND metric_code IN ('temperatura', 'humedad')
    GROUP BY 1
    ORDER BY 1
""")


@router.get("/admin-summary", response_model=AdminSummary, summary="Resumen operativo del Dashboard Admin")
def admin_summary(db: Session = Depends(get_db), _: dict = Depends(require_admin)) -> AdminSummary:
    return AdminSummary(
        devices=dict(db.execute(DEVICE_COUNTS_SQL).mappings().one()),
        alerts=dict(db.execute(ALERT_COUNTS_SQL).mappings().one()),
        tickets=dict(db.execute(TICKET_COUNTS_SQL).mappings().one()),
        readings=dict(db.execute(READING_STATS_SQL).mappings().one()),
        recent_alerts=[dict(row) for row in db.execute(RECENT_ALERTS_SQL, {"limit": RECENT_ALERTS_LIMIT}).mappings()],
        chart_24h=[dict(row) for row in db.execute(CHART_24H_SQL).mappings()],
        generated_at=datetime.now(timezone.utc),
    )
