from pydantic import BaseModel, Field, EmailStr
from datetime import datetime, date
from typing import List, Optional
from ..models.guest import Gender


class GuestBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    gender: Optional[Gender] = None
    date_of_birth: Optional[date] = None
    nationality: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    description: Optional[str] = None


class GuestCreate(GuestBase):
    pass


class GuestUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    gender: Optional[Gender] = None
    date_of_birth: Optional[date] = None
    nationality: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    description: Optional[str] = None


class GuestOut(GuestBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PagedGuestOut(BaseModel):
    total: int
    skip: int
    limit: int
    items: List[GuestOut]
