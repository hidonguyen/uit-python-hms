from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime
from typing import Optional
from ..models.booking_detail import BookingDetailType

class BookingDetailBase(BaseModel):
    booking_id: int
    type: BookingDetailType
    service_id: Optional[int] = None
    description: Optional[str] = None
    quantity: Decimal = Field(default=1, ge=0)
    unit_price: Decimal = Field(default=0, ge=0)
    discount_amount: Decimal = Field(default=0, ge=0)
    amount: Decimal = Field(..., ge=0)

class BookingDetailCreate(BookingDetailBase):
    pass

class BookingDetailUpdate(BaseModel):
    booking_id: Optional[int] = None
    type: Optional[BookingDetailType] = None
    service_id: Optional[int] = None
    description: Optional[str] = None
    quantity: Optional[Decimal] = Field(None, ge=0)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    discount_amount: Optional[Decimal] = Field(None, ge=0)
    amount: Optional[Decimal] = Field(None, ge=0)

class BookingDetailOut(BookingDetailBase):
    id: int
    issued_at: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}