from sqlalchemy import (
    String,
    Text,
    Numeric,
    SmallInteger,
    Index,
)
from sqlalchemy.orm import mapped_column, relationship
from .base import Base


class RoomType(Base):
    __tablename__ = "room_types"

    code = mapped_column(String(50), nullable=False, unique=True)
    name = mapped_column(String(200), nullable=False)
    base_occupancy = mapped_column(SmallInteger, nullable=False)
    max_occupancy = mapped_column(SmallInteger, nullable=False)
    base_rate = mapped_column(Numeric(12, 2), nullable=False)
    hour_rate = mapped_column(Numeric(12, 2), nullable=False)
    extra_adult_fee = mapped_column(Numeric(12, 2), nullable=False, default=0)
    extra_child_fee = mapped_column(Numeric(12, 2), nullable=False, default=0)
    description = mapped_column(Text, nullable=True)

    rooms = relationship("Room", back_populates="room_type")
    bookings = relationship("Booking", back_populates="room_type")

    __table_args__ = (
        Index("ix_room_types_code", "code"),
        Index("ix_room_types_name", "name"),
    )
