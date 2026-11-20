"""系统域 Schema（用户/角色/权限）。"""

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str = Field(..., max_length=64)
    password: str = Field(..., min_length=6, max_length=64)
    real_name: str | None = Field(default=None, max_length=64)
    phone: str | None = Field(default=None, max_length=32)
    email: str | None = Field(default=None, max_length=128)
    status: int = 1
    role_ids: list[int] = Field(default_factory=list)


class UserUpdate(BaseModel):
    real_name: str | None = Field(default=None, max_length=64)
    phone: str | None = Field(default=None, max_length=32)
    email: str | None = Field(default=None, max_length=128)
    status: int | None = None
    role_ids: list[int] | None = None


class ResetPasswordRequest(BaseModel):
    password: str = Field(default="123456", min_length=6, max_length=64)


class RoleCreate(BaseModel):
    role_code: str = Field(..., max_length=32)
    role_name: str = Field(..., max_length=64)
    remark: str | None = Field(default=None, max_length=255)
    status: int = 1


class RoleUpdate(BaseModel):
    role_name: str | None = Field(default=None, max_length=64)
    remark: str | None = Field(default=None, max_length=255)
    status: int | None = None


class PermissionIdsRequest(BaseModel):
    permission_ids: list[int] = Field(default_factory=list)


class ShopIdsRequest(BaseModel):
    shop_ids: list[int] = Field(default_factory=list)
