"""导入全部模型，确保 SQLModel.metadata 完整（建表 / 初始化脚本依赖）。"""

from app.models.order import Order, OrderChange, OrderExt, OrderItem, OrderLog
from app.models.platform import Platform, Shop, SyncLog, SyncTask
from app.models.system import (
    OperationLog,
    Permission,
    Role,
    RolePermission,
    RoleShop,
    User,
    UserRole,
)

__all__ = [
    "Platform",
    "Shop",
    "SyncLog",
    "SyncTask",
    "Order",
    "OrderItem",
    "OrderExt",
    "OrderLog",
    "OrderChange",
    "OperationLog",
    "Permission",
    "Role",
    "RolePermission",
    "RoleShop",
    "User",
    "UserRole",
]
