from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime
from typing import Optional
from ..models.payment import PaymentMethod

class PaymentBase(BaseModel):
    booking_id: int
    payment_method: PaymentMethod
    reference_no: Optional[str] = Field(None, max_length=100)
    amount: Decimal = Field(..., gt=0)
    payer_name: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = None

class PaymentCreate(PaymentBase):
    pass

class PaymentUpdate(BaseModel):
    booking_id: Optional[int] = None
    payment_method: Optional[PaymentMethod] = None
    reference_no: Optional[str] = Field(None, max_length=100)
    amount: Optional[Decimal] = Field(None, gt=0)
    payer_name: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = None

class PaymentOut(PaymentBase):
    id: int
    paid_at: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}

class PaymentWithRelations(PaymentOut):
    booking: Optional["BookingOut"] = None