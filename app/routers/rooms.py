# app/routers/rooms.py
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

from ..db import get_session
from ..models.room import RoomStatus, HousekeepingStatus
from ..repositories.room_repo import RoomRepository
from ..schemas.room import (
    AvailableRoomOut,
    RoomCreate,
    RoomStatusItem,
    RoomUpdate,
    RoomOut,
    PagedRoomOut,
    RoomStatusUpdate,
    HousekeepingStatusUpdate,
)
from app.services.auth_service import require_manager, require_receptionist

router = APIRouter()


def get_room_repo(session: AsyncSession = Depends(get_session)) -> RoomRepository:
    return RoomRepository(session)


@router.get("", response_model=PagedRoomOut)
async def list_rooms(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    name: Optional[str] = None,
    room_type_id: Optional[int] = None,
    status: Optional[RoomStatus] = None,
    housekeeping_status: Optional[HousekeepingStatus] = None,
    repo: RoomRepository = Depends(get_room_repo),
    _: User = Depends(require_receptionist),
):
    filters: Dict[str, Any] = {
        "name": name,
        "room_type_id": room_type_id,
        "status": status,
        "housekeeping_status": housekeeping_status,
    }
    total = await repo.count(filters)
    items = await repo.list(skip=skip, limit=limit, filters=filters)
    return PagedRoomOut(total=total, skip=skip, limit=limit, items=items)


@router.get("/available", response_model=List[AvailableRoomOut])
async def list_available_rooms(
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    room_id: Optional[int] = None,
    room_type_id: Optional[int] = None, 
    occupancy: Optional[int] = None,
    min_base_rate: Optional[Decimal] = None,
    max_base_rate: Optional[Decimal] = None,
    repo: RoomRepository = Depends(get_room_repo),
    _: User = Depends(require_receptionist)
):
    return await repo.get_available_rooms(from_date=from_date, to_date=to_date, room_id=room_id, room_type_id=room_type_id,
        occupancy=occupancy, min_base_rate=min_base_rate, max_base_rate=max_base_rate)


@router.get("/{room_id}", response_model=RoomOut)
async def get_room(room_id: int, repo: RoomRepository = Depends(get_room_repo),
    _: User = Depends(require_receptionist)):
    room = await repo.get(room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy thông tin phòng"
        )
    return room


@router.post("", response_model=RoomOut, status_code=status.HTTP_201_CREATED)
async def create_room(payload: RoomCreate, repo: RoomRepository = Depends(get_room_repo),
    current_user: User = Depends(require_manager)):
    existed = await repo.get_by_name(payload.name)
    if existed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Tên phòng đã tồn tại"
        )
    room = await repo.create(payload.model_dump(exclude_unset=True), current_user)
    return room


@router.put("/{room_id}", response_model=RoomOut)
async def update_room(
    room_id: int, payload: RoomUpdate, repo: RoomRepository = Depends(get_room_repo),
    current_user: User = Depends(require_manager)
):
    data = payload.model_dump(exclude_unset=True)
    new_name = data.get("name")
    if new_name:
        existed = await repo.get_by_name(new_name)
        if existed and existed.id != room_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Tên phòng đã tồn tại"
            )
    updated = await repo.update(room_id, data, current_user)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy thông tin phòng"
        )
    return updated


@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_room(room_id: int, repo: RoomRepository = Depends(get_room_repo),
    _: User = Depends(require_manager)):
    try:
        ok = await repo.delete(room_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Room not found"
        )
    return None


@router.patch("/{room_id}/status", response_model=RoomOut)
async def update_room_status(
    room_id: int, payload: RoomStatusUpdate, repo: RoomRepository = Depends(get_room_repo),
    current_user: User = Depends(require_receptionist)
):
    updated = await repo.update(room_id, {"status": payload.status}, current_user)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy thông tin phòng"
        )
    return updated


@router.patch("/{room_id}/housekeeping", response_model=RoomOut)
async def update_room_housekeeping(
    room_id: int,
    payload: HousekeepingStatusUpdate,
    repo: RoomRepository = Depends(get_room_repo),
    current_user: User = Depends(require_receptionist)
):
    updated = await repo.update(room_id, {"housekeeping_status": payload.housekeeping_status}, current_user)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy thông tin phòng"
        )
    return updated


@router.get("/enum/room-statuses", response_model=List[RoomStatusItem])
async def get_room_statuses(_: User = Depends(require_receptionist)):
    return [
        RoomStatusItem(value=RoomStatus.AVAILABLE.value, label="Trống"),
        RoomStatusItem(value=RoomStatus.OCCUPIED.value, label="Đang sử dụng"),
        RoomStatusItem(value=RoomStatus.OUT_OF_SERVICE.value, label="Ngưng phục vụ"),
    ]

@router.get("/enum/housekeeping-statuses", response_model=List[RoomStatusItem])
async def get_housekeeping_statuses(_: User = Depends(require_receptionist)):
    return [
        RoomStatusItem(value=HousekeepingStatus.CLEAN.value, label="Sạch"),
        RoomStatusItem(value=HousekeepingStatus.DIRTY.value, label="Bẩn"),
        RoomStatusItem(value=HousekeepingStatus.CLEANING.value, label="Đang dọn dẹp"),
        RoomStatusItem(value=HousekeepingStatus.INSPECTED.value, label="Đã kiểm tra"),
    ]