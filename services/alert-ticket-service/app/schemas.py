import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

TicketCategory = Literal[
    "carcasa_rota",
    "tapa_faltante",
    "etiqueta_ilegible",
    "deterioro_estetico",
    "cable_deteriorado",
    "conector_suelto",
    "pantalla_danada",
    "suciedad_acumulada",
    "otro",
]
TicketStatus = Literal["abierto", "en_revision", "resuelto", "cerrado"]


class TicketAttachmentResponse(BaseModel):
    id: uuid.UUID
    original_name: str
    content_type: str
    size_bytes: int
    url: str


class TicketStatusChange(BaseModel):
    previous_status: TicketStatus | None
    new_status: TicketStatus
    note: str | None
    changed_at: datetime


class TicketResponse(BaseModel):
    id: uuid.UUID
    code: str
    device_id: uuid.UUID
    device_name: str | None
    device_code: str | None
    category: TicketCategory
    description: str
    priority: Literal["no_critica"] = "no_critica"
    status: TicketStatus
    created_at: datetime
    updated_at: datetime
    attachment: TicketAttachmentResponse | None = None


class TicketDetailResponse(TicketResponse):
    history: list[TicketStatusChange] = []


class TicketListResponse(BaseModel):
    items: list[TicketResponse]
    total: int
