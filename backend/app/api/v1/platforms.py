"""M1 平台管理接口。"""

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.core.deps import get_db, require_permission
from app.core.response import success, success_page
from app.models.system import User
from app.schemas.common import StatusRequest
from app.schemas.platform import PlatformCreate, PlatformUpdate
from app.services import sync_service

router = APIRouter(prefix="/platforms", tags=["平台管理"])


@router.get("", summary="平台列表")
def list_platforms(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: str | None = None,
    status: int | None = None,
    _: User = Depends(require_permission("platform:list")),
    session: Session = Depends(get_db),
):
    items, total = sync_service.list_platforms(session, page, page_size, keyword, status)
    return success_page(items, total, page, page_size)


@router.get("/options", summary="平台下拉选项")
def platform_options(
    _: User = Depends(require_permission("platform:list")),
    session: Session = Depends(get_db),
):
    return success(sync_service.platform_options(session))


@router.post("", summary="新增平台")
def create_platform(
    payload: PlatformCreate,
    operator: User = Depends(require_permission("platform:create")),
    session: Session = Depends(get_db),
):
    return success(sync_service.create_platform(session, payload, operator))


@router.get("/{platform_id}", summary="平台详情")
def get_platform(
    platform_id: int,
    _: User = Depends(require_permission("platform:list")),
    session: Session = Depends(get_db),
):
    return success(sync_service.get_platform(session, platform_id))


@router.put("/{platform_id}", summary="编辑平台")
def update_platform(
    platform_id: int,
    payload: PlatformUpdate,
    operator: User = Depends(require_permission("platform:edit")),
    session: Session = Depends(get_db),
):
    return success(sync_service.update_platform(session, platform_id, payload, operator))


@router.delete("/{platform_id}", summary="删除平台")
def delete_platform(
    platform_id: int,
    operator: User = Depends(require_permission("platform:delete")),
    session: Session = Depends(get_db),
):
    sync_service.delete_platform(session, platform_id, operator)
    return success(None)


@router.patch("/{platform_id}/status", summary="启用/停用平台")
def set_platform_status(
    platform_id: int,
    payload: StatusRequest,
    operator: User = Depends(require_permission("platform:status")),
    session: Session = Depends(get_db),
):
    return success(sync_service.set_platform_status(session, platform_id, payload.status, operator))
