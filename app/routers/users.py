from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from ..db import get_session
from ..auth import get_password_hash
from ..models.user import User, UserRole, UserStatus
from ..dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=8, max_length=256)
    role: UserRole


class UserUpdate(BaseModel):
    username: Optional[str] = Field(default=None, min_length=3, max_length=100)
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None


class PasswordChange(BaseModel):
    password: str = Field(min_length=8, max_length=256)


class UserOut(BaseModel):
    id: int
    username: str
    role: UserRole
    status: UserStatus
    last_login_at: Optional[datetime] = None
    created_at: datetime
    created_by: Optional[int] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = None

    class Config:
        from_attributes = True


def require_manager(user: User):
    if user.role != UserRole.MANAGER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


@router.get("/", response_model=List[UserOut])
async def list_users(
    q: Optional[str] = Query(default=None, description="search by username"),
    skip: int = 0,
    limit: int = 50,
    session: AsyncSession = Depends(get_session),
    current: User = Depends(get_current_user),
):
    require_manager(current)
    stmt = select(User).offset(skip).limit(limit).order_by(User.id.desc())
    if q:
        stmt = select(User).where(User.username.ilike(f"%{q}%")).offset(skip).limit(limit).order_by(User.id.desc())
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    session: AsyncSession = Depends(get_session),
    current: User = Depends(get_current_user),
):
    require_manager(current)
    existed = await session.execute(select(User).where(User.username == payload.username))
    if existed.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
    user = User(
        username=payload.username,
        role=payload.role,
        password_hash=get_password_hash(payload.password),
        status=UserStatus.ACTIVE,
        created_by=current.id,
    )
    session.add(user)
    await session.flush()
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if payload.username and payload.username != user.username:
        chk = await session.execute(select(User.id).where(User.username == payload.username))
        if chk.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")

    values = {}
    if payload.username is not None:
        values["username"] = payload.username
    if payload.role is not None:
        values["role"] = payload.role
    if payload.status is not None:
        values["status"] = payload.status
    values["updated_at"] = datetime.utcnow()
    values["updated_by"] = current.id

    if values:
        await session.execute(update(User).where(User.id == user_id).values(**values))
    res = await session.execute(select(User).where(User.id == user_id))
    return res.scalar_one()


@router.patch("/{user_id}/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    user_id: int,
    payload: PasswordChange,
    session: AsyncSession = Depends(get_session),
    current: User = Depends(get_current_user),
):
    if current.role != UserRole.MANAGER and current.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    res = await session.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await session.execute(
        update(User)
        .where(User.id == user_id)
        .values(password_hash=get_password_hash(payload.password), updated_at=datetime.utcnow(), updated_by=current.id)
    )
    return


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    current: User = Depends(get_current_user),
):
    require_manager(current)
    if current.id == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete yourself")
    res = await session.execute(select(User.id).where(User.id == user_id))
    if not res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await session.execute(delete(User).where(User.id == user_id))
    return
