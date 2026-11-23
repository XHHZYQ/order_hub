"""适配器工厂：按平台编码返回对应的模拟平台适配器。"""

from app.adapters.base import PlatformAdapter
from app.adapters.douyin import DouyinAdapter
from app.adapters.jd import JdAdapter
from app.adapters.pdd import PddAdapter
from app.adapters.selfmall import SelfMallAdapter
from app.adapters.taobao import TaobaoAdapter
from app.core.exceptions import param_error

_ADAPTERS: dict[str, type[PlatformAdapter]] = {
    TaobaoAdapter.platform_code: TaobaoAdapter,
    JdAdapter.platform_code: JdAdapter,
    PddAdapter.platform_code: PddAdapter,
    DouyinAdapter.platform_code: DouyinAdapter,
    SelfMallAdapter.platform_code: SelfMallAdapter,
}


def get_adapter(platform_code: str) -> PlatformAdapter:
    """返回平台适配器实例；未知平台抛参数异常。"""
    adapter_cls = _ADAPTERS.get((platform_code or "").upper())
    if adapter_cls is None:
        raise param_error(f"不支持的平台编码：{platform_code}")
    return adapter_cls()
