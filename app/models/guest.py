from sqlalchemy import String, Text, Date, Enum, Index
from sqlalchemy.orm import mapped_column, relationship
from .base import Base
import enum


class Gender(str, enum.Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"


class Guest(Base):
    def __init__(self, id=None):
        super().__init__(id=id)

    __tablename__ = "guests"

    name = mapped_column(String(200), nullable=False)
    gender = mapped_column(Enum(Gender, name="Gender", native_enum=False, length=50, validate_strings=True), nullable=True)
    date_of_birth = mapped_column(Date, nullable=True)
    nationality = mapped_column(String(100), nullable=True)
    phone = mapped_column(String(50), nullable=True)
    email = mapped_column(String(255), nullable=True)
    address = mapped_column(Text, nullable=True)
    description = mapped_column(Text, nullable=True)

    bookings = relationship("Booking", back_populates="primary_guest")

    __table_args__ = (
        Index("ix_guests_name", "name"),
        Index("ix_guests_phone", "phone"),
        Index("ix_guests_email", "email"),
        Index("ix_guests_nationality", "nationality"),
    )
