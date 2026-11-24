"""售后管理域 Schema（M7）。"""

from decimal import Decimal

from pydantic import BaseModel, Field


class AfterSaleSyncRequest(BaseModel):
    """手动同步售后申请入参（FR-07-01）。"""

    shop_id: int | None = Field(default=None, description="店铺 ID，为空表示全部启用且已授权店铺")


class AfterSaleHandleRequest(BaseModel):
    """售后处理入参（同意/拒绝/协商/备注，FR-07-02）。

    action 取值：同意 / 拒绝 / 协商 / 备注 / 退货入库。
    """

    action: str = Field(description="处理动作：同意 / 拒绝 / 协商 / 备注 / 退货入库")
    content: str | None = Field(default=None, max_length=500, description="处理说明")
    refund_amount: Decimal | None = Field(default=None, ge=0, description="退款金额（同意退款时可选）")
    goods_returned: bool | None = Field(default=None, description="是否已收到退货（退货入库时使用）")


class AfterSaleRefundRequest(BaseModel):
    """同步退款金额与状态入参（FR-07-03）。"""

    refund_amount: Decimal | None = Field(default=None, ge=0, description="退款金额")
    refund_status: str | None = Field(default=None, description="退款状态：PENDING/SUCCESS/FAILED")
    remark: str | None = Field(default=None, max_length=500, description="备注")
