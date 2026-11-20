"""调度任务体（APScheduler 调用的函数）。"""

import logging

from app.core.database import session_scope
from app.models.platform import SyncTask
from app.services import sync_service

logger = logging.getLogger(__name__)


def run_sync_task(task_id: int) -> None:
    """按任务 ID 执行同步（定时触发）。"""
    with session_scope() as session:
        task = session.get(SyncTask, task_id)
        if not task:
            logger.warning("同步任务不存在：task_id=%s", task_id)
            return
        if task.status != 1:
            logger.info("同步任务已停用，跳过：task_id=%s", task_id)
            return
        log = sync_service.execute_task(session, task, trigger_type="定时")
        logger.info("定时同步完成：task_id=%s log_id=%s", task_id, log.id)
