from sqlalchemy.orm import DeclarativeBase, mapped_column
from sqlalchemy.sql import func
from sqlalchemy import (
    BigInteger,
    DateTime,
)

class Base(DeclarativeBase):
    id = mapped_column(BigInteger, primary_key=True)
    created_at = mapped_column(DateTime(timezone=False), nullable=False, server_default=func.now())
    created_by = mapped_column(BigInteger, nullable=True)
    updated_at = mapped_column(DateTime(timezone=False), nullable=True)
    updated_by = mapped_column(BigInteger, nullable=True)