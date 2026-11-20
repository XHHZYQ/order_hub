"""用户 / 角色 / 权限 / 数据权限 / 操作日志 服务。"""

from sqlmodel import Session, func, select

from app.core.exceptions import duplicate, not_found, param_error
from app.core.security import hash_password
from app.models.system import OperationLog, Permission, Role, RolePermission, RoleShop, User, UserRole
from app.utils.datetime_util import parse_datetime
from app.utils.pagination import normalize


# --------------------------------------------------------------------------- #
# 操作日志
# --------------------------------------------------------------------------- #
def record_operation(
    session: Session,
    operator: User | None,
    module: str,
    action: str,
    target_type: str | None = None,
    target_id: str | int | None = None,
    content: str | None = None,
    ip: str | None = None,
) -> OperationLog:
    """写入一条操作日志（由调用方提交事务）。"""
    log = OperationLog(
        user_id=operator.id if operator else None,
        username=operator.username if operator else None,
        module=module,
        action=action,
        target_type=target_type,
        target_id=str(target_id) if target_id is not None else None,
        content=content,
        ip=ip,
    )
    session.add(log)
    return log


def list_operation_logs(
    session: Session,
    page: int | None = None,
    page_size: int | None = None,
    username: str | None = None,
    module: str | None = None,
    action: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
) -> tuple[list[dict], int]:
    conditions = []
    if username:
        conditions.append(OperationLog.username.contains(username))
    if module:
        conditions.append(OperationLog.module == module)
    if action:
        conditions.append(OperationLog.action == action)
    st = parse_datetime(start_time)
    et = parse_datetime(end_time)
    if st:
        conditions.append(OperationLog.created_at >= st)
    if et:
        conditions.append(OperationLog.created_at <= et)

    p, s, offset = normalize(page, page_size)
    total = session.exec(select(func.count()).select_from(OperationLog).where(*conditions)).one()
    rows = session.exec(
        select(OperationLog).where(*conditions).order_by(OperationLog.created_at.desc()).offset(offset).limit(s)
    ).all()
    return [r.model_dump() for r in rows], int(total)


def get_operation_log(session: Session, log_id: int) -> dict:
    log = session.get(OperationLog, log_id)
    if not log:
        raise not_found("操作日志不存在")
    return log.model_dump()


# --------------------------------------------------------------------------- #
# 用户
# --------------------------------------------------------------------------- #
def _user_dict(session: Session, user: User) -> dict:
    roles = session.exec(
        select(Role).join(UserRole, UserRole.role_id == Role.id).where(UserRole.user_id == user.id)
    ).all()
    data = user.model_dump()
    data.pop("password", None)
    data["roles"] = [{"id": r.id, "role_code": r.role_code, "role_name": r.role_name} for r in roles]
    data["role_ids"] = [r.id for r in roles]
    return data


def _set_user_roles(session: Session, user_id: int, role_ids: list[int]) -> None:
    for ur in session.exec(select(UserRole).where(UserRole.user_id == user_id)).all():
        session.delete(ur)
    for rid in set(role_ids or []):
        if session.get(Role, rid):
            session.add(UserRole(user_id=user_id, role_id=rid))


def list_users(
    session: Session,
    page: int | None = None,
    page_size: int | None = None,
    keyword: str | None = None,
    status: int | None = None,
) -> tuple[list[dict], int]:
    conditions = [User.is_deleted == 0]
    if keyword:
        conditions.append(User.username.contains(keyword) | User.real_name.contains(keyword))
    if status is not None:
        conditions.append(User.status == status)

    p, s, offset = normalize(page, page_size)
    total = session.exec(select(func.count()).select_from(User).where(*conditions)).one()
    rows = session.exec(select(User).where(*conditions).order_by(User.id.desc()).offset(offset).limit(s)).all()
    return [_user_dict(session, u) for u in rows], int(total)


def get_user(session: Session, user_id: int) -> dict:
    user = session.get(User, user_id)
    if not user or user.is_deleted == 1:
        raise not_found("用户不存在")
    return _user_dict(session, user)


def create_user(session: Session, payload, operator: User | None = None) -> dict:
    exists = session.exec(select(User).where(User.username == payload.username)).first()
    if exists:
        raise duplicate("账号已存在")
    user = User(
        username=payload.username,
        password=hash_password(payload.password),
        real_name=payload.real_name,
        phone=payload.phone,
        email=payload.email,
        status=payload.status,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    _set_user_roles(session, user.id, payload.role_ids)
    record_operation(session, operator, "USER", "新增", "用户", user.id, f"新增用户 {user.username}")
    session.commit()
    session.refresh(user)
    return _user_dict(session, user)


def update_user(session: Session, user_id: int, payload, operator: User | None = None) -> dict:
    user = session.get(User, user_id)
    if not user or user.is_deleted == 1:
        raise not_found("用户不存在")
    if payload.real_name is not None:
        user.real_name = payload.real_name
    if payload.phone is not None:
        user.phone = payload.phone
    if payload.email is not None:
        user.email = payload.email
    if payload.status is not None:
        user.status = payload.status
    session.add(user)
    if payload.role_ids is not None:
        _set_user_roles(session, user_id, payload.role_ids)
    record_operation(session, operator, "USER", "编辑", "用户", user.id, f"编辑用户 {user.username}")
    session.commit()
    session.refresh(user)
    return _user_dict(session, user)


def delete_user(session: Session, user_id: int, operator: User | None = None) -> None:
    user = session.get(User, user_id)
    if not user or user.is_deleted == 1:
        raise not_found("用户不存在")
    user.is_deleted = 1
    session.add(user)
    record_operation(session, operator, "USER", "删除", "用户", user.id, f"删除用户 {user.username}")
    session.commit()


def set_user_status(session: Session, user_id: int, status: int, operator: User | None = None) -> dict:
    user = session.get(User, user_id)
    if not user or user.is_deleted == 1:
        raise not_found("用户不存在")
    user.status = status
    session.add(user)
    record_operation(
        session, operator, "USER", "启停", "用户", user.id, f"{'启用' if status == 1 else '停用'}用户 {user.username}"
    )
    session.commit()
    session.refresh(user)
    return _user_dict(session, user)


def reset_password(session: Session, user_id: int, password: str, operator: User | None = None) -> None:
    user = session.get(User, user_id)
    if not user or user.is_deleted == 1:
        raise not_found("用户不存在")
    user.password = hash_password(password)
    session.add(user)
    record_operation(session, operator, "USER", "重置密码", "用户", user.id, f"重置用户 {user.username} 密码")
    session.commit()


# --------------------------------------------------------------------------- #
# 角色
# --------------------------------------------------------------------------- #
def _role_dict(session: Session, role: Role) -> dict:
    data = role.model_dump()
    data["permission_count"] = int(
        session.exec(
            select(func.count()).select_from(RolePermission).where(RolePermission.role_id == role.id)
        ).one()
    )
    return data


def list_roles(
    session: Session, page: int | None = None, page_size: int | None = None, keyword: str | None = None
) -> tuple[list[dict], int]:
    conditions = []
    if keyword:
        conditions.append(Role.role_name.contains(keyword) | Role.role_code.contains(keyword))
    p, s, offset = normalize(page, page_size)
    total = session.exec(select(func.count()).select_from(Role).where(*conditions)).one()
    rows = session.exec(select(Role).where(*conditions).order_by(Role.id).offset(offset).limit(s)).all()
    return [_role_dict(session, r) for r in rows], int(total)


def get_role(session: Session, role_id: int) -> dict:
    role = session.get(Role, role_id)
    if not role:
        raise not_found("角色不存在")
    return _role_dict(session, role)


def create_role(session: Session, payload, operator: User | None = None) -> dict:
    if session.exec(select(Role).where(Role.role_code == payload.role_code)).first():
        raise duplicate("角色编码已存在")
    if session.exec(select(Role).where(Role.role_name == payload.role_name)).first():
        raise duplicate("角色名称已存在")
    role = Role(
        role_code=payload.role_code,
        role_name=payload.role_name,
        remark=payload.remark,
        status=payload.status,
    )
    session.add(role)
    session.commit()
    session.refresh(role)
    record_operation(session, operator, "ROLE", "新增", "角色", role.id, f"新增角色 {role.role_name}")
    session.commit()
    return _role_dict(session, role)


def update_role(session: Session, role_id: int, payload, operator: User | None = None) -> dict:
    role = session.get(Role, role_id)
    if not role:
        raise not_found("角色不存在")
    if payload.role_name and payload.role_name != role.role_name:
        if session.exec(select(Role).where(Role.role_name == payload.role_name)).first():
            raise duplicate("角色名称已存在")
        role.role_name = payload.role_name
    if payload.remark is not None:
        role.remark = payload.remark
    if payload.status is not None:
        role.status = payload.status
    session.add(role)
    record_operation(session, operator, "ROLE", "编辑", "角色", role.id, f"编辑角色 {role.role_name}")
    session.commit()
    session.refresh(role)
    return _role_dict(session, role)


def delete_role(session: Session, role_id: int, operator: User | None = None) -> None:
    role = session.get(Role, role_id)
    if not role:
        raise not_found("角色不存在")
    if role.role_code == "SUPER_ADMIN":
        raise param_error("超级管理员角色不可删除")
    in_use = session.exec(select(func.count()).select_from(UserRole).where(UserRole.role_id == role_id)).one()
    if int(in_use) > 0:
        raise param_error("该角色已被用户使用，无法删除")
    for rp in session.exec(select(RolePermission).where(RolePermission.role_id == role_id)).all():
        session.delete(rp)
    for rs in session.exec(select(RoleShop).where(RoleShop.role_id == role_id)).all():
        session.delete(rs)
    record_operation(session, operator, "ROLE", "删除", "角色", role.id, f"删除角色 {role.role_name}")
    session.delete(role)
    session.commit()


# --------------------------------------------------------------------------- #
# 功能权限与数据权限
# --------------------------------------------------------------------------- #
def permission_tree(session: Session) -> list[dict]:
    rows = list(session.exec(select(Permission).order_by(Permission.sort_no, Permission.id)).all())
    nodes = {p.id: {**p.model_dump(), "children": []} for p in rows}
    roots: list[dict] = []
    for p in rows:
        node = nodes[p.id]
        parent = nodes.get(p.parent_id)
        if parent:
            parent["children"].append(node)
        else:
            roots.append(node)
    return roots


def get_role_permissions(session: Session, role_id: int) -> dict:
    if not session.get(Role, role_id):
        raise not_found("角色不存在")
    ids = session.exec(
        select(RolePermission.permission_id).where(RolePermission.role_id == role_id)
    ).all()
    return {"role_id": role_id, "permission_ids": sorted(set(ids))}


def set_role_permissions(session: Session, role_id: int, permission_ids: list[int], operator: User | None = None) -> dict:
    if not session.get(Role, role_id):
        raise not_found("角色不存在")
    for rp in session.exec(select(RolePermission).where(RolePermission.role_id == role_id)).all():
        session.delete(rp)
    session.flush()
    valid = {p.id for p in session.exec(select(Permission)).all()}
    for pid in set(permission_ids or []):
        if pid in valid:
            session.add(RolePermission(role_id=role_id, permission_id=pid))
    record_operation(session, operator, "PERMISSION", "分配功能权限", "角色", role_id, "更新角色功能权限")
    session.commit()
    return get_role_permissions(session, role_id)


def get_role_data_scope(session: Session, role_id: int) -> dict:
    if not session.get(Role, role_id):
        raise not_found("角色不存在")
    ids = session.exec(select(RoleShop.shop_id).where(RoleShop.role_id == role_id)).all()
    return {"role_id": role_id, "shop_ids": sorted(set(ids))}


def set_role_data_scope(session: Session, role_id: int, shop_ids: list[int], operator: User | None = None) -> dict:
    if not session.get(Role, role_id):
        raise not_found("角色不存在")
    for rs in session.exec(select(RoleShop).where(RoleShop.role_id == role_id)).all():
        session.delete(rs)
    session.flush()
    from app.models.platform import Shop

    valid = {s.id for s in session.exec(select(Shop).where(Shop.is_deleted == 0)).all()}
    for sid in set(shop_ids or []):
        if sid in valid:
            session.add(RoleShop(role_id=role_id, shop_id=sid))
    record_operation(session, operator, "PERMISSION", "配置数据权限", "角色", role_id, "更新角色店铺范围")
    session.commit()
    return get_role_data_scope(session, role_id)
