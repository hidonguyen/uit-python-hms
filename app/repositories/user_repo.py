from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from ..models.user import User, UserRole

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Lấy người dùng theo tên đăng nhập."""
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Lấy người dùng theo ID."""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def create(self, user: User) -> User:
        """Tạo người dùng mới."""
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
    
    async def update_last_login(self, user: User) -> None:
        """Cập nhật thời gian đăng nhập cuối."""
        from datetime import datetime
        user.last_login_at = datetime.now()
        await self.session.commit()
    
    async def count_users(self) -> int:
        """Đếm tổng số người dùng."""
        result = await self.session.execute(select(func.count(User.id)))
        return result.scalar() or 0
    
    async def get_users_by_role(self, role: UserRole) -> list[User]:
        """Lấy danh sách người dùng theo vai trò."""
        result = await self.session.execute(
            select(User).where(User.role == role)
        )
        return list(result.scalars().all())