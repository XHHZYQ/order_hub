"""单号生成：本地订单号、发货单号、售后单号等（全局唯一）。"""

import random
from datetime import datetime, timezone

_counter: dict[str, int] = {}


def _now_prefix() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


def generate_no(prefix: str, length: int = 4) -> str:
    """生成形如 OH202611201200000001 的单号。

    prefix 为大写前缀，时间到秒，后接自增序号，避免同一秒内重复。
    """
    key = f"{prefix}{_now_prefix()}"
    seq = _counter.get(key, 0) + 1
    _counter[key] = seq
    rand = random.randint(0, 999)
    return f"{key}{seq:0{length}d}{rand:03d}"


def gen_order_no() -> str:
    """本地订单号。"""
    return generate_no("OH")


def gen_shipment_no() -> str:
    """发货单号。"""
    return generate_no("SH")


def gen_after_sale_no() -> str:
    """售后单号。"""
    return generate_no("AS")


def gen_bill_no() -> str:
    """账单批次号。"""
    return generate_no("BL")
