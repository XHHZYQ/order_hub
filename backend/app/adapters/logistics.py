"""模拟物流适配器：生成电子面单号 / 运单号、物流轨迹节点与物流异常。

设计说明（与平台适配器 app/adapters/*.py 一致的"模拟外部服务"定位）
------------------------------------------------------------------
- 采用**确定性随机**：以运单号推导固定随机种子，同一运单多次拉取轨迹结果一致，
  可演示"轨迹重复拉取幂等、不产生重复轨迹"。
- 本模块只做纯生成，不访问数据库；落库由 services/shipment_service.py 负责。
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta

# 物流公司字典（编码, 名称, 运单号前缀）—— 与 seed_minimal.LOGISTICS_COMPANIES 保持一致
LOGISTICS_COMPANIES: list[tuple[str, str, str]] = [
    ("SF", "顺丰速运", "SF"),
    ("YTO", "圆通速递", "YT"),
    ("ZTO", "中通快递", "ZTO"),
    ("STO", "申通快递", "STO"),
    ("YUNDA", "韵达速递", "YD"),
    ("JD", "京东物流", "JD"),
    ("EMS", "邮政EMS", "EA"),
    ("JT", "极兔速递", "JT"),
]

_COMPANY_NAME = {code: name for code, name, _ in LOGISTICS_COMPANIES}
_COMPANY_PREFIX = {code: prefix for code, _, prefix in LOGISTICS_COMPANIES}

# 轨迹节点模板（状态码, 文案模板）；按进度依次生成
_TRACE_TEMPLATES: list[tuple[str, str]] = [
    ("COLLECTED", "【{origin_city}】揽投点已揽收，揽投员：{courier}（{phone}）"),
    ("IN_TRANSIT", "快件已从【{origin_city}】发出，下一站【{dest_city}】转运中心"),
    ("ARRIVED", "快件已到达【{dest_city}】分拨中心"),
    ("DELIVERING", "【{dest_city}】快递员{postman}正在派件，请保持电话畅通"),
    ("SIGNED", "快件已签收，签收人：本人，感谢使用{company}"),
]

_CITY_POOL = ["杭州", "上海", "北京", "广州", "深圳", "成都", "武汉", "西安", "南京", "苏州", "郑州", "长沙"]
_COURIER_POOL = ["王建国", "李强", "张伟", "刘洋", "陈晨", "赵磊"]
_POSTMAN_POOL = ["孙师傅", "周师傅", "吴师傅", "郑师傅"]

# 无更新预警阈值（小时）
STALE_HOURS = 48


def list_companies() -> list[dict]:
    """物流公司下拉选项。"""
    return [{"company_code": code, "company_name": name} for code, name, _ in LOGISTICS_COMPANIES]


def company_name(company_code: str | None) -> str | None:
    return _COMPANY_NAME.get((company_code or "").upper())


def pick_company(rng: random.Random) -> tuple[str, str]:
    """随机挑一个物流公司，返回 (编码, 名称)。"""
    code = rng.choice([c for c, _, _ in LOGISTICS_COMPANIES])
    return code, _COMPANY_NAME[code]


def gen_waybill_no(company_code: str, rng: random.Random) -> str:
    """生成运单号（按物流公司前缀 + 12 位数字）。"""
    prefix = _COMPANY_PREFIX.get((company_code or "").upper(), "OH")
    return f"{prefix}{rng.randint(10**11, 10**12 - 1)}"


def gen_face_sheet_no(rng: random.Random) -> str:
    """生成电子面单号。"""
    return f"FS{rng.randint(10**14, 10**15 - 1)}"


def gen_package_no(rng: random.Random, order_no: str) -> str:
    """生成包裹号。"""
    tail = (order_no or "")[-6:]
    return f"PK{tail}{rng.randint(10**3, 10**4 - 1)}"


def _trace_rng(waybill_no: str) -> random.Random:
    """由运单号推导轨迹随机种子，保证同一运单轨迹可复现。"""
    return random.Random(f"trace|{waybill_no}")


def gen_traces(
    *,
    waybill_no: str | None,
    company_code: str | None,
    dest_city: str | None,
    shipped_at: datetime,
    node_count: int = 5,
    abnormal: bool = False,
) -> list[dict]:
    """生成物流轨迹节点列表（按时间升序）。

    node_count 表示已产生的节点数（1=已揽收，5=已签收），用于演示"在途/已签收"。
    """
    rng = _trace_rng(waybill_no or "unknown")
    # 收件城市取订单收件地；发货（揽件）城市按运单确定且与收件城市不同，
    # 保证「揽件地」与「运输起点」一致，且到达/派件/签收均在收件城市。
    dest_city = dest_city or rng.choice(_CITY_POOL)
    origin_city = rng.choice([c for c in _CITY_POOL if c != dest_city] or _CITY_POOL)
    company = company_name(company_code) or "物流"
    courier = rng.choice(_COURIER_POOL)
    postman = rng.choice(_POSTMAN_POOL)
    phone = f"{rng.randint(3, 9)}{rng.randint(10**8, 10**9 - 1)}"

    count = max(1, min(int(node_count), len(_TRACE_TEMPLATES)))
    traces: list[dict] = []
    cursor = shipped_at
    for idx in range(count):
        status, template = _TRACE_TEMPLATES[idx]
        desc = template.format(
            origin_city=origin_city,
            dest_city=dest_city,
            courier=courier,
            phone=phone,
            postman=postman,
            company=company,
        )
        traces.append({"trace_time": cursor, "trace_desc": desc, "trace_status": status})
        # 每个节点之后都推进 4~14 小时，保证节点时间严格递增
        cursor = cursor + timedelta(hours=rng.randint(4, 14))
    if abnormal:
        traces.append(
            {
                "trace_time": cursor + timedelta(hours=rng.randint(12, 36)),
                "trace_desc": f"快件在【{dest_city}】转运中心滞留，长时间无更新，已登记物流异常",
                "trace_status": "ABNORMAL",
            }
        )
    return traces


def trace_node_count_for_rng(rng: random.Random) -> int:
    """随机决定轨迹进度（用于种子数据：部分在途、部分已签收、部分异常）。"""
    return rng.choices([1, 2, 3, 4, 5], weights=[5, 8, 12, 20, 55], k=1)[0]
