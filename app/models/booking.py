from sqlalchemy import BigInteger, String, Text, DateTime, Enum, ForeignKey, Index, CheckConstraint, SmallInteger
from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy.sql import func
from .base import Base
import enum

class ChargeType(str, enum.Enum):
    HOUR = "Hour"
    NIGHT = "Night"

class BookingStatus(str, enum.Enum):
    CHECKED_IN = "CheckedIn"
    CHECKED_OUT = "CheckedOut"

class PaymentStatus(str, enum.Enum):
    UNPAID = "Unpaid"
    PARTIAL = "Partial"
    PAID = "Paid"

class Booking(Base):
    __tablename__ = "bookings"
    
    id = mapped_column(BigInteger, primary_key=True)
    booking_no = mapped_column(String(50), nullable=False, unique=True)
    charge_type = mapped_column(Enum(ChargeType), nullable=False)
    checkin = mapped_column(DateTime(timezone=True), nullable=False)
    checkout = mapped_column(DateTime(timezone=True), nullable=True)
    room_id = mapped_column(BigInteger, ForeignKey("rooms.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False)
    room_type_id = mapped_column(BigInteger, ForeignKey("room_types.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False)
    primary_guest_id = mapped_column(BigInteger, ForeignKey("guests.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    num_adults = mapped_column(SmallInteger, nullable=False, default=1)
    num_children = mapped_column(SmallInteger, nullable=False, default=0)
    status = mapped_column(Enum(BookingStatus), nullable=False, default=BookingStatus.CHECKED_IN)
    payment_status = mapped_column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.UNPAID)
    notes = mapped_column(Text, nullable=True)
    created_at = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_by = mapped_column(BigInteger, ForeignKey("users.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    updated_at = mapped_column(DateTime(timezone=True), nullable=True)
    updated_by = mapped_column(BigInteger, ForeignKey("users.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    
    room = relationship("Room", back_populates="bookings")
    room_type = relationship("RoomType", back_populates="bookings")
    primary_guest = relationship("Guest", back_populates="bookings")
    booking_details = relationship("BookingDetail", back_populates="booking", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="booking", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("ix_bookings_booking_no", "booking_no"),
        Index("ix_bookings_room_id", "room_id"),
        Index("ix_bookings_guest_id", "primary_guest_id"),
        Index("ix_bookings_checkin", "checkin"),
        Index("ix_bookings_checkout", "checkout"),
        Index("ix_bookings_status", "status"),
        Index("ix_bookings_payment_status", "payment_status"),
        CheckConstraint("checkout IS NULL OR checkout >= checkin", name="chk_bookings_dates"),
        CheckConstraint("num_adults + num_children > 0", name="chk_bookings_occupancy"),
    )