from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from .db import get_session
from .models.user import User, UserRole
from .auth import verify_token, check_user_permissions

# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_session),
) -> User:
    token = credentials.credentials
    payload = verify_token(token)

    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Không thể xác thực thông tin đăng nhập",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    result = await session.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Không tìm thấy người dùng",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.status != "Active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tài khoản người dùng đã bị khóa",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user


def require_role(required_roles: List[UserRole]):
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if not check_user_permissions(current_user, required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )
        return current_user

    return role_checker


# Các dependency vai trò thường dùng
require_manager = require_role([UserRole.MANAGER])
require_receptionist = require_role([UserRole.MANAGER, UserRole.RECEPTIONIST])
require_housekeeping = require_role([UserRole.MANAGER, UserRole.HOUSEKEEPING])
require_accountant = require_role([UserRole.MANAGER, UserRole.ACCOUNTANT])
require_hotel_ops = require_role(
    [UserRole.MANAGER, UserRole.RECEPTIONIST, UserRole.HOUSEKEEPING]
)
