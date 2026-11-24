"""数据访问层：财务对账域模型（平台账单批次 / 账单明细 / 对账差异）。

对应《数据库设计》4.5.1~4.5.3；金额用 Decimal 映射 numeric(14,2)。
账单批次为主数据，账单明细与差异为流水性质，仅保留逻辑外键。
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


class Bill(SQLModel, table=True):
    """平台账单批次 bill（见《数据库设计》4.5.1）。唯一键：bill_no。"""

    __tablename__ = "bill"
    __table_args__ = (
        UniqueConstraint("bill_no", name="uk_bill_bill_no"),
        Index("idx_bill_shop_period", "shop_id", "bill_period"),
    )

    id: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    bill_no: str = Field(sa_column=Column(String(32), nullable=False))
    platform_code: str = Field(sa_column=Column(String(32), nullable=False))
    shop_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    bill_period: str = Field(sa_column=Column(String(16), nullable=False))
    file_name: str | None = Field(default=None, sa_column=Column(String(255)))
    total_count: int = Field(default=0, sa_column=Column(Integer, nullable=False, server_default=text("0")))
    total_amount: Decimal = Field(default=Decimal("0"), sa_column=_money())
    reconcile_status: str = Field(
        default="PENDING", sa_column=Column(String(16), nullable=False, server_default=text("'PENDING'"))
    )
    import_time: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )
    operator: str | None = Field(default=None, sa_column=Column(String(64)))
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )


class BillDetail(SQLModel, table=True):
    """账单明细 bill_detail（见《数据库设计》4.5.2）。匹配依据：平台 + 平台订单号。"""

    __tablename__ = "bill_detail"
    __table_args__ = (
        Index("idx_bill_detail_bill_id", "bill_id"),
        Index("idx_bill_detail_platform_order_no", "platform_order_no"),
    )

    id: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    bill_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    platform_code: str = Field(sa_column=Column(String(32), nullable=False))
    shop_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    platform_order_no: str = Field(sa_column=Column(String(64), nullable=False))
    trade_time: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    goods_amount: Decimal = Field(default=Decimal("0"), sa_column=_money())
    freight_amount: Decimal = Field(default=Decimal("0"), sa_column=_money())
    commission_amount: Decimal = Field(default=Decimal("0"), sa_column=_money())
    subsidy_amount: Decimal = Field(default=Decimal("0"), sa_column=_money())
    refund_amount: Decimal = Field(default=Decimal("0"), sa_column=_money())
    settled_amount: Decimal = Field(default=Decimal("0"), sa_column=_money())
    match_status: str = Field(
        default="UNMATCHED", sa_column=Column(String(16), nullable=False, server_default=text("'UNMATCHED'"))
    )
    order_id: int | None = Field(default=None, sa_column=Column(BigInteger))
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )


class ReconcileDiff(SQLModel, table=True):
    """对账差异 reconcile_diff（见《数据库设计》4.5.3）。"""

    __tablename__ = "reconcile_diff"
    __table_args__ = (
        Index("idx_diff_bill_handle_status", "bill_id", "handle_status"),
        Index("idx_diff_platform_order_no", "platform_order_no"),
    )

    id: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    bill_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    bill_detail_id: int | None = Field(default=None, sa_column=Column(BigInteger))
    platform_code: str = Field(sa_column=Column(String(32), nullable=False))
    shop_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    platform_order_no: str = Field(sa_column=Column(String(64), nullable=False))
    order_no: str | None = Field(default=None, sa_column=Column(String(32)))
    diff_type: str = Field(sa_column=Column(String(16), nullable=False))
    local_amount: Decimal = Field(default=Decimal("0"), sa_column=_money())
    bill_amount: Decimal = Field(default=Decimal("0"), sa_column=_money())
    diff_amount: Decimal = Field(default=Decimal("0"), sa_column=_money())
    handle_status: str = Field(
        default="PENDING", sa_column=Column(String(16), nullable=False, server_default=text("'PENDING'"))
    )
    handle_remark: str | None = Field(default=None, sa_column=Column(String(255)))
    operator: str | None = Field(default=None, sa_column=Column(String(64)))
    handle_time: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )
