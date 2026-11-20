"""通用 Schema。"""

from pydantic import BaseModel, Field


class StatusRequest(BaseModel):
    """通用状态变更请求：1 启用 / 0 停用。"""

    status: int = Field(..., description="1 启用 / 0 停用")
