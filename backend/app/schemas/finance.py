"""M8 财务对账：请求/响应模型。"""

from pydantic import BaseModel, Field


class DiffHandleRequest(BaseModel):
    """差异处理入参（FR-08-03）。"""

    action: str | None = Field(default="确认", max_length=16, description="处理动作：确认 / 忽略")
    handle_remark: str | None = Field(default=None, max_length=255, description="处理说明")
