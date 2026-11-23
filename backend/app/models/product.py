"""数据访问层：商品与 SKU 映射域模型（本地商品/SKU、平台商品/规格、SKU 映射）。

对应《数据库设计》4.3.1~4.3.5；金额用 Decimal 映射 numeric(14,2)。
平台商品/规格/映射为高频流水性质，仅保留逻辑外键（沿用订单域写法）。
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


class Product(SQLModel, table=True):
    """本地商品 product（SPU，见《数据库设计》4.3.1）。

    唯一键：spu_code。本地主数据表，保留 is_deleted 软删除。
    """

    __tablename__ = "product"
    __table_args__ = (UniqueConstraint("spu_code", name="uk_product_spu_code"),)

    id: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    spu_code: str = Field(sa_column=Column(String(64), nullable=False))
    spu_name: str = Field(sa_column=Column(String(255), nullable=False))
    category_name: str | None = Field(default=None, sa_column=Column(String(64)))
    brand: str | None = Field(default=None, sa_column=Column(String(64)))
    unit: str | None = Field(default=None, sa_column=Column(String(16)))
    status: int = Field(default=1, sa_column=Column(SmallInteger, nullable=False, server_default=text("1")))
    remark: str | None = Field(default=None, sa_column=Column(String(255)))
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


class Sku(SQLModel, table=True):
    """本地 SKU sku（见《数据库设计》4.3.2）。唯一键：sku_code。"""

    __tablename__ = "sku"
    __table_args__ = (
        UniqueConstraint("sku_code", name="uk_sku_sku_code"),
        Index("idx_sku_spu_id", "spu_id"),
    )

    id: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    sku_code: str = Field(sa_column=Column(String(64), nullable=False))
    spu_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    sku_name: str = Field(sa_column=Column(String(255), nullable=False))
    spec_desc: str | None = Field(default=None, sa_column=Column(String(255)))
    cost_price: Decimal = Field(default=Decimal("0"), sa_column=_money())
    sale_price: Decimal = Field(default=Decimal("0"), sa_column=_money())
    status: int = Field(default=1, sa_column=Column(SmallInteger, nullable=False, server_default=text("1")))
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


class PlatformProduct(SQLModel, table=True):
    """平台商品 platform_product（见《数据库设计》4.3.3）。

    唯一键：uk_platform_product (shop_id, platform_product_id)。
    """

    __tablename__ = "platform_product"
    __table_args__ = (
        UniqueConstraint("shop_id", "platform_product_id", name="uk_platform_product"),
        Index("idx_platform_product_shop_id", "shop_id"),
    )

    id: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    shop_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    platform_code: str = Field(sa_column=Column(String(32), nullable=False))
    platform_product_id: str = Field(sa_column=Column(String(64), nullable=False))
    product_title: str | None = Field(default=None, sa_column=Column(String(255)))
    category_name: str | None = Field(default=None, sa_column=Column(String(64)))
    status: str | None = Field(default=None, sa_column=Column(String(16)))
    sync_time: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )


class PlatformSku(SQLModel, table=True):
    """平台商品规格 platform_sku（见《数据库设计》4.3.4）。

    唯一键：uk_platform_sku (shop_id, platform_sku_id)。
    """

    __tablename__ = "platform_sku"
    __table_args__ = (
        UniqueConstraint("shop_id", "platform_sku_id", name="uk_platform_sku"),
        Index("idx_platform_sku_platform_product_id", "platform_product_id"),
    )

    id: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    platform_product_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    shop_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    platform_code: str = Field(sa_column=Column(String(32), nullable=False))
    platform_sku_id: str = Field(sa_column=Column(String(64), nullable=False))
    sku_name: str | None = Field(default=None, sa_column=Column(String(255)))
    spec_desc: str | None = Field(default=None, sa_column=Column(String(255)))
    outer_sku_code: str | None = Field(default=None, sa_column=Column(String(64)))
    price: Decimal = Field(default=Decimal("0"), sa_column=_money())
    platform_stock: int = Field(default=0, sa_column=Column(Integer, nullable=False, server_default=text("0")))
    is_matched: int = Field(default=0, sa_column=Column(SmallInteger, nullable=False, server_default=text("0")))
    sync_time: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )


class SkuMapping(SQLModel, table=True):
    """SKU 映射 sku_mapping（见《数据库设计》4.3.5）。

    唯一键：uk_sku_mapping (shop_id, platform_sku_id)（一个平台 SKU 只映射一个本地 SKU）。
    """

    __tablename__ = "sku_mapping"
    __table_args__ = (
        UniqueConstraint("shop_id", "platform_sku_id", name="uk_sku_mapping"),
        Index("idx_sku_mapping_sku_id", "sku_id"),
    )

    id: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    platform_code: str = Field(sa_column=Column(String(32), nullable=False))
    shop_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    platform_sku_id: str = Field(sa_column=Column(String(64), nullable=False))
    platform_sku_name: str | None = Field(default=None, sa_column=Column(String(255)))
    sku_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    sku_code: str = Field(sa_column=Column(String(64), nullable=False))
    status: int = Field(default=1, sa_column=Column(SmallInteger, nullable=False, server_default=text("1")))
    remark: str | None = Field(default=None, sa_column=Column(String(255)))
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
