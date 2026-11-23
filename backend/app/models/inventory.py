"""数据访问层：库存域模型（库存主数据、库存流水、库存共享、库存预警）。

对应《数据库设计》4.3.6~4.3.9。库存可售量 = main_qty - occupied_qty（见《概要设计》6.4）。
"""

from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Index,
    Integer,
    SmallInteger,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Inventory(SQLModel, table=True):
    """库存主数据 inventory（见《数据库设计》4.3.6）。唯一键：sku_id。"""

    __tablename__ = "inventory"
    __table_args__ = (UniqueConstraint("sku_id", name="uk_inventory_sku_id"),)

    id: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    sku_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    sku_code: str = Field(sa_column=Column(String(64), nullable=False))
    main_qty: int = Field(default=0, sa_column=Column(Integer, nullable=False, server_default=text("0")))
    occupied_qty: int = Field(default=0, sa_column=Column(Integer, nullable=False, server_default=text("0")))
    status: int = Field(default=1, sa_column=Column(SmallInteger, nullable=False, server_default=text("1")))
    updated_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(
            DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
        ),
    )


class InventoryFlow(SQLModel, table=True):
    """库存流水 inventory_flow（见《数据库设计》4.3.7）。任何库存变动必须落此表。"""

    __tablename__ = "inventory_flow"
    __table_args__ = (Index("idx_inventory_flow_sku_created", "sku_id", "created_at"),)

    id: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    sku_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    sku_code: str = Field(sa_column=Column(String(64), nullable=False))
    flow_type: str = Field(sa_column=Column(String(16), nullable=False))
    change_qty: int = Field(default=0, sa_column=Column(Integer, nullable=False, server_default=text("0")))
    before_qty: int = Field(default=0, sa_column=Column(Integer, nullable=False, server_default=text("0")))
    after_qty: int = Field(default=0, sa_column=Column(Integer, nullable=False, server_default=text("0")))
    source_type: str | None = Field(default=None, sa_column=Column(String(32)))
    source_no: str | None = Field(default=None, sa_column=Column(String(64)))
    remark: str | None = Field(default=None, sa_column=Column(String(255)))
    operator: str | None = Field(default=None, sa_column=Column(String(64)))
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )


class InventoryShare(SQLModel, table=True):
    """库存共享 inventory_share（见《数据库设计》4.3.8）。

    唯一键：uk_inventory_share (sku_id, shop_id)（同一 SKU 在各店铺共享同一盘库存）。
    """

    __tablename__ = "inventory_share"
    __table_args__ = (
        UniqueConstraint("sku_id", "shop_id", name="uk_inventory_share"),
        Index("idx_inventory_share_shop_id", "shop_id"),
    )

    id: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    sku_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    sku_code: str = Field(sa_column=Column(String(64), nullable=False))
    shop_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    platform_code: str | None = Field(default=None, sa_column=Column(String(32)))
    status: int = Field(default=1, sa_column=Column(SmallInteger, nullable=False, server_default=text("1")))
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )


class InventoryAlert(SQLModel, table=True):
    """库存预警配置 inventory_alert（见《数据库设计》4.3.9）。唯一键：sku_id。"""

    __tablename__ = "inventory_alert"
    __table_args__ = (UniqueConstraint("sku_id", name="uk_inventory_alert_sku_id"),)

    id: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    sku_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    sku_code: str = Field(sa_column=Column(String(64), nullable=False))
    alert_qty: int = Field(default=0, sa_column=Column(Integer, nullable=False, server_default=text("0")))
    is_enabled: int = Field(default=1, sa_column=Column(SmallInteger, nullable=False, server_default=text("1")))
    updated_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(
            DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
        ),
    )
