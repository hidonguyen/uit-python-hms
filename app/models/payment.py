from sqlalchemy import (
    BigInteger,
    String,
    Text,
    Numeric,
    DateTime,
    Enum,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy.sql import func
from .base import Base
import enum


class PaymentMethod(str, enum.Enum):
    CASH = "Cash"
    CARD = "Card"
    OTHER = "Other"


class Payment(Base):
    __tablename__ = "payments"

    booking_id = mapped_column(
        BigInteger,
        ForeignKey("bookings.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    paid_at = mapped_column(
        DateTime(timezone=False), nullable=False, server_default=func.now()
    )
    payment_method = mapped_column(Enum(PaymentMethod, name="PaymentMethod", native_enum=False, length=50, validate_strings=True), nullable=False)
    reference_no = mapped_column(String(100), nullable=True)
    amount = mapped_column(Numeric(12, 2), nullable=False)
    payer_name = mapped_column(String(200), nullable=True)
    notes = mapped_column(Text, nullable=True)

    booking = relationship("Booking", back_populates="payments")

    __table_args__ = (
        Index("ix_payments_booking_id", "booking_id"),
        Index("ix_payments_paid_at", "paid_at"),
        Index("ix_payments_payment_method", "payment_method"),
        Index("ix_payments_reference_no", "reference_no"),
    )
