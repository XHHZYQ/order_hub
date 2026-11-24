"""订单状态机（M3，见《概要设计》6.3）。

职责：只做"合法流转"判定，不碰数据库、不产生副作用；副作用（写日志/变更、
释放库存、置时间戳）由 order_service 在通过校验后统一处理。
"""

from __future__ import annotations

from app.core.constants import ORDER_STATUS, ORDER_STATUS_FLOW
from app.core.exceptions import status_not_allowed


def can_transition(from_status: str, to_status: str) -> bool:
    """判断是否允许从 from_status 流转到 to_status。"""
    return to_status in ORDER_STATUS_FLOW.get(from_status, set())


def next_statuses(from_status: str) -> list[dict]:
    """当前状态下允许流转的下一状态列表（用于前端下拉）。"""
    codes = ORDER_STATUS_FLOW.get(from_status, set())
    return [
        {"status": code, "status_name": ORDER_STATUS.get(code, code)}
        for code in ORDER_STATUS
        if code in codes
    ]


def assert_transition(from_status: str, to_status: str) -> None:
    """非法流转直接拒绝（状态码：3002）。"""
    if from_status == to_status:
        raise status_not_allowed("目标状态与当前状态相同")
    if not can_transition(from_status, to_status):
        raise status_not_allowed(
            f"非法状态流转：{ORDER_STATUS.get(from_status, from_status)} → "
            f"{ORDER_STATUS.get(to_status, to_status)}"
        )


def resolve_ship_status(items) -> str:
    """按明细发货数量判定：全部发完 → SHIPPED，否则 PART_SHIPPED。

    items 为 OrderItem 序列（含 quantity / shipped_quantity）。
    """
    total = 0
    shipped = 0
    for row in items:
        total += row.quantity or 0
        shipped += row.shipped_quantity or 0
    return "SHIPPED" if total and shipped >= total else "PART_SHIPPED"
