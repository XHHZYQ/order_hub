"""模拟平台适配器包：把各平台原始订单归一化为统一订单结构。"""

from app.adapters.factory import get_adapter

__all__ = ["get_adapter"]
