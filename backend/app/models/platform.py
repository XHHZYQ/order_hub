"""数据访问层：平台与店铺域模型（平台/店铺/同步任务/同步日志）。"""

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


class Platform(SQLModel, table=True):
    """平台字典（M1，见《数据库设计》4.1.1）。编码固定 5 个。"""

    __tablename__ = "platform"
    __table_args__ = (UniqueConstraint("platform_code", name="uk_platform_platform_code"),)

    id: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    platform_code: str = Field(sa_column=Column(String(32), nullable=False))
    platform_name: str = Field(sa_column=Column(String(64), nullable=False))
    icon: str | None = Field(default=None, sa_column=Column(String(255)))
    sort_no: int = Field(default=0, sa_column=Column(Integer, nullable=False, server_default=text("0")))
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


class Shop(SQLModel, table=True):
    """店铺（M1，见《数据库设计》4.1.2）。"""

    __tablename__ = "shop"
    __table_args__ = (
        UniqueConstraint("platform_code", "shop_code", name="uk_shop_platform_code_shop_code"),
    )

    id: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    platform_code: str = Field(sa_column=Column(String(32), nullable=False))
    shop_code: str = Field(sa_column=Column(String(64), nullable=False))
    shop_name: str = Field(sa_column=Column(String(128), nullable=False))
    seller_account: str | None = Field(default=None, sa_column=Column(String(64)))
    auth_status: int = Field(default=0, sa_column=Column(SmallInteger, nullable=False, server_default=text("0")))
    auth_token: str | None = Field(default=None, sa_column=Column(String(255)))
    contact_name: str | None = Field(default=None, sa_column=Column(String(64)))
    contact_phone: str | None = Field(default=None, sa_column=Column(String(32)))
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


class SyncTask(SQLModel, table=True):
    """同步任务（M1，见《数据库设计》4.1.3）。"""

    __tablename__ = "sync_task"

    id: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    shop_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    sync_type: str = Field(sa_column=Column(String(16), nullable=False))
    cron_expr: str | None = Field(default=None, sa_column=Column(String(64)))
    start_time: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    last_sync_time: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
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


class SyncLog(SQLModel, table=True):
    """同步日志（M1，见《数据库设计》4.1.4）。"""

    __tablename__ = "sync_log"
    __table_args__ = (Index("idx_sync_log_task_created", "task_id", "created_at"),)

    id: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    task_id: int | None = Field(default=None, sa_column=Column(BigInteger))
    shop_id: int | None = Field(default=None, sa_column=Column(BigInteger))
    sync_type: str | None = Field(default=None, sa_column=Column(String(16)))
    start_time: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    end_time: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    status: str | None = Field(default=None, sa_column=Column(String(16)))
    success_count: int = Field(default=0, sa_column=Column(Integer, nullable=False, server_default=text("0")))
    fail_count: int = Field(default=0, sa_column=Column(Integer, nullable=False, server_default=text("0")))
    cost_ms: int = Field(default=0, sa_column=Column(Integer, nullable=False, server_default=text("0")))
    fail_reason: str | None = Field(default=None, sa_column=Column(String(500)))
    trigger_type: str | None = Field(default=None, sa_column=Column(String(16)))
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )
