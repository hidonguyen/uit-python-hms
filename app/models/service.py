from sqlalchemy import BigInteger, String, Text, Numeric, DateTime, Enum, ForeignKey, Index
from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy.sql import func
from .base import Base
import enum


class ServiceStatus(str, enum.Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"


class Service(Base):
    __tablename__ = "services"

    id = mapped_column(BigInteger, primary_key=True)
    name = mapped_column(String(200), nullable=False)
    unit = mapped_column(String(50), nullable=False)
    price = mapped_column(Numeric(12, 2), nullable=False)
    description = mapped_column(Text, nullable=True)
    status = mapped_column(Enum(ServiceStatus), nullable=False, default=ServiceStatus.ACTIVE)
    created_at = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_by = mapped_column(BigInteger, ForeignKey("users.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    updated_at = mapped_column(DateTime(timezone=True), nullable=True)
    updated_by = mapped_column(BigInteger, ForeignKey("users.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)

    booking_details = relationship("BookingDetail", back_populates="service")

    __table_args__ = (
        Index("ix_services_name", "name"),
        Index("ix_services_status", "status"),
    )
