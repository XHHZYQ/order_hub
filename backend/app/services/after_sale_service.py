"""M7 售后管理服务：售后汇聚、处理、退款同步、超时预警、原因分析、退货入库回补库存。"""

from __future__ import annotations

import random
from datetime import timedelta
from decimal import Decimal

from sqlalchemy import func as sa_func
from sqlalchemy import or_
from sqlmodel import Session, func, select

from app.core.constants import (
    AFTER_SALE_STATUS,
    AFTER_SALE_TYPE,
    ORDER_STATUS,
    REFUND_STATUS,
)
from app.core.exceptions import BusinessException, not_found, param_error, status_not_allowed
from app.models.after_sale import AfterSale, AfterSaleLog
from app.models.order import Order, OrderItem
from app.models.platform import Platform, Shop
from app.services import inventory_service, order_service
from app.services.user_service import record_operation
from app.utils.datetime_util import format_datetime, now_utc, parse_datetime
from app.utils.id_generator import gen_after_sale_no
from app.utils.pagination import normalize

_AS_TIME_FIELDS = ("apply_time", "handle_deadline", "finish_time", "created_at", "updated_at")

# 售后处理超时阈值（小时）
HANDLE_DEADLINE_HOURS = 72

# 模拟售后的原因与类型池
_REASON_POOL = [
    "七天无理由退货",
    "不想要了",
    "尺码不合适",
    "商品破损/有瑕疵",
    "发错货/漏发",
    "质量问题",
    "与描述不符",
    "物流太慢",
]
# 平台原始状态（模拟）
_PLATFORM_STATUS = {
    "PENDING": "买家申请售后，待商家处理",
    "PROCESSING": "商家处理中",
    "WAIT_BUYER": "等待买家确认",
    "WAIT_SELLER": "等待商家处理",
    "FINISHED": "售后已完成",
    "CLOSED": "售后已关闭",
}
# 处理动作 → 目标状态
_HANDLE_STATUS = {
    "同意": "PROCESSING",
    "拒绝": "CLOSED",
    "协商": "WAIT_BUYER",
    "退货入库": "FINISHED",
}


def _op(operator) -> str:
    return getattr(operator, "username", None) or "系统"


def _fmt(data: dict, fields: tuple[str, ...]) -> dict:
    for field in fields:
        if field in data:
            data[field] = format_datetime(data.get(field))
    return data


def _add_log(
    session: Session, after_sale: AfterSale, action: str, content: str | None, operator: str | None
) -> None:
    session.add(
        AfterSaleLog(
            after_sale_id=after_sale.id,
            after_sale_no=after_sale.after_sale_no,
            action=action,
            content=content,
            operator=operator,
        )
    )


def _as_dict(after_sale: AfterSale, shop_name: str | None, platform_name: str | None, order: Order | None) -> dict:
    data = _fmt(after_sale.model_dump(), _AS_TIME_FIELDS)
    data["type_name"] = AFTER_SALE_TYPE.get(after_sale.type, after_sale.type)
    data["status_name"] = AFTER_SALE_STATUS.get(after_sale.status, after_sale.status)
    data["refund_status_name"] = REFUND_STATUS.get(after_sale.refund_status, after_sale.refund_status)
    data["shop_name"] = shop_name
    data["platform_name"] = platform_name
    data["order_status"] = order.status if order else None
    data["order_status_name"] = ORDER_STATUS.get(order.status, order.status) if order else None
    return data


def _names(session: Session, rows: list[AfterSale]) -> tuple[dict[int, str], dict[str, str], dict[int, Order]]:
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
    order_map = {
        o.id: o
        for o in session.exec(
            select(Order).where(Order.id.in_({r.order_id for r in rows if r.order_id} or [-1]))
        ).all()
    }
    return shop_names, platform_names, order_map


# --------------------------------------------------------------------------- #
# 查询 / 详情
# --------------------------------------------------------------------------- #
def list_after_sales(
    session: Session,
    *,
    page: int | None,
    page_size: int | None,
    shop_id: int | None = None,
    platform_code: str | None = None,
    status: str | None = None,
    type: str | None = None,
    refund_status: str | None = None,
    keyword: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    allowed_shop_ids: list[int] | None = None,
) -> tuple[list[dict], int]:
    """售后单列表（FR-07-01）。"""
    conditions = []
    if shop_id:
        conditions.append(AfterSale.shop_id == shop_id)
    if platform_code:
        conditions.append(AfterSale.platform_code == platform_code)
    if status:
        conditions.append(AfterSale.status == status)
    if type:
        conditions.append(AfterSale.type == type)
    if refund_status:
        conditions.append(AfterSale.refund_status == refund_status)
    if keyword:
        like = f"%{keyword}%"
        conditions.append(
            or_(
                AfterSale.after_sale_no.like(like),
                AfterSale.platform_after_sale_no.like(like),
                AfterSale.order_no.like(like),
                AfterSale.buyer_account.like(like),
            )
        )
    st = parse_datetime(start_time)
    et = parse_datetime(end_time)
    if st:
        conditions.append(AfterSale.apply_time >= st)
    if et:
        conditions.append(AfterSale.apply_time <= et)
    if allowed_shop_ids is not None:
        conditions.append(AfterSale.shop_id.in_(allowed_shop_ids or [-1]))

    p, s, offset = normalize(page, page_size)
    total = session.exec(select(func.count()).select_from(AfterSale).where(*conditions)).one()
    rows = session.exec(
        select(AfterSale)
        .where(*conditions)
        .order_by(AfterSale.apply_time.desc(), AfterSale.id.desc())
        .offset(offset)
        .limit(s)
    ).all()
    shop_names, platform_names, order_map = _names(session, rows)
    items = [
        _as_dict(r, shop_names.get(r.shop_id), platform_names.get(r.platform_code), order_map.get(r.order_id))
        for r in rows
    ]
    return items, int(total)


def get_after_sale(session: Session, after_sale_id: int) -> dict:
    """售后单详情（含订单摘要与处理记录）。"""
    after_sale = session.get(AfterSale, after_sale_id)
    if not after_sale:
        raise not_found("售后单不存在")
    order = session.get(Order, after_sale.order_id) if after_sale.order_id else None
    shop = session.get(Shop, after_sale.shop_id)
    platform = session.exec(select(Platform).where(Platform.platform_code == after_sale.platform_code)).first()
    data = _as_dict(
        after_sale, shop.shop_name if shop else None, platform.platform_name if platform else None, order
    )
    data["order_pay_amount"] = float(order.pay_amount) if order else None
    data["logs"] = list_logs(session, after_sale_id)
    return data


def list_logs(session: Session, after_sale_id: int) -> list[dict]:
    rows = session.exec(
        select(AfterSaleLog)
        .where(AfterSaleLog.after_sale_id == after_sale_id)
        .order_by(AfterSaleLog.created_at.desc(), AfterSaleLog.id.desc())
    ).all()
    result = []
    for row in rows:
        data = _fmt(row.model_dump(), ("created_at",))
        result.append(data)
    return result


def list_by_order(session: Session, order_id: int) -> list[dict]:
    """按订单查售后单（FR-07-04 订单详情回溯）。"""
    rows = session.exec(
        select(AfterSale).where(AfterSale.order_id == order_id).order_by(AfterSale.apply_time.desc())
    ).all()
    shop_names, platform_names, order_map = _names(session, rows)
    return [
        _as_dict(r, shop_names.get(r.shop_id), platform_names.get(r.platform_code), order_map.get(r.order_id))
        for r in rows
    ]


# --------------------------------------------------------------------------- #
# 同步（模拟从平台汇聚售后申请）
# --------------------------------------------------------------------------- #
def sync_after_sales(session: Session, payload, operator=None) -> dict:
    """手动同步售后申请：从已发货/已完成订单中模拟产生售后单（幂等汇聚，FR-07-01）。"""
    op = _op(operator)
    conditions = [Order.is_deleted == 0, Order.status.in_(["SHIPPED", "FINISHED", "AFTER_SALE"])]
    if payload.shop_id:
        conditions.append(Order.shop_id == payload.shop_id)
    orders = session.exec(select(Order).where(*conditions).order_by(Order.order_time.desc()).limit(80)).all()

    existing = {
        (r.platform_code, r.shop_id, r.platform_after_sale_no)
        for r in session.exec(select(AfterSale)).all()
    }
    rng = random.Random()
    created = 0
    for order in orders:
        if created >= 8:
            break
        if rng.random() > 0.45:
            continue
        platform_no = f"AS{order.platform_order_no[-10:]}{rng.randint(100, 999)}"[:32]
        key = (order.platform_code, order.shop_id, platform_no)
        if key in existing:
            continue
        as_type = rng.choices(
            ["REFUND", "RETURN_REFUND", "EXCHANGE"], weights=[40, 50, 10], k=1
        )[0]
        status = rng.choices(
            ["PENDING", "PROCESSING", "WAIT_BUYER", "FINISHED", "CLOSED"],
            weights=[30, 25, 10, 25, 10],
            k=1,
        )[0]
        refund = Decimal("0")
        refund_status = "NONE"
        apply_time = order.order_time + timedelta(hours=rng.randint(20, 120))
        finish_time = None
        if as_type in ("REFUND", "RETURN_REFUND"):
            refund = (order.pay_amount or Decimal("0")).quantize(Decimal("0.01"))
            if status == "FINISHED":
                refund_status = "SUCCESS"
                finish_time = apply_time + timedelta(hours=rng.randint(6, 60))
            elif status in ("PENDING", "PROCESSING", "WAIT_BUYER"):
                refund_status = "PENDING"
        if as_type == "EXCHANGE" and status == "FINISHED":
            finish_time = apply_time + timedelta(hours=rng.randint(12, 72))

        row = AfterSale(
            after_sale_no=gen_after_sale_no(),
            platform_code=order.platform_code,
            shop_id=order.shop_id,
            platform_after_sale_no=platform_no,
            order_id=order.id,
            order_no=order.order_no,
            buyer_account=order.buyer_account,
            type=as_type,
            reason=rng.choice(_REASON_POOL),
            status=status,
            platform_status=_PLATFORM_STATUS.get(status),
            refund_amount=refund,
            refund_status=refund_status,
            goods_returned=1 if (as_type == "RETURN_REFUND" and status == "FINISHED") else 0,
            apply_time=apply_time,
            handle_deadline=apply_time + timedelta(hours=HANDLE_DEADLINE_HOURS),
            finish_time=finish_time,
            operator=op,
        )
        session.add(row)
        session.flush()
        _add_log(session, row, "同步", f"从平台同步售后申请：{_PLATFORM_STATUS.get(status)}", "系统")
        if status == "FINISHED" and as_type == "RETURN_REFUND":
            _restock(session, row, order, operator)
        _sync_order_status(session, order, row, op)
        existing.add(key)
        created += 1

    record_operation(session, operator, "AFTER_SALE", "同步", "售后单", None, f"同步新增售后单 {created} 单")
    session.commit()
    return {"created": created}


def _sync_order_status(session: Session, order: Order, after_sale: AfterSale, operator: str) -> None:
    """订单状态联动：待发货/已发货 → 售后中（状态机校验后执行）。"""
    from app.services import order_state_machine

    if order.status in ("PENDING_SHIP", "SHIPPED") and order_state_machine.can_transition(order.status, "AFTER_SALE"):
        order_service._apply_status(
            session, order, "AFTER_SALE", operator=operator, source="售后",
            remark=f"售后单 {after_sale.after_sale_no}（{AFTER_SALE_TYPE.get(after_sale.type)}）",
        )


def _restock(session: Session, after_sale: AfterSale, order: Order | None, operator) -> None:
    """退货入库：回补库存并写流水（仅对已匹配本地 SKU 的明细）。"""
    if order is None:
        return
    items = session.exec(select(OrderItem).where(OrderItem.order_id == order.id)).all()
    for row in items:
        qty = (row.refund_quantity or 0) or (row.quantity or 0)
        if row.sku_id and qty > 0:
            inventory_service.return_in(
                session,
                sku_id=row.sku_id,
                qty=qty,
                source_no=order.order_no,
                remark=f"售后退货入库：{after_sale.after_sale_no}",
                operator=operator,
            )


# --------------------------------------------------------------------------- #
# 处理 / 退款同步
# --------------------------------------------------------------------------- #
def handle_after_sale(session: Session, after_sale_id: int, payload, operator=None) -> dict:
    """售后处理：同意/拒绝/协商/备注/退货入库（FR-07-02）。"""
    op = _op(operator)
    after_sale = session.get(AfterSale, after_sale_id)
    if not after_sale:
        raise not_found("售后单不存在")
    if after_sale.status in ("FINISHED", "CLOSED"):
        raise status_not_allowed("该售后单已结束，无法继续处理")
    action = (payload.action or "").strip()
    if action not in {"同意", "拒绝", "协商", "备注", "退货入库"}:
        raise param_error("不支持的处理动作")

    if action == "备注":
        _add_log(session, after_sale, "备注", payload.content or "添加备注", op)
        session.commit()
        return get_after_sale(session, after_sale_id)

    target = _HANDLE_STATUS[action]
    before = after_sale.status
    after_sale.status = target
    after_sale.operator = op
    if payload.refund_amount is not None:
        after_sale.refund_amount = payload.refund_amount

    order = session.get(Order, after_sale.order_id) if after_sale.order_id else None
    if action == "同意":
        if after_sale.type in ("REFUND", "RETURN_REFUND") and after_sale.refund_status == "NONE":
            after_sale.refund_status = "PENDING"
    elif action == "拒绝":
        after_sale.refund_status = "NONE"
    elif action == "退货入库":
        after_sale.goods_returned = 1
        after_sale.finish_time = now_utc()
        after_sale.refund_status = "SUCCESS" if after_sale.refund_status != "NONE" else "NONE"
        _restock(session, after_sale, order, operator)
    session.add(after_sale)
    _add_log(
        session, after_sale,
        action,
        f"{AFTER_SALE_STATUS.get(before, before)} → {AFTER_SALE_STATUS.get(target, target)}"
        + (f"：{payload.content}" if payload.content else ""),
        op,
    )
    record_operation(
        session, operator, "AFTER_SALE", action, "售后单", after_sale_id,
        f"{after_sale.after_sale_no} 处理动作：{action}",
    )
    session.commit()
    return get_after_sale(session, after_sale_id)


def sync_refund(session: Session, after_sale_id: int, payload, operator=None) -> dict:
    """同步退款金额与状态（FR-07-03）。"""
    op = _op(operator)
    after_sale = session.get(AfterSale, after_sale_id)
    if not after_sale:
        raise not_found("售后单不存在")
    if payload.refund_amount is not None:
        after_sale.refund_amount = payload.refund_amount
    target = payload.refund_status
    if target:
        if target not in REFUND_STATUS:
            raise param_error("退款状态不合法")
        after_sale.refund_status = target
        if target == "SUCCESS":
            after_sale.status = "FINISHED"
            after_sale.finish_time = after_sale.finish_time or now_utc()
        elif target == "FAILED":
            after_sale.status = "PROCESSING"
    if not target and payload.refund_amount is None:
        raise param_error("未提供退款金额或退款状态")
    after_sale.operator = op
    session.add(after_sale)
    _add_log(
        session, after_sale, "退款",
        f"退款金额 {after_sale.refund_amount}，状态 {REFUND_STATUS.get(after_sale.refund_status)}"
        + (f"；{payload.remark}" if payload.remark else ""),
        op,
    )
    record_operation(
        session, operator, "AFTER_SALE", "退款同步", "售后单", after_sale_id,
        f"{after_sale.after_sale_no} 退款同步",
    )
    session.commit()
    return get_after_sale(session, after_sale_id)


# --------------------------------------------------------------------------- #
# 超时预警 / 原因分析
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
    """售后超时预警：处理中的售后单超过处理时限（FR-07-06）。"""
    now = now_utc()
    conditions = [
        AfterSale.status.in_(["PENDING", "PROCESSING", "WAIT_BUYER", "WAIT_SELLER"]),
        AfterSale.handle_deadline < now,
    ]
    if shop_id:
        conditions.append(AfterSale.shop_id == shop_id)
    if keyword:
        like = f"%{keyword}%"
        conditions.append(
            or_(AfterSale.after_sale_no.like(like), AfterSale.order_no.like(like), AfterSale.buyer_account.like(like))
        )
    if allowed_shop_ids is not None:
        conditions.append(AfterSale.shop_id.in_(allowed_shop_ids or [-1]))

    rows = session.exec(select(AfterSale).where(*conditions).order_by(AfterSale.apply_time.asc())).all()
    shop_names, platform_names, order_map = _names(session, rows)
    p, s, offset = normalize(page, page_size)
    total = len(rows)
    items = []
    for r in rows[offset : offset + s]:
        data = _as_dict(r, shop_names.get(r.shop_id), platform_names.get(r.platform_code), order_map.get(r.order_id))
        deadline = r.handle_deadline
        data["overdue_hours"] = int((now - deadline).total_seconds() // 3600) if deadline else None
        data["alert_reason"] = "售后处理超时（超过处理时限未完成）"
        items.append(data)
    return items, total


def analysis(session: Session, *, shop_id: int | None = None, allowed_shop_ids: list[int] | None = None) -> dict:
    """售后原因分析（FR-07-05）：按类型/原因/店铺维度汇总。"""
    conditions = []
    if shop_id:
        conditions.append(AfterSale.shop_id == shop_id)
    if allowed_shop_ids is not None:
        conditions.append(AfterSale.shop_id.in_(allowed_shop_ids or [-1]))

    total = session.exec(select(func.count()).select_from(AfterSale).where(*conditions)).one()
    refund_sum = session.exec(
        select(sa_func.coalesce(sa_func.sum(AfterSale.refund_amount), 0)).where(*conditions)
    ).one()

    type_rows = session.exec(
        select(
            AfterSale.type, func.count(), sa_func.coalesce(sa_func.sum(AfterSale.refund_amount), 0)
        )
        .where(*conditions)
        .group_by(AfterSale.type)
    ).all()
    by_type = [
        {
            "type": t,
            "type_name": AFTER_SALE_TYPE.get(t, t),
            "count": int(c),
            "amount": float(a or 0),
        }
        for t, c, a in type_rows
    ]

    reason_rows = session.exec(
        select(AfterSale.reason, func.count()).where(*conditions).group_by(AfterSale.reason).order_by(func.count().desc())
    ).all()
    by_reason = [{"reason": r or "未填写", "count": int(c)} for r, c in reason_rows]

    shop_rows = session.exec(
        select(AfterSale.shop_id, func.count(), sa_func.coalesce(sa_func.sum(AfterSale.refund_amount), 0))
        .where(*conditions)
        .group_by(AfterSale.shop_id)
        .order_by(func.count().desc())
    ).all()
    shop_names = {
        sid: name
        for sid, name in session.exec(
            select(Shop.id, Shop.shop_name).where(Shop.id.in_({sid for sid, _, _ in shop_rows} or [-1]))
        ).all()
    }
    by_shop = [
        {
            "shop_id": sid,
            "shop_name": shop_names.get(sid, str(sid)),
            "count": int(c),
            "amount": float(a or 0),
        }
        for sid, c, a in shop_rows
    ]

    return {
        "total": int(total),
        "refund_amount": float(refund_sum or 0),
        "by_type": by_type,
        "by_reason": by_reason,
        "by_shop": by_shop,
    }
