"""M1 店铺管理接口（含数据权限过滤）。"""

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.core.deps import get_allowed_shop_ids, get_db, require_permission
from app.core.response import success, success_page
from app.models.system import User
from app.schemas.common import StatusRequest
from app.schemas.platform import ShopCreate, ShopUpdate
from app.services import sync_service

router = APIRouter(prefix="/shops", tags=["店铺管理"])


@router.get("", summary="店铺列表")
def list_shops(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: str | None = None,
    platform_code: str | None = None,
    status: int | None = None,
    auth_status: int | None = None,
    _: User = Depends(require_permission("shop:list")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    items, total = sync_service.list_shops(
        session, page, page_size, keyword, platform_code, status, auth_status, allowed_shop_ids
    )
    return success_page(items, total, page, page_size)


@router.get("/options", summary="店铺下拉选项（按数据权限过滤）")
def shop_options(
    _: User = Depends(require_permission("shop:list")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    return success(sync_service.shop_options(session, allowed_shop_ids))


@router.post("", summary="新增店铺")
def create_shop(
    payload: ShopCreate,
    operator: User = Depends(require_permission("shop:create")),
    session: Session = Depends(get_db),
):
    return success(sync_service.create_shop(session, payload, operator))


@router.get("/{shop_id}", summary="店铺详情")
def get_shop(
    shop_id: int,
    _: User = Depends(require_permission("shop:list")),
    session: Session = Depends(get_db),
):
    return success(sync_service.get_shop(session, shop_id))


@router.put("/{shop_id}", summary="编辑店铺")
def update_shop(
    shop_id: int,
    payload: ShopUpdate,
    operator: User = Depends(require_permission("shop:edit")),
    session: Session = Depends(get_db),
):
    return success(sync_service.update_shop(session, shop_id, payload, operator))


@router.delete("/{shop_id}", summary="删除店铺")
def delete_shop(
    shop_id: int,
    operator: User = Depends(require_permission("shop:delete")),
    session: Session = Depends(get_db),
):
    sync_service.delete_shop(session, shop_id, operator)
    return success(None)


@router.patch("/{shop_id}/status", summary="启用/停用店铺")
def set_shop_status(
    shop_id: int,
    payload: StatusRequest,
    operator: User = Depends(require_permission("shop:status")),
    session: Session = Depends(get_db),
):
    return success(sync_service.set_shop_status(session, shop_id, payload.status, operator))


@router.post("/{shop_id}/authorize", summary="店铺授权（模拟）")
def authorize_shop(
    shop_id: int,
    operator: User = Depends(require_permission("shop:authorize")),
    session: Session = Depends(get_db),
):
    return success(sync_service.authorize_shop(session, shop_id, operator))
