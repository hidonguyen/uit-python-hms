from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from ..models.booking import ChargeType, BookingStatus, PaymentStatus

class BookingBase(BaseModel):
    booking_no: str = Field(..., min_length=1, max_length=50)
    charge_type: ChargeType
    checkin: datetime
    checkout: Optional[datetime] = None
    room_id: int
    room_type_id: int
    primary_guest_id: Optional[int] = None
    num_adults: int = Field(default=1, ge=0)
    num_children: int = Field(default=0, ge=0)
    status: BookingStatus = BookingStatus.CHECKED_IN
    payment_status: PaymentStatus = PaymentStatus.UNPAID
    notes: Optional[str] = None

class BookingCreate(BookingBase):
    pass

class BookingUpdate(BaseModel):
    booking_no: Optional[str] = Field(None, min_length=1, max_length=50)
    charge_type: Optional[ChargeType] = None
    checkin: Optional[datetime] = None
    checkout: Optional[datetime] = None
    room_id: Optional[int] = None
    room_type_id: Optional[int] = None
    primary_guest_id: Optional[int] = None
    num_adults: Optional[int] = Field(None, ge=0)
    num_children: Optional[int] = Field(None, ge=0)
    status: Optional[BookingStatus] = None
    payment_status: Optional[PaymentStatus] = None
    notes: Optional[str] = None

class BookingOut(BookingBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}

class BookingWithRelations(BookingOut):
    room: Optional["RoomOut"] = None
    room_type: Optional["RoomTypeOut"] = None
    primary_guest: Optional["GuestOut"] = None
    booking_details: list["BookingDetailOut"] = []
    payments: list["PaymentOut"] = []