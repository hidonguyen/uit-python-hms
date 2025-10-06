from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any
from datetime import datetime
from ..models.payment import Payment, PaymentMethod

class PaymentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def list(
        self, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Payment]:
        """Lấy danh sách payment với phân trang và bộ lọc."""
        query = select(Payment).options(selectinload(Payment.booking))
        
        # Áp dụng bộ lọc nếu có
        if filters:
            conditions = []
            if "booking_id" in filters and filters["booking_id"] is not None:
                conditions.append(Payment.booking_id == filters["booking_id"])
            if "payment_method" in filters and filters["payment_method"]:
                conditions.append(Payment.payment_method == filters["payment_method"])
            if "reference_no" in filters and filters["reference_no"]:
                conditions.append(Payment.reference_no.ilike(f"%{filters['reference_no']}%"))
            if "payer_name" in filters and filters["payer_name"]:
                conditions.append(Payment.payer_name.ilike(f"%{filters['payer_name']}%"))
            if "min_amount" in filters and filters["min_amount"] is not None:
                conditions.append(Payment.amount >= filters["min_amount"])
            if "max_amount" in filters and filters["max_amount"] is not None:
                conditions.append(Payment.amount <= filters["max_amount"])
            if "paid_from" in filters and filters["paid_from"]:
                conditions.append(Payment.paid_at >= filters["paid_from"])
            if "paid_to" in filters and filters["paid_to"]:
                conditions.append(Payment.paid_at <= filters["paid_to"])
            
            if conditions:
                query = query.where(and_(*conditions))
        
        # Sắp xếp theo thời gian thanh toán mới nhất
        query = query.order_by(Payment.paid_at.desc())
        
        # Phân trang
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get(self, payment_id: int) -> Optional[Payment]:
        """Lấy payment theo ID."""
        result = await self.session.execute(
            select(Payment)
            .options(selectinload(Payment.booking))
            .where(Payment.id == payment_id)
        )
        return result.scalar_one_or_none()
    
    async def create(self, payment_data: Dict[str, Any]) -> Payment:
        """Tạo payment mới."""
        payment = Payment(**payment_data)
        self.session.add(payment)
        await self.session.commit()
        await self.session.refresh(payment)
        return payment
    
    async def update(self, payment_id: int, payment_data: Dict[str, Any]) -> Optional[Payment]:
        """Cập nhật payment."""
        payment = await self.get(payment_id)
        if not payment:
            return None
        
        # Cập nhật các trường
        for field, value in payment_data.items():
            if hasattr(payment, field) and value is not None:
                setattr(payment, field, value)
        
        await self.session.commit()
        await self.session.refresh(payment)
        return payment
    
    async def delete(self, payment_id: int) -> bool:
        """Xóa payment."""
        payment = await self.get(payment_id)
        if not payment:
            return False
        
        await self.session.delete(payment)
        await self.session.commit()
        return True
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Đếm tổng số payment với bộ lọc."""
        query = select(func.count(Payment.id))
        
        if filters:
            conditions = []
            if "booking_id" in filters and filters["booking_id"] is not None:
                conditions.append(Payment.booking_id == filters["booking_id"])
            if "payment_method" in filters and filters["payment_method"]:
                conditions.append(Payment.payment_method == filters["payment_method"])
            if "paid_from" in filters and filters["paid_from"]:
                conditions.append(Payment.paid_at >= filters["paid_from"])
            if "paid_to" in filters and filters["paid_to"]:
                conditions.append(Payment.paid_at <= filters["paid_to"])
            
            if conditions:
                query = query.where(and_(*conditions))
        
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def get_by_booking_id(self, booking_id: int) -> List[Payment]:
        """Lấy danh sách payment theo booking ID."""
        result = await self.session.execute(
            select(Payment)
            .where(Payment.booking_id == booking_id)
            .order_by(Payment.paid_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_by_payment_method(self, payment_method: PaymentMethod) -> List[Payment]:
        """Lấy danh sách payment theo phương thức thanh toán."""
        result = await self.session.execute(
            select(Payment).where(Payment.payment_method == payment_method)
        )
        return list(result.scalars().all())
    
    async def get_by_reference_no(self, reference_no: str) -> Optional[Payment]:
        """Lấy payment theo mã tham chiếu."""
        result = await self.session.execute(
            select(Payment).where(Payment.reference_no == reference_no)
        )
        return result.scalar_one_or_none()
    
    async def get_total_amount(self, booking_id: int) -> float:
        """Tính tổng số tiền đã thanh toán cho booking."""
        result = await self.session.execute(
            select(func.sum(Payment.amount))
            .where(Payment.booking_id == booking_id)
        )
        return float(result.scalar() or 0)
    
    async def get_payments_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Payment]:
        """Lấy danh sách payment theo khoảng thời gian."""
        result = await self.session.execute(
            select(Payment)
            .where(
                and_(
                    Payment.paid_at >= start_date,
                    Payment.paid_at <= end_date
                )
            )
            .order_by(Payment.paid_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_daily_revenue(self, date: datetime) -> float:
        """Tính doanh thu theo ngày."""
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        result = await self.session.execute(
            select(func.sum(Payment.amount))
            .where(
                and_(
                    Payment.paid_at >= start_of_day,
                    Payment.paid_at <= end_of_day
                )
            )
        )
        return float(result.scalar() or 0)
    
    async def get_monthly_revenue(self, year: int, month: int) -> float:
        """Tính doanh thu theo tháng."""
        from datetime import date
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        result = await self.session.execute(
            select(func.sum(Payment.amount))
            .where(
                and_(
                    Payment.paid_at >= start_date,
                    Payment.paid_at < end_date
                )
            )
        )
        return float(result.scalar() or 0)