from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional
from ..models.user import UserRole, UserStatus


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    role: UserRole


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    password: Optional[str] = Field(None, min_length=6, max_length=100)


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(UserBase):
    id: int
    status: UserStatus
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
