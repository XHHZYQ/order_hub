"""认证服务：登录、当前用户信息、权限与店铺范围计算。"""

from sqlmodel import Session, select

from app.core.exceptions import forbidden, unauthorized
from app.core.security import create_access_token, verify_password
from app.models.system import Permission, Role, RolePermission, RoleShop, User, UserRole
from app.utils.datetime_util import now_utc


def authenticate(session: Session, username: str, password: str) -> User:
    """校验账号密码，返回用户；失败抛业务异常。"""
    user = session.exec(select(User).where(User.username == username)).first()
    if not user or user.is_deleted == 1:
        raise unauthorized("账号或密码错误")
    if not verify_password(password, user.password):
        raise unauthorized("账号或密码错误")
    if user.status != 1:
        raise forbidden("账号已停用，请联系管理员")
    return user


def login(session: Session, username: str, password: str) -> dict:
    """登录，返回 token 与用户信息。"""
    user = authenticate(session, username, password)
    user.last_login_time = now_utc()
    session.add(user)
    session.commit()
    session.refresh(user)
    token = create_access_token(user.id, extra={"username": user.username})
    return {"token": token, "token_type": "Bearer", "expires_in": None, "user": build_user_profile(session, user)}


def get_roles(session: Session, user_id: int) -> list[Role]:
    return list(
        session.exec(
            select(Role)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id, Role.status == 1)
        ).all()
    )


def get_role_codes(session: Session, user_id: int) -> list[str]:
    return [r.role_code for r in get_roles(session, user_id)]


def get_permission_codes(session: Session, user_id: int) -> list[str]:
    """当前用户的功能权限码集合（多角色并集）。"""
    codes = session.exec(
        select(Permission.perm_code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(UserRole, UserRole.role_id == RolePermission.role_id)
        .join(Role, Role.id == UserRole.role_id)
        .where(UserRole.user_id == user_id, Role.status == 1)
    ).all()
    return sorted(set(codes))


def get_accessible_shop_ids(session: Session, user_id: int) -> list[int]:
    """当前用户可访问的店铺 ID 集合（多角色店铺范围并集）。"""
    shop_ids = session.exec(
        select(RoleShop.shop_id)
        .join(UserRole, UserRole.role_id == RoleShop.role_id)
        .join(Role, Role.id == UserRole.role_id)
        .where(UserRole.user_id == user_id, Role.status == 1)
    ).all()
    return sorted(set(shop_ids))


def is_super_admin(session: Session, user_id: int) -> bool:
    return "SUPER_ADMIN" in get_role_codes(session, user_id)


def build_user_profile(session: Session, user: User) -> dict:
    """组装 /auth/me 所需信息：用户 + 角色 + 功能权限码 + 店铺范围。"""
    roles = get_roles(session, user.id)
    return {
        "id": user.id,
        "username": user.username,
        "real_name": user.real_name,
        "phone": user.phone,
        "email": user.email,
        "status": user.status,
        "last_login_time": user.last_login_time,
        "roles": [{"id": r.id, "role_code": r.role_code, "role_name": r.role_name} for r in roles],
        "role_codes": [r.role_code for r in roles],
        "permissions": get_permission_codes(session, user.id),
        "shop_ids": get_accessible_shop_ids(session, user.id),
    }
