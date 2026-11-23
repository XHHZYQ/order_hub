"""商品与 SKU 映射域 Schema（M4）。"""

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    """新建本地商品（SPU）。"""

    spu_code: str = Field(..., max_length=64)
    spu_name: str = Field(..., max_length=255)
    category_name: str | None = Field(default=None, max_length=64)
    brand: str | None = Field(default=None, max_length=64)
    unit: str | None = Field(default=None, max_length=16)
    status: int = 1
    remark: str | None = Field(default=None, max_length=255)


class ProductUpdate(BaseModel):
    """编辑本地商品。"""

    spu_name: str | None = Field(default=None, max_length=255)
    category_name: str | None = Field(default=None, max_length=64)
    brand: str | None = Field(default=None, max_length=64)
    unit: str | None = Field(default=None, max_length=16)
    status: int | None = None
    remark: str | None = Field(default=None, max_length=255)


class SkuCreate(BaseModel):
    """在某 SPU 下新增 SKU。"""

    sku_code: str = Field(..., max_length=64)
    sku_name: str = Field(..., max_length=255)
    spec_desc: str | None = Field(default=None, max_length=255)
    cost_price: float = 0
    sale_price: float = 0
    status: int = 1


class SkuUpdate(BaseModel):
    """编辑 SKU。"""

    sku_name: str | None = Field(default=None, max_length=255)
    spec_desc: str | None = Field(default=None, max_length=255)
    cost_price: float | None = None
    sale_price: float | None = None
    status: int | None = None


class SkuMappingCreate(BaseModel):
    """新增 SKU 映射（平台 SKU → 本地 SKU，以本地 SKU 编码指定）。"""

    shop_id: int
    platform_code: str | None = Field(default=None, max_length=32)
    platform_sku_id: str = Field(..., max_length=64)
    platform_sku_name: str | None = Field(default=None, max_length=255)
    sku_code: str = Field(..., max_length=64)
    sku_id: int | None = Field(default=None, description="兼容字段，可不传，按 sku_code 解析")
    status: int = 1
    remark: str | None = Field(default=None, max_length=255)


class SkuMappingUpdate(BaseModel):
    """编辑 SKU 映射。"""

    platform_sku_name: str | None = Field(default=None, max_length=255)
    sku_code: str | None = Field(default=None, max_length=64)
    sku_id: int | None = None
    status: int | None = None
    remark: str | None = Field(default=None, max_length=255)


class SkuMappingBatchItem(BaseModel):
    """批量映射项（店铺在顶层，此处不含 shop_id）。"""

    platform_sku_id: str = Field(..., max_length=64)
    platform_sku_name: str | None = Field(default=None, max_length=255)
    sku_code: str = Field(..., max_length=64)
    remark: str | None = Field(default=None, max_length=255)


class SkuMappingBatchRequest(BaseModel):
    """批量维护映射入参（按 (shop_id, platform_sku_id) 覆盖）。"""

    shop_id: int
    platform_code: str | None = Field(default=None, max_length=32)
    items: list[SkuMappingBatchItem] = Field(..., description="批量映射项")


class SkuMappingImportRow(BaseModel):
    """导入映射行（供 CSV 解析后传入服务层，以本地 SKU 编码建立映射）。"""

    shop_id: int
    platform_code: str | None = Field(default=None, max_length=32)
    platform_sku_id: str = Field(..., max_length=64)
    sku_code: str = Field(..., max_length=64)
    platform_sku_name: str | None = Field(default=None, max_length=255)
