"""v1 路由汇总。"""

from fastapi import APIRouter

from app.api.v1 import auth, operation_logs, orders, platforms, roles, shops, sync, users

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
