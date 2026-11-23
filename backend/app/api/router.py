"""v1 路由汇总。"""

from fastapi import APIRouter

from app.api.v1 import (
    auth,
    inventory,
    operation_logs,
    orders,
    platforms,
    products,
    roles,
    shops,
    sku_mappings,
    sync,
    users,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(roles.router)
api_router.include_router(roles.perm_router)
api_router.include_router(operation_logs.router)
api_router.include_router(platforms.router)
api_router.include_router(shops.router)
api_router.include_router(sync.task_router)
api_router.include_router(sync.log_router)
api_router.include_router(orders.router)
api_router.include_router(products.router)
api_router.include_router(products.sku_router)
api_router.include_router(products.platform_product_router)
api_router.include_router(sku_mappings.router)
api_router.include_router(inventory.router)
