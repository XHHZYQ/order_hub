"""M4 商品接口：本地商品（SPU）/SKU 维护、平台商品查询。"""

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.core.deps import get_allowed_shop_ids, get_db, require_permission
from app.core.exceptions import forbidden
from app.core.response import success, success_page
from app.models.system import User
from app.schemas.product import ProductCreate, ProductUpdate, SkuCreate, SkuUpdate
from app.services import product_service

router = APIRouter(prefix="/products", tags=["商品"])
sku_router = APIRouter(prefix="/skus", tags=["SKU"])
platform_product_router = APIRouter(prefix="/platform-products", tags=["平台商品"])


# --------------------------------------------------------------------------- #
# 本地商品（SPU）
# --------------------------------------------------------------------------- #
@router.get("", summary="本地商品列表")
def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: str | None = None,
    category_name: str | None = None,
    brand: str | None = None,
    status: int | None = None,
    _: User = Depends(require_permission("product:list")),
    session: Session = Depends(get_db),
):
    items, total = product_service.list_products(
        session,
        page=page,
        page_size=page_size,
        keyword=keyword,
        category_name=category_name,
        brand=brand,
        status=status,
    )
    return success_page(items, total, page, page_size)


@router.post("", summary="新增本地商品")
def create_product(
    payload: ProductCreate,
    operator: User = Depends(require_permission("product:create")),
    session: Session = Depends(get_db),
):
    return success(product_service.create_product(session, payload, operator))


@router.get("/{product_id}", summary="商品详情")
def get_product(
    product_id: int,
    _: User = Depends(require_permission("product:list")),
    session: Session = Depends(get_db),
):
    return success(product_service.get_product(session, product_id))


@router.put("/{product_id}", summary="编辑本地商品")
def update_product(
    product_id: int,
    payload: ProductUpdate,
    operator: User = Depends(require_permission("product:edit")),
    session: Session = Depends(get_db),
):
    return success(product_service.update_product(session, product_id, payload, operator))


@router.delete("/{product_id}", summary="删除本地商品")
def delete_product(
    product_id: int,
    operator: User = Depends(require_permission("product:delete")),
    session: Session = Depends(get_db),
):
    product_service.delete_product(session, product_id, operator)
    return success(None)


@router.get("/{product_id}/skus", summary="商品 SKU 列表")
def list_product_skus(
    product_id: int,
    _: User = Depends(require_permission("product:list")),
    session: Session = Depends(get_db),
):
    return success(product_service.list_skus(session, product_id))


@router.post("/{product_id}/skus", summary="新增 SKU")
def create_sku(
    product_id: int,
    payload: SkuCreate,
    operator: User = Depends(require_permission("product:edit")),
    session: Session = Depends(get_db),
):
    return success(product_service.create_sku(session, product_id, payload, operator))


# --------------------------------------------------------------------------- #
# SKU
# --------------------------------------------------------------------------- #
@sku_router.put("/{sku_id}", summary="编辑 SKU")
def update_sku(
    sku_id: int,
    payload: SkuUpdate,
    operator: User = Depends(require_permission("product:edit")),
    session: Session = Depends(get_db),
):
    return success(product_service.update_sku(session, sku_id, payload, operator))


@sku_router.delete("/{sku_id}", summary="删除 SKU")
def delete_sku(
    sku_id: int,
    operator: User = Depends(require_permission("product:delete")),
    session: Session = Depends(get_db),
):
    product_service.delete_sku(session, sku_id, operator)
    return success(None)


# --------------------------------------------------------------------------- #
# 平台商品
# --------------------------------------------------------------------------- #
@platform_product_router.get("", summary="平台商品列表")
def list_platform_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    shop_id: int | None = None,
    platform_code: str | None = None,
    keyword: str | None = None,
    _: User = Depends(require_permission("product:platform")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    items, total = product_service.list_platform_products(
        session,
        page=page,
        page_size=page_size,
        shop_id=shop_id,
        platform_code=platform_code,
        keyword=keyword,
        allowed_shop_ids=allowed_shop_ids,
    )
    return success_page(items, total, page, page_size)


@platform_product_router.get("/{platform_product_id}", summary="平台商品详情")
def get_platform_product(
    platform_product_id: int,
    _: User = Depends(require_permission("product:platform")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    detail = product_service.get_platform_product(session, platform_product_id)
    if allowed_shop_ids is not None and detail["shop_id"] not in allowed_shop_ids:
        raise forbidden("无权查看该店铺平台商品")
    return success(detail)
