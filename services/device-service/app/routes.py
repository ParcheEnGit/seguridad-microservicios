import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models import Device, Threshold
from app.schemas import DeviceCreate, DeviceListResponse, DeviceResponse, DeviceStatusUpdate, DeviceUpdate, ThresholdInput, ThresholdResponse
from app.security import get_current_claims, require_admin

router = APIRouter(prefix="/devices", tags=["dispositivos"])


def get_device_or_404(device_id: uuid.UUID, db: Session) -> Device:
    statement = select(Device).options(selectinload(Device.thresholds)).where(Device.id == device_id)
    device = db.scalar(statement)
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispositivo no encontrado")
    return device


@router.get("", response_model=DeviceListResponse, summary="Listar dispositivos")
def list_devices(
    status_filter: str | None = Query(default=None, alias="status"),
    device_type: str | None = Query(default=None, min_length=1, max_length=60),
    location: str | None = Query(default=None, min_length=1, max_length=120),
    search: str | None = Query(default=None, min_length=1, max_length=120),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_claims),
) -> DeviceListResponse:
    statement = select(Device).options(selectinload(Device.thresholds))
    count_statement = select(func.count(Device.id))
    filters = []
    if status_filter:
        filters.append(Device.status == status_filter)
    if device_type:
        filters.append(Device.device_type.ilike(f"%{device_type.strip()}%"))
    if location:
        filters.append(Device.location.ilike(f"%{location.strip()}%"))
    if search:
        term = f"%{search.strip()}%"
        filters.append(Device.name.ilike(term) | Device.device_code.ilike(term))
    if filters:
        statement = statement.where(*filters)
        count_statement = count_statement.where(*filters)
    items = list(db.scalars(statement.order_by(Device.created_at.desc()).offset(offset).limit(limit)).unique())
    return DeviceListResponse(items=items, total=db.scalar(count_statement) or 0)


@router.post("", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED, summary="Registrar dispositivo")
def create_device(
    payload: DeviceCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
) -> Device:
    device = Device(
        device_code=payload.device_code.strip().upper(),
        name=payload.name.strip(),
        device_type=payload.device_type.strip(),
        location=payload.location.strip(),
        status=payload.status,
        metadata_json=payload.metadata,
    )
    device.thresholds = [
        Threshold(metric_code=item.metric_code, unit=item.unit, min_value=item.min_value, max_value=item.max_value)
        for item in payload.thresholds
    ]
    db.add(device)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El código de dispositivo ya está registrado") from exc
    return get_device_or_404(device.id, db)


@router.get("/{device_id}", response_model=DeviceResponse, summary="Obtener detalle de dispositivo")
def get_device(device_id: uuid.UUID, db: Session = Depends(get_db), _: dict = Depends(get_current_claims)) -> Device:
    return get_device_or_404(device_id, db)


@router.patch("/{device_id}", response_model=DeviceResponse, summary="Actualizar dispositivo")
def update_device(
    device_id: uuid.UUID,
    payload: DeviceUpdate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
) -> Device:
    device = get_device_or_404(device_id, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        if isinstance(value, str):
            value = value.strip()
        setattr(device, "metadata_json" if field == "metadata" else field, value)
    db.commit()
    return get_device_or_404(device_id, db)


@router.patch("/{device_id}/deactivate", response_model=DeviceResponse, summary="Desactivar dispositivo")
def deactivate_device(
    device_id: uuid.UUID,
    payload: DeviceStatusUpdate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
) -> Device:
    device = get_device_or_404(device_id, db)
    device.status = payload.status
    db.commit()
    return get_device_or_404(device_id, db)


@router.put("/{device_id}/thresholds", response_model=list[ThresholdResponse], summary="Reemplazar umbrales de un dispositivo")
def replace_thresholds(
    device_id: uuid.UUID,
    payload: list[ThresholdInput],
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
) -> list[Threshold]:
    device = get_device_or_404(device_id, db)
    metric_codes = [item.metric_code for item in payload]
    if len(metric_codes) != len(set(metric_codes)):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No se puede repetir una métrica en los umbrales")
    device.thresholds.clear()
    device.thresholds.extend(
        Threshold(metric_code=item.metric_code, unit=item.unit, min_value=item.min_value, max_value=item.max_value)
        for item in payload
    )
    db.commit()
    return get_device_or_404(device_id, db).thresholds
