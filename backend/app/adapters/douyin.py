"""抖音电商（DOUYIN）平台适配器。字段/状态映射见《数据库设计》7.1 / 7.2。"""

from app.adapters.base import PlatformAdapter
from app.core.constants import ORDER_STATUS_MAP
from app.simulator import seed


class DouyinAdapter(PlatformAdapter):
    platform_code = "DOUYIN"
    field_map = seed.ORDER_FIELD_MAP["DOUYIN"]
    item_field_map = seed.ITEM_FIELD_MAP["DOUYIN"]
    status_map = ORDER_STATUS_MAP["DOUYIN"]
    ext_fields = seed.EXT_FIELD_MAP["DOUYIN"]
