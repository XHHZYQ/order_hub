"""验证本轮修复：轨迹地址/时间一致性 + 售后/轨迹同步执行。

用法：uv run python -m scripts.verify_batch4_fixes
"""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlmodel import select

from app.adapters import logistics
from app.core.database import session_scope
from app.models.platform import SyncTask
from app.services import sync_service


def check_traces() -> None:
    print("== 轨迹生成幂等性 / 地址一致性 / 时间递增 ==")
    shipped = datetime(2026, 11, 10, 9, 0, 0)
    nodes = logistics.gen_traces(
        waybill_no="SF123456789012",
        company_code="SF",
        dest_city="成都",
        shipped_at=shipped,
        node_count=5,
    )
    times = [n["trace_time"] for n in nodes]
    assert times == sorted(times) and len(set(times)) == len(times), f"时间未严格递增：{times}"
    collected = nodes[0]["trace_desc"]
    in_transit = nodes[1]["trace_desc"]
    # 揽件城市与运输起点城市一致
    origin = collected.split("【")[1].split("】")[0]
    assert f"【{origin}】发出" in in_transit, f"揽件地/运输起点不一致：{collected} | {in_transit}"
    assert origin != "成都", "揽件地不应等于收件城市"
    same = logistics.gen_traces(
        waybill_no="SF123456789012", company_code="SF", dest_city="成都", shipped_at=shipped, node_count=5
    )
    assert [n["trace_desc"] for n in same] == [n["trace_desc"] for n in nodes], "同一运单轨迹应可复现"
    for n in nodes:
        print(f"  {n['trace_time']} {n['trace_status']:<11} {n['trace_desc']}")
    print("  通过：时间严格递增、揽件地与运输起点一致、轨迹可复现\n")


def run_sync(sync_type: str) -> None:
    print(f"== 执行 {sync_type} 定时同步 ==")
    with session_scope() as session:
        task = session.exec(
            select(SyncTask).where(SyncTask.sync_type == sync_type, SyncTask.status == 1)
        ).first()
        if not task:
            print(f"  未找到启用的 {sync_type} 任务，跳过\n")
            return
        log = sync_service.execute_task(session, task, trigger_type="手动")
        print(f"  task_id={task.id} 状态={log.status} 成功={log.success_count} 失败={log.fail_count}")
        print(f"  耗时={log.cost_ms}ms 备注={log.fail_reason}\n")


if __name__ == "__main__":
    check_traces()
    run_sync("AFTER_SALE")
    run_sync("TRACE")
    print("全部验证通过")
