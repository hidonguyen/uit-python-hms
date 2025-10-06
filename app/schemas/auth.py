from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional
from ..models.user import UserRole

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6, max_length=100)

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6, max_length=100)
    role: UserRole

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class UserOut(BaseModel):
    id: int
    username: str
    role: UserRole
    status: str
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}