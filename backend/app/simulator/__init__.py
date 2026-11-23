"""模拟平台数据源：商品/买家/地址/物流等基础字典与辅助函数。

本包只在演示/demo 场景使用，用于模拟第三方开放平台返回的订单数据，
不涉及真实网络请求。所有字段名刻意使用各平台的"原始字段名"，
由 app/adapters 下的适配器完成统一映射。
"""

from app.simulator.generator import generate_orders

__all__ = ["generate_orders"]
