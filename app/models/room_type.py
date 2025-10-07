from sqlalchemy import (
    BigInteger,
    String,
    Text,
    Numeric,
    SmallInteger,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy.sql import func
from .base import Base


class RoomType(Base):
    __tablename__ = "room_types"

    id = mapped_column(BigInteger, primary_key=True)
    code = mapped_column(String(50), nullable=False, unique=True)
    name = mapped_column(String(200), nullable=False)
    base_occupancy = mapped_column(SmallInteger, nullable=False)
    max_occupancy = mapped_column(SmallInteger, nullable=False)
    base_rate = mapped_column(Numeric(12, 2), nullable=False)
    hour_rate = mapped_column(Numeric(12, 2), nullable=False)
    extra_adult_fee = mapped_column(Numeric(12, 2), nullable=False, default=0)
    extra_child_fee = mapped_column(Numeric(12, 2), nullable=False, default=0)
    description = mapped_column(Text, nullable=True)
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

    rooms = relationship("Room", back_populates="room_type")
    bookings = relationship("Booking", back_populates="room_type")

    __table_args__ = (
        Index("ix_room_types_code", "code"),
        Index("ix_room_types_name", "name"),
    )
