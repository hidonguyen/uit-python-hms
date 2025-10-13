from decimal import Decimal
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from ..models.booking import ChargeType, BookingStatus, PaymentStatus


class TodayBookingOut(BaseModel):
    id: int
    booking_no: str = Field(..., min_length=1, max_length=50)
    charge_type: ChargeType
    checkin: datetime
    checkout: Optional[datetime] = None
    room_id: int
    room_name: str
    room_type_id: int
    room_type_name: str
    primary_guest_id: int
    primary_guest_name: str
    primary_guest_phone: str
    num_adults: int = Field(default=1, ge=0)
    num_children: int = Field(default=0, ge=0)
    total_room_charges: Decimal = Field(default=0, ge=0)
    total_service_charges: Decimal = Field(default=0, ge=0)
    notes: Optional[str] = None


class PagedTodayBookingOut(BaseModel):
    total: int
    skip: int
    limit: int
    items: List[TodayBookingOut]


class BookingHistoryOut(BaseModel):
    id: int
    booking_no: str = Field(..., min_length=1, max_length=50)
    charge_type: ChargeType
    checkin: datetime
    checkout: Optional[datetime] = None
    room_id: int
    room_name: str
    room_type_id: int
    room_type_name: str
    primary_guest_id: int
    primary_guest_name: str
    primary_guest_phone: str
    num_adults: int = Field(default=1, ge=0)
    num_children: int = Field(default=0, ge=0)
    status: Optional[BookingStatus] = None
    payment_status: Optional[PaymentStatus] = None
    total_amount: Decimal = Field(default=0, ge=0)
    paid_amount: Decimal = Field(default=0, ge=0)
    balance: Decimal = Field(default=0)
    notes: Optional[str] = None


class PagedBookingHistoryOut(BaseModel):
    total: int
    skip: int
    limit: int
    items: List[BookingHistoryOut]


class BookingBase(BaseModel):
    charge_type: ChargeType
    checkin: datetime
    checkout: Optional[datetime] = None
    room_id: int
    room_type_id: int
    primary_guest_id: int
    num_adults: int = Field(default=1, ge=0)
    num_children: int = Field(default=0, ge=0)
    status: BookingStatus = BookingStatus.CHECKED_IN
    payment_status: PaymentStatus = PaymentStatus.UNPAID
    notes: Optional[str] = None


class BookingCreate(BookingBase):
    pass


class BookingUpdate(BaseModel):
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
    booking_no: str = Field(..., min_length=1, max_length=50)
    total_amount: Decimal = Field(default=0, ge=0)
    paid_amount: Decimal = Field(default=0, ge=0)
    balance: Decimal = Field(default=0)
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class BookingStatusUpdate(BaseModel):
    status: BookingStatus


class PaymentStatusUpdate(BaseModel):
    payment_status: PaymentStatus


class CheckInUpdate(BaseModel):
    checkin_time: datetime


class CheckOutUpdate(BaseModel):
    checkout_time: datetime


class BookingDetailIn(BaseModel):
    service_id: int
    quantity: int = Field(default=1, ge=1)
    unit_price: Optional[Decimal] = Field(default=None, ge=0)
    notes: Optional[str] = None


class BookingCreateWithDetails(BookingCreate):
    booking_details: List[BookingDetailIn] = []
