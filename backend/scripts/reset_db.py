"""重置数据库：drop_all 后重建（危险操作，仅用于开发/演示）。

用法（在 backend 目录下）：
    uv run python scripts/reset_db.py
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import app.models  # noqa: F401
from sqlmodel import SQLModel

from app.core.database import engine
from scripts.init_db import create_all


def main() -> None:
    tables = sorted(SQLModel.metadata.tables.keys())
    print(f"[reset_db] 即将删除 {len(tables)} 张表：{', '.join(tables)}")
    SQLModel.metadata.drop_all(engine)
    print("[reset_db] 已删除，开始重建 ...")
    create_all()
    print("[reset_db] 重建完成。")


if __name__ == "__main__":
    main()
