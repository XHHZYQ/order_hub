"""模拟平台适配器基类：拉取原始订单并归一化为统一订单结构。

统一结构（与《数据库设计》4.2 / 《概要设计》6.1 对齐）：
    {
        "platform_order_no", "buyer_account", "buyer_nick",
        "receiver_name", "receiver_phone", "receiver_province",
        "receiver_city", "receiver_district", "receiver_address",
        "goods_amount", "discount_amount", "freight_amount", "pay_amount",
        "platform_status"(原始值), "order_time", "paid_at", "shipped_at",
        "buyer_remark",
        "ext":   [{"ext_key","ext_name","ext_value"}],
        "items": [{... 明细统一字段 ...}],
        "anomaly": str | None,
    }
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation

from app.simulator import seed
from app.simulator.generator import generate_orders
from app.utils.datetime_util import parse_datetime


def _text(value) -> str | None:
    """转成去空白的字符串，空值返回 None。"""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _decimal(value) -> Decimal:
    """转 Decimal，非法值按 0 处理。"""
    if value is None or value == "":
        return Decimal("0")
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def _time(value) -> datetime | None:
    return parse_datetime(value)


class PlatformAdapter:
    """平台适配器抽象基类。子类只需配置 4 张映射表。"""

    platform_code: str = ""
    # {统一字段: 平台原始字段}
    field_map: dict[str, str] = {}
    # {明细统一字段: 平台原始明细字段}
    item_field_map: dict[str, str] = {}
    # {平台原始状态: 统一状态码}
    status_map: dict[str, str] = {}
    # {平台原始字段: 中文名}，用于 order_ext
    ext_fields: dict[str, str] = {}

    def fetch_orders(self, shop, start: datetime, end: datetime) -> list[dict]:
        """拉取并归一化某店铺在 [start, end] 内的订单。"""
        raw_list = generate_orders(self.platform_code, shop, start, end)
        return [self._normalize(raw) for raw in raw_list]

    def _get(self, raw: dict, unified: str):
        return raw.get(self.field_map.get(unified, unified))

    def _normalize(self, raw: dict) -> dict:
        platform_status = _text(self._get(raw, "platform_status"))
        unified_status = self.status_map.get(platform_status or "")

        items = [self._normalize_item(it) for it in (raw.get(seed.ITEM_LIST_KEY[self.platform_code]) or [])]

        ext: list[dict] = []
        for raw_key, cn_name in self.ext_fields.items():
            value = _text(raw.get(raw_key))
            if value is not None:
                ext.append({"ext_key": raw_key, "ext_name": cn_name, "ext_value": value})

        return {
            "platform_order_no": _text(self._get(raw, "platform_order_no")),
            "buyer_account": _text(self._get(raw, "buyer_account")),
            "buyer_nick": _text(self._get(raw, "buyer_nick")),
            "receiver_name": _text(self._get(raw, "receiver_name")),
            "receiver_phone": _text(self._get(raw, "receiver_phone")),
            "receiver_province": _text(self._get(raw, "receiver_province")),
            "receiver_city": _text(self._get(raw, "receiver_city")),
            "receiver_district": _text(self._get(raw, "receiver_district")),
            "receiver_address": _text(self._get(raw, "receiver_address")),
            "goods_amount": _decimal(self._get(raw, "goods_amount")),
            "discount_amount": _decimal(self._get(raw, "discount_amount")),
            "freight_amount": _decimal(self._get(raw, "freight_amount")),
            "pay_amount": _decimal(self._get(raw, "pay_amount")),
            "platform_status": platform_status,
            "status": unified_status,
            "order_time": _time(self._get(raw, "order_time")),
            "paid_at": _time(self._get(raw, "paid_at")),
            "shipped_at": _time(self._get(raw, "shipped_at")),
            "buyer_remark": _text(self._get(raw, "buyer_remark")),
            "ext": ext,
            "items": items,
            "anomaly": raw.get("anomaly"),
        }

    def _normalize_item(self, raw_item: dict) -> dict:
        def g(unified: str):
            return raw_item.get(self.item_field_map.get(unified, unified))

        return {
            "platform_sku_id": _text(g("platform_sku_id")),
            "platform_sku_name": _text(g("platform_sku_name")),
            "outer_sku_code": _text(g("outer_sku_code")),
            "product_name": _text(g("product_name")),
            "spec_desc": _text(g("spec_desc")),
            "price": _decimal(g("price")),
            "quantity": int(_decimal(g("quantity"))) or 1,
            "total_amount": _decimal(g("total_amount")),
            "discount_amount": _decimal(g("discount_amount")),
            "pay_amount": _decimal(g("pay_amount")),
        }
