"""模拟平台账单适配器：生成账单文件、解析账单文件为统一账单行。

设计说明（与 app/adapters/logistics.py 一致的"模拟外部服务"定位）
------------------------------------------------------------------
- 本模块只做**纯计算与文件编解码**，不访问数据库；查询订单/落库由 services/bill_service.py 负责。
- 账单列口径见《数据库设计》7.4「账单字段映射」。
- 生成账单时会**注入三类差异**（本地无单 / 账单无单 / 金额不一致），便于对账演示。
"""

from __future__ import annotations

import csv
import io
import random
from datetime import datetime
from decimal import Decimal, InvalidOperation

# 统一账单列（中文表头）—— 见《数据库设计》7.4
FIELD_HEADER: dict[str, str] = {
    "platform_order_no": "订单号",
    "trade_time": "交易时间",
    "goods_amount": "商品金额",
    "freight_amount": "运费",
    "commission_amount": "平台佣金",
    "subsidy_amount": "平台补贴",
    "refund_amount": "退款",
    "settled_amount": "结算金额",
}
HEADERS: list[str] = list(FIELD_HEADER.values())
_HEADER_TO_FIELD: dict[str, str] = {v: k for k, v in FIELD_HEADER.items()}

# 金额口径：以「商品金额 + 运费」为成交金额比对基准（见服务层说明）
AMOUNT_FIELDS = ("goods_amount", "freight_amount", "commission_amount", "subsidy_amount", "refund_amount", "settled_amount")

# 各平台佣金率（模拟）
PLATFORM_COMMISSION_RATE: dict[str, float] = {
    "TAOBAO": 0.05,
    "JD": 0.06,
    "PDD": 0.04,
    "DOUYIN": 0.08,
    "SELF": 0.02,
}

_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def _d(value) -> Decimal:
    if value is None or value == "":
        return Decimal("0")
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def _round2(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"))


def _money_text(value) -> str:
    return f"{_d(value):.2f}"


def build_bill_rows(
    *,
    platform_code: str,
    orders: list[dict],
    rng: random.Random,
    bill_period: str,
    diff_ratio: float = 0.10,
    missing_ratio: float = 0.06,
) -> list[dict]:
    """根据本地订单生成模拟账单行（含三类差异）。

    orders：每项含 platform_order_no / trade_time(datetime) / goods_amount / freight_amount / pay_amount。
    返回统一字段的账单行列表（值多为 Decimal）。
    """
    rate = Decimal(str(PLATFORM_COMMISSION_RATE.get(platform_code, 0.05)))
    rows: list[dict] = []

    for order in orders:
        roll = rng.random()
        # 账单无单：本地有单、账单缺失（服务层按周期扫描本地订单即可发现）
        if roll < missing_ratio:
            continue

        goods = _d(order.get("goods_amount"))
        freight = _d(order.get("freight_amount"))
        amount_diff = roll < missing_ratio + diff_ratio
        if amount_diff:
            # 金额不一致：账单商品金额与本地存在小额偏差（如平台优惠口径差异）
            delta = _round2(Decimal(str(rng.uniform(-80, 80))))
            goods = _round2(goods + delta)

        commission = _round2((goods + freight) * rate)
        subsidy = _round2(Decimal(str(rng.choice([0, 0, 5, 10, 20]))))
        refund = Decimal("0")
        settled = _round2(goods + freight - commission + subsidy - refund)

        rows.append(
            {
                "platform_order_no": order.get("platform_order_no"),
                "trade_time": order.get("trade_time"),
                "goods_amount": goods,
                "freight_amount": freight,
                "commission_amount": commission,
                "subsidy_amount": subsidy,
                "refund_amount": refund,
                "settled_amount": settled,
            }
        )

    # 本地无单：账单中含本地不存在的订单号
    for _ in range(rng.randint(1, 3)):
        goods = _round2(Decimal(str(rng.uniform(80, 600))))
        commission = _round2(goods * rate)
        rows.append(
            {
                "platform_order_no": f"EXT{rng.randint(10**9, 10**10 - 1)}",
                "trade_time": rng.choice(orders)["trade_time"] if orders else datetime.now(),
                "goods_amount": goods,
                "freight_amount": Decimal("0"),
                "commission_amount": commission,
                "subsidy_amount": Decimal("0"),
                "refund_amount": Decimal("0"),
                "settled_amount": _round2(goods - commission),
            }
        )

    rows.sort(key=lambda r: (r.get("trade_time") or datetime.now()))
    return rows


def rows_to_csv_bytes(rows: list[dict], *, with_bom: bool = True) -> bytes:
    """账单行 → CSV 字节（默认带 UTF-8 BOM，便于 Excel 直接打开）。"""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(HEADERS)
    for row in rows:
        writer.writerow(
            [
                row.get("platform_order_no", ""),
                _fmt_dt(row.get("trade_time")),
                _money_text(row.get("goods_amount")),
                _money_text(row.get("freight_amount")),
                _money_text(row.get("commission_amount")),
                _money_text(row.get("subsidy_amount")),
                _money_text(row.get("refund_amount")),
                _money_text(row.get("settled_amount")),
            ]
        )
    text = buffer.getvalue()
    return ("\ufeff" + text).encode("utf-8") if with_bom else text.encode("utf-8")


def rows_to_xlsx_bytes(rows: list[dict]) -> bytes:
    """账单行 → XLSX 字节（依赖 openpyxl，按需导入）。"""
    from openpyxl import Workbook  # 延迟导入，未安装时仅 XLSX 不可用

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "平台账单"
    sheet.append(HEADERS)
    for row in rows:
        sheet.append(
            [
                row.get("platform_order_no", ""),
                _fmt_dt(row.get("trade_time")),
                float(_d(row.get("goods_amount"))),
                float(_d(row.get("freight_amount"))),
                float(_d(row.get("commission_amount"))),
                float(_d(row.get("subsidy_amount"))),
                float(_d(row.get("refund_amount"))),
                float(_d(row.get("settled_amount"))),
            ]
        )
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def parse_bill_content(filename: str, content: bytes) -> list[dict]:
    """解析账单文件（CSV / XLSX）为统一账单行列表。

    表头按《数据库设计》7.4 中文字段识别，兼容直接使用英文字段名。
    解析失败抛 ValueError（由服务层转为 3001 文件解析失败）。
    """
    name = (filename or "").lower()
    if name.endswith(".xlsx"):
        raw_rows = _read_xlsx(content)
    elif name.endswith(".csv"):
        raw_rows = _read_csv(content)
    else:
        raise ValueError("仅支持 .csv 或 .xlsx 账单文件")

    if not raw_rows:
        raise ValueError("账单文件为空")

    header = [str(h).strip() for h in raw_rows[0]]
    index_map: dict[str, int] = {}
    for idx, col in enumerate(header):
        field = _HEADER_TO_FIELD.get(col) or (col if col in FIELD_HEADER else None)
        if field:
            index_map[field] = idx
    if "platform_order_no" not in index_map:
        raise ValueError("账单文件缺少「订单号」列")

    rows: list[dict] = []
    for raw in raw_rows[1:]:
        if not raw or not any(str(c).strip() for c in raw):
            continue
        row = {
            "platform_order_no": str(raw[index_map["platform_order_no"]]).strip(),
            "trade_time": _parse_dt(raw[index_map["trade_time"]]) if "trade_time" in index_map else None,
        }
        for field in AMOUNT_FIELDS:
            if field in index_map:
                row[field] = _d(raw[index_map[field]])
        if not row["platform_order_no"]:
            continue
        rows.append(row)
    if not rows:
        raise ValueError("账单文件无有效明细")
    return rows


def _read_csv(content: bytes) -> list[list]:
    text = content.decode("utf-8-sig", errors="replace")
    return [row for row in csv.reader(io.StringIO(text))]


def _read_xlsx(content: bytes) -> list[list]:
    from openpyxl import load_workbook  # 延迟导入

    workbook = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    sheet = workbook.active
    return [list(row) for row in sheet.iter_rows(values_only=True)]


def _parse_dt(value) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    for fmt in (_DATETIME_FORMAT, "%Y-%m-%d", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _fmt_dt(value) -> str:
    if isinstance(value, datetime):
        return value.strftime(_DATETIME_FORMAT)
    return str(value or "")
