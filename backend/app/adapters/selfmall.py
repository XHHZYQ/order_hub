"""自有商城（SELF）平台适配器。字段/状态映射见《数据库设计》7.1 / 7.2。"""

from app.adapters.base import PlatformAdapter
from app.core.constants import ORDER_STATUS_MAP
from app.simulator import seed


class SelfMallAdapter(PlatformAdapter):
    platform_code = "SELF"
    field_map = seed.ORDER_FIELD_MAP["SELF"]
    item_field_map = seed.ITEM_FIELD_MAP["SELF"]
    status_map = ORDER_STATUS_MAP["SELF"]
    ext_fields = seed.EXT_FIELD_MAP["SELF"]
