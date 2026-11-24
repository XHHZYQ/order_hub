"""订单域 Schema（M2 / M3）。"""

from decimal import Decimal

from pydantic import BaseModel, Field


class OrderSyncRequest(BaseModel):
    """手动同步 / 手动补单入参。"""

    shop_id: int | None = Field(default=None, description="店铺 ID，为空表示全部启用且已授权店铺")
    start_time: str | None = Field(default=None, description="开始时间 YYYY-MM-DD HH:mm:ss")
    end_time: str | None = Field(default=None, description="结束时间 YYYY-MM-DD HH:mm:ss")


class OrderErrorHandleRequest(BaseModel):
    """同步异常人工处理入参。"""

    note: str | None = Field(default=None, max_length=500, description="处理备注")


# --------------------------------------------------------------------------- #
# M3 订单处理
# --------------------------------------------------------------------------- #
class OrderAuditRequest(BaseModel):
    """单条审核入参。"""

    action: str = Field(description="审核动作：PASS 通过 / REJECT 驳回")
    reason: str | None = Field(default=None, max_length=255, description="审核意见")


class OrderBatchAuditRequest(BaseModel):
    """批量审核入参。"""

    order_ids: list[int] = Field(min_length=1, description="订单 ID 列表")
    action: str = Field(description="审核动作：PASS / REJECT")
    reason: str | None = Field(default=None, max_length=255, description="审核意见")


class OrderPriceRequest(BaseModel):
    """改价入参（仅传入需要修改的金额字段）。"""

    goods_amount: Decimal | None = Field(default=None, ge=0, description="商品金额")
    discount_amount: Decimal | None = Field(default=None, ge=0, description="优惠金额")
    freight_amount: Decimal | None = Field(default=None, ge=0, description="运费")
    pay_amount: Decimal | None = Field(default=None, ge=0, description="实付金额")
    reason: str | None = Field(default=None, max_length=255, description="改价原因")


class OrderAddressRequest(BaseModel):
    """修改收货地址入参（仅传入需要修改的字段）。"""

    receiver_name: str | None = Field(default=None, max_length=64)
    receiver_phone: str | None = Field(default=None, max_length=32)
    receiver_province: str | None = Field(default=None, max_length=32)
    receiver_city: str | None = Field(default=None, max_length=32)
    receiver_district: str | None = Field(default=None, max_length=32)
    receiver_address: str | None = Field(default=None, max_length=255)
    reason: str | None = Field(default=None, max_length=255, description="改址原因")


class OrderRemarkRequest(BaseModel):
    """添加备注/打标入参。"""

    merchant_remark: str | None = Field(default=None, max_length=500, description="商家备注")
    buyer_remark: str | None = Field(default=None, max_length=500, description="买家留言")
    tags: list[str] | None = Field(default=None, description="标签列表（整体覆盖）")
    append: bool = Field(default=True, description="商家备注是否追加（默认追加）")


class OrderBatchRemarkRequest(OrderRemarkRequest):
    """批量备注/打标入参。"""

    order_ids: list[int] = Field(min_length=1, description="订单 ID 列表")


class OrderBatchIdsRequest(BaseModel):
    """仅含订单 ID 列表的批量操作入参。"""

    order_ids: list[int] = Field(min_length=1, description="订单 ID 列表")
    remark: str | None = Field(default=None, max_length=255, description="操作备注")


class OrderMergeRequest(OrderBatchIdsRequest):
    """订单合并入参。"""


class OrderSplitItem(BaseModel):
    """拆分方案中的一条明细。"""

    item_id: int = Field(description="订单明细 ID")
    quantity: int = Field(ge=1, description="拆分数量")


class OrderSplitPart(BaseModel):
    """一个拆分子单。"""

    items: list[OrderSplitItem] = Field(min_length=1, description="该子单包含的明细")


class OrderSplitRequest(BaseModel):
    """订单拆分为多个子订单入参。"""

    parts: list[OrderSplitPart] = Field(min_length=2, description="拆分方案（≥2 个部分）")
    remark: str | None = Field(default=None, max_length=255, description="拆分原因")


class OrderStatusChangeRequest(BaseModel):
    """订单状态流转入参。"""

    to_status: str = Field(description="目标状态")
    remark: str | None = Field(default=None, max_length=255, description="流转备注")
