from sqlalchemy import (
    BigInteger,
    Text,
    Numeric,
    DateTime,
    Enum as PgEnum,
    ForeignKey,
    Index,
    CheckConstraint,
)
from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy.sql import func
from .base import Base
import enum


class BookingDetailType(str, enum.Enum):
    ROOM = "Room"
    SERVICE = "Service"
    FEE = "Fee"
    ADJUSTMENT = "Adjustment"


BOOKING_DETAIL_PG_ENUM = PgEnum(
    BookingDetailType,
    name="bookingdetailtype",
    native_enum=True,
    validate_strings=True,
    create_type=True,
)


class BookingDetail(Base):
    __tablename__ = "booking_details"

    id = mapped_column(BigInteger, primary_key=True)
    booking_id = mapped_column(
        BigInteger,
        ForeignKey("bookings.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    type = mapped_column(BOOKING_DETAIL_PG_ENUM, nullable=False)

    service_id = mapped_column(
        BigInteger,
        ForeignKey("services.id", onupdate="CASCADE", ondelete="SET NULL"),
        nullable=True,
    )
    issued_at = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    description = mapped_column(Text, nullable=True)
    quantity = mapped_column(Numeric(12, 2), nullable=False, default=1)
    unit_price = mapped_column(Numeric(12, 2), nullable=False, default=0)
    discount_amount = mapped_column(Numeric(12, 2), nullable=False, default=0)
    amount = mapped_column(Numeric(12, 2), nullable=False)
    created_at = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_by = mapped_column(
        BigInteger,
        ForeignKey("users.id", onupdate="CASCADE", ondelete="SET NULL"),
        nullable=True,
    )
    updated_at = mapped_column(DateTime(timezone=True), nullable=True)
    updated_by = mapped_column(
        BigInteger,
        ForeignKey("users.id", onupdate="CASCADE", ondelete="SET NULL"),
        nullable=True,
    )

    booking = relationship("Booking", back_populates="booking_details")
    service = relationship("Service", back_populates="booking_details")

    __table_args__ = (
        Index("ix_booking_details_booking_id", "booking_id"),
        Index("ix_booking_details_type", "type"),
        Index("ix_booking_details_service_id", "service_id"),
        Index("ix_booking_details_issued_at", "issued_at"),
        CheckConstraint(
            "(type = 'Service' AND service_id IS NOT NULL) OR (type <> 'Service')",
            name="chk_booking_details_service_ref",
        ),
    )
