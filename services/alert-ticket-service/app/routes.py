from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import AlertDetailResponse, AlertStatusUpdate, AlertSummary
from app.security import get_current_claims

router = APIRouter(tags=["alertas"])

ALERT_FIELDS_SQL = """
    SELECT
        a.id,
        a.device_id,
        d.name AS device_name,
        d.device_code,
        a.reading_id,
        a.metric_code,
        a.value,
        a.unit,
        a.threshold_min,
        a.threshold_max,
        CASE
            WHEN a.threshold_min IS NOT NULL AND a.value < a.threshold_min
                THEN 'below_min'
            ELSE 'above_max'
        END AS condition,
        a.severity,
        a.status,
        a.created_at,
        a.updated_at,
        a.metric_code AS type,
        d.name AS "deviceName",
        a.created_at AS date
    FROM alert_ticket_service.alerts a
    LEFT JOIN device_service.devices d ON d.id = a.device_id
"""

NEXT_ALERT_STATUS = {
    "abierta": "revisada",
    "revisada": "cerrada",
}

STATUS_UPDATE_SQL = {
    "revisada": """
        UPDATE alert_ticket_service.alerts
        SET status = :status,
            reviewed_by_user_id = :user_id,
            reviewed_at = NOW(),
            updated_at = NOW()
        WHERE id = :alert_id
    """,
    "cerrada": """
        UPDATE alert_ticket_service.alerts
        SET status = :status,
            resolved_by_user_id = :user_id,
            resolved_at = NOW(),
            updated_at = NOW()
        WHERE id = :alert_id
    """,
}


@router.get(
    "/alerts",
    response_model=list[AlertSummary],
    summary="Listar y filtrar alertas",
)
def list_alerts(
    device_id: UUID | None = Query(default=None),
    severity: Literal["advertencia", "critica"] | None = Query(default=None),
    status_filter: Literal["active", "all", "abierta", "revisada", "cerrada"] = Query(
        default="active",
        alias="status",
    ),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_claims),
) -> list[dict]:
    filters: list[str] = []
    params: dict[str, object] = {}

    if device_id is not None:
        filters.append("a.device_id = :device_id")
        params["device_id"] = device_id
    if severity is not None:
        filters.append("a.severity = :severity")
        params["severity"] = severity
    if status_filter == "active":
        filters.append("a.status IN ('abierta', 'revisada')")
    elif status_filter != "all":
        filters.append("a.status = :status")
        params["status"] = status_filter

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    rows = db.execute(
        text(f"{ALERT_FIELDS_SQL} {where_clause} ORDER BY a.created_at DESC"),
        params,
    ).mappings().all()
    return [dict(row) for row in rows]


@router.get(
    "/alerts/{alert_id}",
    response_model=AlertDetailResponse,
    summary="Consultar el detalle de una alerta",
)
def get_alert(
    alert_id: UUID,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_claims),
) -> dict:
    alert = db.execute(
        text(f"{ALERT_FIELDS_SQL} WHERE a.id = :alert_id"),
        {"alert_id": alert_id},
    ).mappings().one_or_none()
    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerta no encontrada",
        )

    reading = db.execute(
        text("""
            SELECT id, metric_code, value, unit, equipment_status, source,
                   recorded_at, received_at, payload
            FROM telemetry_service.readings
            WHERE id = :reading_id
        """),
        {"reading_id": alert["reading_id"]},
    ).mappings().one_or_none()
    if reading is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró la lectura que generó esta alerta",
        )
    return {**dict(alert), "reading": dict(reading)}


@router.patch(
    "/alerts/{alert_id}/status",
    response_model=AlertSummary,
    summary="Actualizar el estado de una alerta",
)
def update_alert_status(
    alert_id: UUID,
    payload: AlertStatusUpdate,
    db: Session = Depends(get_db),
    claims: dict = Depends(get_current_claims),
) -> dict:
    if claims.get("role") != 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo un administrador puede actualizar alertas",
        )
    try:
        user_id = int(claims["sub"])
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="La sesión no contiene un identificador de usuario válido",
        ) from exc

    alert = db.execute(
        text("""
            SELECT status
            FROM alert_ticket_service.alerts
            WHERE id = :alert_id
            FOR UPDATE
        """),
        {"alert_id": alert_id},
    ).mappings().one_or_none()
    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerta no encontrada",
        )
    current_status = alert["status"]
    if current_status == "cerrada" and payload.status != "cerrada":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Una alerta cerrada no puede volver a abrirse",
        )
    if current_status != payload.status and NEXT_ALERT_STATUS.get(current_status) != payload.status:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"No se puede pasar una alerta de '{current_status}' a '{payload.status}'",
        )

    if current_status != payload.status:
        db.execute(
            text(STATUS_UPDATE_SQL[payload.status]),
            {
                "alert_id": alert_id,
                "status": payload.status,
                "user_id": user_id,
            },
        )
        db.commit()

    updated_alert = db.execute(
        text(f"{ALERT_FIELDS_SQL} WHERE a.id = :alert_id"),
        {"alert_id": alert_id},
    ).mappings().one_or_none()
    if updated_alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerta no encontrada",
        )
    return dict(updated_alert)
