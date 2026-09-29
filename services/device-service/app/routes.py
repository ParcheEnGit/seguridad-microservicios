import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.core.config import Settings, get_settings
from app.models import Device, DevicePhoto, Threshold
from app.schemas import DeviceCreate, DeviceListResponse, DevicePhotoResponse, DeviceResponse, DeviceStatusUpdate, DeviceUpdate, ThresholdInput, ThresholdResponse
from app.security import get_current_claims, require_admin

router = APIRouter(prefix="/devices", tags=["dispositivos"])


def get_device_or_404(device_id: uuid.UUID, db: Session) -> Device:
    statement = select(Device).options(selectinload(Device.thresholds), selectinload(Device.photos)).where(Device.id == device_id)
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
    statement = select(Device).options(selectinload(Device.thresholds), selectinload(Device.photos))
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


ALLOWED_IMAGE_TYPES = {
    "image/jpeg": (".jpg", b"\xff\xd8\xff"),
    "image/png": (".png", b"\x89PNG\r\n\x1a\n"),
    "image/webp": (".webp", b"RIFF"),
}
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024


def is_valid_image(content_type: str, content: bytes) -> bool:
    expected = ALLOWED_IMAGE_TYPES.get(content_type)
    if expected is None:
        return False
    _, signature = expected
    return content.startswith(signature) and (
        content_type != "image/webp" or content[8:12] == b"WEBP"
    )


@router.post("/{device_id}/photos", response_model=DevicePhotoResponse, status_code=status.HTTP_201_CREATED, summary="Agregar fotografía a un dispositivo")
async def upload_device_photo(
    device_id: uuid.UUID,
    photo: UploadFile = File(..., description="Fotografía JPEG, PNG o WebP de hasta 5 MB"),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: dict = Depends(require_admin),
) -> DevicePhoto:
    device = get_device_or_404(device_id, db)
    content = await photo.read(MAX_IMAGE_SIZE_BYTES + 1)
    content_type = photo.content_type or ""
    if not content or len(content) > MAX_IMAGE_SIZE_BYTES or not is_valid_image(content_type, content):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="La fotografía debe ser JPEG, PNG o WebP válida y no superar 5 MB")
    extension = ALLOWED_IMAGE_TYPES[content_type][0]
    storage_name = f"{uuid.uuid4()}{extension}"
    images_path = Path(settings.device_images_path)
    images_path.mkdir(parents=True, exist_ok=True)
    file_path = images_path / storage_name
    file_path.write_bytes(content)
    record = DevicePhoto(
        device_id=device.id,
        storage_name=storage_name,
        original_name=Path(photo.filename or "fotografia").name[:255],
        content_type=content_type,
        size_bytes=len(content),
    )
    db.add(record)
    try:
        db.commit()
        db.refresh(record)
    except Exception:
        db.rollback()
        file_path.unlink(missing_ok=True)
        raise
    return record


@router.get("/{device_id}/photos/{photo_id}/content", response_class=FileResponse, summary="Consultar fotografía de un dispositivo")
def read_device_photo(
    device_id: uuid.UUID,
    photo_id: uuid.UUID,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: dict = Depends(get_current_claims),
) -> FileResponse:
    record = db.scalar(select(DevicePhoto).where(DevicePhoto.id == photo_id, DevicePhoto.device_id == device_id))
    file_path = Path(settings.device_images_path) / record.storage_name if record else None
    if record is None or not file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fotografía no encontrada")
    return FileResponse(file_path, media_type=record.content_type, filename=record.original_name)


@router.delete("/{device_id}/photos/{photo_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar fotografía de un dispositivo")
def delete_device_photo(
    device_id: uuid.UUID,
    photo_id: uuid.UUID,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: dict = Depends(require_admin),
) -> None:
    record = db.scalar(select(DevicePhoto).where(DevicePhoto.id == photo_id, DevicePhoto.device_id == device_id))
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fotografía no encontrada")
    file_path = Path(settings.device_images_path) / record.storage_name
    db.delete(record)
    db.commit()
    file_path.unlink(missing_ok=True)
