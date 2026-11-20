"""统一响应体封装（见《接口设计》2.3）。"""

from typing import Any

from sqlmodel import SQLModel

from app.core.constants import BizCode
from app.utils.datetime_util import format_datetime


def to_jsonable(obj: Any) -> Any:
    """把 ORM 对象 / datetime / Decimal 递归转换为可 JSON 化的结构。

    - SQLModel 对象 -> dict
    - datetime -> "YYYY-MM-DD HH:mm:ss"（按应用时区）
    - Decimal -> float（接口以数值传输）
    """
    from datetime import date, datetime
    from decimal import Decimal

    if obj is None:
        return None
    if isinstance(obj, SQLModel):
        return to_jsonable(obj.model_dump())
    if isinstance(obj, dict):
        return {k: to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [to_jsonable(v) for v in obj]
    if isinstance(obj, datetime):
        return format_datetime(obj)
    if isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    return obj


def build_response(code: int = BizCode.SUCCESS, message: str = "success", data: Any = None) -> dict:
    return {"code": code, "message": message, "data": to_jsonable(data)}


def success(data: Any = None, message: str = "success") -> dict:
    return build_response(code=BizCode.SUCCESS, message=message, data=data)


def page_data(items: list, total: int, page: int, page_size: int) -> dict:
    """分页响应 data。"""
    return {"list": to_jsonable(items), "total": total, "page": page, "page_size": page_size}


def success_page(items: list, total: int, page: int, page_size: int) -> dict:
    return success(page_data(items, total, page, page_size))
