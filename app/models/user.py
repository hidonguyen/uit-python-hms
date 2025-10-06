from sqlalchemy import BigInteger, String, Text, DateTime, Enum, Index, ForeignKey
from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy.sql import func
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
    __tablename__ = "users"
    
    id = mapped_column(BigInteger, primary_key=True)
    username = mapped_column(String(100), nullable=False, unique=True)
    role = mapped_column(Enum(UserRole), nullable=False)
    password_hash = mapped_column(Text, nullable=False)
    status = mapped_column(Enum(UserStatus), nullable=False, default=UserStatus.ACTIVE)
    last_login_at = mapped_column(DateTime(timezone=True), nullable=True)
    created_at = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_by = mapped_column(BigInteger, ForeignKey("users.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    updated_at = mapped_column(DateTime(timezone=True), nullable=True)
    updated_by = mapped_column(BigInteger, ForeignKey("users.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    
    created_users = relationship("User", foreign_keys=[created_by], remote_side=[id])
    updated_users = relationship("User", foreign_keys=[updated_by], remote_side=[id])
    
    __table_args__ = (
        Index("ix_users_username", "username"),
        Index("ix_users_role", "role"),
        Index("ix_users_status", "status"),
    )