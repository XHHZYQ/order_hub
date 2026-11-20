"""APScheduler 调度骨架：启动时加载启用中的同步任务。"""

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlmodel import select

from app.core.config import settings
from app.core.database import session_scope
from app.models.platform import SyncTask
from app.tasks.jobs import run_sync_task

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(timezone=settings.TIMEZONE)

# 简单支持 5 段式 cron：分 时 日 月 周
_FIELD_NAMES = ("minute", "hour", "day", "month", "day_of_week")
_DEFAULT_CRON = "0 2 * * *"


def parse_cron(expr: str | None) -> CronTrigger | None:
    """把 5 段式 cron 解析为 CronTrigger（解析失败返回 None）。"""
    text = (expr or "").strip()
    parts = text.split()
    if len(parts) != 5:
        parts = _DEFAULT_CRON.split()
    try:
        return CronTrigger(**dict(zip(_FIELD_NAMES, parts, strict=True)))
    except (ValueError, TypeError) as exc:
        logger.warning("cron 解析失败：%s (%s)", expr, exc)
        return None


def _enabled_tasks() -> list[SyncTask]:
    with session_scope() as session:
        return list(session.exec(select(SyncTask).where(SyncTask.status == 1)).all())


def register_task(task: SyncTask) -> None:
    """注册/刷新单个任务的定时作业。"""
    job_id = f"sync_task_{task.id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
    if not task.cron_expr:
        return
    trigger = parse_cron(task.cron_expr)
    if trigger is None:
        return
    scheduler.add_job(run_sync_task, trigger=trigger, args=[task.id], id=job_id, replace_existing=True)


def reload_tasks() -> None:
    """重新加载全部启用中的同步任务。"""
    if not scheduler.running:
        return
    for job in scheduler.get_jobs():
        if job.id.startswith("sync_task_"):
            scheduler.remove_job(job.id)
    for task in _enabled_tasks():
        register_task(task)


def start_scheduler() -> None:
    """应用启动时调用。"""
    if not settings.SCHEDULER_ENABLED:
        logger.info("调度器未启用（SCHEDULER_ENABLED=false）")
        return
    if scheduler.running:
        return
    try:
        for task in _enabled_tasks():
            register_task(task)
        scheduler.start()
        logger.info("调度器已启动，共加载 %s 个同步任务", len([j for j in scheduler.get_jobs()]))
    except Exception as exc:  # 启动失败不影响 API 可用
        logger.warning("调度器启动失败：%s", exc)


def shutdown_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("调度器已停止")
