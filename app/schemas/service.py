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
    description: Optional[str] = None
    status: Optional[ServiceStatus] = None


class ServiceChangePrice(BaseModel):
    price: Decimal = Field(..., ge=0)


class ServiceOut(ServiceBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PagedServiceOut(BaseModel):
    total: int
    skip: int
    limit: int
    items: List[ServiceOut]
