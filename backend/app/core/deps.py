"""FastAPI 依赖：数据库 Session、当前用户、功能权限、数据权限（店铺范围）。"""

from collections.abc import Generator

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from app.core.database import get_session
from app.core.exceptions import forbidden, unauthorized
from app.core.security import decode_token
from app.models.system import User
from app.services import auth_service

bearer_scheme = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    """数据库 Session 依赖。"""
    yield from get_session()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: Session = Depends(get_db),
) -> User:
    """解析 Bearer Token 并加载当前用户；失败抛 1002。"""
    if credentials is None or not credentials.credentials:
        raise unauthorized("未携带登录凭证")
    payload = decode_token(credentials.credentials)
    if not payload or not payload.get("sub"):
        raise unauthorized("登录凭证无效或已过期")
    user = session.get(User, int(payload["sub"]))
    if not user or user.is_deleted == 1:
        raise unauthorized("用户不存在")
    if user.status != 1:
        raise forbidden("账号已停用，请联系管理员")
    return user


def require_permission(code: str):
    """功能权限校验依赖：`user = Depends(require_permission("order:audit"))`。"""

    def _checker(
        user: User = Depends(get_current_user),
        session: Session = Depends(get_db),
    ) -> User:
        if auth_service.is_super_admin(session, user.id):
            return user
        if code not in auth_service.get_permission_codes(session, user.id):
            raise forbidden(f"缺少功能权限：{code}")
        return user

    return _checker


def get_allowed_shop_ids(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> list[int] | None:
    """数据权限：返回可访问店铺 ID 集合；超级管理员返回 None（表示不限）。"""
    if auth_service.is_super_admin(session, user.id):
        return None
    return auth_service.get_accessible_shop_ids(session, user.id)


def get_client_ip(request: Request) -> str | None:
    """获取客户端 IP（兼容反向代理）。"""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else None
