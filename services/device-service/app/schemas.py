import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

ALLOWED_STATUSES = {"activo", "inactivo", "mantenimiento"}


class ThresholdInput(BaseModel):
    metric_code: str = Field(min_length=2, max_length=50, pattern=r"^[a-z0-9_]+$")
    unit: str = Field(min_length=1, max_length=20)
    min_value: float
    max_value: float

    @field_validator("max_value")
    @classmethod
    def range_is_valid(cls, value: float, info) -> float:
        if "min_value" in info.data and value <= info.data["min_value"]:
            raise ValueError("max_value debe ser mayor que min_value")
        return value


class DeviceCreate(BaseModel):
    device_code: str = Field(min_length=3, max_length=80, pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(min_length=2, max_length=120)
    device_type: str = Field(min_length=2, max_length=60)
    location: str = Field(min_length=2, max_length=120)
    status: str = "activo"
    metadata: dict = Field(default_factory=dict)
    thresholds: list[ThresholdInput] = Field(default_factory=list, max_length=20)

    @field_validator("status")
    @classmethod
    def valid_status(cls, value: str) -> str:
        if value not in ALLOWED_STATUSES:
            raise ValueError("Estado no válido")
        return value


class DeviceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    device_type: str | None = Field(default=None, min_length=2, max_length=60)
    location: str | None = Field(default=None, min_length=2, max_length=120)
    status: str | None = None
    metadata: dict | None = None

    @field_validator("status")
    @classmethod
    def valid_optional_status(cls, value: str | None) -> str | None:
        if value is not None and value not in ALLOWED_STATUSES:
            raise ValueError("Estado no válido")
        return value


class ThresholdResponse(ThresholdInput):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    device_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class DeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    id: uuid.UUID
    device_code: str
    name: str
    device_type: str
    location: str
    status: str
    metadata: dict = Field(validation_alias="metadata_json")
    created_at: datetime
    updated_at: datetime
    thresholds: list[ThresholdResponse] = []


class DeviceListResponse(BaseModel):
    items: list[DeviceResponse]
    total: int


class DeviceStatusUpdate(BaseModel):
    status: str = "inactivo"

    @field_validator("status")
    @classmethod
    def only_inactive(cls, value: str) -> str:
        if value != "inactivo":
            raise ValueError("La desactivación solo admite el estado inactivo")
        return value
