"""M2/M3 订单服务：订单查询、订单同步（幂等汇聚）、异常重试与人工处理；
审核、改价、改址、备注打标、合并拆分、异常订单池、批量操作与状态流转。"""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import and_, or_
from sqlmodel import Session, func, select

from app.adapters.factory import get_adapter
from app.core.constants import ORDER_CHANGE_TYPE, ORDER_SOURCE, ORDER_STATUS
from app.core.exceptions import (
    BusinessException,
    not_found,
    param_error,
    status_not_allowed,
)
from app.models.order import Order, OrderChange, OrderExt, OrderItem, OrderLog
from app.models.platform import Platform, Shop
from app.services import inventory_service, order_state_machine, product_service
from app.utils.datetime_util import format_datetime, now_utc, parse_datetime
from app.utils.id_generator import gen_order_no, generate_no
from app.utils.pagination import normalize

# 可执行改价/改址/打标的最晚状态（见《概要设计》6.3 实现要点 3）
EDITABLE_STATUSES = {"PENDING_PAY", "PENDING_AUDIT", "PENDING_SHIP", "AFTER_SALE"}

# 异常订单池类型（FR-03-07）
ABNORMAL_TYPES: dict[str, str] = {
    "SYNC": "同步异常",
    "ADDRESS": "地址异常",
    "AMOUNT": "金额异常",
    "TIMEOUT": "长时间未付/未发",
}

# 未付款/未发货超时阈值
UNPAID_HOURS = 24
UNSHIPPED_HOURS = 48

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
    data["tag_list"] = [t for t in (order.tags or "").split(",") if t]
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
                Platform.platform_code.in_({r.platform_code for r in rows if r.platform_code} or [""])
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
    """对新汇聚订单的已匹配明细占用库存（防超卖，占用失败写订单日志）。

    按 sku_id 升序占用，统一多行的加锁顺序，降低并发同步时的死锁风险。
    """
    for row in sorted(rows, key=lambda r: r.sku_id or 0):
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


# --------------------------------------------------------------------------- #
# M3 订单处理：审核 / 改价 / 改址 / 备注打标 / 状态流转
# --------------------------------------------------------------------------- #
def _op_name(operator) -> str:
    return getattr(operator, "username", None) or "系统"


def _load_order(session: Session, order_id: int) -> Order:
    order = session.get(Order, order_id)
    if not order or order.is_deleted == 1:
        raise not_found("订单不存在")
    return order


def _add_change(
    session: Session,
    order: Order,
    *,
    change_type: str,
    field_name: str,
    before_value,
    after_value,
    reason: str | None = None,
    operator: str | None = None,
) -> None:
    """写一条订单变更记录（不提交）。"""
    session.add(
        OrderChange(
            order_id=order.id,
            order_no=order.order_no,
            change_type=change_type,
            field_name=field_name,
            before_value=_display(before_value),
            after_value=_display(after_value),
            reason=reason,
            operator=operator,
        )
    )


def _apply_status(
    session: Session,
    order: Order,
    to_status: str,
    *,
    operator: str | None,
    source: str,
    remark: str | None = None,
    do_assert: bool = True,
) -> None:
    """执行状态流转（含时间戳、库存释放、日志与变更留痕），不提交事务。"""
    from_status = order.status
    if do_assert:
        order_state_machine.assert_transition(from_status, to_status)

    now = now_utc()
    order.status = to_status
    if to_status == "SHIPPED" and not order.shipped_at:
        order.shipped_at = now
    if to_status == "FINISHED" and not order.finished_at:
        order.finished_at = now
    if to_status == "CLOSED" and not order.closed_at:
        order.closed_at = now
    session.add(order)

    _add_change(
        session,
        order,
        change_type=ORDER_CHANGE_TYPE["STATUS"],
        field_name="status",
        before_value=ORDER_STATUS.get(from_status, from_status),
        after_value=ORDER_STATUS.get(to_status, to_status),
        reason=remark,
        operator=operator,
    )
    _add_log(
        session,
        order,
        action="状态流转",
        content=remark or f"{ORDER_STATUS.get(from_status, from_status)} → {ORDER_STATUS.get(to_status, to_status)}",
        source=source,
        operator=operator,
        from_status=from_status,
        to_status=to_status,
    )
    if to_status == "CLOSED" and from_status != "CLOSED":
        _release_items(session, order)


def _do_audit(session: Session, order: Order, action: str, reason: str | None, operator: str | None) -> None:
    action = (action or "").upper()
    if action not in ("PASS", "REJECT"):
        raise param_error("审核动作不合法，仅支持 PASS / REJECT")
    if order.status != "PENDING_AUDIT":
        raise status_not_allowed("仅待审核订单可执行审核")
    target = "PENDING_SHIP" if action == "PASS" else "CLOSED"
    label = "审核通过" if action == "PASS" else "审核驳回"
    _apply_status(
        session,
        order,
        target,
        operator=operator,
        source="人工",
        remark=f"{label}{('：' + reason) if reason else ''}",
    )


def audit_order(session: Session, order_id: int, payload, operator=None) -> dict:
    """单条审核（通过/驳回）。"""
    order = _load_order(session, order_id)
    _do_audit(session, order, payload.action, payload.reason, _op_name(operator))
    session.commit()
    return get_order(session, order_id)


def batch_audit(session: Session, payload, operator=None) -> dict:
    """批量审核（FR-03-08）。"""
    op = _op_name(operator)
    success, failed = [], []
    for order_id in dict.fromkeys(payload.order_ids):
        order = session.get(Order, order_id)
        if not order or order.is_deleted == 1:
            failed.append({"order_id": order_id, "reason": "订单不存在"})
            continue
        try:
            _do_audit(session, order, payload.action, payload.reason, op)
            success.append(order_id)
        except BusinessException as exc:
            failed.append({"order_id": order_id, "reason": exc.message})
    session.commit()
    return {"success_count": len(success), "fail_count": len(failed), "success_ids": success, "failed": failed}


def _do_price(session: Session, order: Order, payload, operator: str | None) -> None:
    if order.status not in EDITABLE_STATUSES:
        raise status_not_allowed("订单已进入发货流程，不允许改价")
    changes: list[tuple[str, object, object]] = []
    for field in ("goods_amount", "discount_amount", "freight_amount", "pay_amount"):
        value = getattr(payload, field, None)
        if value is None:
            continue
        new_value = Decimal(str(value))
        if new_value < 0:
            raise param_error(f"{FIELD_LABELS.get(field, field)}不能为负数")
        if _display(getattr(order, field)) == _display(new_value):
            continue
        changes.append((field, getattr(order, field), new_value))
        setattr(order, field, new_value)
    if not changes:
        raise param_error("未提供需要修改的金额，或金额与当前一致")
    session.add(order)
    for field, before, after in changes:
        _add_change(
            session, order, change_type=ORDER_CHANGE_TYPE["PRICE"], field_name=field,
            before_value=before, after_value=after, reason=payload.reason, operator=operator,
        )
    detail = "、".join(f"{FIELD_LABELS.get(f, f)} {_display(b)}→{_display(a)}" for f, b, a in changes)
    _add_log(
        session, order, action="改价",
        content=f"{detail}（原因：{payload.reason or '无'}）", source="人工", operator=operator,
    )


def change_price(session: Session, order_id: int, payload, operator=None) -> dict:
    """改价（记录改价人与原因，FR-03-02）。"""
    order = _load_order(session, order_id)
    _do_price(session, order, payload, _op_name(operator))
    session.commit()
    return get_order(session, order_id)


_ADDRESS_FIELDS = (
    "receiver_name",
    "receiver_phone",
    "receiver_province",
    "receiver_city",
    "receiver_district",
    "receiver_address",
)


def _do_address(session: Session, order: Order, payload, operator: str | None) -> None:
    if order.status not in EDITABLE_STATUSES:
        raise status_not_allowed("订单已进入发货流程，不允许修改收货地址")
    changes: list[tuple[str, object, object]] = []
    for field in _ADDRESS_FIELDS:
        value = getattr(payload, field, None)
        if value is None:
            continue
        if _display(getattr(order, field)) == _display(value):
            continue
        changes.append((field, getattr(order, field), value))
        setattr(order, field, value)
    if not changes:
        raise param_error("未提供需要修改的收货信息，或信息与当前一致")
    session.add(order)
    for field, before, after in changes:
        _add_change(
            session, order, change_type=ORDER_CHANGE_TYPE["ADDRESS"], field_name=field,
            before_value=before, after_value=after, reason=payload.reason, operator=operator,
        )
    detail = "、".join(FIELD_LABELS.get(f, f) for f, _, _ in changes)
    _add_log(
        session, order, action="改址",
        content=f"修改收货信息：{detail}（原因：{payload.reason or '无'}）", source="人工", operator=operator,
    )


def change_address(session: Session, order_id: int, payload, operator=None) -> dict:
    """修改收货地址（记录历史，FR-03-03）。"""
    order = _load_order(session, order_id)
    _do_address(session, order, payload, _op_name(operator))
    session.commit()
    return get_order(session, order_id)


def _do_remark(session: Session, order: Order, payload, operator: str | None) -> None:
    changes: list[tuple[str, object, object]] = []
    if payload.merchant_remark is not None:
        new = payload.merchant_remark.strip()
        if payload.append and order.merchant_remark:
            new = f"{order.merchant_remark}；{new}"
        new = new[:500]
        if new != (order.merchant_remark or ""):
            changes.append(("merchant_remark", order.merchant_remark, new))
            order.merchant_remark = new
    if payload.buyer_remark is not None:
        new = payload.buyer_remark.strip()[:500]
        if new != (order.buyer_remark or ""):
            changes.append(("buyer_remark", order.buyer_remark, new))
            order.buyer_remark = new
    if payload.tags is not None:
        tags = [t.strip() for t in payload.tags if t and t.strip()]
        joined = ",".join(dict.fromkeys(tags))[:255]
        if joined != (order.tags or ""):
            changes.append(("tags", order.tags, joined))
            order.tags = joined
    if not changes:
        raise param_error("未提供备注或标签，或内容与当前一致")
    session.add(order)
    for field, before, after in changes:
        change_type = ORDER_CHANGE_TYPE["TAG"] if field == "tags" else ORDER_CHANGE_TYPE["REMARK"]
        _add_change(
            session, order, change_type=change_type, field_name=field,
            before_value=before, after_value=after, operator=operator,
        )
    row = next((c for c in changes if c[0] != "tags"), None)
    if row:
        _add_log(
            session, order, action="备注",
            content=f"{FIELD_LABELS.get(row[0], row[0])}更新", source="人工", operator=operator,
        )
    if any(c[0] == "tags" for c in changes):
        _add_log(
            session, order, action="打标",
            content=f"标签更新为：{order.tags or '（清空）'}", source="人工", operator=operator,
        )


def add_remark(session: Session, order_id: int, payload, operator=None) -> dict:
    """添加备注/打标（FR-03-04）。"""
    order = _load_order(session, order_id)
    _do_remark(session, order, payload, _op_name(operator))
    session.commit()
    return get_order(session, order_id)


def batch_remark(session: Session, payload, operator=None) -> dict:
    """批量备注/打标（FR-03-08）。"""
    op = _op_name(operator)
    success, failed = [], []
    for order_id in dict.fromkeys(payload.order_ids):
        order = session.get(Order, order_id)
        if not order or order.is_deleted == 1:
            failed.append({"order_id": order_id, "reason": "订单不存在"})
            continue
        try:
            _do_remark(session, order, payload, op)
            success.append(order_id)
        except BusinessException as exc:
            failed.append({"order_id": order_id, "reason": exc.message})
    session.commit()
    return {"success_count": len(success), "fail_count": len(failed), "success_ids": success, "failed": failed}


def batch_forward_ship(session: Session, payload, operator=None) -> dict:
    """批量转发货：将待审核订单批量审核通过并转入待发货（FR-03-08）。"""
    op = _op_name(operator)
    success, failed = [], []
    for order_id in dict.fromkeys(payload.order_ids):
        order = session.get(Order, order_id)
        if not order or order.is_deleted == 1:
            failed.append({"order_id": order_id, "reason": "订单不存在"})
            continue
        try:
            _do_audit(session, order, "PASS", "批量转发货", op)
            success.append(order_id)
        except BusinessException as exc:
            failed.append({"order_id": order_id, "reason": exc.message})
    session.commit()
    return {"success_count": len(success), "fail_count": len(failed), "success_ids": success, "failed": failed}


def change_status(session: Session, order_id: int, payload, operator=None) -> dict:
    """订单状态流转（状态机驱动，FR-03-09）。"""
    order = _load_order(session, order_id)
    _apply_status(
        session, order, payload.to_status.value if hasattr(payload.to_status, "value") else str(payload.to_status),
        operator=_op_name(operator), source="人工", remark=payload.remark,
    )
    session.commit()
    return get_order(session, order_id)


def status_options(session: Session, order_id: int) -> dict:
    """当前状态下可流转的下一状态（供前端下拉）。"""
    order = _load_order(session, order_id)
    return {
        "order_id": order.id,
        "current_status": order.status,
        "current_status_name": ORDER_STATUS.get(order.status, order.status),
        "options": order_state_machine.next_statuses(order.status),
    }


# --------------------------------------------------------------------------- #
# M3 订单合并 / 拆分
# --------------------------------------------------------------------------- #
def merge_orders(session: Session, payload, operator=None) -> dict:
    """订单合并：同一买家 + 同一收货信息的多个订单合并为一个待发货批次（FR-03-05）。"""
    op = _op_name(operator)
    ids = list(dict.fromkeys(payload.order_ids))
    if len(ids) < 2:
        raise param_error("至少选择 2 个订单进行合并")
    orders = [session.get(Order, i) for i in ids]
    if any(o is None or o.is_deleted == 1 for o in orders):
        raise not_found("存在无效订单，无法合并")

    keys = {(o.buyer_account, o.receiver_name, o.receiver_phone, o.receiver_address) for o in orders}
    if len(keys) != 1:
        raise param_error("仅支持同一买家、同一收货信息的订单合并")
    for o in orders:
        if o.status not in {"PENDING_PAY", "PENDING_AUDIT", "PENDING_SHIP"}:
            raise status_not_allowed(f"订单 {o.order_no} 当前状态不可合并")
        if o.merge_group_no:
            raise status_not_allowed(f"订单 {o.order_no} 已存在合并批次")

    group_no = generate_no("MG")
    for o in orders:
        o.merge_group_no = group_no
        session.add(o)
        _add_change(
            session, o, change_type=ORDER_CHANGE_TYPE["MERGE"], field_name="merge_group_no",
            before_value=None, after_value=group_no, reason=payload.remark, operator=op,
        )
        _add_log(
            session, o, action="合并",
            content=f"并入合并批次 {group_no}（共 {len(orders)} 单）", source="人工", operator=op,
        )
    session.commit()
    return {
        "merge_group_no": group_no,
        "order_count": len(orders),
        "order_nos": [o.order_no for o in orders],
    }


def split_order(session: Session, order_id: int, payload, operator=None) -> dict:
    """订单拆分：按商品明细拆分为多个子订单（FR-03-06）。

    入参 parts 为拆分方案：[{"items": [{"item_id": 1, "quantity": 1}, ...]}, ...]，
    要求各 part 的明细数量之和等于原单对应明细数量（整单拆分）。
    """
    op = _op_name(operator)
    parent = _load_order(session, order_id)
    if parent.status not in {"PENDING_PAY", "PENDING_AUDIT", "PENDING_SHIP", "AFTER_SALE"}:
        raise status_not_allowed("订单已发货或已关闭，不允许拆分")
    if parent.parent_order_no:
        raise status_not_allowed("子订单不可再次拆分")

    items = session.exec(select(OrderItem).where(OrderItem.order_id == order_id)).all()
    if not items:
        raise param_error("订单无明细，无法拆分")
    item_map = {row.id: row for row in items}
    parts = payload.parts or []
    if len(parts) < 2:
        raise param_error("拆分至少需要 2 个部分")

    requested: dict[int, int] = {}
    for part in parts:
        if not part.items:
            raise param_error("每个拆分部分至少包含一条明细")
        for it in part.items:
            if it.item_id not in item_map:
                raise param_error(f"明细 {it.item_id} 不属于该订单")
            if it.quantity <= 0:
                raise param_error("拆分数量必须大于 0")
            requested[it.item_id] = requested.get(it.item_id, 0) + it.quantity
    for row in items:
        if requested.get(row.id, 0) != row.quantity:
            raise param_error(
                f"拆分需覆盖全部明细数量：{row.product_name or row.sku_code} 应为 {row.quantity}，"
                f"实际 {requested.get(row.id, 0)}"
            )

    parent_goods = sum((row.total_amount or Decimal("0")) for row in items) or Decimal("1")
    # 原单释放占用并关闭
    _release_items(session, parent)
    from_status = parent.status
    parent.status = "CLOSED"
    parent.closed_at = now_utc()
    session.add(parent)
    _add_change(
        session, parent, change_type=ORDER_CHANGE_TYPE["SPLIT"], field_name="status",
        before_value=ORDER_STATUS.get(from_status, from_status), after_value="已拆分关闭",
        reason=payload.remark, operator=op,
    )
    _add_log(
        session, parent, action="拆分",
        content=f"拆分为 {len(parts)} 个子订单并关闭原单", source="人工", operator=op,
        from_status=from_status, to_status="CLOSED",
    )

    children: list[str] = []
    for idx, part in enumerate(parts, start=1):
        child = Order(
            order_no=gen_order_no(),
            platform_code=parent.platform_code,
            shop_id=parent.shop_id,
            platform_order_no=f"{parent.platform_order_no}-{idx}",
            buyer_account=parent.buyer_account,
            buyer_nick=parent.buyer_nick,
            receiver_name=parent.receiver_name,
            receiver_phone=parent.receiver_phone,
            receiver_province=parent.receiver_province,
            receiver_city=parent.receiver_city,
            receiver_district=parent.receiver_district,
            receiver_address=parent.receiver_address,
            goods_amount=Decimal("0"),
            discount_amount=Decimal("0"),
            freight_amount=parent.freight_amount if idx == 1 else Decimal("0"),
            pay_amount=Decimal("0"),
            status="PENDING_SHIP",
            platform_status=parent.platform_status,
            source=parent.source,
            buyer_remark=parent.buyer_remark,
            order_time=parent.order_time,
            paid_at=parent.paid_at,
            parent_order_no=parent.order_no,
            sync_time=now_utc(),
        )
        session.add(child)
        session.flush()

        child_goods = Decimal("0")
        child_rows: list[OrderItem] = []
        for it in part.items:
            src = item_map[it.item_id]
            qty = it.quantity
            unit = (src.total_amount or Decimal("0")) / (src.quantity or 1)
            total = (unit * qty).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            pay = ((src.pay_amount or Decimal("0")) / (src.quantity or 1) * qty).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            row = OrderItem(
                order_id=child.id,
                order_no=child.order_no,
                platform_sku_id=src.platform_sku_id,
                platform_sku_name=src.platform_sku_name,
                outer_sku_code=src.outer_sku_code,
                sku_id=src.sku_id,
                sku_code=src.sku_code,
                product_name=src.product_name,
                spec_desc=src.spec_desc,
                price=src.price,
                quantity=qty,
                total_amount=total,
                discount_amount=Decimal("0"),
                pay_amount=pay,
                shipped_quantity=0,
                refund_quantity=0,
                is_matched=src.is_matched,
            )
            session.add(row)
            child_rows.append(row)
            child_goods += total

        child.goods_amount = child_goods
        child.discount_amount = (
            (parent.discount_amount or Decimal("0")) * child_goods / parent_goods
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        child.pay_amount = (child_goods - child.discount_amount + child.freight_amount).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        session.add(child)
        _occupy_items(session, child, child_rows)
        _add_log(
            session, child, action="拆分",
            content=f"由父订单 {parent.order_no} 拆分生成", source="人工", operator=op,
        )
        children.append(child.order_no)

    session.commit()
    return {"parent_order_no": parent.order_no, "child_count": len(children), "child_order_nos": children}


# --------------------------------------------------------------------------- #
# M3 异常订单池
# --------------------------------------------------------------------------- #
def _timeout_condition(now: datetime):
    return or_(
        and_(Order.status == "PENDING_PAY", Order.order_time < now - timedelta(hours=UNPAID_HOURS)),
        and_(Order.status == "PENDING_SHIP", Order.paid_at < now - timedelta(hours=UNSHIPPED_HOURS)),
    )


def _address_condition():
    return or_(
        Order.receiver_address.is_(None),
        Order.receiver_address == "",
        Order.receiver_phone.is_(None),
        Order.receiver_phone == "",
    )


def _amount_mismatch_ids(session: Session) -> set[int]:
    """找出商品金额与明细合计不一致的订单 id（金额异常）。"""
    totals = dict(
        session.exec(
            select(OrderItem.order_id, func.sum(OrderItem.total_amount)).group_by(OrderItem.order_id)
        ).all()
    )
    if not totals:
        return set()
    rows = session.exec(
        select(Order.id, Order.goods_amount).where(Order.id.in_(list(totals.keys())))
    ).all()
    return {oid for oid, goods in rows if abs(Decimal(goods or 0) - Decimal(totals.get(oid) or 0)) > Decimal("0.01")}


def _abnormal_types_of(order: Order, mismatch_ids: set[int], now: datetime) -> list[str]:
    types: list[str] = []
    if order.is_abnormal == 1:
        types.append("SYNC")
    if not order.receiver_address or not order.receiver_phone:
        types.append("ADDRESS")
    if order.id in mismatch_ids:
        types.append("AMOUNT")
    if order.status == "PENDING_PAY" and order.order_time and order.order_time < now - timedelta(hours=UNPAID_HOURS):
        types.append("TIMEOUT")
    if order.status == "PENDING_SHIP" and order.paid_at and order.paid_at < now - timedelta(hours=UNSHIPPED_HOURS):
        types.append("TIMEOUT")
    return types


def list_abnormal_orders(
    session: Session,
    *,
    page: int | None,
    page_size: int | None,
    shop_id: int | None = None,
    platform_code: str | None = None,
    abnormal_type: str | None = None,
    keyword: str | None = None,
    allowed_shop_ids: list[int] | None = None,
) -> tuple[list[dict], int]:
    """异常订单池（自动识别并集中展示地址/金额/超时/同步异常，FR-03-07）。"""
    now = now_utc()
    mismatch_ids = _amount_mismatch_ids(session)
    type_conditions = {
        "SYNC": Order.is_abnormal == 1,
        "ADDRESS": _address_condition(),
        "AMOUNT": Order.id.in_(list(mismatch_ids) or [-1]),
        "TIMEOUT": _timeout_condition(now),
    }
    if abnormal_type:
        condition = type_conditions.get(abnormal_type)
        if condition is None:
            raise param_error(f"不支持的异常类型：{abnormal_type}")
    else:
        condition = or_(*type_conditions.values())

    conditions = [Order.is_deleted == 0, condition]
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
        select(Order).where(*conditions).order_by(Order.order_time.desc(), Order.id.desc()).offset(offset).limit(s)
    ).all()
    shop_names, platform_names = _name_maps(session, rows)
    items = []
    for r in rows:
        data = _order_dict(r, shop_names.get(r.shop_id), platform_names.get(r.platform_code))
        types = _abnormal_types_of(r, mismatch_ids, now)
        data["abnormal_types"] = types
        data["abnormal_type_names"] = [ABNORMAL_TYPES.get(t, t) for t in types]
        items.append(data)
    return items, int(total)


def record_shipment_change(session: Session, order: Order, shipment, operator: str | None) -> None:
    """发货单生成后写订单变更留痕（供 shipment_service 调用）。"""
    _add_change(
        session,
        order,
        change_type=ORDER_CHANGE_TYPE["SHIP"],
        field_name="shipment_no",
        before_value=None,
        after_value=f"{shipment.shipment_no} / {shipment.waybill_no}",
        operator=operator,
    )
