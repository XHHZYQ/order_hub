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
    'CREATE UNIQUE INDEX IF NOT EXISTS uk_orders_order_no ON orders (order_no)',
    'CREATE UNIQUE INDEX IF NOT EXISTS uk_orders_platform_shop_no ON orders (platform_code, shop_id, platform_order_no)',
    'CREATE UNIQUE INDEX IF NOT EXISTS uk_order_ext_order_key ON order_ext (order_id, ext_key)',
    'CREATE UNIQUE INDEX IF NOT EXISTS uk_product_spu_code ON product (spu_code)',
    'CREATE UNIQUE INDEX IF NOT EXISTS uk_sku_sku_code ON sku (sku_code)',
    'CREATE UNIQUE INDEX IF NOT EXISTS uk_platform_product ON platform_product (shop_id, platform_product_id)',
    'CREATE UNIQUE INDEX IF NOT EXISTS uk_platform_sku ON platform_sku (shop_id, platform_sku_id)',
    'CREATE UNIQUE INDEX IF NOT EXISTS uk_sku_mapping ON sku_mapping (shop_id, platform_sku_id)',
    'CREATE UNIQUE INDEX IF NOT EXISTS uk_inventory_sku_id ON inventory (sku_id)',
    'CREATE UNIQUE INDEX IF NOT EXISTS uk_inventory_share ON inventory_share (sku_id, shop_id)',
    'CREATE UNIQUE INDEX IF NOT EXISTS uk_inventory_alert_sku_id ON inventory_alert (sku_id)',
    'CREATE UNIQUE INDEX IF NOT EXISTS uk_logistics_company_code ON logistics_company (company_code)',
    'CREATE UNIQUE INDEX IF NOT EXISTS uk_shipment_shipment_no ON shipment (shipment_no)',
    'CREATE UNIQUE INDEX IF NOT EXISTS uk_after_sale_no ON after_sale (after_sale_no)',
    'CREATE UNIQUE INDEX IF NOT EXISTS uk_after_sale_platform_no ON after_sale (platform_code, shop_id, platform_after_sale_no)',
    # 5.2 常用索引
    'CREATE INDEX IF NOT EXISTS idx_sync_log_task_created ON sync_log (task_id, created_at)',
    'CREATE INDEX IF NOT EXISTS idx_operation_log_created ON operation_log (created_at)',
    'CREATE INDEX IF NOT EXISTS idx_orders_shop_status_order_time ON orders (shop_id, status, order_time)',
    'CREATE INDEX IF NOT EXISTS idx_orders_platform_order_no ON orders (platform_order_no)',
    'CREATE INDEX IF NOT EXISTS idx_orders_buyer_account ON orders (buyer_account)',
    'CREATE INDEX IF NOT EXISTS idx_orders_is_abnormal ON orders (is_abnormal)',
    'CREATE INDEX IF NOT EXISTS idx_order_item_order_id ON order_item (order_id)',
    'CREATE INDEX IF NOT EXISTS idx_order_item_sku_id ON order_item (sku_id)',
    'CREATE INDEX IF NOT EXISTS idx_order_log_order_id ON order_log (order_id)',
    'CREATE INDEX IF NOT EXISTS idx_order_change_order_id ON order_change (order_id)',
    'CREATE INDEX IF NOT EXISTS idx_sku_spu_id ON sku (spu_id)',
    'CREATE INDEX IF NOT EXISTS idx_platform_product_shop_id ON platform_product (shop_id)',
    'CREATE INDEX IF NOT EXISTS idx_platform_sku_platform_product_id ON platform_sku (platform_product_id)',
    'CREATE INDEX IF NOT EXISTS idx_sku_mapping_sku_id ON sku_mapping (sku_id)',
    'CREATE INDEX IF NOT EXISTS idx_inventory_flow_sku_created ON inventory_flow (sku_id, created_at)',
    'CREATE INDEX IF NOT EXISTS idx_inventory_share_shop_id ON inventory_share (shop_id)',
    'CREATE INDEX IF NOT EXISTS idx_shipment_order_id ON shipment (order_id)',
    'CREATE INDEX IF NOT EXISTS idx_shipment_status_shipped_at ON shipment (status, shipped_at)',
    'CREATE INDEX IF NOT EXISTS idx_logistics_trace_shipment_id ON logistics_trace (shipment_id)',
    'CREATE INDEX IF NOT EXISTS idx_logistics_trace_waybill_no ON logistics_trace (waybill_no)',
    'CREATE INDEX IF NOT EXISTS idx_after_sale_shop_status_time ON after_sale (shop_id, status, apply_time)',
    'CREATE INDEX IF NOT EXISTS idx_after_sale_order_id ON after_sale (order_id)',
    'CREATE INDEX IF NOT EXISTS idx_after_sale_log_after_sale_id ON after_sale_log (after_sale_id)',
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
