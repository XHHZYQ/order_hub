"""调度任务体（APScheduler 调用的函数）。"""

import logging
import threading

from app.core.database import session_scope
from app.models.platform import SyncTask
from app.services import sync_service

logger = logging.getLogger(__name__)

# 全局串行锁：所有定时同步任务互斥执行。
# 避免多个任务在启动瞬间并发写库（如多店铺订单同步并发占用库存导致 Postgres 死锁）。
_SYNC_LOCK = threading.Lock()


def run_sync_task(task_id: int) -> None:
    """按任务 ID 执行同步（定时触发，全局串行）。"""
    with _SYNC_LOCK:
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
