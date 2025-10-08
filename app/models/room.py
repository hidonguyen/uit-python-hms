from sqlalchemy import BigInteger, String, Text, Enum, ForeignKey, Index
from sqlalchemy.orm import mapped_column, relationship
from .base import Base
import enum


class HousekeepingStatus(str, enum.Enum):
    CLEAN = "Clean"
    DIRTY = "Dirty"
    INSPECTED = "Inspected"
    OUT_OF_ORDER = "OutOfOrder"


class RoomStatus(str, enum.Enum):
    AVAILABLE = "Available"
    OCCUPIED = "Occupied"
    OUT_OF_SERVICE = "OutOfService"


class Room(Base):
    def __init__(self, id=None):
        super().__init__(id=id)

    __tablename__ = "rooms"

    name = mapped_column(String(100), nullable=False, unique=True)
    room_type_id = mapped_column(
        BigInteger,
        ForeignKey("room_types.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    description = mapped_column(Text, nullable=True)
    housekeeping_status = mapped_column(
        Enum(HousekeepingStatus, name="HousekeepingStatus", native_enum=False, length=50, validate_strings=True), nullable=False, default=HousekeepingStatus.CLEAN
    )
    status = mapped_column(
        Enum(RoomStatus, name="RoomStatus", native_enum=False, length=50, validate_strings=True), nullable=False, default=RoomStatus.AVAILABLE
    )

    room_type = relationship("RoomType", back_populates="rooms")
    bookings = relationship("Booking", back_populates="room")

    __table_args__ = (
        Index("ix_rooms_name", "name"),
        Index("ix_rooms_room_type_id", "room_type_id"),
        Index("ix_rooms_status", "status"),
        Index("ix_rooms_housekeeping_status", "housekeeping_status"),
    )
