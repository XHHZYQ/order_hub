"""平台与店铺域 Schema。"""

from pydantic import BaseModel, Field


class PlatformCreate(BaseModel):
    platform_code: str = Field(..., max_length=32)
    platform_name: str = Field(..., max_length=64)
    icon: str | None = Field(default=None, max_length=255)
    sort_no: int = 0
    status: int = 1
    remark: str | None = Field(default=None, max_length=255)


class PlatformUpdate(BaseModel):
    platform_name: str | None = Field(default=None, max_length=64)
    icon: str | None = Field(default=None, max_length=255)
    sort_no: int | None = None
    status: int | None = None
    remark: str | None = Field(default=None, max_length=255)


class ShopCreate(BaseModel):
    platform_code: str = Field(..., max_length=32)
    shop_code: str = Field(..., max_length=64)
    shop_name: str = Field(..., max_length=128)
    seller_account: str | None = Field(default=None, max_length=64)
    contact_name: str | None = Field(default=None, max_length=64)
    contact_phone: str | None = Field(default=None, max_length=32)
    status: int = 1
    remark: str | None = Field(default=None, max_length=255)


class ShopUpdate(BaseModel):
    shop_name: str | None = Field(default=None, max_length=128)
    seller_account: str | None = Field(default=None, max_length=64)
    contact_name: str | None = Field(default=None, max_length=64)
    contact_phone: str | None = Field(default=None, max_length=32)
    status: int | None = None
    remark: str | None = Field(default=None, max_length=255)


class SyncTaskCreate(BaseModel):
    shop_id: int
    sync_type: str = Field(..., max_length=16, description="ORDER / INVENTORY / AFTER_SALE")
    cron_expr: str | None = Field(default=None, max_length=64)
    start_time: str | None = Field(default=None, description="YYYY-MM-DD HH:mm:ss")
    status: int = 1
    remark: str | None = Field(default=None, max_length=255)


class SyncTaskUpdate(BaseModel):
    sync_type: str | None = Field(default=None, max_length=16)
    cron_expr: str | None = Field(default=None, max_length=64)
    start_time: str | None = None
    status: int | None = None
    remark: str | None = Field(default=None, max_length=255)
