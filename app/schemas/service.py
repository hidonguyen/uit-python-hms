from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime
from typing import List, Optional
from ..models.service import ServiceStatus


class ServiceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    unit: str = Field(..., min_length=1, max_length=50)
    price: Decimal = Field(..., ge=0)
    description: Optional[str] = None
    status: ServiceStatus = ServiceStatus.ACTIVE


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    unit: Optional[str] = Field(None, min_length=1, max_length=50)
    price: Optional[Decimal] = Field(None, ge=0)
    description: Optional[str] = None
    status: Optional[ServiceStatus] = None


class ServiceOut(ServiceBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ServiceWithRelations(ServiceOut):
    booking_details: list["BookingDetailOut"] = []


class PagedServiceOut(BaseModel):
    total: int
    skip: int
    limit: int
    items: List[ServiceOut]
