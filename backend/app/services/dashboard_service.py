"""M9 数据看板服务：经营总览、渠道对比、商品分析、履约分析、售后分析、库存分析、下钻。

统一约定（见《接口设计》3.9 / 《需求规格说明书》3.9）：
- 所有指标支持 start_time / end_time / platform_code / shop_id 筛选；
- 一律按当前用户的数据权限（allowed_shop_ids）过滤店铺；
- 时间默认口径为「近 30 天」，按业务时间字段过滤。
"""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from sqlmodel import Session, func, select

from app.core.constants import (
    AFTER_SALE_STATUS,
    AFTER_SALE_TYPE,
    ORDER_STATUS,
    REFUND_STATUS,
    SHIPMENT_STATUS,
)
from app.models.after_sale import AfterSale
from app.models.fulfillment import Shipment
from app.models.inventory import Inventory, InventoryAlert
from app.models.order import Order, OrderItem
from app.models.platform import Platform, Shop
from app.models.product import Product, Sku
from app.utils.datetime_util import format_datetime, now_utc, parse_datetime, to_local
from app.utils.pagination import normalize

# 统计销售额时不计入的订单状态（未付款 / 已关闭）
_EXCLUDED_SALES_STATUS = ("PENDING_PAY", "CLOSED")


def _d(value) -> Decimal:
    if value is None:
        return Decimal("0")
    return value if isinstance(value, Decimal) else Decimal(str(value))


def _f(value) -> float:
    return float(_d(value))


def _day(dt: datetime | None) -> str | None:
    return to_local(dt).strftime("%Y-%m-%d") if dt else None


def _range(start_time: str | None, end_time: str | None, default_days: int = 30) -> tuple[datetime, datetime]:
    st = parse_datetime(start_time)
    et = parse_datetime(end_time)
    if not et:
        et = now_utc()
    if not st:
        st = et - timedelta(days=default_days)
    return st, et


def _shop_filter(column, shop_id: int | None, allowed_shop_ids: list[int] | None) -> list:
    conditions = []
    if shop_id:
        conditions.append(column == shop_id)
    if allowed_shop_ids is not None:
        conditions.append(column.in_(allowed_shop_ids or [-1]))
    return conditions


def _order_conditions(start_time, end_time, platform_code, shop_id, allowed_shop_ids) -> tuple[list, datetime, datetime]:
    st, et = _range(start_time, end_time)
    conditions = [Order.is_deleted == 0, Order.order_time >= st, Order.order_time <= et]
    if platform_code:
        conditions.append(Order.platform_code == platform_code)
    conditions.extend(_shop_filter(Order.shop_id, shop_id, allowed_shop_ids))
    return conditions, st, et


def _name_maps(session: Session, shop_ids: set[int], platform_codes: set[str]) -> tuple[dict, dict]:
    shop_names = dict(
        session.exec(select(Shop.id, Shop.shop_name).where(Shop.id.in_(shop_ids or {-1}))).all()
    )
    platform_names = dict(
        session.exec(
            select(Platform.platform_code, Platform.platform_name).where(
                Platform.platform_code.in_(platform_codes or {""})
            )
        ).all()
    )
    return shop_names, platform_names


# --------------------------------------------------------------------------- #
# FR-09-01 经营总览
# --------------------------------------------------------------------------- #
def overview(session: Session, *, start_time=None, end_time=None, platform_code=None, shop_id=None, allowed_shop_ids=None) -> dict:
    conditions, st, et = _order_conditions(start_time, end_time, platform_code, shop_id, allowed_shop_ids)
    rows = session.exec(
        select(Order.order_time, Order.pay_amount, Order.status, Order.buyer_account).where(*conditions)
    ).all()
    valid = [r for r in rows if r[2] not in _EXCLUDED_SALES_STATUS]
    order_count = len(valid)
    sales_amount = sum((_d(r[1]) for r in valid), Decimal("0"))
    buyer_count = len({r[3] for r in valid if r[3]})

    as_conditions = [AfterSale.apply_time >= st, AfterSale.apply_time <= et]
    if platform_code:
        as_conditions.append(AfterSale.platform_code == platform_code)
    as_conditions.extend(_shop_filter(AfterSale.shop_id, shop_id, allowed_shop_ids))
    as_rows = session.exec(
        select(AfterSale.refund_amount, AfterSale.refund_status, AfterSale.apply_time).where(*as_conditions)
    ).all()
    refund_amount = sum((_d(r[0]) for r in as_rows), Decimal("0"))
    refund_count = sum(1 for r in as_rows if r[1] == "SUCCESS")

    bucket: dict[str, dict] = {}
    for r in valid:
        day = _day(r[0])
        item = bucket.setdefault(day, {"date": day, "order_count": 0, "sales_amount": Decimal("0")})
        item["order_count"] += 1
        item["sales_amount"] += _d(r[1])
    trend = [
        {"date": k, "order_count": v["order_count"], "sales_amount": _f(v["sales_amount"])}
        for k, v in sorted(bucket.items())
    ]

    return {
        "start_time": format_datetime(st),
        "end_time": format_datetime(et),
        "order_count": order_count,
        "sales_amount": _f(sales_amount),
        "avg_order_amount": round(_f(sales_amount) / order_count, 2) if order_count else 0.0,
        "buyer_count": buyer_count,
        "refund_amount": _f(refund_amount),
        "refund_count": refund_count,
        "trend": trend,
    }


# --------------------------------------------------------------------------- #
# FR-09-02 渠道与店铺对比
# --------------------------------------------------------------------------- #
def channels(session: Session, *, start_time=None, end_time=None, platform_code=None, shop_id=None, allowed_shop_ids=None) -> dict:
    conditions, st, et = _order_conditions(start_time, end_time, platform_code, shop_id, allowed_shop_ids)
    rows = session.exec(
        select(Order.platform_code, Order.shop_id, Order.pay_amount, Order.status).where(*conditions)
    ).all()
    valid = [r for r in rows if r[3] not in _EXCLUDED_SALES_STATUS]

    by_platform: dict[str, dict] = {}
    by_shop: dict[int, dict] = {}
    for code, sid, pay, _status in valid:
        p = by_platform.setdefault(code, {"platform_code": code, "order_count": 0, "sales_amount": Decimal("0")})
        p["order_count"] += 1
        p["sales_amount"] += _d(pay)
        s = by_shop.setdefault(sid, {"shop_id": sid, "platform_code": code, "order_count": 0, "sales_amount": Decimal("0")})
        s["order_count"] += 1
        s["sales_amount"] += _d(pay)

    shop_names, platform_names = _name_maps(
        session, set(by_shop.keys()), set(by_platform.keys())
    )
    platform_list = []
    for code, v in by_platform.items():
        platform_list.append(
            {
                "platform_code": code,
                "platform_name": platform_names.get(code, code),
                "order_count": v["order_count"],
                "sales_amount": _f(v["sales_amount"]),
                "avg_order_amount": round(_f(v["sales_amount"]) / v["order_count"], 2) if v["order_count"] else 0.0,
            }
        )
    platform_list.sort(key=lambda x: x["sales_amount"], reverse=True)
    shop_list = [
        {
            "shop_id": v["shop_id"],
            "shop_name": shop_names.get(v["shop_id"], str(v["shop_id"])),
            "platform_code": v["platform_code"],
            "platform_name": platform_names.get(v["platform_code"], v["platform_code"]),
            "order_count": v["order_count"],
            "sales_amount": _f(v["sales_amount"]),
        }
        for v in by_shop.values()
    ]
    shop_list.sort(key=lambda x: x["sales_amount"], reverse=True)
    return {"by_platform": platform_list, "by_shop": shop_list}


# --------------------------------------------------------------------------- #
# FR-09-03 商品销售分析
# --------------------------------------------------------------------------- #
def products(session: Session, *, start_time=None, end_time=None, platform_code=None, shop_id=None, allowed_shop_ids=None, top: int = 10) -> dict:
    conditions, st, et = _order_conditions(start_time, end_time, platform_code, shop_id, allowed_shop_ids)
    conditions.append(Order.status.notin_(_EXCLUDED_SALES_STATUS))
    rows = session.exec(
        select(
            OrderItem.sku_id,
            OrderItem.sku_code,
            OrderItem.product_name,
            OrderItem.quantity,
            OrderItem.pay_amount,
            Order.order_time,
        ).join(Order, Order.id == OrderItem.order_id).where(*conditions)
    ).all()

    product_agg: dict = {}
    bucket: dict[str, dict] = {}
    total_qty = 0
    total_sales = Decimal("0")
    for sku_id, sku_code, name, qty, pay, order_time in rows:
        key = sku_id or f"U:{sku_code or name}"
        entry = product_agg.setdefault(
            key, {"sku_id": sku_id, "sku_code": sku_code, "product_name": name, "quantity": 0, "sales_amount": Decimal("0")}
        )
        entry["quantity"] += qty or 0
        entry["sales_amount"] += _d(pay)
        total_qty += qty or 0
        total_sales += _d(pay)
        day = _day(order_time)
        b = bucket.setdefault(day, {"date": day, "quantity": 0, "sales_amount": Decimal("0")})
        b["quantity"] += qty or 0
        b["sales_amount"] += _d(pay)

    hot = sorted(product_agg.values(), key=lambda x: x["sales_amount"], reverse=True)[:top]
    hot_list = [
        {
            "sku_id": h["sku_id"],
            "sku_code": h["sku_code"],
            "product_name": h["product_name"],
            "quantity": h["quantity"],
            "sales_amount": _f(h["sales_amount"]),
        }
        for h in hot
    ]

    # 品类分布（关联 SKU → 商品类目）
    category_agg: dict[str, dict] = {}
    sku_ids = {h["sku_id"] for h in hot if h["sku_id"]}
    sku_cat = {}
    if sku_ids:
        sku_cat = {
            sid: cat
            for sid, cat in session.exec(
                select(Sku.id, Product.category_name).join(Product, Product.id == Sku.spu_id).where(Sku.id.in_(sku_ids))
            ).all()
        }
    for h in hot:
        cat = sku_cat.get(h["sku_id"]) or "未分类"
        c = category_agg.setdefault(cat, {"category_name": cat, "quantity": 0, "sales_amount": Decimal("0")})
        c["quantity"] += h["quantity"]
        c["sales_amount"] += h["sales_amount"]
    categories = [
        {"category_name": c["category_name"], "quantity": c["quantity"], "sales_amount": _f(c["sales_amount"])}
        for c in sorted(category_agg.values(), key=lambda x: x["sales_amount"], reverse=True)
    ]

    trend = [
        {"date": k, "quantity": v["quantity"], "sales_amount": _f(v["sales_amount"])}
        for k, v in sorted(bucket.items())
    ]
    return {
        "total_quantity": total_qty,
        "total_sales_amount": _f(total_sales),
        "sku_count": len(product_agg),
        "hot": hot_list,
        "categories": categories,
        "trend": trend,
    }


# --------------------------------------------------------------------------- #
# FR-09-04 订单与履约分析
# --------------------------------------------------------------------------- #
def fulfillment(session: Session, *, start_time=None, end_time=None, platform_code=None, shop_id=None, allowed_shop_ids=None) -> dict:
    conditions, st, et = _order_conditions(start_time, end_time, platform_code, shop_id, allowed_shop_ids)
    rows = session.exec(select(Order.status, Order.order_time).where(*conditions)).all()
    status_agg: dict[str, int] = {}
    for status, _ in rows:
        status_agg[status] = status_agg.get(status, 0) + 1
    total = len(rows)
    status_distribution = [
        {"status": code, "status_name": ORDER_STATUS.get(code, code), "count": count}
        for code, count in sorted(status_agg.items(), key=lambda x: x[1], reverse=True)
    ]
    finished = status_agg.get("FINISHED", 0)
    shipped_like = sum(status_agg.get(s, 0) for s in ("SHIPPED", "PART_SHIPPED", "FINISHED"))
    fulfillment_rate = round(shipped_like / total, 4) if total else 0.0

    # 发货时效：发货时间 − 付款时间
    ship_conditions = [Shipment.shipped_at >= st, Shipment.shipped_at <= et]
    if platform_code:
        ship_conditions.append(Shipment.platform_code == platform_code)
    ship_conditions.extend(_shop_filter(Shipment.shop_id, shop_id, allowed_shop_ids))
    ship_rows = session.exec(
        select(Shipment.shipped_at, Order.paid_at)
        .join(Order, Order.id == Shipment.order_id)
        .where(*ship_conditions)
    ).all()
    durations = [
        (s - p).total_seconds() / 3600
        for s, p in ship_rows
        if s is not None and p is not None and s >= p
    ]
    avg_ship_hours = round(sum(durations) / len(durations), 2) if durations else 0.0

    ship_status_agg: dict[str, int] = {}
    ship_status_rows = session.exec(select(Shipment.status).where(*ship_conditions)).all()
    for status in ship_status_rows:
        ship_status_agg[status] = ship_status_agg.get(status, 0) + 1
    shipment_distribution = [
        {"status": code, "status_name": SHIPMENT_STATUS.get(code, code), "count": count}
        for code, count in sorted(ship_status_agg.items(), key=lambda x: x[1], reverse=True)
    ]

    return {
        "order_count": total,
        "finished_count": finished,
        "shipment_count": len(ship_rows),
        "avg_ship_hours": avg_ship_hours,
        "fulfillment_rate": fulfillment_rate,
        "status_distribution": status_distribution,
        "shipment_distribution": shipment_distribution,
    }


# --------------------------------------------------------------------------- #
# FR-09-05 售后分析
# --------------------------------------------------------------------------- #
def after_sales(session: Session, *, start_time=None, end_time=None, platform_code=None, shop_id=None, allowed_shop_ids=None, top: int = 10) -> dict:
    st, et = _range(start_time, end_time)
    conditions = [AfterSale.apply_time >= st, AfterSale.apply_time <= et]
    if platform_code:
        conditions.append(AfterSale.platform_code == platform_code)
    conditions.extend(_shop_filter(AfterSale.shop_id, shop_id, allowed_shop_ids))
    rows = session.exec(
        select(AfterSale.type, AfterSale.reason, AfterSale.status, AfterSale.refund_amount, AfterSale.refund_status, AfterSale.apply_time).where(*conditions)
    ).all()

    total = len(rows)
    refund_amount = sum((_d(r[3]) for r in rows), Decimal("0"))
    refund_success = sum(1 for r in rows if r[4] == "SUCCESS")
    type_agg: dict[str, int] = {}
    status_agg: dict[str, int] = {}
    reason_agg: dict[str, int] = {}
    bucket: dict[str, int] = {}
    for type_, reason, status, _amount, _rs, apply_time in rows:
        type_agg[type_] = type_agg.get(type_, 0) + 1
        status_agg[status] = status_agg.get(status, 0) + 1
        reason_key = reason or "未填写"
        reason_agg[reason_key] = reason_agg.get(reason_key, 0) + 1
        day = _day(apply_time)
        bucket[day] = bucket.get(day, 0) + 1

    return {
        "total": total,
        "refund_amount": _f(refund_amount),
        "refund_success_count": refund_success,
        "type_distribution": [
            {"type": k, "type_name": AFTER_SALE_TYPE.get(k, k), "count": v}
            for k, v in sorted(type_agg.items(), key=lambda x: x[1], reverse=True)
        ],
        "status_distribution": [
            {"status": k, "status_name": AFTER_SALE_STATUS.get(k, k), "count": v}
            for k, v in sorted(status_agg.items(), key=lambda x: x[1], reverse=True)
        ],
        "reason_distribution": [
            {"reason": k, "count": v}
            for k, v in sorted(reason_agg.items(), key=lambda x: x[1], reverse=True)[:top]
        ],
        "trend": [{"date": k, "count": v} for k, v in sorted(bucket.items())],
        "refund_status_names": REFUND_STATUS,
    }


# --------------------------------------------------------------------------- #
# FR-09-06 库存分析
# --------------------------------------------------------------------------- #
def inventory_analysis(session: Session, *, start_time=None, end_time=None, platform_code=None, shop_id=None, allowed_shop_ids=None, top: int = 10) -> dict:
    st, et = _range(start_time, end_time)
    inventories = session.exec(select(Inventory).order_by(Inventory.sku_id.asc())).all()
    sku_ids = {i.sku_id for i in inventories}
    skus = {s.id: s for s in session.exec(select(Sku).where(Sku.id.in_(sku_ids or {-1}))).all()}
    alerts = {
        a.sku_id: a
        for a in session.exec(select(InventoryAlert).where(InventoryAlert.sku_id.in_(sku_ids or {-1}))).all()
    }

    total_main = total_occupied = 0
    alert_rows = []
    available_map: dict[int, int] = {}
    for inv in inventories:
        available = (inv.main_qty or 0) - (inv.occupied_qty or 0)
        available_map[inv.sku_id] = available
        total_main += inv.main_qty or 0
        total_occupied += inv.occupied_qty or 0
        alert = alerts.get(inv.sku_id)
        threshold = alert.alert_qty if alert else 0
        if available <= threshold and (alert.is_enabled if alert else 1) == 1:
            sku = skus.get(inv.sku_id)
            alert_rows.append(
                {
                    "sku_id": inv.sku_id,
                    "sku_code": inv.sku_code,
                    "sku_name": sku.sku_name if sku else inv.sku_code,
                    "available_qty": available,
                    "alert_qty": threshold,
                    "risk": "缺货" if available <= 0 else "预警",
                }
            )
    alert_rows.sort(key=lambda x: x["available_qty"])

    # 出货量（近区间）→ 近似周转
    sold_conditions = [Order.order_time >= st, Order.order_time <= et, Order.status.notin_(_EXCLUDED_SALES_STATUS)]
    if platform_code:
        sold_conditions.append(Order.platform_code == platform_code)
    sold_conditions.extend(_shop_filter(Order.shop_id, shop_id, allowed_shop_ids))
    sold_rows = session.exec(
        select(OrderItem.sku_id, OrderItem.quantity).join(Order, Order.id == OrderItem.order_id).where(*sold_conditions)
    ).all()
    sold: dict[int, int] = {}
    for sku_id, qty in sold_rows:
        if sku_id:
            sold[sku_id] = sold.get(sku_id, 0) + (qty or 0)
    turnover_rows = []
    for sku_id, qty in sold.items():
        sku = skus.get(sku_id)
        available = available_map.get(sku_id, 0)
        turnover_rows.append(
            {
                "sku_id": sku_id,
                "sku_code": sku.sku_code if sku else str(sku_id),
                "sku_name": sku.sku_name if sku else str(sku_id),
                "sold_qty": qty,
                "available_qty": available,
                "turnover_rate": round(qty / available, 2) if available > 0 else float(qty),
            }
        )
    turnover_rows.sort(key=lambda x: x["sold_qty"], reverse=True)

    return {
        "sku_count": len(inventories),
        "main_qty": total_main,
        "occupied_qty": total_occupied,
        "available_qty": total_main - total_occupied,
        "alert_count": len(alert_rows),
        "shortage_count": sum(1 for r in alert_rows if r["available_qty"] <= 0),
        "alerts": alert_rows[:top],
        "turnover": turnover_rows[:top],
    }


# --------------------------------------------------------------------------- #
# FR-09-07 下钻
# --------------------------------------------------------------------------- #
def drill_down(
    session: Session,
    *,
    metric: str,
    start_time=None,
    end_time=None,
    platform_code=None,
    shop_id=None,
    sku_id=None,
    page: int | None = None,
    page_size: int | None = None,
    allowed_shop_ids=None,
) -> tuple[list[dict], int]:
    """汇总下钻到明细；metric ∈ order / product / after_sale / inventory_alert。"""
    p, s, offset = normalize(page, page_size)
    conditions, st, et = _order_conditions(start_time, end_time, platform_code, shop_id, allowed_shop_ids)

    if metric == "product":
        conditions.append(Order.status.notin_(_EXCLUDED_SALES_STATUS))
        if sku_id:
            conditions.append(OrderItem.sku_id == sku_id)
        base = select(OrderItem, Order).join(Order, Order.id == OrderItem.order_id).where(*conditions)
        count_stmt = (
            select(func.count()).select_from(OrderItem).join(Order, Order.id == OrderItem.order_id).where(*conditions)
        )
        total = int(session.exec(count_stmt).one())
        rows = session.exec(base.order_by(Order.order_time.desc()).offset(offset).limit(s)).all()
        items = [
            {
                "order_no": order.order_no,
                "platform_order_no": order.platform_order_no,
                "sku_code": item.sku_code,
                "product_name": item.product_name,
                "quantity": item.quantity,
                "pay_amount": _f(item.pay_amount),
                "order_time": format_datetime(order.order_time),
                "status": order.status,
                "status_name": ORDER_STATUS.get(order.status, order.status),
            }
            for item, order in rows
        ]
        return items, total

    if metric == "after_sale":
        as_conditions = [AfterSale.apply_time >= st, AfterSale.apply_time <= et]
        if platform_code:
            as_conditions.append(AfterSale.platform_code == platform_code)
        as_conditions.extend(_shop_filter(AfterSale.shop_id, shop_id, allowed_shop_ids))
        total = int(session.exec(select(func.count()).select_from(AfterSale).where(*as_conditions)).one())
        rows = session.exec(
            select(AfterSale).where(*as_conditions).order_by(AfterSale.apply_time.desc()).offset(offset).limit(s)
        ).all()
        items = [
            {
                "after_sale_no": a.after_sale_no,
                "order_no": a.order_no,
                "type": a.type,
                "type_name": AFTER_SALE_TYPE.get(a.type, a.type),
                "reason": a.reason,
                "status": a.status,
                "status_name": AFTER_SALE_STATUS.get(a.status, a.status),
                "refund_amount": _f(a.refund_amount),
                "apply_time": format_datetime(a.apply_time),
            }
            for a in rows
        ]
        return items, total

    if metric == "inventory_alert":
        rows = session.exec(select(Inventory, InventoryAlert).join(InventoryAlert, InventoryAlert.sku_id == Inventory.sku_id)).all()
        data = []
        for inv, alert in rows:
            available = (inv.main_qty or 0) - (inv.occupied_qty or 0)
            if alert.is_enabled == 1 and available <= alert.alert_qty:
                data.append(
                    {
                        "sku_id": inv.sku_id,
                        "sku_code": inv.sku_code,
                        "main_qty": inv.main_qty,
                        "occupied_qty": inv.occupied_qty,
                        "available_qty": available,
                        "alert_qty": alert.alert_qty,
                    }
                )
        data.sort(key=lambda x: x["available_qty"])
        total = len(data)
        return data[offset : offset + s], total

    # 默认：订单明细
    total = int(session.exec(select(func.count()).select_from(Order).where(*conditions)).one())
    rows = session.exec(select(Order).where(*conditions).order_by(Order.order_time.desc()).offset(offset).limit(s)).all()
    shop_names, platform_names = _name_maps(session, {o.shop_id for o in rows}, {o.platform_code for o in rows})
    items = [
        {
            "id": o.id,
            "order_no": o.order_no,
            "platform_order_no": o.platform_order_no,
            "platform_name": platform_names.get(o.platform_code, o.platform_code),
            "shop_name": shop_names.get(o.shop_id, str(o.shop_id)),
            "buyer_account": o.buyer_account,
            "pay_amount": _f(o.pay_amount),
            "status": o.status,
            "status_name": ORDER_STATUS.get(o.status, o.status),
            "order_time": format_datetime(o.order_time),
        }
        for o in rows
    ]
    return items, total
