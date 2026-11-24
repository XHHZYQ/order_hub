"""数据访问层：售后域模型（售后单 / 售后处理记录）。

对应《数据库设计》4.4.4~4.4.5。
"""

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Index,
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
    return Column(Numeric(14, 2), nullable=False, server_default=text(default))


class AfterSale(SQLModel, table=True):
    """售后单 after_sale（见《数据库设计》4.4.4）。

    唯一键：(platform_code, shop_id, platform_after_sale_no)，保证售后汇聚幂等。
    """

    __tablename__ = "after_sale"
    __table_args__ = (
        UniqueConstraint("after_sale_no", name="uk_after_sale_no"),
        UniqueConstraint(
            "platform_code", "shop_id", "platform_after_sale_no", name="uk_after_sale_platform_shop_no"
        ),
        Index("idx_after_sale_order_id", "order_id"),
        Index("idx_after_sale_shop_status", "shop_id", "status"),
    )

    id: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    after_sale_no: str = Field(sa_column=Column(String(32), nullable=False))
    platform_code: str = Field(sa_column=Column(String(32), nullable=False))
    shop_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    platform_after_sale_no: str = Field(sa_column=Column(String(64), nullable=False))
    order_id: int | None = Field(default=None, sa_column=Column(BigInteger))
    order_no: str | None = Field(default=None, sa_column=Column(String(32)))
    buyer_account: str | None = Field(default=None, sa_column=Column(String(64)))
    type: str = Field(sa_column=Column(String(16), nullable=False))
    reason: str | None = Field(default=None, sa_column=Column(String(255)))
    status: str = Field(sa_column=Column(String(16), nullable=False))
    platform_status: str | None = Field(default=None, sa_column=Column(String(64)))
    refund_amount: Decimal = Field(default=Decimal("0"), sa_column=_money())
    refund_status: str = Field(default="NONE", sa_column=Column(String(16), nullable=False, server_default=text("'NONE'")))
    goods_returned: int = Field(default=0, sa_column=Column(SmallInteger, nullable=False, server_default=text("0")))
    apply_time: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    handle_deadline: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    finish_time: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    operator: str | None = Field(default=None, sa_column=Column(String(64)))
    remark: str | None = Field(default=None, sa_column=Column(String(500)))
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


class AfterSaleLog(SQLModel, table=True):
    """售后处理记录 after_sale_log（见《数据库设计》4.4.5）。"""

    __tablename__ = "after_sale_log"
    __table_args__ = (Index("idx_after_sale_log_after_sale_id", "after_sale_id"),)

    id: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    after_sale_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    after_sale_no: str = Field(sa_column=Column(String(32), nullable=False))
    action: str = Field(sa_column=Column(String(32), nullable=False))
    content: str | None = Field(default=None, sa_column=Column(String(500)))
    operator: str | None = Field(default=None, sa_column=Column(String(64)))
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )
