"""并发死锁回归：多任务同时执行定时同步，验证已串行化、无死锁。

用法：uv run python -m scripts.verify_no_deadlock
"""

from __future__ import annotations

import threading
import time

from sqlmodel import select

from app.core.database import session_scope
from app.models.platform import SyncTask
from app.tasks import jobs


def main() -> None:
    with session_scope() as session:
        task_ids = [
            row for row in session.exec(select(SyncTask.id).where(SyncTask.status == 1)).all()
        ]
    print(f"启用中的同步任务：{task_ids}，并发触发（模拟启动瞬间）…")

    errors: list[tuple[int, str]] = []

    def worker(tid: int) -> None:
        try:
            for _ in range(2):
                jobs.run_sync_task(tid)
        except Exception as exc:  # noqa: BLE001
            errors.append((tid, repr(exc)))

    threads = [threading.Thread(target=worker, args=(tid,)) for tid in task_ids]
    started = time.perf_counter()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    cost = time.perf_counter() - started

    print(f"全部完成，耗时 {cost:.2f}s，异常 {len(errors)} 条")
    for tid, err in errors:
        print(f"  task_id={tid} -> {err}")
    assert not errors, "存在异常（疑似死锁/报错）"
    print("通过：并发触发未出现死锁或异常")


if __name__ == "__main__":
    main()
