from sqlalchemy import String, Text, DateTime, Enum, Index
from sqlalchemy.orm import mapped_column
from .base import Base
import enum

class UserRole(str, enum.Enum):
    MANAGER = "Manager"
    RECEPTIONIST = "Receptionist" 
    HOUSEKEEPING = "Housekeeping"
    ACCOUNTANT = "Accountant"

class UserStatus(str, enum.Enum):
    ACTIVE = "Active"
    LOCKED = "Locked"

class User(Base):
    def __init__(self, id=None, username=None, role=None, password_hash=None, status=UserStatus.ACTIVE):
        super().__init__(id=id)
        self.username = username
        self.role = role
        self.password_hash = password_hash
        self.status = status

    __tablename__ = "users"
    
    username = mapped_column(String(100), nullable=False, unique=True)
    role = mapped_column(Enum(UserRole, name="UserRole", native_enum=False, length=50, validate_strings=True), nullable=False)
    password_hash = mapped_column(Text, nullable=False)
    status = mapped_column(Enum(UserStatus, name="UserStatus", native_enum=False, length=50, validate_strings=True), nullable=False, default=UserStatus.ACTIVE)
    last_login_at = mapped_column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        Index("ix_users_username", "username"),
        Index("ix_users_role", "role"),
        Index("ix_users_status", "status"),
    )