"""M9 数据看板接口：经营总览、渠道对比、商品分析、履约分析、售后分析、库存分析、下钻。

接口清单见《接口设计》3.9；统一按当前用户数据权限过滤店铺。
"""

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.core.deps import get_allowed_shop_ids, get_current_user, get_db, require_permission
from app.core.exceptions import forbidden
from app.core.response import success, success_page
from app.models.system import User
from app.services import auth_service, dashboard_service

router = APIRouter(prefix="/dashboard", tags=["数据看板"])

_DRILL_PERM = {
    "order": "dashboard:overview",
    "product": "dashboard:product",
    "after_sale": "dashboard:after_sale",
    "inventory_alert": "dashboard:inventory",
}


@router.get("/overview", summary="经营总览")
def overview(
    start_time: str | None = None,
    end_time: str | None = None,
    platform_code: str | None = None,
    shop_id: int | None = None,
    _: User = Depends(require_permission("dashboard:overview")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    return success(
        dashboard_service.overview(
            session, start_time=start_time, end_time=end_time, platform_code=platform_code,
            shop_id=shop_id, allowed_shop_ids=allowed_shop_ids,
        )
    )


@router.get("/channels", summary="渠道与店铺对比")
def channels(
    start_time: str | None = None,
    end_time: str | None = None,
    platform_code: str | None = None,
    shop_id: int | None = None,
    _: User = Depends(require_permission("dashboard:channel")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    return success(
        dashboard_service.channels(
            session, start_time=start_time, end_time=end_time, platform_code=platform_code,
            shop_id=shop_id, allowed_shop_ids=allowed_shop_ids,
        )
    )


@router.get("/products", summary="商品销售分析")
def products(
    start_time: str | None = None,
    end_time: str | None = None,
    platform_code: str | None = None,
    shop_id: int | None = None,
    top: int = Query(10, ge=1, le=50),
    _: User = Depends(require_permission("dashboard:product")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    return success(
        dashboard_service.products(
            session, start_time=start_time, end_time=end_time, platform_code=platform_code,
            shop_id=shop_id, top=top, allowed_shop_ids=allowed_shop_ids,
        )
    )


@router.get("/fulfillment", summary="订单与履约分析")
def fulfillment(
    start_time: str | None = None,
    end_time: str | None = None,
    platform_code: str | None = None,
    shop_id: int | None = None,
    _: User = Depends(require_permission("dashboard:fulfillment")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    return success(
        dashboard_service.fulfillment(
            session, start_time=start_time, end_time=end_time, platform_code=platform_code,
            shop_id=shop_id, allowed_shop_ids=allowed_shop_ids,
        )
    )


@router.get("/after-sales", summary="售后分析")
def after_sales(
    start_time: str | None = None,
    end_time: str | None = None,
    platform_code: str | None = None,
    shop_id: int | None = None,
    top: int = Query(10, ge=1, le=50),
    _: User = Depends(require_permission("dashboard:after_sale")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    return success(
        dashboard_service.after_sales(
            session, start_time=start_time, end_time=end_time, platform_code=platform_code,
            shop_id=shop_id, top=top, allowed_shop_ids=allowed_shop_ids,
        )
    )


@router.get("/inventory", summary="库存分析")
def inventory(
    start_time: str | None = None,
    end_time: str | None = None,
    platform_code: str | None = None,
    shop_id: int | None = None,
    top: int = Query(10, ge=1, le=50),
    _: User = Depends(require_permission("dashboard:inventory")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    return success(
        dashboard_service.inventory_analysis(
            session, start_time=start_time, end_time=end_time, platform_code=platform_code,
            shop_id=shop_id, top=top, allowed_shop_ids=allowed_shop_ids,
        )
    )


@router.get("/drill-down", summary="汇总下钻到明细")
def drill_down(
    metric: str = Query("order", pattern="^(order|product|after_sale|inventory_alert)$"),
    start_time: str | None = None,
    end_time: str | None = None,
    platform_code: str | None = None,
    shop_id: int | None = None,
    sku_id: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    user: User = Depends(get_current_user),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    code = _DRILL_PERM.get(metric, "dashboard:overview")
    if not auth_service.is_super_admin(session, user.id) and code not in auth_service.get_permission_codes(session, user.id):
        raise forbidden(f"缺少功能权限：{code}")
    items, total = dashboard_service.drill_down(
        session,
        metric=metric,
        start_time=start_time,
        end_time=end_time,
        platform_code=platform_code,
        shop_id=shop_id,
        sku_id=sku_id,
        page=page,
        page_size=page_size,
        allowed_shop_ids=allowed_shop_ids,
    )
    return success_page(items, total, page, page_size)
