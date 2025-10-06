from sqlalchemy import BigInteger, String, Text, Numeric, DateTime, Enum, ForeignKey, Index
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
    
    id = mapped_column(BigInteger, primary_key=True)
    booking_id = mapped_column(BigInteger, ForeignKey("bookings.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    paid_at = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    payment_method = mapped_column(Enum(PaymentMethod), nullable=False)
    reference_no = mapped_column(String(100), nullable=True)
    amount = mapped_column(Numeric(12, 2), nullable=False)
    payer_name = mapped_column(String(200), nullable=True)
    notes = mapped_column(Text, nullable=True)
    created_at = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_by = mapped_column(BigInteger, ForeignKey("users.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    updated_at = mapped_column(DateTime(timezone=True), nullable=True)
    updated_by = mapped_column(BigInteger, ForeignKey("users.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    booking = relationship("Booking", back_populates="payments")
    
    # Indexes
    __table_args__ = (
        Index("ix_payments_booking_id", "booking_id"),
        Index("ix_payments_paid_at", "paid_at"),
        Index("ix_payments_payment_method", "payment_method"),
        Index("ix_payments_reference_no", "reference_no"),
    )