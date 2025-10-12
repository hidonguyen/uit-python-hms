from datetime import datetime, timedelta
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..db import get_session
from ..schemas.user import UserCreate, UserOut, UserUpdate, UserLogin, Token
from ..models.user import User, UserRole, UserStatus
from ..services.auth_service import (
    create_access_token,
    get_current_user,
    get_password_hash,
    require_manager,
    verify_password,
)
from app.repositories.user_repo import UserRepository

router = APIRouter()

@router.post("/login", response_model=Token)
async def login(
    payload: UserLogin,
    session: AsyncSession = Depends(get_session),
):
    user_repo = UserRepository(session)
    user = await user_repo.get_by_username(payload.username)

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tên người dùng hoặc mật khẩu không đúng",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.status != UserStatus.ACTIVE:
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


@router.get("/", response_model=List[UserOut])
async def list_users(
    q: Optional[str] = Query(default=None, description="search by username"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
    current: User = Depends(get_current_user),
):
    await require_manager(current)
    
    stmt = select(User).order_by(User.id.desc()).offset(skip).limit(limit)
    if q:
        stmt = (
            select(User)
            .where(User.username.ilike(f"%{q}%"))
            .order_by(User.id.desc())
            .offset(skip)
            .limit(limit)
        )
    res = await session.execute(stmt)
    return list(res.scalars().all())


@router.get("/{user_id}", response_model=UserOut)
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    current: User = Depends(get_current_user),
):
    require_manager(current)
    res = await session.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    session: AsyncSession = Depends(get_session),
    current: User = Depends(get_current_user),
):
    require_manager(current)
    existed = await session.execute(
        select(User.id).where(User.username == payload.username)
    )
    if existed.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists"
        )

    user = User(
        username=payload.username,
        role=payload.role,
        password_hash=get_password_hash(payload.password),
        status=UserStatus.ACTIVE,
        created_by=current.id,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@router.put("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int,
    payload: UserUpdate,
    session: AsyncSession = Depends(get_session),
    current: User = Depends(get_current_user),
):
    require_manager(current)

    res = await session.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if payload.username and payload.username != user.username:
        chk = await session.execute(
            select(User.id).where(User.username == payload.username)
        )
        if chk.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )

    values = {}
    if payload.username is not None:
        values["username"] = payload.username
    if payload.role is not None:
        values["role"] = payload.role
    if payload.status is not None:
        values["status"] = payload.status
    if payload.password is not None:
        values["password_hash"] = get_password_hash(payload.password)
    values["updated_at"] = datetime.now()
    values["updated_by"] = current.id

    if values:
        await session.execute(update(User).where(User.id == user_id).values(**values))
        await session.commit()

    res = await session.execute(select(User).where(User.id == user_id))
    return res.scalar_one()


@router.patch("/{user_id}/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    user_id: int,
    payload: UserUpdate,
    session: AsyncSession = Depends(get_session),
    current: User = Depends(get_current_user),
):
    if current.role != UserRole.MANAGER and current.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    if payload.password is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Password is required"
        )

    res = await session.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    await session.execute(
        update(User)
        .where(User.id == user_id)
        .values(
            password_hash=get_password_hash(payload.password),
            updated_at=datetime.now(),
            updated_by=current.id,
        )
    )
    await session.commit()
    return


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    current: User = Depends(get_current_user),
):
    require_manager(current)

    if current.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete yourself"
        )

    res = await session.execute(select(User.id).where(User.id == user_id))
    if not res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    await session.execute(delete(User).where(User.id == user_id))
    await session.commit()
    return
