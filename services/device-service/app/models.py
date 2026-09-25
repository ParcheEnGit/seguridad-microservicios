import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Device(Base):
    __tablename__ = "devices"
    __table_args__ = (
        CheckConstraint("status IN ('activo', 'inactivo', 'mantenimiento')", name="chk_devices_status"),
        {"schema": "device_service"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    device_code: Mapped[str] = mapped_column(String(80), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    device_type: Mapped[str] = mapped_column(String(60))
    location: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(20), default="activo")
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    thresholds: Mapped[list["Threshold"]] = relationship(
        back_populates="device", cascade="all, delete-orphan"
    )


class Threshold(Base):
    __tablename__ = "thresholds"
    __table_args__ = (
        UniqueConstraint("device_id", "metric_code", name="uq_threshold_device_metric"),
        CheckConstraint("max_value > min_value", name="chk_threshold_range"),
        {"schema": "device_service"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("device_service.devices.id"))
    metric_code: Mapped[str] = mapped_column(String(50))
    unit: Mapped[str] = mapped_column(String(20))
    min_value: Mapped[float] = mapped_column(Numeric(12, 4))
    max_value: Mapped[float] = mapped_column(Numeric(12, 4))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    device: Mapped[Device] = relationship(back_populates="thresholds")
