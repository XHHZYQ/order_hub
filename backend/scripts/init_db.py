"""初始化数据库：建全部表 + 业务唯一键 / 常用索引。

用法（在 backend 目录下）：
    uv run python scripts/init_db.py
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import app.models  # noqa: F401  导入全部模型以注册元数据
from sqlalchemy import text
from sqlmodel import SQLModel

from app.core.database import engine

# 本批次相关表的业务唯一键与常用索引（IF NOT EXISTS，安全幂等）
# 命名遵循《数据库设计》第 5 章：uk_{表}_{字段} / idx_{表}_{字段}
EXTRA_DDL: list[str] = [
    # 5.1 唯一键
    'CREATE UNIQUE INDEX IF NOT EXISTS uk_platform_platform_code ON platform (platform_code)',
    'CREATE UNIQUE INDEX IF NOT EXISTS uk_shop_platform_code_shop_code ON shop (platform_code, shop_code)',
    'CREATE UNIQUE INDEX IF NOT EXISTS uk_user_username ON "user" (username)',
    'CREATE UNIQUE INDEX IF NOT EXISTS uk_role_role_code ON role (role_code)',
    'CREATE UNIQUE INDEX IF NOT EXISTS uk_permission_perm_code ON permission (perm_code)',
    'CREATE UNIQUE INDEX IF NOT EXISTS uk_user_role ON user_role (user_id, role_id)',
    'CREATE UNIQUE INDEX IF NOT EXISTS uk_role_permission ON role_permission (role_id, permission_id)',
    'CREATE UNIQUE INDEX IF NOT EXISTS uk_role_shop ON role_shop (role_id, shop_id)',
    # 5.2 常用索引
    'CREATE INDEX IF NOT EXISTS idx_sync_log_task_created ON sync_log (task_id, created_at)',
    'CREATE INDEX IF NOT EXISTS idx_operation_log_created ON operation_log (created_at)',
]


def create_indexes() -> None:
    with engine.begin() as conn:
        for ddl in EXTRA_DDL:
            conn.execute(text(ddl))


def create_all() -> None:
    SQLModel.metadata.create_all(engine)
    create_indexes()


def main() -> None:
    print("[init_db] 创建表结构 ...")
    create_all()
    tables = sorted(SQLModel.metadata.tables.keys())
    print(f"[init_db] 完成，共 {len(tables)} 张表：{', '.join(tables)}")
    print("[init_db] 业务唯一键与常用索引已就绪。")


if __name__ == "__main__":
    main()
