"""库存域 Schema（M5）。"""

from pydantic import BaseModel, Field


class InventoryUpdateRequest(BaseModel):
    """编辑主库存（生成盘点调整流水）。"""

    main_qty: int = Field(..., ge=0, description="主库存数量")
    remark: str | None = Field(default=None, max_length=255)


class InventoryOccupyRequest(BaseModel):
    """订单占用库存入参。"""

    sku_id: int
    qty: int = Field(..., gt=0, description="占用数量")
    source_no: str | None = Field(default=None, max_length=64, description="来源单号（如订单号）")
    remark: str | None = Field(default=None, max_length=255)


class InventoryReleaseRequest(BaseModel):
    """订单释放占用入参。"""

    sku_id: int
    qty: int = Field(..., gt=0, description="释放数量")
    source_no: str | None = Field(default=None, max_length=64, description="来源单号（如订单号）")
    remark: str | None = Field(default=None, max_length=255)


class InventoryShareCreate(BaseModel):
    """新增库存共享（同一 SKU 共享给某店铺）。"""

    sku_id: int
    shop_id: int
    platform_code: str | None = Field(default=None, max_length=32)
    status: int = 1


class InventoryShareUpdate(BaseModel):
    """编辑库存共享。"""

    platform_code: str | None = Field(default=None, max_length=32)
    status: int | None = None


class AlertConfigUpdate(BaseModel):
    """编辑库存预警配置。"""

    alert_qty: int | None = Field(default=None, ge=0)
    is_enabled: int | None = None


class StocktakeItem(BaseModel):
    """盘点明细项。"""

    sku_id: int
    actual_qty: int = Field(..., ge=0, description="实盘数量")
    remark: str | None = Field(default=None, max_length=255)


class StocktakeRequest(BaseModel):
    """盘点提交入参（批量）。"""

    items: list[StocktakeItem] = Field(..., description="盘点明细")
