"""M10 用户管理接口。"""

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.core.deps import get_db, require_permission
from app.core.response import success, success_page
from app.models.system import User
from app.schemas.common import StatusRequest
from app.schemas.system import ResetPasswordRequest, UserCreate, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.get("", summary="用户列表")
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: str | None = None,
    status: int | None = None,
    _: User = Depends(require_permission("user:list")),
    session: Session = Depends(get_db),
):
    items, total = user_service.list_users(session, page, page_size, keyword, status)
    return success_page(items, total, page, page_size)


@router.post("", summary="新增用户")
def create_user(
    payload: UserCreate,
    operator: User = Depends(require_permission("user:create")),
    session: Session = Depends(get_db),
):
    return success(user_service.create_user(session, payload, operator))


@router.get("/{user_id}", summary="用户详情")
def get_user(
    user_id: int,
    _: User = Depends(require_permission("user:list")),
    session: Session = Depends(get_db),
):
    return success(user_service.get_user(session, user_id))


@router.put("/{user_id}", summary="编辑用户")
def update_user(
    user_id: int,
    payload: UserUpdate,
    operator: User = Depends(require_permission("user:edit")),
    session: Session = Depends(get_db),
):
    return success(user_service.update_user(session, user_id, payload, operator))


@router.delete("/{user_id}", summary="删除用户")
def delete_user(
    user_id: int,
    operator: User = Depends(require_permission("user:delete")),
    session: Session = Depends(get_db),
):
    user_service.delete_user(session, user_id, operator)
    return success(None)


@router.patch("/{user_id}/status", summary="启用/停用用户")
def set_user_status(
    user_id: int,
    payload: StatusRequest,
    operator: User = Depends(require_permission("user:status")),
    session: Session = Depends(get_db),
):
    return success(user_service.set_user_status(session, user_id, payload.status, operator))


@router.post("/{user_id}/reset-password", summary="重置密码")
def reset_password(
    user_id: int,
    payload: ResetPasswordRequest,
    operator: User = Depends(require_permission("user:reset_pwd")),
    session: Session = Depends(get_db),
):
    user_service.reset_password(session, user_id, payload.password, operator)
    return success(None, message="密码已重置")
