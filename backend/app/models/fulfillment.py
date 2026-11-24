"""数据访问层：履约域模型（物流公司字典 / 发货单 / 物流轨迹）。

对应《数据库设计》4.4.1~4.4.3。一个订单可对应多个发货单（多包裹）。
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


class LogisticsCompany(SQLModel, table=True):
    """物流公司字典 logistics_company（见《数据库设计》4.4.1）。唯一键：company_code。"""

    __tablename__ = "logistics_company"
    __table_args__ = (UniqueConstraint("company_code", name="uk_logistics_company_code"),)

    id: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    company_code: str = Field(sa_column=Column(String(32), nullable=False))
    company_name: str = Field(sa_column=Column(String(64), nullable=False))
    sort_no: int = Field(default=0, sa_column=Column(Integer, nullable=False, server_default=text("0")))
    status: int = Field(default=1, sa_column=Column(SmallInteger, nullable=False, server_default=text("1")))


class Shipment(SQLModel, table=True):
    """发货单 shipment（见《数据库设计》4.4.2）。唯一键：shipment_no。"""

    __tablename__ = "shipment"
    __table_args__ = (
        UniqueConstraint("shipment_no", name="uk_shipment_no"),
        Index("idx_shipment_order_id", "order_id"),
        Index("idx_shipment_waybill_no", "waybill_no"),
        Index("idx_shipment_shop_status", "shop_id", "status"),
    )

    id: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    shipment_no: str = Field(sa_column=Column(String(32), nullable=False))
    order_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    order_no: str = Field(sa_column=Column(String(32), nullable=False))
    shop_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    platform_code: str = Field(sa_column=Column(String(32), nullable=False))
    logistics_company_code: str | None = Field(default=None, sa_column=Column(String(32)))
    logistics_company_name: str | None = Field(default=None, sa_column=Column(String(64)))
    waybill_no: str | None = Field(default=None, sa_column=Column(String(64)))
    face_sheet_no: str | None = Field(default=None, sa_column=Column(String(64)))
    package_no: str | None = Field(default=None, sa_column=Column(String(32)))
    ship_qty: int = Field(default=0, sa_column=Column(Integer, nullable=False, server_default=text("0")))
    print_status: int = Field(default=0, sa_column=Column(SmallInteger, nullable=False, server_default=text("0")))
    push_status: int = Field(default=0, sa_column=Column(SmallInteger, nullable=False, server_default=text("0")))
    push_fail_reason: str | None = Field(default=None, sa_column=Column(String(255)))
    status: str = Field(sa_column=Column(String(16), nullable=False))
    shipped_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    operator: str | None = Field(default=None, sa_column=Column(String(64)))
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )


class LogisticsTrace(SQLModel, table=True):
    """物流轨迹 logistics_trace（见《数据库设计》4.4.3）。"""

    __tablename__ = "logistics_trace"
    __table_args__ = (Index("idx_logistics_trace_shipment", "shipment_id", "trace_time"),)

    id: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    shipment_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    waybill_no: str | None = Field(default=None, sa_column=Column(String(64)))
    trace_time: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    trace_desc: str | None = Field(default=None, sa_column=Column(String(255)))
    trace_status: str | None = Field(default=None, sa_column=Column(String(32)))
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )
