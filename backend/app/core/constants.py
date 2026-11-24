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
SYNC_TYPES = ["ORDER", "INVENTORY", "AFTER_SALE", "TRACE"]

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

# 库存变动类型（inventory_flow.flow_type，见《数据库设计》6.3）
INVENTORY_FLOW_TYPE: dict[str, str] = {
    "PURCHASE_IN": "采购入库",
    "ORDER_OCCUPY": "订单占用",
    "ORDER_RELEASE": "订单释放",
    "SHIP_DEDUCT": "发货扣减",
    "RETURN_IN": "退货入库",
    "STOCKTAKE": "盘点调整",
}

# 库存流水来源类型（inventory_flow.source_type）
INVENTORY_SOURCE_TYPE: dict[str, str] = {
    "ORDER": "订单",
    "STOCKTAKE": "盘点",
    "PURCHASE": "采购",
}

# 库存状态
INVENTORY_STATUS: dict[int, str] = {1: "正常", 0: "停用"}

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
    "PRODUCT": "商品管理",
    "MAPPING": "SKU映射",
    "INVENTORY": "库存管理",
    "SHIPMENT": "发货履约",
    "AFTER_SALE": "售后管理",
}

# --------------------------------------------------------------------------- #
# M3 订单处理
# --------------------------------------------------------------------------- #
# 订单可打标标签（FR-03-04）
ORDER_TAG_OPTIONS = ["急单", "需核验", "大客户", "预售", "补发", "高价值"]

# 审核动作 → 目标状态（FR-03-01）
AUDIT_ACTIONS = {"PASS": "审核通过", "REJECT": "审核驳回"}

# 订单变更类型（order_change.change_type）
ORDER_CHANGE_TYPE = {
    "AUDIT": "审核",
    "PRICE": "改价",
    "ADDRESS": "改址",
    "REMARK": "备注",
    "TAG": "打标",
    "STATUS": "状态",
    "MERGE": "合并",
    "SPLIT": "拆分",
    "SHIP": "发货",
}

# 状态机：合法流转（key 当前状态 → 允许流转到的状态集合，见《数据库设计》7.2）
ORDER_STATUS_FLOW: dict[str, set[str]] = {
    "PENDING_PAY": {"PENDING_AUDIT", "CLOSED"},
    "PENDING_AUDIT": {"PENDING_SHIP", "CLOSED"},
    "PENDING_SHIP": {"PART_SHIPPED", "SHIPPED", "AFTER_SALE", "CLOSED"},
    "PART_SHIPPED": {"SHIPPED", "AFTER_SALE"},
    "SHIPPED": {"FINISHED", "AFTER_SALE"},
    "AFTER_SALE": {"SHIPPED", "FINISHED", "CLOSED"},
    "FINISHED": set(),
    "CLOSED": set(),
}

# --------------------------------------------------------------------------- #
# M6 发货与物流
# --------------------------------------------------------------------------- #
# 发货单物流状态（shipment.status）
SHIPMENT_STATUS: dict[str, str] = {
    "SHIPPED": "已发货",
    "IN_TRANSIT": "运输中",
    "SIGNED": "已签收",
    "ABNORMAL": "异常",
}

# 发货单回写平台状态（shipment.push_status）
PUSH_STATUS: dict[int, str] = {0: "待回写", 1: "成功", 2: "失败"}

# 打印状态
PRINT_STATUS: dict[int, str] = {0: "未打印", 1: "已打印"}

# 物流轨迹节点状态（logistics_trace.trace_status）
TRACE_STATUS: dict[str, str] = {
    "COLLECTED": "已揽收",
    "IN_TRANSIT": "运输中",
    "ARRIVED": "到达网点",
    "DELIVERING": "派送中",
    "SIGNED": "已签收",
    "ABNORMAL": "异常",
}

# 物流异常预警原因（FR-06-06）
LOGISTICS_ALERT_REASON = "物流长时间无更新（超 48 小时未揽收/未更新轨迹）"

# --------------------------------------------------------------------------- #
# M7 售后管理
# --------------------------------------------------------------------------- #
# 售后类型（after_sale.type）
AFTER_SALE_TYPE: dict[str, str] = {
    "REFUND": "退款",
    "RETURN_REFUND": "退货退款",
    "EXCHANGE": "换货",
}

# 统一售后状态（after_sale.status）
AFTER_SALE_STATUS: dict[str, str] = {
    "PENDING": "待处理",
    "PROCESSING": "处理中",
    "WAIT_BUYER": "等待买家",
    "WAIT_SELLER": "等待商家",
    "FINISHED": "已完成",
    "CLOSED": "已关闭",
}

# 退款状态（after_sale.refund_status）
REFUND_STATUS: dict[str, str] = {
    "NONE": "无需退款",
    "PENDING": "退款中",
    "SUCCESS": "退款成功",
    "FAILED": "退款失败",
}

# 售后处理动作（after_sale_log.action，FR-07-02）
AFTER_SALE_ACTIONS = ["同意", "拒绝", "协商", "退款", "备注", "同步", "退货入库"]

# --------------------------------------------------------------------------- #
# M8 财务对账
# --------------------------------------------------------------------------- #
# 账单对账状态（bill.reconcile_status）
BILL_RECONCILE_STATUS: dict[str, str] = {
    "PENDING": "待对账",
    "MATCHING": "对账中",
    "RECONCILED": "已对账",
    "CLOSED": "已封账",
}

# 账单明细匹配状态（bill_detail.match_status）
BILL_MATCH_STATUS: dict[str, str] = {
    "MATCHED": "已匹配",
    "AMOUNT_DIFF": "金额不一致",
    "UNMATCHED": "未匹配",
}

# 差异类型（reconcile_diff.diff_type）
RECONCILE_DIFF_TYPE: dict[str, str] = {
    "LOCAL_MISSING": "本地无单",
    "BILL_MISSING": "账单无单",
    "AMOUNT_DIFF": "金额不一致",
}

# 差异处理状态（reconcile_diff.handle_status）
DIFF_HANDLE_STATUS: dict[str, str] = {
    "PENDING": "待处理",
    "HANDLED": "已处理",
}

# 账单导入支持的文件扩展名
BILL_FILE_EXT = [".csv", ".xlsx"]

# --------------------------------------------------------------------------- #
# M9 数据看板
# --------------------------------------------------------------------------- #
# 下钻指标类型（/dashboard/drill-down）
DRILL_METRICS: dict[str, str] = {
    "order": "订单",
    "product": "商品",
    "after_sale": "售后单",
    "inventory_alert": "库存预警",
}
