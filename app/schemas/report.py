from decimal import Decimal
from typing import List
from pydantic import BaseModel, field_serializer
from datetime import date


class SummaryOut(BaseModel):
    total_revenue: Decimal
    room_revenue: Decimal
    service_revenue: Decimal
    total_guests: int
    currency: str = "VND"

    @field_serializer("total_revenue", "room_revenue", "service_revenue")
    def _ser_decimal(self, v: Decimal, _info):
        return float(v)


class RoomTypeRevenueItem(BaseModel):
    name: str
    revenue: Decimal
    percent: float

    @field_serializer("revenue")
    def _ser_decimal(self, v: Decimal, _info):
        return float(v)


class RoomTypeRevenueOut(BaseModel):
    total: Decimal
    items: List[RoomTypeRevenueItem]

    @field_serializer("total")
    def _ser_total(self, v: Decimal, _info):
        return float(v)


class ServiceRevenueItem(BaseModel):
    name: str
    revenue: Decimal
    percent: float

    @field_serializer("revenue")
    def _ser_decimal(self, v: Decimal, _info):
        return float(v)


class ServiceRevenueOut(BaseModel):
    total: Decimal
    items: List[ServiceRevenueItem]

    @field_serializer("total")
    def _ser_total(self, v: Decimal, _info):
        return float(v)


class CustomerDistributionOut(BaseModel):
    new_customers: int
    returning_customers: int
    percent_new: float
    percent_returning: float


class DailyBookingPoint(BaseModel):
    date: date
    bookings: int


class DailyBookingsOut(BaseModel):
    total: int
    points: List[DailyBookingPoint]
