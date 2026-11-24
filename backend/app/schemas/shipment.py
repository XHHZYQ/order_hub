"""发货与物流域 Schema（M6）。"""

from pydantic import BaseModel, Field


class WaybillRequest(BaseModel):
    """获取电子面单入参（单个/批量，FR-06-02）。

    单个：传 order_id；批量：传 order_ids。
    """

    order_id: int | None = Field(default=None, description="订单 ID（单个取面单）")
    order_ids: list[int] | None = Field(default=None, description="订单 ID 列表（批量取面单）")
    logistics_company_code: str | None = Field(default=None, description="指定物流公司编码，为空则随机分配")


class ShipmentItem(BaseModel):
    """发货明细。"""

    item_id: int = Field(description="订单明细 ID")
    quantity: int = Field(ge=1, description="本次发货数量")


class ShipmentCreateRequest(BaseModel):
    """发货入参（录入物流公司与运单号并回传平台，FR-06-04）。"""

    order_id: int = Field(description="订单 ID")
    logistics_company_code: str | None = Field(default=None, description="物流公司编码")
    waybill_no: str | None = Field(default=None, max_length=64, description="运单号，为空则自动生成")
    face_sheet_no: str | None = Field(default=None, max_length=64, description="电子面单号")
    package_no: str | None = Field(default=None, max_length=32, description="包裹号")
    items: list[ShipmentItem] | None = Field(default=None, description="本次发货明细，为空则按订单未发数量整单发货")


class BatchShipmentRequest(BaseModel):
    """批量发货入参（FR-06-04）。"""

    order_ids: list[int] = Field(min_length=1, description="订单 ID 列表")
    logistics_company_code: str | None = Field(default=None, description="物流公司编码，为空则逐单随机分配")


class PrintRequest(BaseModel):
    """批量打单入参（FR-06-03）。"""

    order_ids: list[int] = Field(min_length=1, description="订单 ID 列表")
    logistics_company_code: str | None = Field(default=None, description="指定物流公司编码，为空则随机分配")
