"""M10 角色与权限管理接口。"""

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.core.deps import get_db, require_permission
from app.core.response import success, success_page
from app.models.system import User
from app.schemas.system import PermissionIdsRequest, RoleCreate, RoleUpdate, ShopIdsRequest
from app.services import user_service

router = APIRouter(prefix="/roles", tags=["角色管理"])
perm_router = APIRouter(prefix="/permissions", tags=["权限管理"])


@router.get("", summary="角色列表")
def list_roles(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: str | None = None,
    _: User = Depends(require_permission("role:list")),
    session: Session = Depends(get_db),
):
    items, total = user_service.list_roles(session, page, page_size, keyword)
    return success_page(items, total, page, page_size)


@router.post("", summary="新增角色")
def create_role(
    payload: RoleCreate,
    operator: User = Depends(require_permission("role:create")),
    session: Session = Depends(get_db),
):
    return success(user_service.create_role(session, payload, operator))


@router.get("/{role_id}", summary="角色详情")
def get_role(
    role_id: int,
    _: User = Depends(require_permission("role:list")),
    session: Session = Depends(get_db),
):
    return success(user_service.get_role(session, role_id))


@router.put("/{role_id}", summary="编辑角色")
def update_role(
    role_id: int,
    payload: RoleUpdate,
    operator: User = Depends(require_permission("role:edit")),
    session: Session = Depends(get_db),
):
    return success(user_service.update_role(session, role_id, payload, operator))


@router.delete("/{role_id}", summary="删除角色")
def delete_role(
    role_id: int,
    operator: User = Depends(require_permission("role:delete")),
    session: Session = Depends(get_db),
):
    user_service.delete_role(session, role_id, operator)
    return success(None)


@router.get("/{role_id}/permissions", summary="角色功能权限")
def get_role_permissions(
    role_id: int,
    _: User = Depends(require_permission("role:permission")),
    session: Session = Depends(get_db),
):
    return success(user_service.get_role_permissions(session, role_id))


@router.put("/{role_id}/permissions", summary="配置角色功能权限")
def set_role_permissions(
    role_id: int,
    payload: PermissionIdsRequest,
    operator: User = Depends(require_permission("role:permission")),
    session: Session = Depends(get_db),
):
    return success(user_service.set_role_permissions(session, role_id, payload.permission_ids, operator))


@router.get("/{role_id}/data-scope", summary="角色数据权限（店铺范围）")
def get_role_data_scope(
    role_id: int,
    _: User = Depends(require_permission("role:data_scope")),
    session: Session = Depends(get_db),
):
    return success(user_service.get_role_data_scope(session, role_id))


@router.put("/{role_id}/data-scope", summary="配置角色数据权限（店铺范围）")
def set_role_data_scope(
    role_id: int,
    payload: ShopIdsRequest,
    operator: User = Depends(require_permission("role:data_scope")),
    session: Session = Depends(get_db),
):
    return success(user_service.set_role_data_scope(session, role_id, payload.shop_ids, operator))


@perm_router.get("/tree", summary="权限树")
def permission_tree(
    _: User = Depends(require_permission("role:permission")),
    session: Session = Depends(get_db),
):
    return success(user_service.permission_tree(session))
