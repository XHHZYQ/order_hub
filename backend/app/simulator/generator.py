"""订单数据生成器：按平台"原始字段名"生成可复现的模拟订单。

关键约束（对应《概要设计》6.2 模拟平台适配器 / 6.6 定时同步与幂等）：
- 使用由 (平台编码 + 店铺 ID + 时间窗口) 推导的固定随机种子，
  同一店铺、同一时间窗口重复生成，结果完全一致 —— 这是"重复同步不产生重复订单"演示的前提。
- 返回的字典使用各平台的"原始字段名"（见 app/simulator/seed.ORDER_FIELD_MAP），
  以便适配器做真实的字段映射与状态归一化。
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta

from app.core.constants import ORDER_STATUS_MAP
from app.simulator import seed
from app.utils.datetime_util import DATETIME_FORMAT, to_local

# 约 8% 的订单标记为异常
ANOMALY_RATE = 0.08
# 异常原因文案
ANOMALY_ADDRESS = "收货地址缺失"
ANOMALY_AMOUNT = "金额校验不一致：商品金额与明细合计不符"


def _seed_of(platform_code: str, shop_id: int, start: datetime, end: datetime) -> str:
    """由平台、店铺与时间窗口推导固定随机种子。"""
    return f"{platform_code}|{shop_id}|{start.isoformat()}|{end.isoformat()}"


def _fmt(dt: datetime | None) -> str:
    return dt.strftime(DATETIME_FORMAT) if dt else ""


def _platform_order_no(rng: random.Random, platform_code: str, dt: datetime) -> str:
    """生成各平台形态的原始订单号。"""
    if platform_code == "TAOBAO":
        return str(rng.randint(10**14, 10**15 - 1))
    if platform_code == "JD":
        return str(rng.randint(10**9, 10**10 - 1))
    if platform_code == "PDD":
        return f"{dt:%y%m%d}-{rng.randint(10**11, 10**12 - 1)}"
    if platform_code == "DOUYIN":
        return str(rng.randint(10**17, 10**18 - 1))
    return f"SN{rng.randint(10**11, 10**12 - 1)}"


def _pick_unified_status(rng: random.Random) -> str:
    keys = list(seed.STATUS_WEIGHTS)
    weights = [seed.STATUS_WEIGHTS[k] for k in keys]
    return rng.choices(keys, weights=weights, k=1)[0]


def _build_items(rng: random.Random, platform_code: str, shop_code: str) -> tuple[list[dict], float, float]:
    """生成明细列表，返回 (原始明细列表, 商品金额合计, 明细优惠合计)。

    platform_sku_id 采用确定性编码 platform_sku_code(店铺, SPU, 规格序号)，
    与种子数据中的平台规格/SKU 映射口径一致，使同步时能命中映射。
    """
    item_fm = seed.ITEM_FIELD_MAP[platform_code]
    items: list[dict] = []
    goods_total = 0.0
    discount_total = 0.0
    for _ in range(rng.randint(1, 3)):
        detail = seed.random_product_detail(rng)
        name, spec, price = detail["name"], detail["spec"], detail["price"]
        qty = rng.randint(1, 3)
        total = round(price * qty, 2)
        discount = round(total * rng.choice([0, 0, 0, 0, 0.05, 0.1]), 2)
        pay = round(total - discount, 2)
        items.append(
            {
                item_fm["platform_sku_id"]: seed.platform_sku_code(shop_code, detail["spu"], detail["spec_index"]),
                item_fm["platform_sku_name"]: f"{name} {spec}",
                item_fm["outer_sku_code"]: detail["sku_code"],
                item_fm["product_name"]: name,
                item_fm["spec_desc"]: spec,
                item_fm["price"]: f"{price:.2f}",
                item_fm["quantity"]: qty,
                item_fm["total_amount"]: f"{total:.2f}",
                item_fm["discount_amount"]: f"{discount:.2f}",
                item_fm["pay_amount"]: f"{pay:.2f}",
            }
        )
        goods_total += total
        discount_total += discount
    return items, round(goods_total, 2), round(discount_total, 2)


def generate_orders(platform_code: str, shop, start: datetime, end: datetime) -> list[dict]:
    """生成某店铺在 [start, end] 时间窗口内的订单原始数据列表。

    每店每天生成 4~12 单；约 8% 的订单带 anomaly 标记。
    """
    rng = random.Random(_seed_of(platform_code, shop.id, start, end))

    field_map = seed.ORDER_FIELD_MAP.get(platform_code)
    if not field_map:
        return []

    status_map = ORDER_STATUS_MAP.get(platform_code, {})
    raw_by_unified = {v: k for k, v in status_map.items()}
    if not raw_by_unified:
        return []

    # 时间窗口（按应用时区的本地墙钟时间生成，模拟平台返回北京时间字符串）
    local_start = to_local(start).replace(tzinfo=None)
    local_end = to_local(end).replace(tzinfo=None)
    if local_end <= local_start:
        return []

    results: list[dict] = []
    day = local_start.date()
    last_day = local_end.date()
    while day <= last_day:
        for _ in range(rng.randint(4, 12)):
            hour, minute, second = rng.randint(0, 23), rng.randint(0, 59), rng.randint(0, 59)
            order_dt = datetime(day.year, day.month, day.day, hour, minute, second)
            if order_dt < local_start:
                order_dt = local_start + timedelta(seconds=rng.randint(0, 3600))
            if order_dt > local_end:
                order_dt = local_end - timedelta(seconds=rng.randint(0, 3600))

            results.append(
                _build_one(
                    rng, platform_code, shop, field_map, raw_by_unified, order_dt, local_end
                )
            )
        day += timedelta(days=1)
    return results


def _build_one(
    rng: random.Random,
    platform_code: str,
    shop,
    field_map: dict[str, str],
    raw_by_unified: dict[str, str],
    order_dt: datetime,
    local_end: datetime,
) -> dict:
    """构造单条订单原始数据。"""
    account, nick = seed.random_buyer(rng, platform_code)
    receiver = seed.random_receiver(rng)
    items, goods_total, item_discount = _build_items(rng, platform_code, shop.shop_code)

    freight = rng.choice([0.0, 0.0, 0.0, 8.0, 12.0, 15.0])
    discount = item_discount
    pay = round(goods_total - discount + freight, 2)

    unified_status = _pick_unified_status(rng)
    raw_status = raw_by_unified.get(unified_status, next(iter(raw_by_unified.values())))

    # 付款 / 发货时间
    paid_at = None
    if unified_status != "PENDING_PAY":
        paid_at = min(order_dt + timedelta(minutes=rng.randint(1, 180)), local_end)
    shipped_at = None
    if unified_status in ("PART_SHIPPED", "SHIPPED", "FINISHED", "AFTER_SALE"):
        base = paid_at or order_dt
        shipped_at = min(base + timedelta(hours=rng.randint(6, 72)), local_end)

    buyer_remark = rng.choice(["", "", "", "尽快发货，谢谢！", "需要发票", "不要放快递柜", "周末送达"])

    # 异常订单（约 8%）
    anomaly: str | None = None
    address_missing = False
    if rng.random() < ANOMALY_RATE:
        if rng.random() < 0.5:
            anomaly = ANOMALY_ADDRESS
            address_missing = True
        else:
            anomaly = ANOMALY_AMOUNT

    pno = _platform_order_no(rng, platform_code, order_dt)

    raw: dict = {
        field_map["platform_order_no"]: pno,
        field_map["buyer_account"]: account,
        field_map["goods_amount"]: f"{goods_total:.2f}",
        field_map["discount_amount"]: f"{discount:.2f}",
        field_map["freight_amount"]: f"{freight:.2f}",
        field_map["pay_amount"]: f"{pay:.2f}",
        field_map["platform_status"]: raw_status,
        field_map["order_time"]: _fmt(order_dt),
        field_map["paid_at"]: _fmt(paid_at),
        field_map["shipped_at"]: _fmt(shipped_at),
        field_map["buyer_remark"]: buyer_remark,
    }
    if field_map["buyer_nick"] != field_map["buyer_account"]:
        raw[field_map["buyer_nick"]] = nick

    if address_missing:
        for key in ("receiver_name", "receiver_phone", "receiver_province", "receiver_city", "receiver_district", "receiver_address"):
            raw[field_map[key]] = ""
    else:
        raw[field_map["receiver_name"]] = receiver["name"]
        raw[field_map["receiver_phone"]] = receiver["phone"]
        raw[field_map["receiver_province"]] = receiver["province"]
        raw[field_map["receiver_city"]] = receiver["city"]
        raw[field_map["receiver_district"]] = receiver["district"]
        raw[field_map["receiver_address"]] = receiver["detail"]

    # 金额校验不一致：让商品金额与明细合计对不上
    if anomaly == ANOMALY_AMOUNT:
        delta = round(goods_total * rng.choice([0.1, 0.15, -0.1, -0.12]), 2)
        raw[field_map["goods_amount"]] = f"{goods_total + delta:.2f}"

    # 平台扩展字段（含平台原始状态）
    for raw_key in seed.EXT_FIELD_MAP[platform_code]:
        if raw_key == field_map["platform_status"]:
            raw[raw_key] = raw_status
        elif raw_key == "seller_nick":
            raw[raw_key] = shop.shop_name
        elif raw_key in ("venderId", "mall_id", "shop_id"):
            raw[raw_key] = str(shop.id)
        elif raw_key in seed.EXT_VALUE_POOL:
            value = rng.choice(seed.EXT_VALUE_POOL[raw_key])
            if value:
                raw[raw_key] = value
        elif raw_key in ("buyer_message", "buyerMessage", "buyer_remark"):
            raw[raw_key] = buyer_remark

    raw[seed.ITEM_LIST_KEY[platform_code]] = items
    raw["anomaly"] = anomaly
    return raw
