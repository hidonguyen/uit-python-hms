from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.models.user import User
from ..models.booking_detail import BookingDetail, BookingDetailType


class BookingDetailRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(
        self, skip: int = 0, limit: int = 100, filters: Optional[Dict[str, Any]] = None
    ) -> List[BookingDetail]:
        """Lấy danh sách booking detail với phân trang và bộ lọc."""
        query = select(BookingDetail).options(
            selectinload(BookingDetail.booking), selectinload(BookingDetail.service)
        )

        if filters:
            conditions = []
            if "booking_id" in filters and filters["booking_id"] is not None:
                conditions.append(BookingDetail.booking_id == filters["booking_id"])
            if "type" in filters and filters["type"]:
                conditions.append(BookingDetail.type == filters["type"])
            if "service_id" in filters and filters["service_id"] is not None:
                conditions.append(BookingDetail.service_id == filters["service_id"])
            if "min_amount" in filters and filters["min_amount"] is not None:
                conditions.append(BookingDetail.amount >= filters["min_amount"])
            if "max_amount" in filters and filters["max_amount"] is not None:
                conditions.append(BookingDetail.amount <= filters["max_amount"])
            if "issued_from" in filters and filters["issued_from"]:
                conditions.append(BookingDetail.issued_at >= filters["issued_from"])
            if "issued_to" in filters and filters["issued_to"]:
                conditions.append(BookingDetail.issued_at <= filters["issued_to"])

            if conditions:
                query = query.where(and_(*conditions))

        # Sắp xếp theo thời gian phát hành mới nhất
        query = query.order_by(BookingDetail.issued_at.desc())

        # Phân trang
        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Đếm tổng số booking detail với bộ lọc."""
        query = select(func.count(BookingDetail.id))

        if filters:
            conditions = []
            if "booking_id" in filters and filters["booking_id"] is not None:
                conditions.append(BookingDetail.booking_id == filters["booking_id"])
            if "type" in filters and filters["type"]:
                conditions.append(BookingDetail.type == filters["type"])
            if "service_id" in filters and filters["service_id"] is not None:
                conditions.append(BookingDetail.service_id == filters["service_id"])

            if conditions:
                query = query.where(and_(*conditions))

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_by_booking_id(self, booking_id: int) -> List[BookingDetail]:
        """Lấy danh sách booking detail theo booking ID."""
        result = await self.session.execute(
            select(BookingDetail)
            .options(selectinload(BookingDetail.service))
            .where(BookingDetail.booking_id == booking_id)
            .order_by(BookingDetail.issued_at.desc())
        )
        return list(result.scalars().all())

    async def get(self, booking_detail_id: int) -> Optional[BookingDetail]:
        """Lấy booking detail theo ID."""
        result = await self.session.execute(
            select(BookingDetail)
            .options(
                selectinload(BookingDetail.booking), selectinload(BookingDetail.service)
            )
            .where(BookingDetail.id == booking_detail_id)
        )
        return result.scalar_one_or_none()

    async def create(self, booking_detail_data: Dict[str, Any], current_user: User) -> BookingDetail:
        """Tạo booking detail mới."""
        booking_detail = BookingDetail(**booking_detail_data)

        booking_detail.created_by = current_user.id
        booking_detail.created_at = datetime.now()

        self.session.add(booking_detail)

        await self.session.commit()
        await self.session.refresh(booking_detail)
        return booking_detail

    async def update(
        self, booking_detail_id: int, booking_detail_data: Dict[str, Any], current_user: User
    ) -> Optional[BookingDetail]:
        """Cập nhật booking detail."""
        booking_detail = await self.get(booking_detail_id)
        if not booking_detail:
            return None

        for field, value in booking_detail_data.items():
            if hasattr(booking_detail, field) and value is not None:
                setattr(booking_detail, field, value)

        booking_detail.updated_by = current_user.id
        booking_detail.updated_at = datetime.now()

        await self.session.commit()
        await self.session.refresh(booking_detail)
        return booking_detail

    async def delete(self, booking_detail_id: int) -> bool:
        """Xóa booking detail."""
        booking_detail = await self.get(booking_detail_id)
        if not booking_detail:
            return False

        await self.session.delete(booking_detail)
        await self.session.commit()
        return True

    async def get_room_charges(self, booking_id: int) -> List[BookingDetail]:
        """Lấy danh sách phí phòng cho booking."""
        result = await self.session.execute(
            select(BookingDetail).where(
                and_(
                    BookingDetail.booking_id == booking_id,
                    BookingDetail.type == BookingDetailType.ROOM,
                )
            )
        )
        return list(result.scalars().all())

    async def get_service_charges(self, booking_id: int) -> List[BookingDetail]:
        """Lấy danh sách phí dịch vụ cho booking."""
        result = await self.session.execute(
            select(BookingDetail)
            .options(selectinload(BookingDetail.service))
            .where(
                and_(
                    BookingDetail.booking_id == booking_id,
                    BookingDetail.type != BookingDetailType.ROOM,
                )
            )
        )
        return list(result.scalars().all())

    async def get_total_amount(self, booking_id: int) -> float:
        """Tính tổng số tiền của booking."""
        result = await self.session.execute(
            select(func.sum(BookingDetail.amount)).where(
                BookingDetail.booking_id == booking_id
            )
        )
        return float(result.scalar() or 0)

    async def get_total_discount(self, booking_id: int) -> float:
        """Tính tổng số tiền giảm giá của booking."""
        result = await self.session.execute(
            select(func.sum(BookingDetail.discount_amount)).where(
                BookingDetail.booking_id == booking_id
            )
        )
        return float(result.scalar() or 0)
