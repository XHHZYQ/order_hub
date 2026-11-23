"""订单域 Schema（M2）。"""

from pydantic import BaseModel, Field


class OrderSyncRequest(BaseModel):
    """手动同步 / 手动补单入参。"""

    shop_id: int | None = Field(default=None, description="店铺 ID，为空表示全部启用且已授权店铺")
    start_time: str | None = Field(default=None, description="开始时间 YYYY-MM-DD HH:mm:ss")
    end_time: str | None = Field(default=None, description="结束时间 YYYY-MM-DD HH:mm:ss")


class OrderErrorHandleRequest(BaseModel):
    """同步异常人工处理入参。"""

    note: str | None = Field(default=None, max_length=500, description="处理备注")
