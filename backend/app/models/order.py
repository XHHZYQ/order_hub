"""数据访问层：订单域模型（订单主表/明细/平台扩展/操作日志/变更记录）。

对应《数据库设计》4.2 订单域 5 张表；金额用 Decimal 映射 numeric(14,2)。
"""

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _money(default: str = "0") -> Column:
    """金额列：numeric(14,2)，默认 0。"""
    return Column(Numeric(14, 2), nullable=False, server_default=text(default))


class Order(SQLModel, table=True):
    """订单主表 orders（M2，见《数据库设计》4.2.1）。

    唯一键：order_no；幂等去重键：(platform_code, shop_id, platform_order_no)。
    """

    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("order_no", name="uk_orders_order_no"),
        UniqueConstraint("platform_code", "shop_id", "platform_order_no", name="uk_orders_platform_shop_no"),
        Index("idx_orders_shop_status_order_time", "shop_id", "status", "order_time"),
        Index("idx_orders_platform_order_no", "platform_order_no"),
        Index("idx_orders_buyer_account", "buyer_account"),
        Index("idx_orders_is_abnormal", "is_abnormal"),
    )

    id: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    order_no: str = Field(sa_column=Column(String(32), nullable=False))
    platform_code: str = Field(sa_column=Column(String(32), nullable=False))
    shop_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    platform_order_no: str = Field(sa_column=Column(String(64), nullable=False))
    buyer_account: str | None = Field(default=None, sa_column=Column(String(64)))
    buyer_nick: str | None = Field(default=None, sa_column=Column(String(64)))
    receiver_name: str | None = Field(default=None, sa_column=Column(String(64)))
    receiver_phone: str | None = Field(default=None, sa_column=Column(String(32)))
    receiver_province: str | None = Field(default=None, sa_column=Column(String(32)))
    receiver_city: str | None = Field(default=None, sa_column=Column(String(32)))
    receiver_district: str | None = Field(default=None, sa_column=Column(String(32)))
    receiver_address: str | None = Field(default=None, sa_column=Column(String(255)))
    goods_amount: Decimal = Field(default=Decimal("0"), sa_column=_money())
    discount_amount: Decimal = Field(default=Decimal("0"), sa_column=_money())
    freight_amount: Decimal = Field(default=Decimal("0"), sa_column=_money())
    pay_amount: Decimal = Field(default=Decimal("0"), sa_column=_money())
    status: str = Field(sa_column=Column(String(16), nullable=False))
    platform_status: str | None = Field(default=None, sa_column=Column(String(64)))
    source: str = Field(sa_column=Column(String(16), nullable=False))
    is_abnormal: int = Field(default=0, sa_column=Column(SmallInteger, nullable=False, server_default=text("0")))
    abnormal_reason: str | None = Field(default=None, sa_column=Column(String(255)))
    merchant_remark: str | None = Field(default=None, sa_column=Column(String(500)))
    buyer_remark: str | None = Field(default=None, sa_column=Column(String(500)))
    tags: str | None = Field(default=None, sa_column=Column(String(255)))
    order_time: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    paid_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    shipped_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    finished_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    closed_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    merge_group_no: str | None = Field(default=None, sa_column=Column(String(32)))
    parent_order_no: str | None = Field(default=None, sa_column=Column(String(32)))
    sync_time: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    is_deleted: int = Field(default=0, sa_column=Column(SmallInteger, nullable=False, server_default=text("0")))
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )
    updated_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(
            DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
        ),
    )


class OrderItem(SQLModel, table=True):
    """订单明细 order_item（M2，见《数据库设计》4.2.2）。"""

    __tablename__ = "order_item"
    __table_args__ = (
        Index("idx_order_item_order_id", "order_id"),
        Index("idx_order_item_sku_id", "sku_id"),
    )

    id: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    order_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    order_no: str = Field(sa_column=Column(String(32), nullable=False))
    platform_sku_id: str | None = Field(default=None, sa_column=Column(String(64)))
    platform_sku_name: str | None = Field(default=None, sa_column=Column(String(255)))
    outer_sku_code: str | None = Field(default=None, sa_column=Column(String(64)))
    sku_id: int | None = Field(default=None, sa_column=Column(BigInteger))
    sku_code: str | None = Field(default=None, sa_column=Column(String(64)))
    product_name: str | None = Field(default=None, sa_column=Column(String(255)))
    spec_desc: str | None = Field(default=None, sa_column=Column(String(255)))
    price: Decimal = Field(default=Decimal("0"), sa_column=_money())
    quantity: int = Field(default=1, sa_column=Column(Integer, nullable=False, server_default=text("1")))
    total_amount: Decimal = Field(default=Decimal("0"), sa_column=_money())
    discount_amount: Decimal = Field(default=Decimal("0"), sa_column=_money())
    pay_amount: Decimal = Field(default=Decimal("0"), sa_column=_money())
    shipped_quantity: int = Field(default=0, sa_column=Column(Integer, nullable=False, server_default=text("0")))
    refund_quantity: int = Field(default=0, sa_column=Column(Integer, nullable=False, server_default=text("0")))
    is_matched: int = Field(default=0, sa_column=Column(SmallInteger, nullable=False, server_default=text("0")))
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )


class OrderExt(SQLModel, table=True):
    """订单平台扩展 order_ext（M2，见《数据库设计》4.2.3）。键值对存储平台特有字段。"""

    __tablename__ = "order_ext"
    __table_args__ = (UniqueConstraint("order_id", "ext_key", name="uk_order_ext_order_key"),)

    id: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    order_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    ext_key: str = Field(sa_column=Column(String(64), nullable=False))
    ext_name: str | None = Field(default=None, sa_column=Column(String(128)))
    ext_value: str | None = Field(default=None, sa_column=Column(String(500)))
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )


class OrderLog(SQLModel, table=True):
    """订单操作日志 order_log（M2，见《数据库设计》4.2.4）。"""

    __tablename__ = "order_log"
    __table_args__ = (Index("idx_order_log_order_id", "order_id"),)

    id: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    order_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    order_no: str = Field(sa_column=Column(String(32), nullable=False))
    action: str | None = Field(default=None, sa_column=Column(String(32)))
    from_status: str | None = Field(default=None, sa_column=Column(String(16)))
    to_status: str | None = Field(default=None, sa_column=Column(String(16)))
    content: str | None = Field(default=None, sa_column=Column(String(500)))
    operator: str | None = Field(default=None, sa_column=Column(String(64)))
    source: str | None = Field(default=None, sa_column=Column(String(16)))
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )


class OrderChange(SQLModel, table=True):
    """订单变更记录 order_change（M2，见《数据库设计》4.2.5）。

    记录字段级变更：变更类型、变更字段、变更前后值与原因，用于订单详情页展示变更历史。
    """

    __tablename__ = "order_change"
    __table_args__ = (Index("idx_order_change_order_id", "order_id"),)

    id: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    order_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    order_no: str = Field(sa_column=Column(String(32), nullable=False))
    change_type: str | None = Field(default=None, sa_column=Column(String(16)))
    field_name: str = Field(sa_column=Column(String(64), nullable=False))
    before_value: str | None = Field(default=None, sa_column=Column(String(500)))
    after_value: str | None = Field(default=None, sa_column=Column(String(500)))
    reason: str | None = Field(default=None, sa_column=Column(String(255)))
    operator: str | None = Field(default=None, sa_column=Column(String(64)))
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )
