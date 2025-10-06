from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime
from typing import Optional

class RoomTypeBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    base_occupancy: int = Field(..., gt=0)
    max_occupancy: int = Field(..., gt=0)
    base_rate: Decimal = Field(..., ge=0)
    hour_rate: Decimal = Field(..., ge=0)
    extra_adult_fee: Decimal = Field(default=0, ge=0)
    extra_child_fee: Decimal = Field(default=0, ge=0)
    description: Optional[str] = None

class RoomTypeCreate(RoomTypeBase):
    pass

class RoomTypeUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    base_occupancy: Optional[int] = Field(None, gt=0)
    max_occupancy: Optional[int] = Field(None, gt=0)
    base_rate: Optional[Decimal] = Field(None, ge=0)
    hour_rate: Optional[Decimal] = Field(None, ge=0)
    extra_adult_fee: Optional[Decimal] = Field(None, ge=0)
    extra_child_fee: Optional[Decimal] = Field(None, ge=0)
    description: Optional[str] = None

class RoomTypeOut(RoomTypeBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}

class RoomTypeWithRelations(RoomTypeOut):
    rooms: list["RoomOut"] = []
    bookings: list["BookingOut"] = []