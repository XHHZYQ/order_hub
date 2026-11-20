"""M1 同步任务与同步日志接口。"""

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.core.deps import get_allowed_shop_ids, get_db, require_permission
from app.core.response import success, success_page
from app.models.system import User
from app.schemas.common import StatusRequest
from app.schemas.platform import SyncTaskCreate, SyncTaskUpdate
from app.services import sync_service

task_router = APIRouter(prefix="/sync-tasks", tags=["同步任务"])
log_router = APIRouter(prefix="/sync-logs", tags=["同步日志"])


@task_router.get("", summary="同步任务列表")
def list_sync_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    shop_id: int | None = None,
    sync_type: str | None = None,
    status: int | None = None,
    _: User = Depends(require_permission("sync:task_list")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    items, total = sync_service.list_sync_tasks(
        session, page, page_size, shop_id, sync_type, status, allowed_shop_ids
    )
    return success_page(items, total, page, page_size)


@task_router.post("", summary="新增同步任务")
def create_sync_task(
    payload: SyncTaskCreate,
    operator: User = Depends(require_permission("sync:task_create")),
    session: Session = Depends(get_db),
):
    return success(sync_service.create_sync_task(session, payload, operator))


@task_router.put("/{task_id}", summary="编辑同步任务")
def update_sync_task(
    task_id: int,
    payload: SyncTaskUpdate,
    operator: User = Depends(require_permission("sync:task_edit")),
    session: Session = Depends(get_db),
):
    return success(sync_service.update_sync_task(session, task_id, payload, operator))


@task_router.delete("/{task_id}", summary="删除同步任务")
def delete_sync_task(
    task_id: int,
    operator: User = Depends(require_permission("sync:task_delete")),
    session: Session = Depends(get_db),
):
    sync_service.delete_sync_task(session, task_id, operator)
    return success(None)


@task_router.patch("/{task_id}/status", summary="启用/停用同步任务")
def set_sync_task_status(
    task_id: int,
    payload: StatusRequest,
    operator: User = Depends(require_permission("sync:task_status")),
    session: Session = Depends(get_db),
):
    return success(sync_service.set_sync_task_status(session, task_id, payload.status, operator))


@task_router.post("/{task_id}/trigger", summary="手动触发同步（批次1 仅跑通链路）")
def trigger_sync_task(
    task_id: int,
    operator: User = Depends(require_permission("sync:trigger")),
    session: Session = Depends(get_db),
):
    return success(sync_service.trigger_sync_task(session, task_id, operator))


@log_router.get("", summary="同步日志列表")
def list_sync_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    task_id: int | None = None,
    shop_id: int | None = None,
    sync_type: str | None = None,
    status: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    _: User = Depends(require_permission("sync:log_list")),
    allowed_shop_ids: list[int] | None = Depends(get_allowed_shop_ids),
    session: Session = Depends(get_db),
):
    items, total = sync_service.list_sync_logs(
        session, page, page_size, task_id, shop_id, sync_type, status, start_time, end_time, allowed_shop_ids
    )
    return success_page(items, total, page, page_size)


@log_router.get("/{log_id}", summary="同步日志详情")
def get_sync_log(
    log_id: int,
    _: User = Depends(require_permission("sync:log_list")),
    session: Session = Depends(get_db),
):
    return success(sync_service.get_sync_log(session, log_id))


@log_router.post("/{log_id}/retry", summary="重试同步")
def retry_sync_log(
    log_id: int,
    operator: User = Depends(require_permission("sync:retry")),
    session: Session = Depends(get_db),
):
    return success(sync_service.retry_sync_log(session, log_id, operator))
