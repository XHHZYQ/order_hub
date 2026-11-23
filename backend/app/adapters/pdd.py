"""拼多多（PDD）平台适配器。字段/状态映射见《数据库设计》7.1 / 7.2。"""

from app.adapters.base import PlatformAdapter
from app.core.constants import ORDER_STATUS_MAP
from app.simulator import seed


class PddAdapter(PlatformAdapter):
    platform_code = "PDD"
    field_map = seed.ORDER_FIELD_MAP["PDD"]
    item_field_map = seed.ITEM_FIELD_MAP["PDD"]
    status_map = ORDER_STATUS_MAP["PDD"]
    ext_fields = seed.EXT_FIELD_MAP["PDD"]
