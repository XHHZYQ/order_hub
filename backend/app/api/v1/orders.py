"""M2 订单接口：订单列表/详情/明细/扩展/日志，手动同步、补单与同步异常处理。"""

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.core.deps import get_allowed_shop_ids, get_db, require_permission
from app.core.exceptions import forbidden
from app.core.response import success, success_page
from app.models.system import User
from app.schemas.order import (
    OrderAddressRequest,
    OrderAuditRequest,
    OrderBatchAuditRequest,
    OrderBatchIdsRequest,
    OrderBatchRemarkRequest,
    OrderErrorHandleRequest,
    OrderMergeRequest,
    OrderPriceRequest,
    OrderRemarkRequest,
    OrderSplitRequest,
    OrderStatusChangeRequest,
    OrderSyncRequest,
)
from app.services import after_sale_service, order_service, sync_service

router = APIRouter(prefix="/orders", tags=["订单"])


def _assert_shop_allowed(session: Session, order_id: int, allowed_shop_ids: list[int] | None) -> None:
    """数据权限校验：非超管用户仅能操作其可访问店铺的订单。"""
    if allowed_shop_ids is None:
        return
    order = order_service.get_order(session, order_id)
    if order["shop_id"] not in allowed_shop_ids:
        raise forbidden("无权操作该店铺订单")


# --- 静态路径须注册在 /{order_id} 之前，避免被当作 id 解析 --- #
@router.get("", summary="订单列表")
def list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    shop_id: int | None = None,
    platform_code: str | None = None,
    status: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    keyword: str | None = None,
    goods_keyword: str | None = None,
    _: User = Depends(require_permission("order:list")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    items, total = order_service.list_orders(
        session,
        page=page,
        page_size=page_size,
        shop_id=shop_id,
        platform_code=platform_code,
        status=status,
        start_time=start_time,
        end_time=end_time,
        keyword=keyword,
        goods_keyword=goods_keyword,
        allowed_shop_ids=allowed_shop_ids,
    )
    return success_page(items, total, page, page_size)


@router.get("/sync-errors", summary="同步异常订单列表")
def list_sync_errors(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    shop_id: int | None = None,
    platform_code: str | None = None,
    status: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    keyword: str | None = None,
    goods_keyword: str | None = None,
    _: User = Depends(require_permission("order:list")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    items, total = order_service.list_sync_errors(
        session,
        page=page,
        page_size=page_size,
        shop_id=shop_id,
        platform_code=platform_code,
        status=status,
        start_time=start_time,
        end_time=end_time,
        keyword=keyword,
        goods_keyword=goods_keyword,
        allowed_shop_ids=allowed_shop_ids,
    )
    return success_page(items, total, page, page_size)


@router.post("/sync", summary="手动同步订单")
def manual_sync(
    payload: OrderSyncRequest,
    operator: User = Depends(require_permission("order:sync")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    return success(
        sync_service.manual_order_sync(
            session,
            shop_id=payload.shop_id,
            start_time=payload.start_time,
            end_time=payload.end_time,
            operator=operator,
            trigger_type="手动",
            allowed_shop_ids=allowed_shop_ids,
        )
    )


@router.post("/supplement", summary="手动补单")
def supplement_orders(
    payload: OrderSyncRequest,
    operator: User = Depends(require_permission("order:sync")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    return success(
        sync_service.manual_order_sync(
            session,
            shop_id=payload.shop_id,
            start_time=payload.start_time,
            end_time=payload.end_time,
            operator=operator,
            trigger_type="补单",
            allowed_shop_ids=allowed_shop_ids,
        )
    )


@router.post("/sync-errors/{order_id}/retry", summary="同步异常重试")
def retry_sync_error(
    order_id: int,
    operator: User = Depends(require_permission("order:sync")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    _assert_shop_allowed(session, order_id, allowed_shop_ids)
    return success(order_service.retry_sync_error(session, order_id, operator))


@router.post("/sync-errors/{order_id}/handle", summary="同步异常人工处理")
def handle_sync_error(
    order_id: int,
    payload: OrderErrorHandleRequest,
    operator: User = Depends(require_permission("order:sync")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    _assert_shop_allowed(session, order_id, allowed_shop_ids)
    return success(order_service.handle_sync_error(session, order_id, payload.note, operator))


# ---------------- M3 订单处理（静态路径须在 /{order_id} 之前） ---------------- #
@router.get("/abnormal", summary="异常订单池")
def list_abnormal_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    shop_id: int | None = None,
    platform_code: str | None = None,
    abnormal_type: str | None = None,
    keyword: str | None = None,
    _: User = Depends(require_permission("order:abnormal")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    items, total = order_service.list_abnormal_orders(
        session,
        page=page,
        page_size=page_size,
        shop_id=shop_id,
        platform_code=platform_code,
        abnormal_type=abnormal_type,
        keyword=keyword,
        allowed_shop_ids=allowed_shop_ids,
    )
    return success_page(items, total, page, page_size)


@router.post("/batch/audit", summary="批量审核")
def batch_audit(
    payload: OrderBatchAuditRequest,
    operator: User = Depends(require_permission("order:audit")),
    session: Session = Depends(get_db),
):
    return success(order_service.batch_audit(session, payload, operator))


@router.post("/batch/remark", summary="批量备注/打标")
def batch_remark(
    payload: OrderBatchRemarkRequest,
    operator: User = Depends(require_permission("order:list")),
    session: Session = Depends(get_db),
):
    return success(order_service.batch_remark(session, payload, operator))


@router.post("/batch/forward", summary="批量转发货")
def batch_forward(
    payload: OrderBatchIdsRequest,
    operator: User = Depends(require_permission("order:audit")),
    session: Session = Depends(get_db),
):
    return success(order_service.batch_forward_ship(session, payload, operator))


@router.post("/merge", summary="订单合并")
def merge_orders(
    payload: OrderMergeRequest,
    operator: User = Depends(require_permission("order:list")),
    session: Session = Depends(get_db),
):
    return success(order_service.merge_orders(session, payload, operator))


@router.post("/{order_id}/audit", summary="订单审核")
def audit_order(
    order_id: int,
    payload: OrderAuditRequest,
    operator: User = Depends(require_permission("order:audit")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    _assert_shop_allowed(session, order_id, allowed_shop_ids)
    return success(order_service.audit_order(session, order_id, payload, operator))


@router.post("/{order_id}/price", summary="订单改价")
def change_price(
    order_id: int,
    payload: OrderPriceRequest,
    operator: User = Depends(require_permission("order:price")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    _assert_shop_allowed(session, order_id, allowed_shop_ids)
    return success(order_service.change_price(session, order_id, payload, operator))


@router.post("/{order_id}/address", summary="修改收货地址")
def change_address(
    order_id: int,
    payload: OrderAddressRequest,
    operator: User = Depends(require_permission("order:address")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    _assert_shop_allowed(session, order_id, allowed_shop_ids)
    return success(order_service.change_address(session, order_id, payload, operator))


@router.post("/{order_id}/remark", summary="订单备注/打标")
def add_remark(
    order_id: int,
    payload: OrderRemarkRequest,
    operator: User = Depends(require_permission("order:list")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    _assert_shop_allowed(session, order_id, allowed_shop_ids)
    return success(order_service.add_remark(session, order_id, payload, operator))


@router.post("/{order_id}/split", summary="订单拆分")
def split_order(
    order_id: int,
    payload: OrderSplitRequest,
    operator: User = Depends(require_permission("order:list")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    _assert_shop_allowed(session, order_id, allowed_shop_ids)
    return success(order_service.split_order(session, order_id, payload, operator))


@router.patch("/{order_id}/status", summary="订单状态流转")
def change_status(
    order_id: int,
    payload: OrderStatusChangeRequest,
    operator: User = Depends(require_permission("order:list")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    _assert_shop_allowed(session, order_id, allowed_shop_ids)
    return success(order_service.change_status(session, order_id, payload, operator))


@router.get("/{order_id}/status-options", summary="可流转状态选项")
def status_options(
    order_id: int,
    _: User = Depends(require_permission("order:detail")),
    session: Session = Depends(get_db),
):
    return success(order_service.status_options(session, order_id))


@router.get("/{order_id}/after-sales", summary="订单关联售后单")
def order_after_sales(
    order_id: int,
    _: User = Depends(require_permission("order:detail")),
    session: Session = Depends(get_db),
):
    return success(after_sale_service.list_by_order(session, order_id))


@router.get("/{order_id}", summary="订单详情")
def get_order(
    order_id: int,
    _: User = Depends(require_permission("order:detail")),
    session: Session = Depends(get_db),
):
    return success(order_service.get_order(session, order_id))


@router.get("/{order_id}/items", summary="订单明细")
def get_order_items(
    order_id: int,
    _: User = Depends(require_permission("order:detail")),
    session: Session = Depends(get_db),
):
    return success(order_service.list_order_items(session, order_id))


@router.get("/{order_id}/ext", summary="订单平台扩展字段")
def get_order_ext(
    order_id: int,
    _: User = Depends(require_permission("order:detail")),
    session: Session = Depends(get_db),
):
    return success(order_service.list_order_ext(session, order_id))


@router.get("/{order_id}/logs", summary="订单操作日志与变更记录")
def get_order_logs(
    order_id: int,
    _: User = Depends(require_permission("order:detail")),
    session: Session = Depends(get_db),
):
    return success(order_service.list_order_logs(session, order_id))
