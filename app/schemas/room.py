from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from ..models.room import HousekeepingStatus, RoomStatus


class RoomBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    room_type_id: int
    description: Optional[str] = None
    housekeeping_status: HousekeepingStatus = HousekeepingStatus.CLEAN
    status: RoomStatus = RoomStatus.AVAILABLE


class RoomCreate(RoomBase):
    pass


class RoomUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    room_type_id: Optional[int] = None
    description: Optional[str] = None
    housekeeping_status: Optional[HousekeepingStatus] = None
    status: Optional[RoomStatus] = None


class RoomOut(RoomBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class RoomWithRelations(RoomOut):
    room_type: Optional["RoomTypeOut"] = None
    bookings: list["BookingOut"] = []


class PagedRoomOut(BaseModel):
    total: int
    skip: int
    limit: int
    items: List[RoomOut]


class RoomStatusUpdate(BaseModel):
    status: RoomStatus


class HousekeepingStatusUpdate(BaseModel):
    housekeeping_status: HousekeepingStatus
