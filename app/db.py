from datetime import datetime
from typing import AsyncGenerator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from .config import settings
from .models import Base

engine = create_async_engine(
    settings.db_url(),
    echo=settings.app_debug,
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
    async with AsyncSessionLocal() as session:
        await seed_users(session)
        await seed_room_types(session)
        await seed_rooms(session)
        await seed_services(session)
        await seed_guests(session)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def seed_users(session: AsyncSession) -> None:
    from .models.user import User, UserRole, UserStatus
    from .services.auth_service import get_password_hash

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

    # Seed default receptionist user if not exists
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

async def seed_room_types(session: AsyncSession) -> None:
    from .models.room_type import RoomType
    from decimal import Decimal

    result = await session.execute(select(RoomType))
    room_type = result.scalars().first()
    if not room_type:
        room_types = [
            RoomType(
                code="STD",
                name="Standard",
                base_occupancy=2,
                max_occupancy=3,
                base_rate=Decimal("400000"),
                hour_rate=Decimal("80000"),
                extra_adult_fee=Decimal("100000"),
                extra_child_fee=Decimal("50000"),
                description="Phòng cơ bản 1 giường đôi",
            ),
            RoomType(
                code="DLX",
                name="Deluxe",
                base_occupancy=2,
                max_occupancy=4,
                base_rate=Decimal("600000"),
                hour_rate=Decimal("100000"),
                extra_adult_fee=Decimal("150000"),
                extra_child_fee=Decimal("70000"),
                description="Phòng cao cấp có ban công",
            ),
            RoomType(
                code="STE",
                name="Suite",
                base_occupancy=2,
                max_occupancy=5,
                base_rate=Decimal("1000000"),
                hour_rate=Decimal("150000"),
                extra_adult_fee=Decimal("200000"),
                extra_child_fee=Decimal("100000"),
                description="Phòng hạng sang view đẹp",
            ),
            RoomType(
                code="FAM",
                name="Family",
                base_occupancy=3,
                max_occupancy=6,
                base_rate=Decimal("750000"),
                hour_rate=Decimal("120000"),
                extra_adult_fee=Decimal("180000"),
                extra_child_fee=Decimal("90000"),
                description="Phòng gia đình rộng rãi",
            ),
            RoomType(
                code="SPR",
                name="Superior",
                base_occupancy=2,
                max_occupancy=3,
                base_rate=Decimal("500000"),
                hour_rate=Decimal("90000"),
                extra_adult_fee=Decimal("120000"),
                extra_child_fee=Decimal("60000"),
                description="Phòng superior nâng cấp",
            ),
        ]
        session.add_all(room_types)
        await session.commit()

async def seed_rooms(session: AsyncSession) -> None:
    from .models.room import Room, RoomStatus, HousekeepingStatus
    from .models.room_type import RoomType

    result = await session.execute(select(Room))
    room = result.scalars().first()
    if not room:
        result = await session.execute(select(RoomType))
        room_types = result.scalars().all()
        rooms = []
        for i in range(1, 21):
            room_type = room_types[i % len(room_types)]
            room = Room(
                name=f"Phòng {i:03}",
                room_type_id=room_type.id,
                status=RoomStatus.AVAILABLE,
                housekeeping_status=HousekeepingStatus.CLEAN,
            )
            rooms.append(room)
        session.add_all(rooms)
        await session.commit()

async def seed_services(session: AsyncSession) -> None:
    from .models.service import Service, ServiceStatus
    from decimal import Decimal

    result = await session.execute(select(Service))
    service = result.scalars().first()
    if not service:
        services = [
            Service(
                name="Giặt ủi",
                unit="lần",
                price=Decimal("50000"),
                description="Giặt ủi quần áo cho khách",
                status=ServiceStatus.ACTIVE,
            ),
            Service(
                name="Ăn sáng",
                unit="suất",
                price=Decimal("80000"),
                description="Buffet sáng tại nhà hàng",
                status=ServiceStatus.ACTIVE,
            ),
            Service(
                name="Spa",
                unit="lần",
                price=Decimal("300000"),
                description="Dịch vụ massage thư giãn",
                status=ServiceStatus.ACTIVE,
            ),
            Service(
                name="Đưa đón sân bay",
                unit="lượt",
                price=Decimal("250000"),
                description="Xe 4 chỗ đưa/đón sân bay",
                status=ServiceStatus.ACTIVE,
            ),
            Service(
                name="Mini bar",
                unit="lần",
                price=Decimal("120000"),
                description="Set minibar tiêu chuẩn",
                status=ServiceStatus.ACTIVE,
            ),
            Service(
                name="Late checkout",
                unit="lần",
                price=Decimal("200000"),
                description="Trả phòng muộn đến 15:00",
                status=ServiceStatus.ACTIVE,
            ),
        ]
        session.add_all(services)
        await session.commit()

async def seed_guests(session: AsyncSession) -> None:
    from .models.guest import Guest, Gender, DocumentType

    result = await session.execute(select(Guest))
    guest = result.scalars().first()
    if not guest:
        guests = [
            Guest(
                name="Nguyễn Văn A",
                gender=Gender.MALE,
                date_of_birth=datetime.strptime("1990-01-01", "%Y-%m-%d"),
                nationality="Việt Nam",
                document_type=DocumentType.ID_CARD,
                document_no="123456789",
                document_issue_date=datetime.strptime("2010-01-01", "%Y-%m-%d"),
                document_expiry_date=datetime.strptime("2030-01-01", "%Y-%m-%d"),
                document_issue_place="Công an TP.HCM",
                phone="0123456789",
                email="nguyenvana@example.com",
                address="123 Đường ABC, Quận 1, TP.HCM",
                description="Khách hàng VIP",
            ),
            Guest(
                name="Trần Thị B",
                gender=Gender.FEMALE,
                date_of_birth=datetime.strptime("1995-05-05", "%Y-%m-%d"),
                nationality="Việt Nam",
                document_type=DocumentType.ID_CARD,
                document_no="987654321",
                document_issue_date=datetime.strptime("2015-05-05", "%Y-%m-%d"),
                document_expiry_date=datetime.strptime("2025-05-05", "%Y-%m-%d"),
                document_issue_place="Công an TP.HCM",
                phone="0987654321",
                email="tranthib@example.com",
                address="456 Đường DEF, Quận 2, TP.HCM",
                description="Khách hàng thường",
            ),
            Guest(
                name="Hoàng Minh C",
                gender=Gender.MALE,
                date_of_birth=datetime.strptime("1985-03-15", "%Y-%m-%d"),
                nationality="Việt Nam",
                document_type=DocumentType.ID_CARD,
                document_no="456789123",
                document_issue_date=datetime.strptime("2010-01-01", "%Y-%m-%d"),
                document_expiry_date=datetime.strptime("2030-01-01", "%Y-%m-%d"),
                document_issue_place="Công an TP.HCM",
                phone="0123456788",
                email="hoangminhc@example.com",
                address="789 Đường GHI, Quận 3, TP.HCM",
                description="Khách hàng VIP",
            )
        ]
        session.add_all(guests)
        await session.commit()