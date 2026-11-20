"""数据访问层：系统域模型（用户/角色/权限/操作日志）。"""

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


class User(SQLModel, table=True):
    """用户（M10，见《数据库设计》4.5.4）。"""

    __tablename__ = "user"
    __table_args__ = (UniqueConstraint("username", name="uk_user_username"),)

    id: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    username: str = Field(sa_column=Column(String(64), nullable=False))
    password: str = Field(sa_column=Column(String(128), nullable=False))
    real_name: str | None = Field(default=None, sa_column=Column(String(64)))
    phone: str | None = Field(default=None, sa_column=Column(String(32)))
    email: str | None = Field(default=None, sa_column=Column(String(128)))
    status: int = Field(default=1, sa_column=Column(SmallInteger, nullable=False, server_default=text("1")))
    last_login_time: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
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


class Role(SQLModel, table=True):
    """角色（M10，见《数据库设计》4.5.5）。"""

    __tablename__ = "role"
    __table_args__ = (UniqueConstraint("role_code", name="uk_role_role_code"),)

    id: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    role_code: str = Field(sa_column=Column(String(32), nullable=False))
    role_name: str = Field(sa_column=Column(String(64), nullable=False))
    remark: str | None = Field(default=None, sa_column=Column(String(255)))
    status: int = Field(default=1, sa_column=Column(SmallInteger, nullable=False, server_default=text("1")))
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


class UserRole(SQLModel, table=True):
    """用户角色关联（M10，见《数据库设计》4.5.6）。"""

    __tablename__ = "user_role"
    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uk_user_role"),)

    id: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    user_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    role_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )


class Permission(SQLModel, table=True):
    """功能权限（M10，见《数据库设计》4.5.7）。"""

    __tablename__ = "permission"
    __table_args__ = (UniqueConstraint("perm_code", name="uk_permission_perm_code"),)

    id: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    parent_id: int = Field(default=0, sa_column=Column(BigInteger, nullable=False, server_default=text("0")))
    perm_code: str = Field(sa_column=Column(String(64), nullable=False))
    perm_name: str = Field(sa_column=Column(String(64), nullable=False))
    perm_type: str = Field(sa_column=Column(String(16), nullable=False))
    route_path: str | None = Field(default=None, sa_column=Column(String(128)))
    icon: str | None = Field(default=None, sa_column=Column(String(64)))
    sort_no: int = Field(default=0, sa_column=Column(Integer, nullable=False, server_default=text("0")))
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )


class RolePermission(SQLModel, table=True):
    """角色功能权限关联（M10，见《数据库设计》4.5.8）。"""

    __tablename__ = "role_permission"
    __table_args__ = (UniqueConstraint("role_id", "permission_id", name="uk_role_permission"),)

    id: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    role_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    permission_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )


class RoleShop(SQLModel, table=True):
    """角色数据权限（店铺范围）（M10，见《数据库设计》4.5.9）。"""

    __tablename__ = "role_shop"
    __table_args__ = (UniqueConstraint("role_id", "shop_id", name="uk_role_shop"),)

    id: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    role_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    shop_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )


class OperationLog(SQLModel, table=True):
    """操作日志（M10，见《数据库设计》4.5.10）。"""

    __tablename__ = "operation_log"
    __table_args__ = (Index("idx_operation_log_created", "created_at"),)

    id: int | None = Field(
        default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True)
    )
    user_id: int | None = Field(default=None, sa_column=Column(BigInteger))
    username: str | None = Field(default=None, sa_column=Column(String(64)))
    module: str | None = Field(default=None, sa_column=Column(String(32)))
    action: str | None = Field(default=None, sa_column=Column(String(32)))
    target_type: str | None = Field(default=None, sa_column=Column(String(32)))
    target_id: str | None = Field(default=None, sa_column=Column(String(64)))
    content: str | None = Field(default=None, sa_column=Column(String(1000)))
    ip: str | None = Field(default=None, sa_column=Column(String(64)))
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )
