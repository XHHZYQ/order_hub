"""M5 库存接口：库存列表/详情/编辑、流水、共享、占用释放、回写平台、盘点、预警。"""

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.core.deps import get_allowed_shop_ids, get_db, require_permission
from app.core.exceptions import forbidden
from app.core.response import success, success_page
from app.models.system import User
from app.schemas.inventory import (
    AlertConfigUpdate,
    InventoryOccupyRequest,
    InventoryReleaseRequest,
    InventoryShareCreate,
    InventoryShareUpdate,
    InventoryUpdateRequest,
    StocktakeRequest,
)
from app.services import inventory_service

router = APIRouter(prefix="/inventory", tags=["库存"])


def _assert_shop_allowed(shop_id: int, allowed_shop_ids: list[int] | None) -> None:
    if allowed_shop_ids is not None and shop_id not in allowed_shop_ids:
        raise forbidden("无权操作该店铺库存共享")


# --- 静态路径须注册在 /{sku_id} 之前，避免被当作 sku_id 解析 --- #
@router.get("", summary="库存列表")
def list_inventory(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: str | None = None,
    status: int | None = None,
    alert_only: bool = False,
    _: User = Depends(require_permission("inventory:list")),
    session: Session = Depends(get_db),
):
    items, total = inventory_service.list_inventory(
        session, page=page, page_size=page_size, keyword=keyword, status=status, alert_only=alert_only
    )
    return success_page(items, total, page, page_size)


@router.get("/flows", summary="库存流水列表")
def list_flows(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    sku_id: int | None = None,
    flow_type: str | None = None,
    source_type: str | None = None,
    source_no: str | None = None,
    keyword: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    _: User = Depends(require_permission("inventory:flow")),
    session: Session = Depends(get_db),
):
    from app.utils.datetime_util import parse_datetime

    items, total = inventory_service.list_flows(
        session,
        page=page,
        page_size=page_size,
        sku_id=sku_id,
        flow_type=flow_type,
        source_type=source_type,
        source_no=source_no,
        keyword=keyword,
        start_time=parse_datetime(start_time),
        end_time=parse_datetime(end_time),
    )
    return success_page(items, total, page, page_size)


# --------------------------------------------------------------------------- #
# 库存共享
# --------------------------------------------------------------------------- #
@router.get("/shares", summary="库存共享列表")
def list_shares(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: str | None = None,
    sku_id: int | None = None,
    shop_id: int | None = None,
    platform_code: str | None = None,
    status: int | None = None,
    _: User = Depends(require_permission("inventory:share")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    items, total = inventory_service.list_shares(
        session,
        page=page,
        page_size=page_size,
        keyword=keyword,
        sku_id=sku_id,
        shop_id=shop_id,
        platform_code=platform_code,
        status=status,
        allowed_shop_ids=allowed_shop_ids,
    )
    return success_page(items, total, page, page_size)


@router.post("/shares", summary="新增库存共享")
def create_share(
    payload: InventoryShareCreate,
    operator: User = Depends(require_permission("inventory:share_edit")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    _assert_shop_allowed(payload.shop_id, allowed_shop_ids)
    return success(inventory_service.create_share(session, payload, operator))


@router.put("/shares/{share_id}", summary="编辑库存共享")
def update_share(
    share_id: int,
    payload: InventoryShareUpdate,
    operator: User = Depends(require_permission("inventory:share_edit")),
    session: Session = Depends(get_db),
):
    return success(inventory_service.update_share(session, share_id, payload, operator))


@router.delete("/shares/{share_id}", summary="删除库存共享")
def delete_share(
    share_id: int,
    operator: User = Depends(require_permission("inventory:share_edit")),
    session: Session = Depends(get_db),
):
    inventory_service.delete_share(session, share_id, operator)
    return success(None)


# --------------------------------------------------------------------------- #
# 占用 / 释放
# --------------------------------------------------------------------------- #
@router.post("/occupy", summary="订单占用库存")
def occupy_stock(
    payload: InventoryOccupyRequest,
    operator: User = Depends(require_permission("inventory:edit")),
    session: Session = Depends(get_db),
):
    result = inventory_service.occupy_stock(
        session, sku_id=payload.sku_id, qty=payload.qty, source_no=payload.source_no, remark=payload.remark, operator=operator
    )
    session.commit()
    return success(result)


@router.post("/release", summary="订单释放占用")
def release_stock(
    payload: InventoryReleaseRequest,
    operator: User = Depends(require_permission("inventory:edit")),
    session: Session = Depends(get_db),
):
    result = inventory_service.release_stock(
        session, sku_id=payload.sku_id, qty=payload.qty, source_no=payload.source_no, remark=payload.remark, operator=operator
    )
    session.commit()
    return success(result)


# --------------------------------------------------------------------------- #
# 预警
# --------------------------------------------------------------------------- #
@router.get("/alerts", summary="库存预警列表")
def list_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: str | None = None,
    _: User = Depends(require_permission("inventory:alert")),
    session: Session = Depends(get_db),
):
    items, total = inventory_service.list_alerts(session, page=page, page_size=page_size, keyword=keyword)
    return success_page(items, total, page, page_size)


@router.get("/alert-configs", summary="库存预警配置列表")
def list_alert_configs(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: str | None = None,
    is_enabled: int | None = None,
    _: User = Depends(require_permission("inventory:alert")),
    session: Session = Depends(get_db),
):
    items, total = inventory_service.list_alert_configs(
        session, page=page, page_size=page_size, keyword=keyword, is_enabled=is_enabled
    )
    return success_page(items, total, page, page_size)


@router.put("/alert-configs/{alert_id}", summary="编辑库存预警配置")
def update_alert_config(
    alert_id: int,
    payload: AlertConfigUpdate,
    operator: User = Depends(require_permission("inventory:alert_edit")),
    session: Session = Depends(get_db),
):
    return success(inventory_service.update_alert_config(session, alert_id, payload, operator))


# --------------------------------------------------------------------------- #
# 盘点
# --------------------------------------------------------------------------- #
@router.post("/stocktake", summary="库存盘点提交")
def submit_stocktake(
    payload: StocktakeRequest,
    operator: User = Depends(require_permission("inventory:stocktake")),
    session: Session = Depends(get_db),
):
    return success(inventory_service.stocktake(session, payload, operator))


# --------------------------------------------------------------------------- #
# 库存详情 / 编辑 / 回写
# --------------------------------------------------------------------------- #
@router.get("/{sku_id}", summary="库存详情")
def get_inventory(
    sku_id: int,
    _: User = Depends(require_permission("inventory:list")),
    session: Session = Depends(get_db),
):
    return success(inventory_service.get_inventory(session, sku_id))


@router.put("/{sku_id}", summary="编辑主库存")
def update_inventory(
    sku_id: int,
    payload: InventoryUpdateRequest,
    operator: User = Depends(require_permission("inventory:edit")),
    session: Session = Depends(get_db),
):
    return success(inventory_service.update_main_qty(session, sku_id, payload, operator))


@router.post("/{sku_id}/push", summary="回写平台库存")
def push_inventory(
    sku_id: int,
    operator: User = Depends(require_permission("inventory:push")),
    session: Session = Depends(get_db),
):
    return success(inventory_service.push_inventory(session, sku_id, operator))
