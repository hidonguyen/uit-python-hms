# app/routers/services.py
from decimal import Decimal
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.auth_service import require_manager, require_receptionist

from ..db import get_session
from ..models.service import ServiceStatus
from ..repositories.service_repo import ServiceRepository
from ..schemas.service import PagedServiceOut, ServiceChangePrice, ServiceCreate, ServiceOut, ServiceUpdate

router = APIRouter()

def get_service_repo(session: AsyncSession = Depends(get_session)) -> ServiceRepository:
    return ServiceRepository(session)


@router.get("", response_model=PagedServiceOut)
async def list_services(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    name: Optional[str] = None,
    unit: Optional[str] = None,
    status: Optional[ServiceStatus] = None,
    min_price: Optional[Decimal] = Query(None, ge=0),
    max_price: Optional[Decimal] = Query(None, ge=0),
    service_repo: ServiceRepository = Depends(get_service_repo),
    _: User = Depends(require_receptionist)
):
    filters: Dict[str, Any] = {
        "name": name,
        "unit": unit,
        "status": status,
        "min_price": min_price,
        "max_price": max_price,
    }

    total = await service_repo.count(filters)
    services = await service_repo.list(skip=skip, limit=limit, filters=filters)

    return PagedServiceOut(total=total, skip=skip, limit=limit, items=services)


@router.get("/{service_id}", response_model=ServiceOut)
async def get_service(
    service_id: int,
    service_repo: ServiceRepository = Depends(get_service_repo),
    _: User = Depends(require_receptionist)
):
    service = await service_repo.get(service_id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy thông tin dịch vụ"
        )
    return service


@router.post("", response_model=ServiceOut, status_code=status.HTTP_201_CREATED)
async def create_service(
    payload: ServiceCreate,
    service_repo: ServiceRepository = Depends(get_service_repo),
    current_user: User = Depends(require_receptionist)
):
    existed = await service_repo.get_by_name(payload.name)
    if existed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Tên dịch vụ đã tồn tại"
        )
    
    return await service_repo.create(payload.model_dump(exclude_unset=True), current_user)


@router.put("/{service_id}", response_model=ServiceOut)
async def update_service(
    service_id: int, 
    payload: ServiceUpdate, 
    service_repo: ServiceRepository = Depends(get_service_repo),
    current_user: User = Depends(require_receptionist)
):
    new_name = payload.name
    if new_name:
        existed = await service_repo.get_by_name(new_name)
        if existed and existed.id != service_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Tên dịch vụ đã tồn tại"
            )

    updated = await service_repo.update(service_id, payload.model_dump(exclude_unset=True), current_user)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy thông tin dịch vụ"
        )

    return updated


@router.patch("/{service_id}/change-price", response_model=ServiceOut)
async def change_service_price(
    service_id: int, 
    payload: ServiceChangePrice, 
    repo: ServiceRepository = Depends(get_service_repo),
    current_user: User = Depends(require_manager)
):
    new_price = payload.price
    if new_price is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Giá mới không được để trống"
        )

    updated = await repo.update(service_id, {"price": new_price}, current_user)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy thông tin dịch vụ"
        )

    return updated


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(
    service_id: int, 
    repo: ServiceRepository = Depends(get_service_repo),
    _: User = Depends(require_manager)
):
    try:
        deleted = await repo.delete(service_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy thông tin dịch vụ"
        )
    
    return None
