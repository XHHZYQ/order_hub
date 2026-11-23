"""M2 订单服务：订单查询、订单同步（幂等汇聚）、异常重试与人工处理。"""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import or_
from sqlmodel import Session, func, select

from app.adapters.factory import get_adapter
from app.core.constants import ORDER_SOURCE, ORDER_STATUS
from app.core.exceptions import BusinessException, not_found, status_not_allowed
from app.models.order import Order, OrderChange, OrderExt, OrderItem, OrderLog
from app.models.platform import Platform, Shop
from app.services import inventory_service, product_service
from app.utils.datetime_util import format_datetime, now_utc, parse_datetime
from app.utils.id_generator import gen_order_no
from app.utils.pagination import normalize

# 字段中文名（用于变更记录展示）
FIELD_LABELS: dict[str, str] = {
    "goods_amount": "商品金额",
    "discount_amount": "优惠金额",
    "freight_amount": "运费",
    "pay_amount": "实付金额",
    "status": "订单状态",
    "platform_status": "平台原始状态",
    "receiver_name": "收货人",
    "receiver_phone": "收货电话",
    "receiver_province": "收货省份",
    "receiver_city": "收货城市",
    "receiver_district": "收货区县",
    "receiver_address": "收货地址",
    "buyer_account": "买家账号",
    "buyer_nick": "买家昵称",
    "buyer_remark": "买家留言",
}

# 已进入发货流程的订单状态（见《概要设计》6.1 规则 4/5）
LOCKED_STATUSES = {"SHIPPED", "PART_SHIPPED", "FINISHED"}

# 时间字段列表（出参统一格式化）
_ORDER_TIME_FIELDS = (
    "order_time",
    "paid_at",
    "shipped_at",
    "finished_at",
    "closed_at",
    "sync_time",
    "created_at",
    "updated_at",
)


def _display(value) -> str:
    """把值转成用于展示/对比的字符串。"""
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, datetime):
        return format_datetime(value) or ""
    return str(value)


def _order_dict(order: Order, shop_name: str | None, platform_name: str | None) -> dict:
    data = order.model_dump()
    for field in _ORDER_TIME_FIELDS:
        data[field] = format_datetime(data.get(field))
    data["status_name"] = ORDER_STATUS.get(order.status, order.status)
    data["source_name"] = ORDER_SOURCE.get(order.source, order.source)
    data["shop_name"] = shop_name
    data["platform_name"] = platform_name
    return data


def _name_maps(session: Session, rows: list[Order]) -> tuple[dict[int, str], dict[str, str]]:
    shop_names = {
        sid: name
        for sid, name in session.exec(
            select(Shop.id, Shop.shop_name).where(Shop.id.in_({r.shop_id for r in rows} or [-1]))
        ).all()
    }
    platform_names = {
        code: name
        for code, name in session.exec(
            select(Platform.platform_code, Platform.platform_name).where(
                Platform.platform_code.in_({r.platform_code for r in rows} or [-1])
            )
        ).all()
    }
    return shop_names, platform_names


# --------------------------------------------------------------------------- #
# 查询
# --------------------------------------------------------------------------- #
def _query_orders(
    session: Session,
    *,
    page: int | None,
    page_size: int | None,
    shop_id: int | None = None,
    platform_code: str | None = None,
    status: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    keyword: str | None = None,
    goods_keyword: str | None = None,
    allowed_shop_ids: list[int] | None = None,
    is_abnormal: int | None = None,
) -> tuple[list[dict], int]:
    conditions = [Order.is_deleted == 0]
    if shop_id:
        conditions.append(Order.shop_id == shop_id)
    if platform_code:
        conditions.append(Order.platform_code == platform_code)
    if status:
        conditions.append(Order.status == status)
    if is_abnormal is not None:
        conditions.append(Order.is_abnormal == is_abnormal)

    st = parse_datetime(start_time)
    et = parse_datetime(end_time)
    if st:
        conditions.append(Order.order_time >= st)
    if et:
        conditions.append(Order.order_time <= et)

    if keyword:
        like = f"%{keyword}%"
        conditions.append(
            or_(
                Order.order_no.like(like),
                Order.platform_order_no.like(like),
                Order.buyer_account.like(like),
                Order.receiver_name.like(like),
            )
        )
    if goods_keyword:
        sub = select(OrderItem.order_id).where(OrderItem.product_name.contains(goods_keyword))
        conditions.append(Order.id.in_(sub))
    if allowed_shop_ids is not None:
        conditions.append(Order.shop_id.in_(allowed_shop_ids or [-1]))

    p, s, offset = normalize(page, page_size)
    total = session.exec(select(func.count()).select_from(Order).where(*conditions)).one()
    rows = session.exec(
        select(Order)
        .where(*conditions)
        .order_by(Order.order_time.desc(), Order.id.desc())
        .offset(offset)
        .limit(s)
    ).all()
    shop_names, platform_names = _name_maps(session, rows)
    items = [
        _order_dict(r, shop_names.get(r.shop_id), platform_names.get(r.platform_code)) for r in rows
    ]
    return items, int(total)


def list_orders(
    session: Session,
    *,
    page: int | None,
    page_size: int | None,
    shop_id: int | None = None,
    platform_code: str | None = None,
    status: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    keyword: str | None = None,
    goods_keyword: str | None = None,
    allowed_shop_ids: list[int] | None = None,
) -> tuple[list[dict], int]:
    """订单列表（含店铺/平台名称与状态中文）。"""
    return _query_orders(
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


def list_sync_errors(
    session: Session,
    *,
    page: int | None,
    page_size: int | None,
    shop_id: int | None = None,
    platform_code: str | None = None,
    status: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    keyword: str | None = None,
    goods_keyword: str | None = None,
    allowed_shop_ids: list[int] | None = None,
) -> tuple[list[dict], int]:
    """同步异常订单列表（is_abnormal=1）。"""
    return _query_orders(
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
        is_abnormal=1,
    )


def get_order(session: Session, order_id: int) -> dict:
    order = session.get(Order, order_id)
    if not order or order.is_deleted == 1:
        raise not_found("订单不存在")
    shop = session.get(Shop, order.shop_id)
    platform = session.exec(select(Platform).where(Platform.platform_code == order.platform_code)).first()
    return _order_dict(
        order,
        shop.shop_name if shop else None,
        platform.platform_name if platform else None,
    )


def list_order_items(session: Session, order_id: int) -> list[dict]:
    rows = session.exec(select(OrderItem).where(OrderItem.order_id == order_id).order_by(OrderItem.id)).all()
    result = []
    for row in rows:
        data = row.model_dump()
        data["created_at"] = format_datetime(data.get("created_at"))
        result.append(data)
    return result


def list_order_ext(session: Session, order_id: int) -> list[dict]:
    rows = session.exec(
        select(OrderExt).where(OrderExt.order_id == order_id).order_by(OrderExt.id)
    ).all()
    result = []
    for row in rows:
        data = row.model_dump()
        data["created_at"] = format_datetime(data.get("created_at"))
        result.append(data)
    return result


def list_order_logs(session: Session, order_id: int) -> dict:
    log_rows = session.exec(
        select(OrderLog).where(OrderLog.order_id == order_id).order_by(OrderLog.created_at.desc(), OrderLog.id.desc())
    ).all()
    change_rows = session.exec(
        select(OrderChange)
        .where(OrderChange.order_id == order_id)
        .order_by(OrderChange.created_at.desc(), OrderChange.id.desc())
    ).all()

    logs = []
    for row in log_rows:
        data = row.model_dump()
        data["created_at"] = format_datetime(data.get("created_at"))
        logs.append(data)
    changes = []
    for row in change_rows:
        data = row.model_dump()
        data["created_at"] = format_datetime(data.get("created_at"))
        changes.append(data)
    return {"logs": logs, "changes": changes}


# --------------------------------------------------------------------------- #
# 同步（幂等汇聚）
# --------------------------------------------------------------------------- #
def _save_items(session: Session, order: Order, items: list[dict]) -> list[OrderItem]:
    """落订单明细，并按 (shop_id, platform_sku_id) 匹配本地 SKU。"""
    rows: list[OrderItem] = []
    for item in items:
        mapping = product_service.find_mapping(session, order.shop_id, item.get("platform_sku_id"))
        row = OrderItem(
            order_id=order.id,
            order_no=order.order_no,
            platform_sku_id=item.get("platform_sku_id"),
            platform_sku_name=item.get("platform_sku_name"),
            outer_sku_code=item.get("outer_sku_code"),
            sku_id=mapping.sku_id if mapping else None,
            sku_code=(mapping.sku_code if mapping else item.get("outer_sku_code")),
            product_name=item.get("product_name"),
            spec_desc=item.get("spec_desc"),
            price=item.get("price") or Decimal("0"),
            quantity=item.get("quantity") or 1,
            total_amount=item.get("total_amount") or Decimal("0"),
            discount_amount=item.get("discount_amount") or Decimal("0"),
            pay_amount=item.get("pay_amount") or Decimal("0"),
            shipped_quantity=0,
            refund_quantity=0,
            is_matched=1 if mapping else 0,
        )
        session.add(row)
        rows.append(row)
    return rows


def _save_ext(session: Session, order: Order, ext: list[dict]) -> None:
    for entry in ext:
        session.add(
            OrderExt(
                order_id=order.id,
                ext_key=entry.get("ext_key"),
                ext_name=entry.get("ext_name"),
                ext_value=entry.get("ext_value"),
            )
        )


def _add_log(
    session: Session,
    order: Order,
    *,
    action: str,
    content: str | None,
    source: str,
    operator: str | None = None,
    from_status: str | None = None,
    to_status: str | None = None,
) -> None:
    session.add(
        OrderLog(
            order_id=order.id,
            order_no=order.order_no,
            action=action,
            from_status=from_status,
            to_status=to_status,
            content=content,
            operator=operator,
            source=source,
        )
    )


def _insert_order(session: Session, shop: Shop, payload: dict, sync_time: datetime) -> None:
    order = Order(
        order_no=gen_order_no(),
        platform_code=shop.platform_code,
        shop_id=shop.id,
        platform_order_no=payload["platform_order_no"],
        buyer_account=payload.get("buyer_account"),
        buyer_nick=payload.get("buyer_nick"),
        receiver_name=payload.get("receiver_name"),
        receiver_phone=payload.get("receiver_phone"),
        receiver_province=payload.get("receiver_province"),
        receiver_city=payload.get("receiver_city"),
        receiver_district=payload.get("receiver_district"),
        receiver_address=payload.get("receiver_address"),
        goods_amount=payload.get("goods_amount") or Decimal("0"),
        discount_amount=payload.get("discount_amount") or Decimal("0"),
        freight_amount=payload.get("freight_amount") or Decimal("0"),
        pay_amount=payload.get("pay_amount") or Decimal("0"),
        status=payload.get("status") or "PENDING_PAY",
        platform_status=payload.get("platform_status"),
        source="平台",
        is_abnormal=1 if payload.get("anomaly") else 0,
        abnormal_reason=payload.get("anomaly"),
        buyer_remark=payload.get("buyer_remark"),
        order_time=payload.get("order_time") or sync_time,
        paid_at=payload.get("paid_at"),
        shipped_at=payload.get("shipped_at"),
        sync_time=sync_time,
    )
    session.add(order)
    session.flush()  # 生成主键，供明细/扩展落库使用

    rows = _save_items(session, order, payload.get("items") or [])
    _save_ext(session, order, payload.get("ext") or [])
    _add_log(session, order, action="同步", content="首次汇聚订单", source="系统")
    if order.status != "CLOSED":
        _occupy_items(session, order, rows)


def _occupy_items(session: Session, order: Order, rows: list[OrderItem]) -> None:
    """对新汇聚订单的已匹配明细占用库存（防超卖，占用失败写订单日志）。"""
    for row in rows:
        if not row.sku_id or not row.quantity:
            continue
        result = inventory_service.occupy_stock(
            session,
            sku_id=row.sku_id,
            qty=row.quantity,
            source_no=order.order_no,
            remark=f"订单 {order.order_no} 占用",
            raise_on_fail=False,
        )
        if not result.get("success"):
            _add_log(
                session,
                order,
                action="库存占用",
                content=f"占用失败：{result.get('reason')}（SKU {row.sku_code} 数量 {row.quantity}）",
                source="系统",
                to_status=order.status,
            )


def _release_items(session: Session, order: Order) -> None:
    """订单关闭时释放其已匹配明细占用的库存。"""
    rows = session.exec(
        select(OrderItem).where(OrderItem.order_id == order.id, OrderItem.sku_id.is_not(None))
    ).all()
    for row in rows:
        if not row.quantity:
            continue
        result = inventory_service.release_stock(
            session,
            sku_id=row.sku_id,
            qty=row.quantity,
            source_no=order.order_no,
            remark=f"订单 {order.order_no} 关闭释放",
            raise_on_fail=False,
        )
        if not result.get("success"):
            _add_log(
                session,
                order,
                action="库存释放",
                content=f"释放失败：{result.get('reason')}（SKU {row.sku_code} 数量 {row.quantity}）",
                source="系统",
                to_status=order.status,
            )


# 变更类型映射（见《数据库设计》4.2.5：改价/改址/备注/打标；状态类归为"状态"）
_CHANGE_TYPE_BY_FIELD = {
    "goods_amount": "改价",
    "discount_amount": "改价",
    "freight_amount": "改价",
    "pay_amount": "改价",
    "receiver_name": "改址",
    "receiver_phone": "改址",
    "receiver_province": "改址",
    "receiver_city": "改址",
    "receiver_district": "改址",
    "receiver_address": "改址",
    "merchant_remark": "备注",
    "buyer_remark": "备注",
    "tags": "打标",
}


def _change_type(field_name: str) -> str:
    """按变更字段推导变更类型。"""
    return _CHANGE_TYPE_BY_FIELD.get(field_name, "状态")


def _update_order(session: Session, order: Order, payload: dict, sync_time: datetime) -> None:
    """按平台最新数据更新已存在订单；已进入发货流程的订单仅更新同步时间与平台状态。"""
    changes: list[tuple[str, str, str]] = []
    old_status = order.status

    if payload.get("platform_status") != order.platform_status:
        changes.append(
            ("platform_status", _display(order.platform_status), _display(payload.get("platform_status")))
        )
        order.platform_status = payload.get("platform_status")
    order.sync_time = sync_time

    locked = order.status in LOCKED_STATUSES
    if not locked:
        updatable = (
            "goods_amount",
            "discount_amount",
            "freight_amount",
            "pay_amount",
            "status",
            "receiver_name",
            "receiver_phone",
            "receiver_province",
            "receiver_city",
            "receiver_district",
            "receiver_address",
            "buyer_account",
            "buyer_nick",
            "buyer_remark",
        )
        for field in updatable:
            new_value = payload.get(field)
            if new_value is None or new_value == "":
                continue
            if field == "status" and not payload.get("status"):
                continue
            if _display(getattr(order, field)) == _display(new_value):
                continue
            changes.append((field, _display(getattr(order, field)), _display(new_value)))
            setattr(order, field, new_value)

    if payload.get("anomaly"):
        order.is_abnormal = 1
        order.abnormal_reason = payload["anomaly"]

    session.add(order)
    for field_name, before_value, after_value in changes:
        session.add(
            OrderChange(
                order_id=order.id,
                order_no=order.order_no,
                change_type=_change_type(field_name),
                field_name=field_name,
                before_value=before_value,
                after_value=after_value,
                reason=None,
                operator=None,
            )
        )
    content = (
        f"平台数据更新：{'、'.join(FIELD_LABELS.get(c[0], c[0]) for c in changes)}"
        if changes
        else "重复同步，数据无变化"
    )
    _add_log(session, order, action="同步", content=content, source="系统")
    if old_status != "CLOSED" and order.status == "CLOSED":
        _release_items(session, order)


def run_order_sync(session: Session, *, shops: list[Shop], start: datetime, end: datetime) -> dict:
    """执行订单同步（幂等）。

    以 (platform_code, shop_id, platform_order_no) 为唯一键 upsert，
    重复同步同一时间窗口不会产生重复订单。
    """
    started = time.perf_counter()
    total = success = fail = 0
    for shop in shops:
        if shop is None or shop.platform_code is None:
            continue
        try:
            adapter = get_adapter(shop.platform_code)
        except BusinessException:
            continue
        orders = adapter.fetch_orders(shop, start, end)
        for payload in orders:
            platform_order_no = payload.get("platform_order_no")
            if not platform_order_no:
                continue
            total += 1
            if payload.get("anomaly"):
                fail += 1
            else:
                success += 1
            _upsert_order(session, shop, payload)
    session.commit()
    return {
        "total": total,
        "success_count": success,
        "fail_count": fail,
        "cost_ms": int((time.perf_counter() - started) * 1000),
    }


def _upsert_order(session: Session, shop: Shop, payload: dict) -> None:
    existing = session.exec(
        select(Order).where(
            Order.platform_code == shop.platform_code,
            Order.shop_id == shop.id,
            Order.platform_order_no == payload["platform_order_no"],
        )
    ).first()
    sync_time = now_utc()
    if existing is None:
        _insert_order(session, shop, payload, sync_time)
    else:
        _update_order(session, existing, payload, sync_time)


# --------------------------------------------------------------------------- #
# 异常重试 / 人工处理
# --------------------------------------------------------------------------- #
def retry_sync_error(session: Session, order_id: int, operator) -> dict:
    """重试单条同步异常订单：按店铺与下单时间附近窗口重新拉取平台数据。"""
    order = session.get(Order, order_id)
    if not order or order.is_deleted == 1:
        raise not_found("订单不存在")
    if order.is_abnormal != 1:
        raise status_not_allowed("仅同步异常订单可重试")
    shop = session.get(Shop, order.shop_id)
    if not shop:
        raise not_found("店铺不存在")

    adapter = get_adapter(order.platform_code)
    base_time = order.order_time or now_utc()
    start = base_time - timedelta(days=1)
    end = base_time + timedelta(days=1)
    found = next(
        (o for o in adapter.fetch_orders(shop, start, end) if o.get("platform_order_no") == order.platform_order_no),
        None,
    )
    operator_name = getattr(operator, "username", None) or "系统"

    if found and not found.get("anomaly"):
        _update_order(session, order, found, now_utc())
        order.is_abnormal = 0
        order.abnormal_reason = None
        session.add(order)
        _add_log(
            session,
            order,
            action="异常重试",
            content="重新拉取平台数据成功，异常已消除",
            source="系统",
            operator=operator_name,
        )
        session.commit()
        session.refresh(order)
        return {"order_id": order.id, "success": True, "abnormal": 0, "abnormal_reason": None}

    reason = (found or {}).get("anomaly") or order.abnormal_reason or "平台未返回该订单"
    order.is_abnormal = 1
    order.abnormal_reason = reason
    order.sync_time = now_utc()
    session.add(order)
    _add_log(
        session,
        order,
        action="异常重试",
        content=f"重试未消除异常：{reason}",
        source="系统",
        operator=operator_name,
    )
    session.commit()
    session.refresh(order)
    return {"order_id": order.id, "success": False, "abnormal": 1, "abnormal_reason": reason}


def handle_sync_error(session: Session, order_id: int, note: str | None, operator) -> dict:
    """同步异常人工处理：清除异常标记并把备注追加到商家备注。"""
    order = session.get(Order, order_id)
    if not order or order.is_deleted == 1:
        raise not_found("订单不存在")
    if order.is_abnormal != 1:
        raise status_not_allowed("仅同步异常订单可人工处理")

    order.is_abnormal = 0
    if note:
        merged = f"{order.merchant_remark}；{note}" if order.merchant_remark else note
        order.merchant_remark = merged[:500]
    order.sync_time = now_utc()
    session.add(order)
    _add_log(
        session,
        order,
        action="异常处理",
        content=note or "人工确认异常",
        source="人工",
        operator=getattr(operator, "username", None),
    )
    session.commit()
    return get_order(session, order_id)
