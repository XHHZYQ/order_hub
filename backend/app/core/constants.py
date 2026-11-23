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

# 订单统一状态（见《数据库设计》6.3 / 7.2）
ORDER_STATUS: dict[str, str] = {
    "PENDING_PAY": "待付款",
    "PENDING_AUDIT": "待审核",
    "PENDING_SHIP": "待发货",
    "PART_SHIPPED": "部分发货",
    "SHIPPED": "已发货",
    "FINISHED": "已完成",
    "CLOSED": "已关闭",
    "AFTER_SALE": "售后中",
}

# 订单来源
ORDER_SOURCE = {"PLATFORM": "平台", "MANUAL": "手工"}

# 订单同步类型标识
ORDER_SYNC_TYPE = "ORDER"

# 平台原始状态 → 统一状态码（键为平台编码，见《数据库设计》7.2）
ORDER_STATUS_MAP: dict[str, dict[str, str]] = {
    "TAOBAO": {
        "WAIT_BUYER_PAY": "PENDING_PAY",
        "PAID": "PENDING_AUDIT",
        "WAIT_SELLER_SEND_GOODS": "PENDING_SHIP",
        "PART_SENT": "PART_SHIPPED",
        "WAIT_BUYER_CONFIRM_GOODS": "SHIPPED",
        "TRADE_FINISHED": "FINISHED",
        "TRADE_CLOSED": "CLOSED",
        "REFUNDING": "AFTER_SALE",
    },
    "JD": {
        "WAIT_PAY": "PENDING_PAY",
        "PAID": "PENDING_AUDIT",
        "WAIT_SHIP": "PENDING_SHIP",
        "PART_SENT": "PART_SHIPPED",
        "SHIPPED": "SHIPPED",
        "FINISHED": "FINISHED",
        "CLOSED": "CLOSED",
        "REFUNDING": "AFTER_SALE",
    },
    "PDD": {
        "待支付": "PENDING_PAY",
        "已支付": "PENDING_AUDIT",
        "待发货": "PENDING_SHIP",
        "部分发货": "PART_SHIPPED",
        "已发货": "SHIPPED",
        "已完成": "FINISHED",
        "已关闭": "CLOSED",
        "售后中": "AFTER_SALE",
    },
    "DOUYIN": {
        "待支付": "PENDING_PAY",
        "已支付": "PENDING_AUDIT",
        "待发货": "PENDING_SHIP",
        "部分发货": "PART_SHIPPED",
        "已发货": "SHIPPED",
        "已完成": "FINISHED",
        "已关闭": "CLOSED",
        "售后中": "AFTER_SALE",
    },
    "SELF": {
        "pending_pay": "PENDING_PAY",
        "paid": "PENDING_AUDIT",
        "wait_ship": "PENDING_SHIP",
        "part_sent": "PART_SHIPPED",
        "shipped": "SHIPPED",
        "finished": "FINISHED",
        "closed": "CLOSED",
        "after_sale": "AFTER_SALE",
    },
}

# 操作日志所属模块
LOG_MODULES = {
    "AUTH": "登录认证",
    "USER": "用户管理",
    "ROLE": "角色管理",
    "PERMISSION": "权限管理",
    "PLATFORM": "平台管理",
    "SHOP": "店铺管理",
    "SYNC": "同步任务",
    "ORDER": "订单管理",
}
