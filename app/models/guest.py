from sqlalchemy import BigInteger, String, Text, Date, DateTime, Enum, ForeignKey, Index
from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy.sql import func
from .base import Base
import enum

class Gender(str, enum.Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"

class Guest(Base):
    __tablename__ = "guests"
    
    id = mapped_column(BigInteger, primary_key=True)
    name = mapped_column(String(200), nullable=False)
    gender = mapped_column(Enum(Gender), nullable=True)
    date_of_birth = mapped_column(Date, nullable=True)
    nationality = mapped_column(String(100), nullable=True)
    phone = mapped_column(String(50), nullable=True)
    email = mapped_column(String(255), nullable=True)
    address = mapped_column(Text, nullable=True)
    description = mapped_column(Text, nullable=True)
    created_at = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_by = mapped_column(BigInteger, ForeignKey("users.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    updated_at = mapped_column(DateTime(timezone=True), nullable=True)
    updated_by = mapped_column(BigInteger, ForeignKey("users.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    bookings = relationship("Booking", back_populates="primary_guest")
    
    # Indexes
    __table_args__ = (
        Index("ix_guests_name", "name"),
        Index("ix_guests_phone", "phone"),
        Index("ix_guests_email", "email"),
        Index("ix_guests_nationality", "nationality"),
    )