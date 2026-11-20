"""M1 平台与店铺服务：平台字典、店铺授权、同步任务与同步日志。"""

import random
import string
import time

from sqlmodel import Session, func, select

from app.core.exceptions import duplicate, not_found, param_error, status_not_allowed
from app.models.platform import Platform, Shop, SyncLog, SyncTask
from app.models.system import User
from app.services.user_service import record_operation
from app.utils.datetime_util import now_utc, parse_datetime
from app.utils.pagination import normalize


def _gen_auth_token() -> str:
    """生成模拟授权凭证。"""
    body = "".join(random.choices(string.ascii_letters + string.digits, k=32))
    return f"mock-{body}"


# --------------------------------------------------------------------------- #
# 平台字典
# --------------------------------------------------------------------------- #
def list_platforms(
    session: Session,
    page: int | None = None,
    page_size: int | None = None,
    keyword: str | None = None,
    status: int | None = None,
) -> tuple[list[dict], int]:
    conditions = []
    if keyword:
        conditions.append(Platform.platform_name.contains(keyword) | Platform.platform_code.contains(keyword))
    if status is not None:
        conditions.append(Platform.status == status)
    p, s, offset = normalize(page, page_size)
    total = session.exec(select(func.count()).select_from(Platform).where(*conditions)).one()
    rows = session.exec(
        select(Platform).where(*conditions).order_by(Platform.sort_no, Platform.id).offset(offset).limit(s)
    ).all()
    return [r.model_dump() for r in rows], int(total)


def platform_options(session: Session) -> list[dict]:
    rows = session.exec(select(Platform).where(Platform.status == 1).order_by(Platform.sort_no)).all()
    return [{"platform_code": r.platform_code, "platform_name": r.platform_name} for r in rows]


def get_platform(session: Session, platform_id: int) -> dict:
    row = session.get(Platform, platform_id)
    if not row:
        raise not_found("平台不存在")
    return row.model_dump()


def create_platform(session: Session, payload, operator: User | None = None) -> dict:
    if session.exec(select(Platform).where(Platform.platform_code == payload.platform_code)).first():
        raise duplicate("平台编码已存在")
    row = Platform(**payload.model_dump())
    session.add(row)
    session.commit()
    session.refresh(row)
    record_operation(session, operator, "PLATFORM", "新增", "平台", row.id, f"新增平台 {row.platform_name}")
    session.commit()
    return row.model_dump()


def update_platform(session: Session, platform_id: int, payload, operator: User | None = None) -> dict:
    row = session.get(Platform, platform_id)
    if not row:
        raise not_found("平台不存在")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    session.add(row)
    record_operation(session, operator, "PLATFORM", "编辑", "平台", row.id, f"编辑平台 {row.platform_name}")
    session.commit()
    session.refresh(row)
    return row.model_dump()


def delete_platform(session: Session, platform_id: int, operator: User | None = None) -> None:
    row = session.get(Platform, platform_id)
    if not row:
        raise not_found("平台不存在")
    shop_count = session.exec(select(func.count()).select_from(Shop).where(Shop.platform_code == row.platform_code)).one()
    if int(shop_count) > 0:
        raise param_error("该平台下存在店铺，无法删除")
    record_operation(session, operator, "PLATFORM", "删除", "平台", row.id, f"删除平台 {row.platform_name}")
    session.delete(row)
    session.commit()


def set_platform_status(session: Session, platform_id: int, status: int, operator: User | None = None) -> dict:
    row = session.get(Platform, platform_id)
    if not row:
        raise not_found("平台不存在")
    row.status = status
    session.add(row)
    record_operation(
        session, operator, "PLATFORM", "启停", "平台", row.id, f"{'启用' if status == 1 else '停用'}平台 {row.platform_name}"
    )
    session.commit()
    session.refresh(row)
    return row.model_dump()


# --------------------------------------------------------------------------- #
# 店铺
# --------------------------------------------------------------------------- #
def list_shops(
    session: Session,
    page: int | None = None,
    page_size: int | None = None,
    keyword: str | None = None,
    platform_code: str | None = None,
    status: int | None = None,
    auth_status: int | None = None,
    allowed_shop_ids: list[int] | None = None,
) -> tuple[list[dict], int]:
    conditions = [Shop.is_deleted == 0]
    if keyword:
        conditions.append(Shop.shop_name.contains(keyword) | Shop.shop_code.contains(keyword))
    if platform_code:
        conditions.append(Shop.platform_code == platform_code)
    if status is not None:
        conditions.append(Shop.status == status)
    if auth_status is not None:
        conditions.append(Shop.auth_status == auth_status)
    if allowed_shop_ids is not None:
        conditions.append(Shop.id.in_(allowed_shop_ids or [-1]))

    p, s, offset = normalize(page, page_size)
    total = session.exec(select(func.count()).select_from(Shop).where(*conditions)).one()
    rows = session.exec(select(Shop).where(*conditions).order_by(Shop.id).offset(offset).limit(s)).all()
    return [r.model_dump() for r in rows], int(total)


def shop_options(session: Session, allowed_shop_ids: list[int] | None = None) -> list[dict]:
    conditions = [Shop.is_deleted == 0, Shop.status == 1]
    if allowed_shop_ids is not None:
        conditions.append(Shop.id.in_(allowed_shop_ids or [-1]))
    rows = session.exec(select(Shop).where(*conditions).order_by(Shop.platform_code, Shop.id)).all()
    return [{"id": r.id, "shop_code": r.shop_code, "shop_name": r.shop_name, "platform_code": r.platform_code} for r in rows]


def get_shop(session: Session, shop_id: int) -> dict:
    row = session.get(Shop, shop_id)
    if not row or row.is_deleted == 1:
        raise not_found("店铺不存在")
    return row.model_dump()


def create_shop(session: Session, payload, operator: User | None = None) -> dict:
    exists = session.exec(
        select(Shop).where(Shop.platform_code == payload.platform_code, Shop.shop_code == payload.shop_code)
    ).first()
    if exists:
        raise duplicate("同平台下店铺编码已存在")
    if not session.exec(select(Platform).where(Platform.platform_code == payload.platform_code)).first():
        raise param_error("平台编码不存在")
    row = Shop(**payload.model_dump(), auth_status=1, auth_token=_gen_auth_token())
    session.add(row)
    session.commit()
    session.refresh(row)
    record_operation(session, operator, "SHOP", "新增", "店铺", row.id, f"新增店铺 {row.shop_name} 并完成模拟授权")
    session.commit()
    return row.model_dump()


def update_shop(session: Session, shop_id: int, payload, operator: User | None = None) -> dict:
    row = session.get(Shop, shop_id)
    if not row or row.is_deleted == 1:
        raise not_found("店铺不存在")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    session.add(row)
    record_operation(session, operator, "SHOP", "编辑", "店铺", row.id, f"编辑店铺 {row.shop_name}")
    session.commit()
    session.refresh(row)
    return row.model_dump()


def delete_shop(session: Session, shop_id: int, operator: User | None = None) -> None:
    row = session.get(Shop, shop_id)
    if not row or row.is_deleted == 1:
        raise not_found("店铺不存在")
    row.is_deleted = 1
    session.add(row)
    record_operation(session, operator, "SHOP", "删除", "店铺", row.id, f"删除店铺 {row.shop_name}")
    session.commit()


def set_shop_status(session: Session, shop_id: int, status: int, operator: User | None = None) -> dict:
    row = session.get(Shop, shop_id)
    if not row or row.is_deleted == 1:
        raise not_found("店铺不存在")
    row.status = status
    session.add(row)
    record_operation(
        session, operator, "SHOP", "启停", "店铺", row.id, f"{'启用' if status == 1 else '停用'}店铺 {row.shop_name}"
    )
    session.commit()
    session.refresh(row)
    return row.model_dump()


def authorize_shop(session: Session, shop_id: int, operator: User | None = None) -> dict:
    row = session.get(Shop, shop_id)
    if not row or row.is_deleted == 1:
        raise not_found("店铺不存在")
    row.auth_status = 1
    row.auth_token = _gen_auth_token()
    session.add(row)
    record_operation(session, operator, "SHOP", "重新授权", "店铺", row.id, f"店铺 {row.shop_name} 重新授权")
    session.commit()
    session.refresh(row)
    return row.model_dump()


# --------------------------------------------------------------------------- #
# 同步任务
# --------------------------------------------------------------------------- #
def list_sync_tasks(
    session: Session,
    page: int | None = None,
    page_size: int | None = None,
    shop_id: int | None = None,
    sync_type: str | None = None,
    status: int | None = None,
    allowed_shop_ids: list[int] | None = None,
) -> tuple[list[dict], int]:
    conditions = []
    if shop_id:
        conditions.append(SyncTask.shop_id == shop_id)
    if sync_type:
        conditions.append(SyncTask.sync_type == sync_type)
    if status is not None:
        conditions.append(SyncTask.status == status)
    if allowed_shop_ids is not None:
        conditions.append(SyncTask.shop_id.in_(allowed_shop_ids or [-1]))

    p, s, offset = normalize(page, page_size)
    total = session.exec(select(func.count()).select_from(SyncTask).where(*conditions)).one()
    rows = session.exec(select(SyncTask).where(*conditions).order_by(SyncTask.id.desc()).offset(offset).limit(s)).all()
    return [_task_dict(session, r) for r in rows], int(total)


def _task_dict(session: Session, task: SyncTask) -> dict:
    data = task.model_dump()
    shop = session.get(Shop, task.shop_id)
    data["shop_name"] = shop.shop_name if shop else None
    data["platform_code"] = shop.platform_code if shop else None
    return data


def get_sync_task(session: Session, task_id: int) -> dict:
    task = session.get(SyncTask, task_id)
    if not task:
        raise not_found("同步任务不存在")
    return _task_dict(session, task)


def _validate_sync_type(sync_type: str) -> None:
    from app.core.constants import SYNC_TYPES

    if sync_type not in SYNC_TYPES:
        raise param_error(f"同步类型非法，应为 {'/'.join(SYNC_TYPES)}")


def create_sync_task(session: Session, payload, operator: User | None = None) -> dict:
    _validate_sync_type(payload.sync_type)
    if not session.get(Shop, payload.shop_id):
        raise param_error("店铺不存在")
    task = SyncTask(
        shop_id=payload.shop_id,
        sync_type=payload.sync_type,
        cron_expr=payload.cron_expr,
        start_time=parse_datetime(payload.start_time),
        status=payload.status,
        remark=payload.remark,
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    record_operation(session, operator, "SYNC", "新增任务", "同步任务", task.id, f"新增 {task.sync_type} 同步任务")
    session.commit()
    return _task_dict(session, task)


def update_sync_task(session: Session, task_id: int, payload, operator: User | None = None) -> dict:
    task = session.get(SyncTask, task_id)
    if not task:
        raise not_found("同步任务不存在")
    data = payload.model_dump(exclude_unset=True)
    if "sync_type" in data and data["sync_type"]:
        _validate_sync_type(data["sync_type"])
        task.sync_type = data["sync_type"]
    if "cron_expr" in data:
        task.cron_expr = data["cron_expr"]
    if "start_time" in data:
        task.start_time = parse_datetime(data["start_time"])
    if "status" in data and data["status"] is not None:
        task.status = data["status"]
    if "remark" in data:
        task.remark = data["remark"]
    session.add(task)
    record_operation(session, operator, "SYNC", "编辑任务", "同步任务", task.id, "编辑同步任务")
    session.commit()
    session.refresh(task)
    return _task_dict(session, task)


def delete_sync_task(session: Session, task_id: int, operator: User | None = None) -> None:
    task = session.get(SyncTask, task_id)
    if not task:
        raise not_found("同步任务不存在")
    record_operation(session, operator, "SYNC", "删除任务", "同步任务", task.id, "删除同步任务")
    session.delete(task)
    session.commit()


def set_sync_task_status(session: Session, task_id: int, status: int, operator: User | None = None) -> dict:
    task = session.get(SyncTask, task_id)
    if not task:
        raise not_found("同步任务不存在")
    task.status = status
    session.add(task)
    record_operation(
        session, operator, "SYNC", "启停任务", "同步任务", task.id, f"{'启用' if status == 1 else '停用'}同步任务"
    )
    session.commit()
    session.refresh(task)
    return _task_dict(session, task)


# --------------------------------------------------------------------------- #
# 同步执行（批次1 仅跑通链路）
# --------------------------------------------------------------------------- #
def execute_task(session: Session, task: SyncTask, trigger_type: str = "手动") -> SyncLog:
    """执行一次同步任务，写入一条同步日志。

    批次1：真实拉数（模拟平台适配器）尚未实现，仅跑通链路，记录成功、counts=0。
    TODO 批次2：改为调用平台适配器 fetch_orders/fetch_inventory/fetch_after_sales 真实拉取并幂等落库。
    """
    if task.status != 1:
        raise status_not_allowed("同步任务已停用，无法执行")
    started = time.perf_counter()
    end_time = now_utc()
    start_time = task.last_sync_time or task.start_time or end_time

    log = SyncLog(
        task_id=task.id,
        shop_id=task.shop_id,
        sync_type=task.sync_type,
        start_time=start_time,
        end_time=end_time,
        status="成功",
        success_count=0,
        fail_count=0,
        cost_ms=int((time.perf_counter() - started) * 1000),
        fail_reason=None,
        trigger_type=trigger_type,
    )
    task.last_sync_time = end_time
    session.add(task)
    session.add(log)
    session.commit()
    session.refresh(log)
    return log


def trigger_sync_task(session: Session, task_id: int, operator: User | None = None) -> dict:
    task = session.get(SyncTask, task_id)
    if not task:
        raise not_found("同步任务不存在")
    log = execute_task(session, task, trigger_type="手动")
    record_operation(session, operator, "SYNC", "手动触发", "同步任务", task.id, "手动触发一次同步")
    session.commit()
    return log.model_dump()


# --------------------------------------------------------------------------- #
# 同步日志
# --------------------------------------------------------------------------- #
def list_sync_logs(
    session: Session,
    page: int | None = None,
    page_size: int | None = None,
    task_id: int | None = None,
    shop_id: int | None = None,
    sync_type: str | None = None,
    status: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    allowed_shop_ids: list[int] | None = None,
) -> tuple[list[dict], int]:
    conditions = []
    if task_id:
        conditions.append(SyncLog.task_id == task_id)
    if shop_id:
        conditions.append(SyncLog.shop_id == shop_id)
    if sync_type:
        conditions.append(SyncLog.sync_type == sync_type)
    if status:
        conditions.append(SyncLog.status == status)
    st = parse_datetime(start_time)
    et = parse_datetime(end_time)
    if st:
        conditions.append(SyncLog.created_at >= st)
    if et:
        conditions.append(SyncLog.created_at <= et)
    if allowed_shop_ids is not None:
        conditions.append(SyncLog.shop_id.in_(allowed_shop_ids or [-1]))

    p, s, offset = normalize(page, page_size)
    total = session.exec(select(func.count()).select_from(SyncLog).where(*conditions)).one()
    rows = session.exec(select(SyncLog).where(*conditions).order_by(SyncLog.created_at.desc()).offset(offset).limit(s)).all()
    return [_log_dict(session, r) for r in rows], int(total)


def _log_dict(session: Session, log: SyncLog) -> dict:
    data = log.model_dump()
    shop = session.get(Shop, log.shop_id) if log.shop_id else None
    data["shop_name"] = shop.shop_name if shop else None
    data["platform_code"] = shop.platform_code if shop else None
    return data


def get_sync_log(session: Session, log_id: int) -> dict:
    log = session.get(SyncLog, log_id)
    if not log:
        raise not_found("同步日志不存在")
    return _log_dict(session, log)


def retry_sync_log(session: Session, log_id: int, operator: User | None = None) -> dict:
    log = session.get(SyncLog, log_id)
    if not log:
        raise not_found("同步日志不存在")
    if log.status not in ("失败", "部分失败"):
        raise status_not_allowed("仅失败或部分失败的日志可重试")
    task = session.get(SyncTask, log.task_id) if log.task_id else None
    if not task:
        raise not_found("原同步任务不存在，无法重试")
    new_log = execute_task(session, task, trigger_type="手动")
    record_operation(session, operator, "SYNC", "重试同步", "同步日志", log.id, "按失败日志重新触发同步")
    session.commit()
    return new_log.model_dump()
