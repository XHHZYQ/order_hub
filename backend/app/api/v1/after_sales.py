"""M7 售后管理接口：售后单列表/详情、同步、处理、退款同步、超时预警、原因分析。"""

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.core.deps import get_allowed_shop_ids, get_db, require_permission
from app.core.response import success, success_page
from app.models.system import User
from app.schemas.after_sale import (
    AfterSaleHandleRequest,
    AfterSaleRefundRequest,
    AfterSaleSyncRequest,
)
from app.services import after_sale_service

router = APIRouter(prefix="/after-sales", tags=["售后管理"])


@router.get("", summary="售后单列表")
def list_after_sales(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    shop_id: int | None = None,
    platform_code: str | None = None,
    status: str | None = None,
    type: str | None = None,
    refund_status: str | None = None,
    keyword: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    _: User = Depends(require_permission("order:after_sale")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    items, total = after_sale_service.list_after_sales(
        session,
        page=page,
        page_size=page_size,
        shop_id=shop_id,
        platform_code=platform_code,
        status=status,
        type=type,
        refund_status=refund_status,
        keyword=keyword,
        start_time=start_time,
        end_time=end_time,
        allowed_shop_ids=allowed_shop_ids,
    )
    return success_page(items, total, page, page_size)


@router.post("/sync", summary="同步售后申请")
def sync_after_sales(
    payload: AfterSaleSyncRequest,
    operator: User = Depends(require_permission("order:after_sale")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    return success(after_sale_service.sync_after_sales(session, payload, operator))


@router.get("/alerts", summary="售后超时预警")
def list_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    shop_id: int | None = None,
    keyword: str | None = None,
    _: User = Depends(require_permission("order:after_sale")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    items, total = after_sale_service.list_alerts(
        session,
        page=page,
        page_size=page_size,
        shop_id=shop_id,
        keyword=keyword,
        allowed_shop_ids=allowed_shop_ids,
    )
    return success_page(items, total, page, page_size)


@router.get("/analysis", summary="售后原因分析")
def analysis(
    shop_id: int | None = None,
    _: User = Depends(require_permission("order:after_sale")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    return success(
        after_sale_service.analysis(session, shop_id=shop_id, allowed_shop_ids=allowed_shop_ids)
    )


@router.get("/{after_sale_id}", summary="售后单详情")
def get_after_sale(
    after_sale_id: int,
    _: User = Depends(require_permission("order:after_sale")),
    session: Session = Depends(get_db),
):
    return success(after_sale_service.get_after_sale(session, after_sale_id))


@router.post("/{after_sale_id}/handle", summary="售后处理")
def handle_after_sale(
    after_sale_id: int,
    payload: AfterSaleHandleRequest,
    operator: User = Depends(require_permission("order:after_sale")),
    session: Session = Depends(get_db),
):
    return success(after_sale_service.handle_after_sale(session, after_sale_id, payload, operator))


@router.post("/{after_sale_id}/refund", summary="退款同步")
def sync_refund(
    after_sale_id: int,
    payload: AfterSaleRefundRequest,
    operator: User = Depends(require_permission("order:after_sale")),
    session: Session = Depends(get_db),
):
    return success(after_sale_service.sync_refund(session, after_sale_id, payload, operator))
