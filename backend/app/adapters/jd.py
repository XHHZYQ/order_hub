"""京东（JD）平台适配器。字段/状态映射见《数据库设计》7.1 / 7.2。"""

from app.adapters.base import PlatformAdapter
from app.core.constants import ORDER_STATUS_MAP
from app.simulator import seed


class JdAdapter(PlatformAdapter):
    platform_code = "JD"
    field_map = seed.ORDER_FIELD_MAP["JD"]
    item_field_map = seed.ITEM_FIELD_MAP["JD"]
    status_map = ORDER_STATUS_MAP["JD"]
    ext_fields = seed.EXT_FIELD_MAP["JD"]
