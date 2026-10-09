import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db import get_db
from app.schemas import TicketCategory, TicketDetailResponse, TicketListResponse, TicketStatus
from app.security import ROLE_ADMIN, require_ticket_author

router = APIRouter(prefix="/tickets", tags=["tickets"])

MIN_DESCRIPTION_LENGTH = 10
MAX_DESCRIPTION_LENGTH = 2000
MAX_ATTACHMENT_SIZE_BYTES = 5 * 1024 * 1024
ALLOWED_ATTACHMENT_TYPES = {
    "application/pdf": (".pdf", b"%PDF-"),
    "image/jpeg": (".jpg", b"\xff\xd8\xff"),
    "image/png": (".png", b"\x89PNG\r\n\x1a\n"),
}

# Debe coincidir con el código que arma to_ticket(): TK-<año>-<número de 6 dígitos>.
TICKET_CODE_SQL = "('TK-' || EXTRACT(YEAR FROM t.created_at)::int || '-' || LPAD(t.ticket_number::text, 6, '0'))"

TICKET_SELECT = """
    SELECT
        t.id,
        t.ticket_number,
        t.device_id,
        d.name AS device_name,
        d.device_code,
        t.category,
        t.description,
        t.status,
        t.created_by_user_id,
        t.created_at,
        t.updated_at,
        a.id AS attachment_id,
        a.original_name AS attachment_name,
        a.content_type AS attachment_type,
        a.size_bytes AS attachment_size
    FROM alert_ticket_service.tickets t
    LEFT JOIN device_service.devices d ON d.id = t.device_id
    LEFT JOIN alert_ticket_service.ticket_attachments a ON a.ticket_id = t.id
"""


def to_ticket(row) -> dict:
    ticket = {
        "id": row["id"],
        "code": f"TK-{row['created_at'].year}-{row['ticket_number']:06d}",
        "device_id": row["device_id"],
        "device_name": row["device_name"],
        "device_code": row["device_code"],
        "category": row["category"],
        "description": row["description"],
        "status": row["status"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "attachment": None,
    }
    if row["attachment_id"]:
        ticket["attachment"] = {
            "id": row["attachment_id"],
            "original_name": row["attachment_name"],
            "content_type": row["attachment_type"],
            "size_bytes": row["attachment_size"],
            "url": f"/api/alerts-tickets/tickets/{row['id']}/attachment",
        }
    return ticket


def get_visible_ticket(ticket_id: uuid.UUID, claims: dict, db: Session):
    row = db.execute(text(f"{TICKET_SELECT} WHERE t.id = :ticket_id"), {"ticket_id": ticket_id}).mappings().first()
    # Un lector no distingue entre tickets ajenos e inexistentes.
    if row is None or (claims["role"] != ROLE_ADMIN and row["created_by_user_id"] != claims["user_id"]):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket no encontrado")
    return row


def is_valid_attachment(content_type: str, content: bytes) -> bool:
    expected = ALLOWED_ATTACHMENT_TYPES.get(content_type)
    return expected is not None and content.startswith(expected[1])


@router.post("", response_model=TicketDetailResponse, status_code=status.HTTP_201_CREATED, summary="Registrar ticket no crítico")
async def create_ticket(
    device_id: uuid.UUID = Form(...),
    category: TicketCategory = Form(...),
    description: str = Form(..., max_length=MAX_DESCRIPTION_LENGTH),
    attachment: UploadFile | None = File(default=None, description="PDF, PNG o JPG de hasta 5 MB"),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    claims: dict = Depends(require_ticket_author),
) -> dict:
    description = description.strip()
    if len(description) < MIN_DESCRIPTION_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"La descripción debe tener al menos {MIN_DESCRIPTION_LENGTH} caracteres",
        )

    attachment_content = None
    if attachment is not None and attachment.filename:
        attachment_content = await attachment.read(MAX_ATTACHMENT_SIZE_BYTES + 1)
        content_type = attachment.content_type or ""
        if not attachment_content or len(attachment_content) > MAX_ATTACHMENT_SIZE_BYTES or not is_valid_attachment(content_type, attachment_content):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El adjunto debe ser un PDF, PNG o JPG válido y no superar 5 MB",
            )

    device = db.execute(text("SELECT id FROM device_service.devices WHERE id = :device_id"), {"device_id": device_id}).first()
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispositivo no encontrado")

    file_path = None
    try:
        ticket_id = db.execute(
            text("""
                INSERT INTO alert_ticket_service.tickets (device_id, created_by_user_id, category, description)
                VALUES (:device_id, :user_id, :category, :description)
                RETURNING id
            """),
            {"device_id": device_id, "user_id": claims["user_id"], "category": category, "description": description},
        ).scalar_one()
        db.execute(
            text("""
                INSERT INTO alert_ticket_service.ticket_status_history (ticket_id, previous_status, new_status, changed_by_user_id, note)
                VALUES (:ticket_id, NULL, 'abierto', :user_id, 'Ticket registrado')
            """),
            {"ticket_id": ticket_id, "user_id": claims["user_id"]},
        )
        if attachment_content is not None:
            extension, _ = ALLOWED_ATTACHMENT_TYPES[attachment.content_type]
            storage_name = f"{uuid.uuid4()}{extension}"
            attachments_path = Path(settings.ticket_attachments_path)
            attachments_path.mkdir(parents=True, exist_ok=True)
            file_path = attachments_path / storage_name
            file_path.write_bytes(attachment_content)
            db.execute(
                text("""
                    INSERT INTO alert_ticket_service.ticket_attachments
                        (ticket_id, storage_name, original_name, content_type, size_bytes, uploaded_by_user_id)
                    VALUES (:ticket_id, :storage_name, :original_name, :content_type, :size_bytes, :user_id)
                """),
                {
                    "ticket_id": ticket_id,
                    "storage_name": storage_name,
                    "original_name": Path(attachment.filename).name[:255],
                    "content_type": attachment.content_type,
                    "size_bytes": len(attachment_content),
                    "user_id": claims["user_id"],
                },
            )
        db.commit()
    except Exception:
        db.rollback()
        if file_path is not None:
            file_path.unlink(missing_ok=True)
        raise

    return read_ticket(ticket_id, db, claims)


@router.get("/mine", response_model=TicketListResponse, summary="Listar mis tickets")
def list_my_tickets(
    status_filter: TicketStatus | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None, min_length=1, max_length=120),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    claims: dict = Depends(require_ticket_author),
) -> dict:
    conditions = ["t.created_by_user_id = :user_id"]
    params: dict = {"user_id": claims["user_id"], "limit": limit, "offset": offset}
    if status_filter:
        conditions.append("t.status = :status")
        params["status"] = status_filter
    if search:
        conditions.append(f"(d.name ILIKE :search OR d.device_code ILIKE :search OR t.description ILIKE :search OR {TICKET_CODE_SQL} ILIKE :search)")
        params["search"] = f"%{search.strip()}%"
    where = " AND ".join(conditions)
    rows = db.execute(
        text(f"{TICKET_SELECT} WHERE {where} ORDER BY t.created_at DESC LIMIT :limit OFFSET :offset"),
        params,
    ).mappings().all()
    total = db.execute(
        text(f"""
            SELECT COUNT(*) FROM alert_ticket_service.tickets t
            LEFT JOIN device_service.devices d ON d.id = t.device_id
            WHERE {where}
        """),
        params,
    ).scalar_one()
    return {"items": [to_ticket(row) for row in rows], "total": total}


@router.get("/{ticket_id}", response_model=TicketDetailResponse, summary="Consultar detalle de un ticket propio")
def get_ticket(
    ticket_id: uuid.UUID,
    db: Session = Depends(get_db),
    claims: dict = Depends(require_ticket_author),
) -> dict:
    return read_ticket(ticket_id, db, claims)


def read_ticket(ticket_id: uuid.UUID, db: Session, claims: dict) -> dict:
    ticket = to_ticket(get_visible_ticket(ticket_id, claims, db))
    history = db.execute(
        text("""
            SELECT previous_status, new_status, note, changed_at
            FROM alert_ticket_service.ticket_status_history
            WHERE ticket_id = :ticket_id
            ORDER BY changed_at
        """),
        {"ticket_id": ticket_id},
    ).mappings().all()
    ticket["history"] = [dict(row) for row in history]
    return ticket


@router.get("/{ticket_id}/attachment", response_class=FileResponse, summary="Descargar el adjunto de un ticket")
def read_ticket_attachment(
    ticket_id: uuid.UUID,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    claims: dict = Depends(require_ticket_author),
) -> FileResponse:
    get_visible_ticket(ticket_id, claims, db)
    record = db.execute(
        text("SELECT storage_name, original_name, content_type FROM alert_ticket_service.ticket_attachments WHERE ticket_id = :ticket_id"),
        {"ticket_id": ticket_id},
    ).mappings().first()
    file_path = Path(settings.ticket_attachments_path) / record["storage_name"] if record else None
    if record is None or not file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Adjunto no encontrado")
    return FileResponse(file_path, media_type=record["content_type"], filename=record["original_name"])
