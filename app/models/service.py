from sqlalchemy import (
    String,
    Text,
    Numeric,
    Enum,
    Index,
)
from sqlalchemy.orm import mapped_column, relationship
from .base import Base
import enum


class ServiceStatus(str, enum.Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"


class Service(Base):
    __tablename__ = "services"

    name = mapped_column(String(200), nullable=False)
    unit = mapped_column(String(50), nullable=False)
    price = mapped_column(Numeric(12, 2), nullable=False)
    description = mapped_column(Text, nullable=True)
    status = mapped_column(
        Enum(ServiceStatus, name="ServiceStatus", native_enum=False, length=50, validate_strings=True), nullable=False, default=ServiceStatus.ACTIVE
    )

    booking_details = relationship("BookingDetail", back_populates="service")

    __table_args__ = (
        Index("ix_services_name", "name"),
        Index("ix_services_status", "status"),
    )
