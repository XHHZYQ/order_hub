"""M8 财务对账服务：账单导入、订单匹配、差异处理、结算汇总、毛利核算、报表导出。

对账口径（与《概要设计》6.7 一致）：
- 匹配依据：平台 + 平台订单号；
- 金额比对基准：成交金额 = 商品金额 + 运费；
- 差异类型：本地无单 / 账单无单 / 金额不一致；
- 毛利口径：毛利 = 实收（账单结算金额） − 成本（订单明细数量 × SKU 成本价）。
"""

from __future__ import annotations

import io
import csv
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import delete, or_
from sqlalchemy import func as sa_func
from sqlmodel import Session, func, select

from app.adapters import finance as finance_adapter
from app.core.constants import (
    BILL_MATCH_STATUS,
    BILL_RECONCILE_STATUS,
    DIFF_HANDLE_STATUS,
    RECONCILE_DIFF_TYPE,
    BizCode,
)
from app.core.exceptions import BusinessException, not_found, param_error
from app.models.finance import Bill, BillDetail, ReconcileDiff
from app.models.order import Order, OrderItem
from app.models.platform import Platform, Shop
from app.models.product import Sku
from app.services.user_service import record_operation
from app.utils.datetime_util import APP_TZ, format_datetime, now_utc, parse_datetime
from app.utils.id_generator import gen_bill_no
from app.utils.pagination import normalize

_BILL_TIME_FIELDS = ("import_time", "created_at")
_DETAIL_TIME_FIELDS = ("trade_time", "created_at")
_DIFF_TIME_FIELDS = ("handle_time", "created_at")


def _op(operator) -> str:
    return getattr(operator, "username", None) or "系统"


def _d(value) -> Decimal:
    if value is None:
        return Decimal("0")
    return value if isinstance(value, Decimal) else Decimal(str(value))


def _f(value) -> float:
    return float(_d(value))


def _fmt(data: dict, fields: tuple[str, ...]) -> dict:
    for field in fields:
        if field in data:
            data[field] = format_datetime(data.get(field))
    return data


def _period_range(bill_period: str) -> tuple[datetime, datetime] | None:
    """账期（YYYY-MM）→ [起, 止) 的 UTC 时间区间。"""
    try:
        year, month = int(bill_period[:4]), int(bill_period[5:7])
    except (TypeError, ValueError):
        return None
    start = datetime(year, month, 1, tzinfo=APP_TZ).astimezone(timezone.utc)
    if month == 12:
        end = datetime(year + 1, 1, 1, tzinfo=APP_TZ).astimezone(timezone.utc)
    else:
        end = datetime(year, month + 1, 1, tzinfo=APP_TZ).astimezone(timezone.utc)
    return start, end


def _names(session: Session, shop_ids: set[int], platform_codes: set[str]) -> tuple[dict[int, str], dict[str, str]]:
    shop_names = {
        sid: name
        for sid, name in session.exec(
            select(Shop.id, Shop.shop_name).where(Shop.id.in_(shop_ids or {-1}))
        ).all()
    }
    platform_names = {
        code: name
        for code, name in session.exec(
            select(Platform.platform_code, Platform.platform_name).where(
                Platform.platform_code.in_(platform_codes or {""})
            )
        ).all()
    }
    return shop_names, platform_names


def _bill_dict(bill: Bill, shop_name: str | None, platform_name: str | None) -> dict:
    data = _fmt(bill.model_dump(), _BILL_TIME_FIELDS)
    data["platform_name"] = platform_name
    data["shop_name"] = shop_name
    data["reconcile_status_name"] = BILL_RECONCILE_STATUS.get(bill.reconcile_status, bill.reconcile_status)
    return data


# --------------------------------------------------------------------------- #
# 导入 / 列表 / 详情
# --------------------------------------------------------------------------- #
def import_bill(
    session: Session,
    *,
    platform_code: str,
    shop_id: int,
    bill_period: str,
    file_name: str | None = None,
    content: bytes | None = None,
    auto_generate: bool = False,
    operator=None,
) -> dict:
    """导入平台账单文件（FR-08-01）；auto_generate=True 时按本地订单生成模拟账单。"""
    op = _op(operator)
    if not platform_code or not shop_id or not bill_period:
        raise param_error("平台、店铺、账期均为必填")

    if auto_generate or content is None:
        period = _period_range(bill_period)
        conditions = [
            Order.is_deleted == 0,
            Order.shop_id == shop_id,
            Order.platform_code == platform_code,
        ]
        if period:
            conditions.append(Order.order_time >= period[0])
            conditions.append(Order.order_time < period[1])
        orders = session.exec(select(Order).where(*conditions).order_by(Order.order_time.asc())).all()
        if not orders:
            raise param_error("该店铺在所选账期内无可用于生成账单的订单")
        order_dicts = [
            {
                "platform_order_no": o.platform_order_no,
                "trade_time": o.order_time,
                "goods_amount": o.goods_amount,
                "freight_amount": o.freight_amount,
                "pay_amount": o.pay_amount,
            }
            for o in orders
        ]
        import random as _random

        rng = _random.Random(f"bill|{platform_code}|{shop_id}|{bill_period}")
        rows = finance_adapter.build_bill_rows(
            platform_code=platform_code, orders=order_dicts, rng=rng, bill_period=bill_period
        )
        file_name = file_name or f"账单_{platform_code}_{bill_period}.csv"
    else:
        try:
            rows = finance_adapter.parse_bill_content(file_name or "", content)
        except ValueError as exc:
            raise BusinessException(BizCode.FILE_PARSE_ERROR, f"账单文件解析失败：{exc}")

    if not rows:
        raise BusinessException(BizCode.FILE_PARSE_ERROR, "账单文件无有效明细")

    total_amount = sum((_d(r.get("settled_amount")) for r in rows), Decimal("0"))
    bill = Bill(
        bill_no=gen_bill_no(),
        platform_code=platform_code,
        shop_id=shop_id,
        bill_period=bill_period,
        file_name=file_name,
        total_count=len(rows),
        total_amount=total_amount,
        reconcile_status="PENDING",
        import_time=now_utc(),
        operator=op,
    )
    session.add(bill)
    session.flush()

    for row in rows:
        session.add(
            BillDetail(
                bill_id=bill.id,
                platform_code=platform_code,
                shop_id=shop_id,
                platform_order_no=str(row.get("platform_order_no")),
                trade_time=row.get("trade_time"),
                goods_amount=_d(row.get("goods_amount")),
                freight_amount=_d(row.get("freight_amount")),
                commission_amount=_d(row.get("commission_amount")),
                subsidy_amount=_d(row.get("subsidy_amount")),
                refund_amount=_d(row.get("refund_amount")),
                settled_amount=_d(row.get("settled_amount")),
                match_status="UNMATCHED",
            )
        )

    record_operation(
        session, operator, "FINANCE", "账单导入", "账单", bill.id,
        f"{bill.bill_no} 导入明细 {len(rows)} 条，金额 {total_amount}",
    )
    session.commit()
    return get_bill(session, bill.id)


def mock_bill_file(
    session: Session, *, platform_code: str, shop_id: int, bill_period: str, file_type: str = "csv"
) -> tuple[bytes, str]:
    """生成模拟账单文件（供演示下载后重新导入）。"""
    period = _period_range(bill_period)
    conditions = [Order.is_deleted == 0, Order.shop_id == shop_id, Order.platform_code == platform_code]
    if period:
        conditions.append(Order.order_time >= period[0])
        conditions.append(Order.order_time < period[1])
    orders = session.exec(select(Order).where(*conditions).order_by(Order.order_time.asc())).all()
    if not orders:
        raise param_error("该店铺在所选账期内无订单，无法生成账单文件")
    order_dicts = [
        {
            "platform_order_no": o.platform_order_no,
            "trade_time": o.order_time,
            "goods_amount": o.goods_amount,
            "freight_amount": o.freight_amount,
            "pay_amount": o.pay_amount,
        }
        for o in orders
    ]
    import random as _random

    rng = _random.Random(f"billfile|{platform_code}|{shop_id}|{bill_period}")
    rows = finance_adapter.build_bill_rows(
        platform_code=platform_code, orders=order_dicts, rng=rng, bill_period=bill_period
    )
    if file_type == "xlsx":
        return finance_adapter.rows_to_xlsx_bytes(rows), f"账单_{platform_code}_{bill_period}.xlsx"
    return finance_adapter.rows_to_csv_bytes(rows), f"账单_{platform_code}_{bill_period}.csv"


def list_bills(
    session: Session,
    *,
    page: int | None,
    page_size: int | None,
    shop_id: int | None = None,
    platform_code: str | None = None,
    reconcile_status: str | None = None,
    bill_period: str | None = None,
    keyword: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    allowed_shop_ids: list[int] | None = None,
) -> tuple[list[dict], int]:
    """账单批次列表（FR-08-01）。"""
    conditions = []
    if shop_id:
        conditions.append(Bill.shop_id == shop_id)
    if platform_code:
        conditions.append(Bill.platform_code == platform_code)
    if reconcile_status:
        conditions.append(Bill.reconcile_status == reconcile_status)
    if bill_period:
        conditions.append(Bill.bill_period == bill_period)
    if keyword:
        like = f"%{keyword}%"
        conditions.append(or_(Bill.bill_no.like(like), Bill.file_name.like(like)))
    st = parse_datetime(start_time)
    et = parse_datetime(end_time)
    if st:
        conditions.append(Bill.import_time >= st)
    if et:
        conditions.append(Bill.import_time <= et)
    if allowed_shop_ids is not None:
        conditions.append(Bill.shop_id.in_(allowed_shop_ids or [-1]))

    p, s, offset = normalize(page, page_size)
    total = session.exec(select(func.count()).select_from(Bill).where(*conditions)).one()
    rows = session.exec(
        select(Bill).where(*conditions).order_by(Bill.import_time.desc(), Bill.id.desc()).offset(offset).limit(s)
    ).all()
    shop_names, platform_names = _names(
        session, {r.shop_id for r in rows}, {r.platform_code for r in rows}
    )
    items = [_bill_dict(r, shop_names.get(r.shop_id), platform_names.get(r.platform_code)) for r in rows]
    return items, int(total)


def get_bill(session: Session, bill_id: int) -> dict:
    """账单批次详情（含明细条数与差异条数统计）。"""
    bill = session.get(Bill, bill_id)
    if not bill:
        raise not_found("账单批次不存在")
    shop = session.get(Shop, bill.shop_id)
    platform = session.exec(select(Platform).where(Platform.platform_code == bill.platform_code)).first()
    data = _bill_dict(bill, shop.shop_name if shop else None, platform.platform_name if platform else None)
    data["diff_count"] = int(
        session.exec(select(func.count()).select_from(ReconcileDiff).where(ReconcileDiff.bill_id == bill_id)).one()
    )
    data["pending_diff_count"] = int(
        session.exec(
            select(func.count())
            .select_from(ReconcileDiff)
            .where(ReconcileDiff.bill_id == bill_id, ReconcileDiff.handle_status == "PENDING")
        ).one()
    )
    return data


def list_bill_details(
    session: Session,
    bill_id: int,
    *,
    page: int | None,
    page_size: int | None,
    match_status: str | None = None,
    keyword: str | None = None,
) -> tuple[list[dict], int]:
    """账单明细列表（FR-08-01）。"""
    conditions = [BillDetail.bill_id == bill_id]
    if match_status:
        conditions.append(BillDetail.match_status == match_status)
    if keyword:
        like = f"%{keyword}%"
        conditions.append(or_(BillDetail.platform_order_no.like(like)))

    p, s, offset = normalize(page, page_size)
    total = session.exec(select(func.count()).select_from(BillDetail).where(*conditions)).one()
    rows = session.exec(
        select(BillDetail).where(*conditions).order_by(BillDetail.id.asc()).offset(offset).limit(s)
    ).all()
    order_ids = {r.order_id for r in rows if r.order_id}
    order_nos = {
        oid: ono
        for oid, ono in session.exec(select(Order.id, Order.order_no).where(Order.id.in_(order_ids or {-1}))).all()
    }
    items = []
    for r in rows:
        data = _fmt(r.model_dump(), _DETAIL_TIME_FIELDS)
        data["match_status_name"] = BILL_MATCH_STATUS.get(r.match_status, r.match_status)
        data["order_no"] = order_nos.get(r.order_id)
        items.append(data)
    return items, int(total)


# --------------------------------------------------------------------------- #
# 匹配
# --------------------------------------------------------------------------- #
def match_bill(session: Session, bill_id: int, operator=None) -> dict:
    """账单与订单自动匹配（FR-08-02），生成三类差异（FR-08-03）。"""
    bill = session.get(Bill, bill_id)
    if not bill:
        raise not_found("账单批次不存在")
    if bill.reconcile_status == "CLOSED":
        raise BusinessException(BizCode.BILL_CLOSED, "对账期已封账，不可重新对账")

    op = _op(operator)
    bill.reconcile_status = "MATCHING"
    details = list(session.exec(select(BillDetail).where(BillDetail.bill_id == bill_id)).all())

    order_nos = [d.platform_order_no for d in details]
    orders = session.exec(
        select(Order).where(
            Order.platform_code == bill.platform_code,
            Order.shop_id == bill.shop_id,
            Order.is_deleted == 0,
            Order.platform_order_no.in_(order_nos or ["__none__"]),
        )
    ).all()
    order_map = {o.platform_order_no: o for o in orders}

    # 重新对账需清理旧的差异记录，保证幂等
    session.exec(delete(ReconcileDiff).where(ReconcileDiff.bill_id == bill_id))

    matched = amount_diff = unmatched = 0
    for detail in details:
        order = order_map.get(detail.platform_order_no)
        bill_amount = _d(detail.goods_amount) + _d(detail.freight_amount)
        if not order:
            detail.match_status = "UNMATCHED"
            detail.order_id = None
            unmatched += 1
            _add_diff(
                session, bill, detail, diff_type="LOCAL_MISSING", order_no=None,
                local_amount=Decimal("0"), bill_amount=bill_amount,
            )
        else:
            detail.order_id = order.id
            local_amount = _d(order.goods_amount) + _d(order.freight_amount)
            if _d(local_amount) == _d(bill_amount):
                detail.match_status = "MATCHED"
                matched += 1
            else:
                detail.match_status = "AMOUNT_DIFF"
                amount_diff += 1
                _add_diff(
                    session, bill, detail, diff_type="AMOUNT_DIFF", order_no=order.order_no,
                    local_amount=local_amount, bill_amount=bill_amount,
                )
        session.add(detail)

    # 账单无单：账期内本地有单、账单中缺失
    bill_nos = {d.platform_order_no for d in details}
    period = _period_range(bill.bill_period)
    local_conditions = [
        Order.platform_code == bill.platform_code,
        Order.shop_id == bill.shop_id,
        Order.is_deleted == 0,
    ]
    if period:
        local_conditions.append(Order.order_time >= period[0])
        local_conditions.append(Order.order_time < period[1])
    local_orders = session.exec(select(Order).where(*local_conditions)).all()
    bill_missing = 0
    for order in local_orders:
        if order.platform_order_no in bill_nos:
            continue
        bill_missing += 1
        local_amount = _d(order.goods_amount) + _d(order.freight_amount)
        _add_diff(
            session, bill, None, diff_type="BILL_MISSING", order_no=order.order_no,
            local_amount=local_amount, bill_amount=Decimal("0"), platform_order_no=order.platform_order_no,
        )

    bill.reconcile_status = "RECONCILED"
    session.add(bill)
    diff_count = matched_diffs = amount_diff + unmatched + bill_missing
    record_operation(
        session, operator, "FINANCE", "账单匹配", "账单", bill_id,
        f"{bill.bill_no} 匹配完成：已匹配 {matched}，金额不一致 {amount_diff}，本地无单 {unmatched}，账单无单 {bill_missing}",
    )
    session.commit()
    return {
        "bill_id": bill_id,
        "matched": matched,
        "amount_diff": amount_diff,
        "unmatched": unmatched,
        "bill_missing": bill_missing,
        "diff_count": matched_diffs,
    }


def _add_diff(
    session: Session,
    bill: Bill,
    detail: BillDetail | None,
    *,
    diff_type: str,
    order_no: str | None,
    local_amount: Decimal,
    bill_amount: Decimal,
    platform_order_no: str | None = None,
) -> None:
    session.add(
        ReconcileDiff(
            bill_id=bill.id,
            bill_detail_id=detail.id if detail else None,
            platform_code=bill.platform_code,
            shop_id=bill.shop_id,
            platform_order_no=platform_order_no or (detail.platform_order_no if detail else ""),
            order_no=order_no,
            diff_type=diff_type,
            local_amount=local_amount,
            bill_amount=bill_amount,
            diff_amount=_d(bill_amount) - _d(local_amount),
            handle_status="PENDING",
        )
    )


def close_bill(session: Session, bill_id: int, operator=None) -> dict:
    """对账期封账：封账后历史数据不可再被同步/重新对账覆盖。"""
    bill = session.get(Bill, bill_id)
    if not bill:
        raise not_found("账单批次不存在")
    if bill.reconcile_status == "CLOSED":
        raise BusinessException(BizCode.BILL_CLOSED, "该对账期已封账")
    bill.reconcile_status = "CLOSED"
    session.add(bill)
    record_operation(session, operator, "FINANCE", "封账", "账单", bill_id, f"{bill.bill_no} 已封账")
    session.commit()
    return get_bill(session, bill_id)


# --------------------------------------------------------------------------- #
# 差异处理
# --------------------------------------------------------------------------- #
def list_differences(
    session: Session,
    *,
    page: int | None,
    page_size: int | None,
    bill_id: int | None = None,
    diff_type: str | None = None,
    handle_status: str | None = None,
    shop_id: int | None = None,
    platform_code: str | None = None,
    keyword: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    allowed_shop_ids: list[int] | None = None,
) -> tuple[list[dict], int]:
    """对账差异列表（FR-08-03）。"""
    conditions = []
    if bill_id:
        conditions.append(ReconcileDiff.bill_id == bill_id)
    if diff_type:
        conditions.append(ReconcileDiff.diff_type == diff_type)
    if handle_status:
        conditions.append(ReconcileDiff.handle_status == handle_status)
    if shop_id:
        conditions.append(ReconcileDiff.shop_id == shop_id)
    if platform_code:
        conditions.append(ReconcileDiff.platform_code == platform_code)
    if keyword:
        like = f"%{keyword}%"
        conditions.append(
            or_(
                ReconcileDiff.platform_order_no.like(like),
                ReconcileDiff.order_no.like(like),
                ReconcileDiff.handle_remark.like(like),
            )
        )
    st = parse_datetime(start_time)
    et = parse_datetime(end_time)
    if st:
        conditions.append(ReconcileDiff.created_at >= st)
    if et:
        conditions.append(ReconcileDiff.created_at <= et)
    if allowed_shop_ids is not None:
        conditions.append(ReconcileDiff.shop_id.in_(allowed_shop_ids or [-1]))

    p, s, offset = normalize(page, page_size)
    total = session.exec(select(func.count()).select_from(ReconcileDiff).where(*conditions)).one()
    rows = session.exec(
        select(ReconcileDiff)
        .where(*conditions)
        .order_by(ReconcileDiff.id.desc())
        .offset(offset)
        .limit(s)
    ).all()
    shop_names, platform_names = _names(
        session, {r.shop_id for r in rows}, {r.platform_code for r in rows}
    )
    bill_nos = {
        bid: bno
        for bid, bno in session.exec(
            select(Bill.id, Bill.bill_no).where(Bill.id.in_({r.bill_id for r in rows} or {-1}))
        ).all()
    }
    items = []
    for r in rows:
        data = _fmt(r.model_dump(), _DIFF_TIME_FIELDS)
        data["diff_type_name"] = RECONCILE_DIFF_TYPE.get(r.diff_type, r.diff_type)
        data["handle_status_name"] = DIFF_HANDLE_STATUS.get(r.handle_status, r.handle_status)
        data["bill_no"] = bill_nos.get(r.bill_id)
        data["shop_name"] = shop_names.get(r.shop_id)
        data["platform_name"] = platform_names.get(r.platform_code)
        items.append(data)
    return items, int(total)


def handle_difference(session: Session, diff_id: int, payload, operator=None) -> dict:
    """人工确认并标记差异已处理（FR-08-03），处理结果可追溯。"""
    op = _op(operator)
    diff = session.get(ReconcileDiff, diff_id)
    if not diff:
        raise not_found("对账差异不存在")
    bill = session.get(Bill, diff.bill_id)
    if bill and bill.reconcile_status == "CLOSED":
        raise BusinessException(BizCode.BILL_CLOSED, "对账期已封账，不可处理差异")
    if diff.handle_status == "HANDLED":
        raise BusinessException(BizCode.STATUS_NOT_ALLOWED, "该差异已处理，无需重复处理")
    action = (getattr(payload, "action", None) or "确认").strip()
    diff.handle_status = "HANDLED"
    diff.operator = op
    diff.handle_time = now_utc()
    diff.handle_remark = (getattr(payload, "handle_remark", None) or action)[:255]
    session.add(diff)
    record_operation(
        session, operator, "FINANCE", "差异处理", "对账差异", diff_id,
        f"{diff.platform_order_no}（{RECONCILE_DIFF_TYPE.get(diff.diff_type)}）处理：{diff.handle_remark}",
    )
    session.commit()
    return {"id": diff_id, "handle_status": diff.handle_status, "handle_remark": diff.handle_remark}


# --------------------------------------------------------------------------- #
# 结算汇总
# --------------------------------------------------------------------------- #
def settlement_summary(
    session: Session,
    *,
    start_time: str | None = None,
    end_time: str | None = None,
    platform_code: str | None = None,
    shop_id: int | None = None,
    group_by: str = "platform",
    allowed_shop_ids: list[int] | None = None,
) -> dict:
    """结算汇总（FR-08-04）：按平台/店铺汇总应收、平台费用、实收金额。"""
    conditions = _detail_conditions(
        start_time=start_time, end_time=end_time, platform_code=platform_code,
        shop_id=shop_id, allowed_shop_ids=allowed_shop_ids,
    )
    receivable = _sum_expr(BillDetail.goods_amount) + _sum_expr(BillDetail.freight_amount)
    totals = session.exec(
        select(
            receivable,
            _sum_expr(BillDetail.commission_amount),
            _sum_expr(BillDetail.subsidy_amount),
            _sum_expr(BillDetail.refund_amount),
            _sum_expr(BillDetail.settled_amount),
            func.count(),
        ).where(*conditions)
    ).one()

    key_col = BillDetail.shop_id if group_by == "shop" else BillDetail.platform_code
    group_rows = session.exec(
        select(
            key_col,
            receivable,
            _sum_expr(BillDetail.commission_amount),
            _sum_expr(BillDetail.subsidy_amount),
            _sum_expr(BillDetail.refund_amount),
            _sum_expr(BillDetail.settled_amount),
            func.count(),
        )
        .where(*conditions)
        .group_by(key_col)
    ).all()

    rows = []
    for key, recv, fee, subsidy, refund, settled, count in group_rows:
        name = key
        if group_by == "shop":
            shop = session.get(Shop, key)
            name = shop.shop_name if shop else str(key)
        else:
            platform = session.exec(select(Platform).where(Platform.platform_code == key)).first()
            name = platform.platform_name if platform else key
        rows.append(
            {
                "key": key,
                "name": name,
                "receivable": _f(recv),
                "platform_fee": _f(fee),
                "subsidy": _f(subsidy),
                "refund": _f(refund),
                "settled": _f(settled),
                "order_count": int(count),
            }
        )
    rows.sort(key=lambda r: r["settled"], reverse=True)

    return {
        "receivable": _f(totals[0]),
        "platform_fee": _f(totals[1]),
        "subsidy": _f(totals[2]),
        "refund": _f(totals[3]),
        "settled": _f(totals[4]),
        "order_count": int(totals[5]),
        "rows": rows,
    }


# --------------------------------------------------------------------------- #
# 毛利核算
# --------------------------------------------------------------------------- #
def profit_summary(
    session: Session,
    *,
    start_time: str | None = None,
    end_time: str | None = None,
    platform_code: str | None = None,
    shop_id: int | None = None,
    limit: int = 100,
    allowed_shop_ids: list[int] | None = None,
) -> dict:
    """毛利核算（FR-08-05）：毛利 = 实收 − 成本，按订单与商品两个维度。"""
    conditions = _detail_conditions(
        start_time=start_time, end_time=end_time, platform_code=platform_code,
        shop_id=shop_id, allowed_shop_ids=allowed_shop_ids,
    )
    conditions.append(BillDetail.order_id.is_not(None))
    details = session.exec(select(BillDetail).where(*conditions)).all()
    order_ids = {d.order_id for d in details}
    orders = {
        o.id: o
        for o in session.exec(select(Order).where(Order.id.in_(order_ids or {-1}))).all()
    }
    items = session.exec(select(OrderItem).where(OrderItem.order_id.in_(order_ids or {-1}))).all()
    sku_ids = {i.sku_id for i in items if i.sku_id}
    skus = {s.id: s for s in session.exec(select(Sku).where(Sku.id.in_(sku_ids or {-1}))).all()}
    # 未映射（sku_id 为空）的明细回退按 sku_code 取成本价，避免成本被漏算
    codes = {i.sku_code for i in items if not i.sku_id and i.sku_code}
    sku_by_code = {
        s.sku_code: s for s in session.exec(select(Sku).where(Sku.sku_code.in_(codes or {""}))).all()
    }

    def _sku_of(item: OrderItem) -> Sku | None:
        return skus.get(item.sku_id) or sku_by_code.get(item.sku_code)

    # 订单 → (成本, 明细销售小计)
    order_cost: dict[int, Decimal] = {}
    order_item_pay: dict[int, Decimal] = {}
    product_agg: dict[int, dict] = {}
    for item in items:
        sku = _sku_of(item)
        cost = _d(sku.cost_price) if sku else Decimal("0")
        line_cost = cost * (item.quantity or 0)
        order_cost[item.order_id] = order_cost.get(item.order_id, Decimal("0")) + line_cost
        order_item_pay[item.order_id] = order_item_pay.get(item.order_id, Decimal("0")) + _d(item.pay_amount)

        if sku:
            entry = product_agg.setdefault(
                sku.id,
                {"sku_id": sku.id, "sku_code": sku.sku_code, "product_name": sku.sku_name,
                 "quantity": 0, "cost": Decimal("0"), "sale": Decimal("0")},
            )
            entry["quantity"] += item.quantity or 0
            entry["cost"] += line_cost
            entry["sale"] += _d(item.pay_amount)

    by_order = []
    total_settled = total_cost = Decimal("0")
    for detail in details:
        order = orders.get(detail.order_id)
        if not order:
            continue
        settled = _d(detail.settled_amount)
        cost = order_cost.get(detail.order_id, Decimal("0"))
        profit = settled - cost
        total_settled += settled
        total_cost += cost
        # 商品维度：按明细销售小占比分摊实收
        item_pay = order_item_pay.get(detail.order_id, Decimal("0"))
        ratio = (settled / item_pay) if item_pay > 0 else Decimal("0")
        for item in [i for i in items if i.order_id == detail.order_id]:
            sku = _sku_of(item)
            if not sku:
                continue
            entry = product_agg[sku.id]
            entry.setdefault("settled", Decimal("0"))
            entry["settled"] += _d(item.pay_amount) * ratio
        by_order.append(
            {
                "order_id": detail.order_id,
                "order_no": order.order_no,
                "platform_order_no": detail.platform_order_no,
                "buyer_account": order.buyer_account,
                "settled": _f(settled),
                "cost": _f(cost),
                "profit": _f(profit),
                "profit_rate": round(_f(profit) / _f(settled), 4) if _f(settled) else 0.0,
                "trade_time": format_datetime(detail.trade_time or order.order_time),
            }
        )

    by_order.sort(key=lambda r: r["profit"], reverse=True)
    by_product = []
    for entry in product_agg.values():
        settled = entry.get("settled", Decimal("0"))
        profit = settled - entry["cost"]
        by_product.append(
            {
                "sku_id": entry["sku_id"],
                "sku_code": entry["sku_code"],
                "product_name": entry["product_name"],
                "quantity": entry["quantity"],
                "settled": _f(settled),
                "cost": _f(entry["cost"]),
                "profit": _f(profit),
                "profit_rate": round(_f(profit) / _f(settled), 4) if _f(settled) else 0.0,
            }
        )
    by_product.sort(key=lambda r: r["profit"], reverse=True)

    total_profit = total_settled - total_cost
    return {
        "settled": _f(total_settled),
        "cost": _f(total_cost),
        "profit": _f(total_profit),
        "profit_rate": round(_f(total_profit) / _f(total_settled), 4) if _f(total_settled) else 0.0,
        "order_count": len(by_order),
        "by_order": by_order[: max(1, limit)],
        "by_product": by_product[: max(1, limit)],
    }


# --------------------------------------------------------------------------- #
# 报表导出
# --------------------------------------------------------------------------- #
def export_reconciliation(
    session: Session,
    *,
    export_type: str = "detail",
    start_time: str | None = None,
    end_time: str | None = None,
    platform_code: str | None = None,
    shop_id: int | None = None,
    bill_id: int | None = None,
    allowed_shop_ids: list[int] | None = None,
) -> tuple[bytes, str]:
    """导出对账结果明细/差异/结算汇总（FR-08-06），返回 (文件字节, 文件名)。"""
    buffer = io.StringIO()
    writer = csv.writer(buffer)

    if export_type == "difference":
        items, _ = list_differences(
            session, page=1, page_size=1000, bill_id=bill_id, shop_id=shop_id,
            platform_code=platform_code, start_time=start_time, end_time=end_time,
            allowed_shop_ids=allowed_shop_ids,
        )
        writer.writerow(["账单批次号", "平台", "店铺", "平台订单号", "本地订单号", "差异类型", "本地金额", "账单金额", "差异金额", "处理状态", "处理说明"])
        for r in items:
            writer.writerow([
                r.get("bill_no"), r.get("platform_name"), r.get("shop_name"), r.get("platform_order_no"),
                r.get("order_no"), r.get("diff_type_name"), r.get("local_amount"), r.get("bill_amount"),
                r.get("diff_amount"), r.get("handle_status_name"), r.get("handle_remark"),
            ])
        filename = "对账差异明细.csv"
    elif export_type == "settlement":
        summary = settlement_summary(
            session, start_time=start_time, end_time=end_time, platform_code=platform_code,
            shop_id=shop_id, group_by="shop", allowed_shop_ids=allowed_shop_ids,
        )
        writer.writerow(["店铺", "应收金额", "平台费用", "平台补贴", "退款金额", "实收金额", "订单数"])
        for r in summary["rows"]:
            writer.writerow([r["name"], r["receivable"], r["platform_fee"], r["subsidy"], r["refund"], r["settled"], r["order_count"]])
        writer.writerow(["合计", summary["receivable"], summary["platform_fee"], summary["subsidy"], summary["refund"], summary["settled"], summary["order_count"]])
        filename = "结算汇总.csv"
    else:
        conditions = _detail_conditions(
            start_time=start_time, end_time=end_time, platform_code=platform_code,
            shop_id=shop_id, allowed_shop_ids=allowed_shop_ids,
        )
        if bill_id:
            conditions.append(BillDetail.bill_id == bill_id)
        rows = session.exec(select(BillDetail).where(*conditions).order_by(BillDetail.id.asc()).limit(5000)).all()
        order_ids = {r.order_id for r in rows if r.order_id}
        order_nos = {
            oid: ono
            for oid, ono in session.exec(select(Order.id, Order.order_no).where(Order.id.in_(order_ids or {-1}))).all()
        }
        writer.writerow(["平台订单号", "本地订单号", "交易时间", "商品金额", "运费", "平台佣金", "平台补贴", "退款", "结算金额", "匹配状态"])
        for r in rows:
            writer.writerow([
                r.platform_order_no, order_nos.get(r.order_id),
                format_datetime(r.trade_time), _f(r.goods_amount), _f(r.freight_amount),
                _f(r.commission_amount), _f(r.subsidy_amount), _f(r.refund_amount),
                _f(r.settled_amount), BILL_MATCH_STATUS.get(r.match_status, r.match_status),
            ])
        filename = "对账明细.csv"

    return ("\ufeff" + buffer.getvalue()).encode("utf-8"), filename


# --------------------------------------------------------------------------- #
# 内部工具
# --------------------------------------------------------------------------- #
def _sum_expr(column):
    return sa_func.coalesce(sa_func.sum(column), 0)


def _detail_conditions(
    *,
    start_time: str | None,
    end_time: str | None,
    platform_code: str | None,
    shop_id: int | None,
    allowed_shop_ids: list[int] | None,
) -> list:
    conditions = []
    if platform_code:
        conditions.append(BillDetail.platform_code == platform_code)
    if shop_id:
        conditions.append(BillDetail.shop_id == shop_id)
    st = parse_datetime(start_time)
    et = parse_datetime(end_time)
    if st:
        conditions.append(BillDetail.trade_time >= st)
    if et:
        conditions.append(BillDetail.trade_time <= et)
    if allowed_shop_ids is not None:
        conditions.append(BillDetail.shop_id.in_(allowed_shop_ids or [-1]))
    return conditions
