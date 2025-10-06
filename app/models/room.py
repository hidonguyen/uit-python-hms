from sqlalchemy import BigInteger, String, Text, DateTime, Enum, ForeignKey, Index
from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy.sql import func
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
    __tablename__ = "rooms"
    
    id = mapped_column(BigInteger, primary_key=True)
    name = mapped_column(String(100), nullable=False, unique=True)
    room_type_id = mapped_column(BigInteger, ForeignKey("room_types.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False)
    description = mapped_column(Text, nullable=True)
    housekeeping_status = mapped_column(Enum(HousekeepingStatus), nullable=False, default=HousekeepingStatus.CLEAN)
    status = mapped_column(Enum(RoomStatus), nullable=False, default=RoomStatus.AVAILABLE)
    created_at = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_by = mapped_column(BigInteger, ForeignKey("users.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    updated_at = mapped_column(DateTime(timezone=True), nullable=True)
    updated_by = mapped_column(BigInteger, ForeignKey("users.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    room_type = relationship("RoomType", back_populates="rooms")
    bookings = relationship("Booking", back_populates="room")
    
    # Indexes
    __table_args__ = (
        Index("ix_rooms_name", "name"),
        Index("ix_rooms_room_type_id", "room_type_id"),
        Index("ix_rooms_status", "status"),
        Index("ix_rooms_housekeeping_status", "housekeeping_status"),
    )