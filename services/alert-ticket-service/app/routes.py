from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.security import get_current_claims

router = APIRouter(tags=["alertas"])

ALERTS_SQL = text("""
    SELECT
        a.id,
        a.metric_code AS type,
        a.severity,
        a.status,
        d.name AS "deviceName",
        a.created_at AS date
    FROM alert_ticket_service.alerts a
    LEFT JOIN device_service.devices d
        ON d.id = a.device_id
    WHERE a.status IN ('abierta', 'revisada')
    ORDER BY a.created_at DESC
""")


@router.get("/alerts", summary="Listar alertas activas")
def list_alerts(
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_claims),
) -> list[dict]:
    rows = db.execute(ALERTS_SQL).mappings().all()
    return [dict(row) for row in rows]