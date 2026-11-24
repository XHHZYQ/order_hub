"""M6 发货与物流服务：待发货、电子面单、批量打单、发货回传、轨迹、物流异常预警。

物流为**适配层模拟**（app/adapters/logistics.py），不依赖真实物流开放平台。
"""

from __future__ import annotations

import random
from datetime import timedelta
from decimal import Decimal

from sqlalchemy import or_
from sqlmodel import Session, func, select

from app.adapters import logistics
from app.core.constants import (
    LOGISTICS_ALERT_REASON,
    ORDER_STATUS,
    PUSH_STATUS,
    SHIPMENT_STATUS,
    TRACE_STATUS,
)
from app.core.exceptions import BusinessException, not_found, param_error, status_not_allowed
from app.models.fulfillment import LogisticsCompany, LogisticsTrace, Shipment
from app.models.order import Order, OrderItem
from app.models.platform import Platform, Shop
from app.services import inventory_service, order_service, order_state_machine
from app.utils.datetime_util import format_datetime, now_utc, parse_datetime
from app.utils.id_generator import gen_shipment_no
from app.utils.pagination import normalize

_SHIPMENT_TIME_FIELDS = ("shipped_at", "created_at")
_TRACE_TIME_FIELDS = ("trace_time", "created_at")


def _fmt(data: dict, fields: tuple[str, ...]) -> dict:
    for field in fields:
        if field in data:
            data[field] = format_datetime(data.get(field))
    return data


def _company_options(session: Session) -> list[dict]:
    """优先取库内字典，为空则回落到适配层内置字典。"""
    rows = session.exec(
        select(LogisticsCompany).where(LogisticsCompany.status == 1).order_by(LogisticsCompany.sort_no)
    ).all()
    if rows:
        return [{"company_code": r.company_code, "company_name": r.company_name} for r in rows]
    return logistics.list_companies()


def _company_name(session: Session, code: str | None) -> str | None:
    if not code:
        return None
    row = session.exec(select(LogisticsCompany).where(LogisticsCompany.company_code == code)).first()
    return row.company_name if row else logistics.company_name(code)


def list_logistics_companies(session: Session) -> list[dict]:
    return _company_options(session)


def _new_waybill(session: Session, rng: random.Random, code: str | None) -> tuple[str, str]:
    """返回 (物流公司编码, 名称)。"""
    if not code:
        options = _company_options(session)
        code = rng.choice([o["company_code"] for o in options]) if options else "SF"
    name = _company_name(session, code) or code
    return code, name


# --------------------------------------------------------------------------- #
# 待发货 / 面单 / 打单
# --------------------------------------------------------------------------- #
def list_pending(
    session: Session,
    *,
    page: int | None,
    page_size: int | None,
    shop_id: int | None = None,
    platform_code: str | None = None,
    keyword: str | None = None,
    allowed_shop_ids: list[int] | None = None,
) -> tuple[list[dict], int]:
    """待发货订单列表（status=PENDING_SHIP，FR-06-01）。"""
    conditions = [Order.is_deleted == 0, Order.status == "PENDING_SHIP"]
    if shop_id:
        conditions.append(Order.shop_id == shop_id)
    if platform_code:
        conditions.append(Order.platform_code == platform_code)
    if keyword:
        like = f"%{keyword}%"
        conditions.append(
            or_(Order.order_no.like(like), Order.platform_order_no.like(like), Order.receiver_name.like(like))
        )
    if allowed_shop_ids is not None:
        conditions.append(Order.shop_id.in_(allowed_shop_ids or [-1]))

    p, s, offset = normalize(page, page_size)
    total = session.exec(select(func.count()).select_from(Order).where(*conditions)).one()
    rows = session.exec(
        select(Order).where(*conditions).order_by(Order.order_time.asc(), Order.id.asc()).offset(offset).limit(s)
    ).all()
    shop_names = _shop_names(session, rows)
    platform_names = _platform_names(session, rows)
    items = []
    for r in rows:
        data = order_service._order_dict(r, shop_names.get(r.shop_id), platform_names.get(r.platform_code))
        qty_rows = session.exec(
            select(OrderItem).where(OrderItem.order_id == r.id, OrderItem.sku_id.is_not(None))
        ).all()
        data["item_count"] = len(qty_rows)
        data["total_qty"] = sum((row.quantity or 0) for row in qty_rows)
        data["unmatched_count"] = sum(1 for row in qty_rows if row.is_matched != 1)
        items.append(data)
    return items, int(total)


def _shop_names(session: Session, rows) -> dict[int, str]:
    return {
        sid: name
        for sid, name in session.exec(
            select(Shop.id, Shop.shop_name).where(Shop.id.in_({r.shop_id for r in rows} or [-1]))
        ).all()
    }


def _platform_names(session: Session, rows) -> dict[str, str]:
    return {
        code: name
        for code, name in session.exec(
            select(Platform.platform_code, Platform.platform_name).where(
                Platform.platform_code.in_({r.platform_code for r in rows if r.platform_code} or [""])
            )
        ).all()
    }


def _face_sheet(session: Session, order: Order, code: str | None, rng: random.Random) -> dict:
    """生成一条面单数据（不落库）。"""
    company_code, company_name = _new_waybill(session, rng, code)
    return {
        "order_id": order.id,
        "order_no": order.order_no,
        "platform_code": order.platform_code,
        "logistics_company_code": company_code,
        "logistics_company_name": company_name,
        "waybill_no": logistics.gen_waybill_no(company_code, rng),
        "face_sheet_no": logistics.gen_face_sheet_no(rng),
        "package_no": logistics.gen_package_no(rng, order.order_no),
        "receiver_name": order.receiver_name,
        "receiver_phone": order.receiver_phone,
        "receiver_address": "".join(
            filter(None, [order.receiver_province, order.receiver_city, order.receiver_district, order.receiver_address])
        ),
    }


def get_waybills(session: Session, payload, operator=None) -> list[dict]:
    """获取电子面单（单个/批量，FR-06-02）。"""
    ids: list[int] = []
    if payload.order_id:
        ids.append(payload.order_id)
    if payload.order_ids:
        ids.extend(payload.order_ids)
    ids = list(dict.fromkeys(ids))
    if not ids:
        raise param_error("请至少指定一个订单")
    rng = random.Random()
    result = []
    for order_id in ids:
        order = order_service._load_order(session, order_id)
        if order.status not in {"PENDING_SHIP", "PART_SHIPPED"}:
            raise status_not_allowed(f"订单 {order.order_no} 当前状态不可获取面单")
        result.append(_face_sheet(session, order, payload.logistics_company_code, rng))
    return result


def print_shipments(session: Session, payload, operator=None) -> dict:
    """批量打单：生成打印数据（面单号 + 收件信息），FR-06-03。"""
    rng = random.Random()
    sheets = []
    for order_id in dict.fromkeys(payload.order_ids):
        order = order_service._load_order(session, order_id)
        if order.status not in {"PENDING_SHIP", "PART_SHIPPED"}:
            raise status_not_allowed(f"订单 {order.order_no} 当前状态不可打单")
        sheets.append(_face_sheet(session, order, payload.logistics_company_code, rng))
    if operator is not None:
        from app.services.user_service import record_operation

        record_operation(
            session, operator, "SHIPMENT", "打印", "发货单", None, f"批量打单 {len(sheets)} 单"
        )
        session.commit()
    return {"count": len(sheets), "sheets": sheets}


# --------------------------------------------------------------------------- #
# 发货（落发货单 + 回传平台 + 扣减库存）
# --------------------------------------------------------------------------- #
def _insert_traces(session: Session, shipment: Shipment, order: Order, nodes: list[dict]) -> int:
    """按 (trace_status, trace_desc) 去重后写入轨迹，返回新增条数。"""
    if not shipment.id:
        session.flush()
    existing = {
        (row.trace_status, row.trace_desc)
        for row in session.exec(
            select(LogisticsTrace).where(LogisticsTrace.shipment_id == shipment.id)
        ).all()
    }
    added = 0
    for node in nodes:
        key = (node.get("trace_status"), node.get("trace_desc"))
        if key in existing:
            continue
        session.add(
            LogisticsTrace(
                shipment_id=shipment.id,
                waybill_no=shipment.waybill_no,
                trace_time=node["trace_time"],
                trace_desc=node["trace_desc"],
                trace_status=node["trace_status"],
            )
        )
        existing.add(key)
        added += 1
    return added


def _refresh_shipment_status(session: Session, shipment: Shipment) -> None:
    """按轨迹节点推进发货单物流状态。"""
    statuses = {
        row.trace_status
        for row in session.exec(select(LogisticsTrace).where(LogisticsTrace.shipment_id == shipment.id)).all()
    }
    if "ABNORMAL" in statuses:
        shipment.status = "ABNORMAL"
    elif "SIGNED" in statuses:
        shipment.status = "SIGNED"
    elif "ARRIVED" in statuses or "DELIVERING" in statuses:
        shipment.status = "IN_TRANSIT"
    else:
        shipment.status = "SHIPPED"
    session.add(shipment)


def ship(session: Session, payload, operator=None, *, commit: bool = True) -> dict:
    """发货：创建发货单、写轨迹、扣减库存、更新订单状态并回传平台（FR-06-04）。"""
    op = order_service._op_name(operator)
    order = order_service._load_order(session, payload.order_id)
    if order.status not in {"PENDING_SHIP", "PART_SHIPPED"}:
        raise status_not_allowed(f"订单 {order.order_no} 当前状态不可发货")

    items = session.exec(select(OrderItem).where(OrderItem.order_id == order.id)).all()
    item_map = {row.id: row for row in items}
    remain = {row.id: max((row.quantity or 0) - (row.shipped_quantity or 0), 0) for row in items}

    plan: list[tuple[OrderItem, int]] = []
    if payload.items:
        for it in payload.items:
            row = item_map.get(it.item_id)
            if row is None:
                raise param_error(f"明细 {it.item_id} 不属于该订单")
            if it.quantity <= 0 or it.quantity > remain.get(row.id, 0):
                raise param_error(f"{row.product_name or row.sku_code} 发货数量非法（可发 {remain.get(row.id, 0)}）")
            plan.append((row, it.quantity))
    else:
        plan = [(row, remain[row.id]) for row in items if remain.get(row.id, 0) > 0]
    if not plan:
        raise status_not_allowed("订单已全部发货，无需重复发货")

    rng = random.Random()
    company_code, company_name = _new_waybill(session, rng, payload.logistics_company_code)
    now = now_utc()
    shipment = Shipment(
        shipment_no=gen_shipment_no(),
        order_id=order.id,
        order_no=order.order_no,
        shop_id=order.shop_id,
        platform_code=order.platform_code,
        logistics_company_code=company_code,
        logistics_company_name=company_name,
        waybill_no=payload.waybill_no or logistics.gen_waybill_no(company_code, rng),
        face_sheet_no=payload.face_sheet_no or logistics.gen_face_sheet_no(rng),
        package_no=payload.package_no or logistics.gen_package_no(rng, order.order_no),
        ship_qty=sum(q for _, q in plan),
        print_status=1,
        push_status=1,
        status="SHIPPED",
        shipped_at=now,
        operator=op,
    )
    session.add(shipment)
    session.flush()

    # 轨迹（揽收 + 发出）
    _insert_traces(
        session,
        shipment,
        order,
        logistics.gen_traces(
            waybill_no=shipment.waybill_no,
            company_code=company_code,
            dest_city=order.receiver_city,
            shipped_at=now,
            node_count=2,
        ),
    )
    _refresh_shipment_status(session, shipment)

    # 明细已发数量 + 库存扣减
    for row, qty in plan:
        row.shipped_quantity = (row.shipped_quantity or 0) + qty
        session.add(row)
        if row.sku_id:
            inventory_service.ship_deduct(
                session,
                sku_id=row.sku_id,
                qty=qty,
                source_no=order.order_no,
                remark=f"订单 {order.order_no} 发货扣减",
                operator=operator,
            )

    # 订单状态推进
    new_status = order_state_machine.resolve_ship_status(items)
    if new_status != order.status:
        order_service._apply_status(
            session, order, new_status, operator=op, source="发货",
            remark=f"发货：{shipment.shipment_no} / {shipment.waybill_no}",
        )
    else:
        order_service._add_log(
            session, order, action="发货",
            content=f"追加发货：{shipment.shipment_no} / {shipment.waybill_no}", source="发货", operator=op,
        )
    order_service.record_shipment_change(session, order, shipment, op)

    if commit:
        session.commit()
        session.refresh(shipment)
    return get_shipment(session, shipment.id)


def batch_ship(session: Session, payload, operator=None) -> dict:
    """批量发货（FR-06-04）。"""
    from app.schemas.shipment import ShipmentCreateRequest

    success, failed = [], []
    for order_id in dict.fromkeys(payload.order_ids):
        try:
            data = ship(
                session,
                ShipmentCreateRequest(order_id=order_id, logistics_company_code=payload.logistics_company_code),
                operator,
                commit=False,
            )
            success.append({"order_id": order_id, "shipment_no": data["shipment_no"]})
        except BusinessException as exc:
            session.rollback()
            failed.append({"order_id": order_id, "reason": exc.message})
    session.commit()
    return {"success_count": len(success), "fail_count": len(failed), "success": success, "failed": failed}


# --------------------------------------------------------------------------- #
# 发货单查询 / 详情 / 轨迹
# --------------------------------------------------------------------------- #
def _shipment_dict(
    shipment: Shipment, shop_name: str | None, platform_name: str | None, order: Order | None
) -> dict:
    data = _fmt(shipment.model_dump(), _SHIPMENT_TIME_FIELDS)
    data["status_name"] = SHIPMENT_STATUS.get(shipment.status, shipment.status)
    data["push_status_name"] = PUSH_STATUS.get(shipment.push_status, shipment.push_status)
    data["shop_name"] = shop_name
    data["platform_name"] = platform_name
    data["receiver_name"] = order.receiver_name if order else None
    data["receiver_phone"] = order.receiver_phone if order else None
    data["receiver_address"] = (
        "".join(
            filter(None, [order.receiver_province, order.receiver_city, order.receiver_district, order.receiver_address])
        )
        if order
        else None
    )
    return data


def list_shipments(
    session: Session,
    *,
    page: int | None,
    page_size: int | None,
    shop_id: int | None = None,
    platform_code: str | None = None,
    status: str | None = None,
    keyword: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    allowed_shop_ids: list[int] | None = None,
) -> tuple[list[dict], int]:
    """发货单列表（FR-06-05）。"""
    conditions = []
    if shop_id:
        conditions.append(Shipment.shop_id == shop_id)
    if platform_code:
        conditions.append(Shipment.platform_code == platform_code)
    if status:
        conditions.append(Shipment.status == status)
    if keyword:
        like = f"%{keyword}%"
        conditions.append(
            or_(
                Shipment.shipment_no.like(like),
                Shipment.order_no.like(like),
                Shipment.waybill_no.like(like),
            )
        )
    st = parse_datetime(start_time)
    et = parse_datetime(end_time)
    if st:
        conditions.append(Shipment.shipped_at >= st)
    if et:
        conditions.append(Shipment.shipped_at <= et)
    if allowed_shop_ids is not None:
        conditions.append(Shipment.shop_id.in_(allowed_shop_ids or [-1]))

    p, s, offset = normalize(page, page_size)
    total = session.exec(select(func.count()).select_from(Shipment).where(*conditions)).one()
    rows = session.exec(
        select(Shipment).where(*conditions).order_by(Shipment.shipped_at.desc(), Shipment.id.desc()).offset(offset).limit(s)
    ).all()
    shop_names = _shop_names(session, rows)
    platform_names = _platform_names(session, rows)
    order_map = _order_map(session, rows)
    items = [
        _shipment_dict(r, shop_names.get(r.shop_id), platform_names.get(r.platform_code), order_map.get(r.order_id))
        for r in rows
    ]
    return items, int(total)


def _order_map(session: Session, rows) -> dict[int, Order]:
    ids = {r.order_id for r in rows}
    return {
        o.id: o for o in session.exec(select(Order).where(Order.id.in_(ids or [-1]))).all()
    }


def get_shipment(session: Session, shipment_id: int) -> dict:
    """发货单详情（含订单摘要、明细与轨迹）。"""
    shipment = session.get(Shipment, shipment_id)
    if not shipment:
        raise not_found("发货单不存在")
    order = session.get(Order, shipment.order_id)
    shop = session.get(Shop, shipment.shop_id)
    platform = session.exec(select(Platform).where(Platform.platform_code == shipment.platform_code)).first()
    data = _shipment_dict(
        shipment, shop.shop_name if shop else None, platform.platform_name if platform else None, order
    )
    data["order_status"] = order.status if order else None
    data["order_status_name"] = ORDER_STATUS.get(order.status, order.status) if order else None
    data["traces"] = list_traces(session, shipment_id)
    return data


def list_traces(session: Session, shipment_id: int) -> list[dict]:
    """物流轨迹列表（时间升序）。"""
    rows = session.exec(
        select(LogisticsTrace)
        .where(LogisticsTrace.shipment_id == shipment_id)
        .order_by(LogisticsTrace.trace_time.asc(), LogisticsTrace.id.asc())
    ).all()
    result = []
    for row in rows:
        data = _fmt(row.model_dump(), _TRACE_TIME_FIELDS)
        data["trace_status_name"] = TRACE_STATUS.get(row.trace_status, row.trace_status)
        result.append(data)
    return result


def _pull_new_traces(session: Session, shipment: Shipment) -> int:
    """为单个发货单追加新的物流轨迹节点（不提交事务），返回新增条数。"""
    if not shipment.waybill_no:
        return 0
    current = int(
        session.exec(
            select(func.count()).select_from(LogisticsTrace).where(LogisticsTrace.shipment_id == shipment.id)
        ).one()
        or 0
    )
    if current >= 5 or shipment.status == "SIGNED":
        return 0
    order = session.get(Order, shipment.order_id)
    rng = random.Random(shipment.waybill_no)
    step = rng.choice([1, 1, 2])
    node_count = min(5, max(current, 2) + step)
    nodes = logistics.gen_traces(
        waybill_no=shipment.waybill_no,
        company_code=shipment.logistics_company_code,
        dest_city=order.receiver_city if order else None,
        shipped_at=shipment.shipped_at or now_utc(),
        node_count=node_count,
    )
    added = _insert_traces(session, shipment, order, nodes)
    if added:
        _refresh_shipment_status(session, shipment)
    return added


def sync_trace(session: Session, shipment_id: int, operator=None) -> dict:
    """拉取物流轨迹（FR-06-05）：模拟物流有更新时追加新节点。"""
    shipment = session.get(Shipment, shipment_id)
    if not shipment:
        raise not_found("发货单不存在")
    if not shipment.waybill_no:
        raise param_error("该发货单无运单号，无法拉取轨迹")
    added = _pull_new_traces(session, shipment)
    from app.services.user_service import record_operation

    record_operation(
        session, operator, "SHIPMENT", "拉取轨迹", "发货单", shipment_id,
        f"运单 {shipment.waybill_no} 新增轨迹 {added} 条",
    )
    session.commit()
    return {
        "shipment_id": shipment_id,
        "added": added,
        "status": shipment.status,
        "status_name": SHIPMENT_STATUS.get(shipment.status, shipment.status),
        "traces": list_traces(session, shipment_id),
    }


def sync_traces_by_shop(session: Session, *, shop_id: int) -> int:
    """批量拉取某店铺在途发货单的新物流轨迹（供定时同步），返回新增条数。"""
    shipments = session.exec(
        select(Shipment).where(
            Shipment.shop_id == shop_id,
            Shipment.status.in_(["SHIPPED", "IN_TRANSIT", "ABNORMAL"]),
        )
    ).all()
    added = 0
    for shipment in shipments:
        added += _pull_new_traces(session, shipment)
    session.commit()
    return added


# --------------------------------------------------------------------------- #
# 物流异常预警
# --------------------------------------------------------------------------- #
def list_alerts(
    session: Session,
    *,
    page: int | None,
    page_size: int | None,
    shop_id: int | None = None,
    keyword: str | None = None,
    allowed_shop_ids: list[int] | None = None,
) -> tuple[list[dict], int]:
    """物流异常预警：已发货/在途但超过 48 小时无轨迹更新（FR-06-06）。"""
    now = now_utc()
    threshold = now - timedelta(hours=logistics.STALE_HOURS)
    latest = dict(
        session.exec(
            select(LogisticsTrace.shipment_id, func.max(LogisticsTrace.trace_time)).group_by(
                LogisticsTrace.shipment_id
            )
        ).all()
    )
    conditions = [Shipment.status.in_(["SHIPPED", "IN_TRANSIT"])]
    if shop_id:
        conditions.append(Shipment.shop_id == shop_id)
    if keyword:
        like = f"%{keyword}%"
        conditions.append(
            or_(Shipment.shipment_no.like(like), Shipment.order_no.like(like), Shipment.waybill_no.like(like))
        )
    if allowed_shop_ids is not None:
        conditions.append(Shipment.shop_id.in_(allowed_shop_ids or [-1]))

    rows = session.exec(select(Shipment).where(*conditions).order_by(Shipment.shipped_at.asc())).all()
    stale = [r for r in rows if (latest.get(r.id) or r.shipped_at) and (latest.get(r.id) or r.shipped_at) < threshold]
    shop_names = _shop_names(session, stale)
    platform_names = _platform_names(session, stale)
    order_map = _order_map(session, stale)
    p, s, offset = normalize(page, page_size)
    total = len(stale)
    page_rows = stale[offset : offset + s]
    items = []
    for r in page_rows:
        data = _shipment_dict(r, shop_names.get(r.shop_id), platform_names.get(r.platform_code), order_map.get(r.order_id))
        last = latest.get(r.id) or r.shipped_at
        data["last_trace_time"] = format_datetime(last)
        data["stale_hours"] = int((now - last).total_seconds() // 3600) if last else None
        data["alert_reason"] = LOGISTICS_ALERT_REASON
        items.append(data)
    return items, total
