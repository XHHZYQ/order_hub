"""M10 操作日志接口。"""

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.core.deps import get_db, require_permission
from app.core.response import success, success_page
from app.models.system import User
from app.services import user_service

router = APIRouter(prefix="/operation-logs", tags=["操作日志"])


@router.get("", summary="操作日志列表")
def list_operation_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    username: str | None = None,
    module: str | None = None,
    action: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    _: User = Depends(require_permission("log:list")),
    session: Session = Depends(get_db),
):
    items, total = user_service.list_operation_logs(
        session, page, page_size, username, module, action, start_time, end_time
    )
    return success_page(items, total, page, page_size)


@router.get("/{log_id}", summary="操作日志详情")
def get_operation_log(
    log_id: int,
    _: User = Depends(require_permission("log:list")),
    session: Session = Depends(get_db),
):
    return success(user_service.get_operation_log(session, log_id))
