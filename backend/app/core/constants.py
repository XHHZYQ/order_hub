"""常量与字典：业务错误码、状态、类型等。"""


class BizCode:
    """业务码（见《接口设计》2.4）。"""

    SUCCESS = 0
    PARAM_ERROR = 1001
    UNAUTHORIZED = 1002
    FORBIDDEN = 1003
    NOT_FOUND = 1004
    DUPLICATE = 2001
    STATUS_NOT_ALLOWED = 2002
    STOCK_NOT_ENOUGH = 2003
    PLATFORM_PUSH_FAILED = 2004
    BILL_CLOSED = 2005
    FILE_PARSE_ERROR = 3001
    DB_ERROR = 5001
    UNKNOWN = 9999


class Status:
    """通用启停状态：1 启用 / 0 停用。"""

    ENABLED = 1
    DISABLED = 0


# 平台编码（固定 5 个，见《数据库设计》6.1）
PLATFORM_CODES = ["TAOBAO", "JD", "PDD", "DOUYIN", "SELF"]

# 同步类型
SYNC_TYPES = ["ORDER", "INVENTORY", "AFTER_SALE"]

# 同步日志状态
SYNC_STATUS = {
    "PENDING": "待执行",
    "RUNNING": "执行中",
    "SUCCESS": "成功",
    "PART_FAILED": "部分失败",
    "FAILED": "失败",
}

# 触发方式
TRIGGER_TYPES = {"SCHEDULED": "定时", "MANUAL": "手动"}

# 授权状态
AUTH_STATUS = {"AUTHORIZED": 1, "UNAUTHORIZED": 0}

# 权限类型
PERM_TYPES = {"MENU": "菜单", "BUTTON": "按钮"}

# 操作日志所属模块
LOG_MODULES = {
    "AUTH": "登录认证",
    "USER": "用户管理",
    "ROLE": "角色管理",
    "PERMISSION": "权限管理",
    "PLATFORM": "平台管理",
    "SHOP": "店铺管理",
    "SYNC": "同步任务",
}
