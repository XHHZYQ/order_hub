"""淘宝（TAOBAO）平台适配器。字段/状态映射见《数据库设计》7.1 / 7.2。"""

from app.adapters.base import PlatformAdapter
from app.core.constants import ORDER_STATUS_MAP
from app.simulator import seed


class TaobaoAdapter(PlatformAdapter):
    platform_code = "TAOBAO"
    field_map = seed.ORDER_FIELD_MAP["TAOBAO"]
    item_field_map = seed.ITEM_FIELD_MAP["TAOBAO"]
    status_map = ORDER_STATUS_MAP["TAOBAO"]
    ext_fields = seed.EXT_FIELD_MAP["TAOBAO"]
