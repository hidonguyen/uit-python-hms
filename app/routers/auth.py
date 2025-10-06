from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
from typing import Annotated

from ..db import get_session
from ..models.user import User, UserRole
from ..schemas.auth import RegisterRequest, Token, UserOut
from ..auth import verify_password, get_password_hash, create_access_token
from ..repositories.user_repo import UserRepository
from ..config import settings
from ..dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: RegisterRequest, session: AsyncSession = Depends(get_session)
):
    user_repo = UserRepository(session)
    existing_user = await user_repo.get_by_username(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tên người dùng đã được đăng ký",
        )

    user_count = await user_repo.count_users()
    if user_count > 0 and user_data.role != UserRole.MANAGER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ Manager mới có thể tạo người dùng mới",
        )

    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        role=user_data.role,
        password_hash=hashed_password,
        status="Active",
    )

    created_user = await user_repo.create(db_user)
    return created_user


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: AsyncSession = Depends(get_session),
):
    user_repo = UserRepository(session)
    user = await user_repo.get_by_username(form_data.username)

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tên người dùng hoặc mật khẩu không đúng",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.status != "Active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tài khoản người dùng đã bị khóa",
            headers={"WWW-Authenticate": "Bearer"},
        )

    await user_repo.update_last_login(user)

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value},
        expires_delta=access_token_expires,
    )

    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
    }


@router.get("/me", response_model=UserOut)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user
