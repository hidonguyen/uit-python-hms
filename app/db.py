from typing import AsyncGenerator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from .config import settings
from .models import Base

engine = create_async_engine(
    settings.db_url(),
    echo=True,
    pool_pre_ping=True,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def create_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def seed_initial_data() -> None:
    from .models.user import User, UserRole, UserStatus
    from .services.auth_service import get_password_hash

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.role == UserRole.MANAGER)
        )
        admin_user = result.scalars().first()
        if not admin_user:
            admin_user = User(
                username="manager",
                role=UserRole.MANAGER,
                password_hash=get_password_hash("manager"),
                status=UserStatus.ACTIVE,
            )
            session.add(admin_user)
            await session.commit()

        
        result = await session.execute(
            select(User).where(User.role == UserRole.RECEPTIONIST)
        )
        receptionist_user = result.scalars().first()
        if not receptionist_user:
            receptionist_user = User(
                username="receptionist",
                role=UserRole.RECEPTIONIST,
                password_hash=get_password_hash("receptionist"),
                status=UserStatus.ACTIVE,
            )
            session.add(receptionist_user)
            await session.commit()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
