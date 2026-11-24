"""M6 发货与物流接口：待发货、电子面单、批量打单、发货回传、发货单/轨迹、物流异常预警。"""

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.core.deps import get_allowed_shop_ids, get_db, require_permission
from app.core.response import success, success_page
from app.models.system import User
from app.schemas.shipment import (
    BatchShipmentRequest,
    PrintRequest,
    ShipmentCreateRequest,
    WaybillRequest,
)
from app.services import shipment_service

router = APIRouter(tags=["发货与物流"])


@router.get("/logistics-companies", summary="物流公司列表")
def list_logistics_companies(
    _: User = Depends(require_permission("shipment:pending")),
    session: Session = Depends(get_db),
):
    return success(shipment_service.list_logistics_companies(session))


# ---------------- 静态路径须在 /shipments/{shipment_id} 之前 ---------------- #
@router.get("/shipments/pending", summary="待发货订单列表")
def list_pending(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    shop_id: int | None = None,
    platform_code: str | None = None,
    keyword: str | None = None,
    _: User = Depends(require_permission("shipment:pending")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    items, total = shipment_service.list_pending(
        session,
        page=page,
        page_size=page_size,
        shop_id=shop_id,
        platform_code=platform_code,
        keyword=keyword,
        allowed_shop_ids=allowed_shop_ids,
    )
    return success_page(items, total, page, page_size)


@router.post("/shipments/waybill", summary="获取电子面单")
def get_waybills(
    payload: WaybillRequest,
    operator: User = Depends(require_permission("shipment:ship")),
    session: Session = Depends(get_db),
):
    return success(shipment_service.get_waybills(session, payload, operator))


@router.post("/shipments/print", summary="批量打单")
def print_shipments(
    payload: PrintRequest,
    operator: User = Depends(require_permission("shipment:ship")),
    session: Session = Depends(get_db),
):
    return success(shipment_service.print_shipments(session, payload, operator))


@router.post("/shipments/batch", summary="批量发货")
def batch_ship(
    payload: BatchShipmentRequest,
    operator: User = Depends(require_permission("shipment:batch_ship")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    return success(shipment_service.batch_ship(session, payload, operator))


@router.get("/shipments/alerts", summary="物流异常预警")
def list_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    shop_id: int | None = None,
    keyword: str | None = None,
    _: User = Depends(require_permission("shipment:alert")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    items, total = shipment_service.list_alerts(
        session,
        page=page,
        page_size=page_size,
        shop_id=shop_id,
        keyword=keyword,
        allowed_shop_ids=allowed_shop_ids,
    )
    return success_page(items, total, page, page_size)


@router.post("/shipments", summary="发货")
def ship(
    payload: ShipmentCreateRequest,
    operator: User = Depends(require_permission("shipment:ship")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    return success(shipment_service.ship(session, payload, operator))


@router.get("/shipments", summary="发货单列表")
def list_shipments(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    shop_id: int | None = None,
    platform_code: str | None = None,
    status: str | None = None,
    keyword: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    _: User = Depends(require_permission("shipment:list")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    items, total = shipment_service.list_shipments(
        session,
        page=page,
        page_size=page_size,
        shop_id=shop_id,
        platform_code=platform_code,
        status=status,
        keyword=keyword,
        start_time=start_time,
        end_time=end_time,
        allowed_shop_ids=allowed_shop_ids,
    )
    return success_page(items, total, page, page_size)


@router.get("/shipments/{shipment_id}", summary="发货单详情")
def get_shipment(
    shipment_id: int,
    _: User = Depends(require_permission("shipment:list")),
    session: Session = Depends(get_db),
):
    return success(shipment_service.get_shipment(session, shipment_id))


@router.get("/shipments/{shipment_id}/traces", summary="物流轨迹")
def list_traces(
    shipment_id: int,
    _: User = Depends(require_permission("shipment:list")),
    session: Session = Depends(get_db),
):
    return success(shipment_service.list_traces(session, shipment_id))


@router.post("/shipments/{shipment_id}/sync-trace", summary="拉取物流轨迹")
def sync_trace(
    shipment_id: int,
    operator: User = Depends(require_permission("shipment:ship")),
    session: Session = Depends(get_db),
):
    return success(shipment_service.sync_trace(session, shipment_id, operator))
