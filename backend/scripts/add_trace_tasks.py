"""为已存在的库补齐「轨迹(TRACE)」定时同步任务（幂等）。

用法：uv run python scripts/add_trace_tasks.py
"""

from __future__ import annotations

from sqlmodel import select

from app.core.database import session_scope
from app.models.platform import Shop, SyncTask

# (店铺编码, cron, 状态, 备注)
PLAN = [
    ("TB001", "*/30 * * * *", 1, "物流轨迹每 30 分钟拉取"),
    ("SELF001", "0 */1 * * *", 1, "物流轨迹每小时拉取"),
    ("DY001", "0 */2 * * *", 0, "物流轨迹每 2 小时拉取（暂停）"),
]


def main() -> None:
    with session_scope() as session:
        created = 0
        for shop_code, cron, status, remark in PLAN:
            shop = session.exec(select(Shop).where(Shop.shop_code == shop_code)).first()
            if not shop:
                print(f"跳过：店铺不存在 {shop_code}")
                continue
            exists = session.exec(
                select(SyncTask).where(SyncTask.shop_id == shop.id, SyncTask.sync_type == "TRACE")
            ).first()
            if exists:
                print(f"跳过：已存在 TRACE 任务 {shop_code}")
                continue
            session.add(
                SyncTask(
                    shop_id=shop.id,
                    sync_type="TRACE",
                    cron_expr=cron,
                    status=status,
                    remark=remark,
                )
            )
            created += 1
            print(f"新增 TRACE 任务：{shop_code} {cron} status={status}")
        session.commit()
        print(f"完成，新增 {created} 条")


if __name__ == "__main__":
    main()
