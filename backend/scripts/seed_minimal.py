"""最小演示数据（幂等、可重复执行，固定随机种子）。

用法（在 backend 目录下）：
    uv run python scripts/seed_minimal.py

覆盖表：platform / shop / role / permission / role_permission / user / user_role /
role_shop / sync_task / sync_log / operation_log /
product / sku / platform_product / platform_sku / sku_mapping /
inventory / inventory_flow / inventory_share / inventory_alert /
orders / order_item / order_ext / order_log / order_change
"""

import pathlib
import random
import sys
from datetime import datetime, timedelta
from decimal import Decimal

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from sqlmodel import Session, delete  # noqa: E402

from app.core.constants import ORDER_STATUS_MAP  # noqa: E402
from app.core.database import engine  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models.order import (  # noqa: E402
    Order,
    OrderChange,
    OrderExt,
    OrderItem,
    OrderLog,
)
from app.models.inventory import (  # noqa: E402
    Inventory,
    InventoryAlert,
    InventoryFlow,
    InventoryShare,
)
from app.models.platform import Platform, Shop, SyncLog, SyncTask  # noqa: E402
from app.models.product import (  # noqa: E402
    PlatformProduct,
    PlatformSku,
    Product,
    Sku,
    SkuMapping,
)
from app.models.system import (  # noqa: E402
    OperationLog,
    Permission,
    Role,
    RolePermission,
    RoleShop,
    User,
    UserRole,
)
from app.simulator import seed  # noqa: E402
from app.utils.datetime_util import now_utc  # noqa: E402

random.seed(20260101)

DEFAULT_PASSWORD = "123456"

# --------------------------------------------------------------------------- #
# 静态定义
# --------------------------------------------------------------------------- #
PLATFORMS = [
    ("TAOBAO", "淘宝", "platform-taobao", 1),
    ("JD", "京东", "platform-jd", 2),
    ("PDD", "拼多多", "platform-pdd", 3),
    ("DOUYIN", "抖音电商", "platform-douyin", 4),
    ("SELF", "自有商城", "platform-self", 5),
]

# (platform_code, shop_code, shop_name, seller_account, auth_status, status)
SHOPS = [
    ("TAOBAO", "TB001", "优选旗舰店", "yvxuan_tb", 1, 1),
    ("TAOBAO", "TB002", "品质生活馆", "pzsh_tb", 1, 1),
    ("JD", "JD001", "京东自营优选", "jd_yx", 1, 1),
    ("JD", "JD002", "数码专营店", "jd_sm", 0, 0),
    ("PDD", "PDD001", "拼团好物", "pdd_pt", 1, 1),
    ("PDD", "PDD002", "实惠百货", "pdd_sh", 1, 0),
    ("DOUYIN", "DY001", "抖音直播优选", "dy_zb", 1, 1),
    ("DOUYIN", "DY002", "潮流精选", "dy_cl", 0, 0),
    ("SELF", "SELF001", "官方商城", "self_official", 1, 1),
    ("SELF", "SELF002", "会员专享店", "self_vip", 1, 1),
]

ROLES = [
    ("SUPER_ADMIN", "超级管理员", "拥有全部功能与数据权限"),
    ("OPERATION", "运营专员", "订单/履约/商品运营"),
    ("CUSTOMER_SERVICE", "客服", "售后与订单处理"),
    ("WAREHOUSE", "仓管", "库存与发货履约"),
    ("FINANCE", "财务", "对账与结算"),
    ("VIEWER", "只读用户", "仅可查看"),
]

# 一级菜单：(code, name, route, icon, sort)
MENUS = [
    ("dashboard", "数据看板", "/dashboard", "DataLine", 1),
    ("order", "订单中心", "/order", "Tickets", 2),
    ("shipment", "发货履约", "/shipment", "Van", 3),
    ("product", "商品与库存", "/product", "Goods", 4),
    ("finance", "财务对账", "/finance", "Money", 5),
    ("platform", "平台与店铺", "/platform", "Shop", 6),
    ("system", "系统管理", "/system", "Setting", 7),
]

# 页面：(code, name, parent, route, sort)
PAGES = [
    ("dashboard:overview", "经营总览", "dashboard", "/dashboard/overview", 1),
    ("dashboard:channel", "渠道与店铺对比", "dashboard", "/dashboard/channel", 2),
    ("dashboard:product", "商品销售分析", "dashboard", "/dashboard/product", 3),
    ("dashboard:fulfillment", "订单与履约分析", "dashboard", "/dashboard/fulfillment", 4),
    ("dashboard:after_sale", "售后分析", "dashboard", "/dashboard/after-sale", 5),
    ("dashboard:inventory", "库存分析", "dashboard", "/dashboard/inventory", 6),
    ("order:list", "订单列表", "order", "/order/list", 1),
    ("order:detail", "订单详情", "order", "/order/detail", 2),
    ("order:abnormal", "异常订单池", "order", "/order/abnormal", 3),
    ("order:after_sale", "售后管理", "order", "/after-sale/list", 4),
    ("shipment:pending", "待发货列表", "shipment", "/shipment/pending", 1),
    ("shipment:ship", "打单发货", "shipment", "/shipment/ship", 2),
    ("shipment:list", "发货记录", "shipment", "/shipment/list", 3),
    ("shipment:alert", "物流异常", "shipment", "/shipment/alert", 4),
    ("product:list", "本地商品", "product", "/product/list", 1),
    ("product:platform", "平台商品", "product", "/product/platform", 2),
    ("product:mapping", "SKU 映射", "product", "/product/mapping", 3),
    ("inventory:list", "库存管理", "product", "/inventory/list", 4),
    ("inventory:flow", "库存流水", "product", "/inventory/flow", 5),
    ("inventory:share", "库存共享", "product", "/inventory/share", 6),
    ("inventory:alert", "库存预警", "product", "/inventory/alert", 7),
    ("inventory:stocktake", "库存盘点", "product", "/inventory/stocktake", 8),
    ("finance:bill", "账单导入", "finance", "/finance/bill", 1),
    ("finance:difference", "对账差异", "finance", "/finance/difference", 2),
    ("finance:settlement", "结算汇总", "finance", "/finance/settlement", 3),
    ("finance:profit", "毛利分析", "finance", "/finance/profit", 4),
    ("platform:list", "平台管理", "platform", "/platform/list", 1),
    ("shop:list", "店铺管理", "platform", "/platform/shop", 2),
    ("sync:task_list", "同步任务", "platform", "/platform/sync-task", 3),
    ("sync:log_list", "同步日志", "platform", "/platform/sync-log", 4),
    ("user:list", "用户管理", "system", "/system/user", 1),
    ("role:list", "角色管理", "system", "/system/role", 2),
    ("log:list", "操作日志", "system", "/system/log", 3),
]

# 按钮：(code, name, parent, sort)
BUTTONS = [
    ("user:create", "新增用户", "user:list", 1),
    ("user:edit", "编辑用户", "user:list", 2),
    ("user:delete", "删除用户", "user:list", 3),
    ("user:status", "启用/停用", "user:list", 4),
    ("user:reset_pwd", "重置密码", "user:list", 5),
    ("role:create", "新增角色", "role:list", 1),
    ("role:edit", "编辑角色", "role:list", 2),
    ("role:delete", "删除角色", "role:list", 3),
    ("role:permission", "分配功能权限", "role:list", 4),
    ("role:data_scope", "配置数据权限", "role:list", 5),
    ("log:export", "导出日志", "log:list", 1),
    ("platform:create", "新增平台", "platform:list", 1),
    ("platform:edit", "编辑平台", "platform:list", 2),
    ("platform:delete", "删除平台", "platform:list", 3),
    ("platform:status", "启用/停用", "platform:list", 4),
    ("shop:create", "新增店铺", "shop:list", 1),
    ("shop:edit", "编辑店铺", "shop:list", 2),
    ("shop:delete", "删除店铺", "shop:list", 3),
    ("shop:status", "启用/停用", "shop:list", 4),
    ("shop:authorize", "重新授权", "shop:list", 5),
    ("sync:task_create", "新增任务", "sync:task_list", 1),
    ("sync:task_edit", "编辑任务", "sync:task_list", 2),
    ("sync:task_delete", "删除任务", "sync:task_list", 3),
    ("sync:task_status", "启用/停用", "sync:task_list", 4),
    ("sync:trigger", "手动触发", "sync:task_list", 5),
    ("sync:retry", "重试同步", "sync:log_list", 1),
    ("order:audit", "订单审核", "order:list", 1),
    ("order:price", "订单改价", "order:list", 2),
    ("order:address", "修改地址", "order:list", 3),
    ("order:export", "导出订单", "order:list", 4),
    ("order:sync", "同步/补单/异常处理", "order:list", 5),
    ("shipment:batch_ship", "批量发货", "shipment:ship", 1),
    ("inventory:edit", "库存调整", "inventory:list", 1),
    ("inventory:push", "回写平台", "inventory:list", 2),
    ("inventory:share_edit", "编辑共享", "inventory:share", 1),
    ("inventory:alert_edit", "配置预警", "inventory:alert", 1),
    ("product:create", "新增商品", "product:list", 1),
    ("product:edit", "编辑商品", "product:list", 2),
    ("product:delete", "删除商品", "product:list", 3),
    ("mapping:create", "新增映射", "product:mapping", 1),
    ("mapping:edit", "编辑映射", "product:mapping", 2),
    ("mapping:delete", "删除映射", "product:mapping", 3),
    ("mapping:import", "导入映射", "product:mapping", 4),
    ("mapping:export", "导出映射", "product:mapping", 5),
    ("finance:import", "账单导入", "finance:bill", 1),
    ("finance:confirm_diff", "差异确认", "finance:difference", 1),
]

# 用户：(username, real_name, role_code, status, created_days_ago)
USERS = [
    ("admin", "系统管理员", "SUPER_ADMIN", 1, 180),
    ("ops01", "李运营", "OPERATION", 1, 160),
    ("ops02", "王运营", "OPERATION", 0, 150),
    ("cs01", "张客服", "CUSTOMER_SERVICE", 1, 140),
    ("cs02", "赵客服", "CUSTOMER_SERVICE", 1, 120),
    ("wh01", "钱仓管", "WAREHOUSE", 1, 110),
    ("wh02", "孙仓管", "WAREHOUSE", 0, 100),
    ("fin01", "周财务", "FINANCE", 1, 90),
    ("fin02", "吴财务", "FINANCE", 1, 70),
    ("viewer01", "郑访客", "VIEWER", 1, 50),
    ("viewer02", "冯访客", "VIEWER", 0, 30),
]


# --------------------------------------------------------------------------- #
# 工具
# --------------------------------------------------------------------------- #
def days_ago(days: int, jitter_minutes: bool = True) -> datetime:
    minutes = random.randint(0, 24 * 60) if jitter_minutes else 0
    return now_utc() - timedelta(days=days, minutes=minutes)


def _group_menu(code: str) -> str:
    if code.startswith("dashboard"):
        return "dashboard"
    if code.startswith("order"):
        return "order"
    if code.startswith("shipment"):
        return "shipment"
    if code.startswith("product") or code.startswith("inventory"):
        return "product"
    if code.startswith("finance"):
        return "finance"
    if code.startswith("platform") or code.startswith("shop:") or code.startswith("sync:"):
        return "platform"
    return "system"


def with_menus(page_codes: list[str]) -> set[str]:
    codes = set(page_codes)
    for c in page_codes:
        codes.add(_group_menu(c))
    return codes


def clear_tables(session: Session) -> None:
    for model in (
        InventoryFlow,
        InventoryAlert,
        InventoryShare,
        Inventory,
        SkuMapping,
        PlatformSku,
        PlatformProduct,
        Sku,
        Product,
        OrderChange,
        OrderLog,
        OrderExt,
        OrderItem,
        Order,
        OperationLog,
        SyncLog,
        SyncTask,
        Shop,
        Platform,
        RoleShop,
        RolePermission,
        UserRole,
        Permission,
        Role,
        User,
    ):
        session.exec(delete(model))
    session.commit()


# --------------------------------------------------------------------------- #
# 各域数据
# --------------------------------------------------------------------------- #
def seed_platforms(session: Session) -> dict[str, Platform]:
    result: dict[str, Platform] = {}
    for code, name, icon, sort_no in PLATFORMS:
        row = Platform(
            platform_code=code,
            platform_name=name,
            icon=icon,
            sort_no=sort_no,
            status=1,
            remark=f"{name}开放平台",
            created_at=days_ago(200),
        )
        session.add(row)
        result[code] = row
    session.flush()
    return result


def seed_shops(session: Session) -> dict[str, Shop]:
    result: dict[str, Shop] = {}
    for idx, (pcode, scode, sname, seller, auth_status, status) in enumerate(SHOPS):
        row = Shop(
            platform_code=pcode,
            shop_code=scode,
            shop_name=sname,
            seller_account=seller,
            auth_status=auth_status,
            auth_token=f"mock-{scode.lower()}-token" if auth_status == 1 else None,
            contact_name=random.choice(["李经理", "王主管", "赵店长", "钱运营"]),
            contact_phone=f"1{random.choice(['3', '5', '8'])}{random.randint(100000000, 999999999)}",
            status=status,
            remark="演示店铺" if status == 1 else "已停用演示店铺",
            created_at=days_ago(180 - idx * 3),
        )
        session.add(row)
        result[scode] = row
    session.flush()
    return result


def seed_roles(session: Session) -> dict[str, Role]:
    result: dict[str, Role] = {}
    for idx, (code, name, remark) in enumerate(ROLES):
        row = Role(role_code=code, role_name=name, remark=remark, status=1, created_at=days_ago(200 - idx))
        session.add(row)
        result[code] = row
    session.flush()
    return result


def seed_permissions(session: Session) -> tuple[dict[str, Permission], list[str], list[str]]:
    code_map: dict[str, Permission] = {}

    for code, name, route, icon, sort_no in MENUS:
        row = Permission(
            parent_id=0,
            perm_code=code,
            perm_name=name,
            perm_type="菜单",
            route_path=route,
            icon=icon,
            sort_no=sort_no,
        )
        session.add(row)
        code_map[code] = row
    session.flush()

    for code, name, parent, route, sort_no in PAGES:
        row = Permission(
            parent_id=code_map[parent].id,
            perm_code=code,
            perm_name=name,
            perm_type="菜单",
            route_path=route,
            icon=None,
            sort_no=sort_no,
        )
        session.add(row)
        code_map[code] = row
    session.flush()

    for code, name, parent, sort_no in BUTTONS:
        row = Permission(
            parent_id=code_map[parent].id,
            perm_code=code,
            perm_name=name,
            perm_type="按钮",
            route_path=None,
            icon=None,
            sort_no=sort_no,
        )
        session.add(row)
        code_map[code] = row
    session.flush()

    all_codes = [c for c, *_ in MENUS] + [c for c, *_ in PAGES] + [c for c, *_ in BUTTONS]
    page_codes = [c for c, *_ in PAGES]
    return code_map, all_codes, page_codes


def role_permission_codes(page_codes: list[str]) -> dict[str, list[str]]:
    menu_codes = [c for c, *_ in MENUS]
    dash = [c for c in page_codes if c.startswith("dashboard")]
    order_pages = [c for c in page_codes if c.startswith("order")]
    ship_pages = [c for c in page_codes if c.startswith("shipment")]
    prod_pages = [c for c in page_codes if c.startswith(("product", "inventory"))]
    fin_pages = [c for c in page_codes if c.startswith("finance")]
    view_all = menu_codes + page_codes

    return {
        "SUPER_ADMIN": ["*"],
        "OPERATION": sorted(
            set(view_all)
            | {
                "order:audit",
                "order:price",
                "order:address",
                "order:export",
                "order:sync",
                "shipment:batch_ship",
                "inventory:edit",
                "inventory:push",
                "product:create",
                "product:edit",
                "product:delete",
                "mapping:create",
                "mapping:edit",
                "mapping:delete",
                "mapping:import",
                "mapping:export",
                "sync:trigger",
            }
        ),
        "CUSTOMER_SERVICE": sorted(
            with_menus(["dashboard:overview", "order:list", "order:detail", "order:after_sale", "shipment:list", "product:list"])
            | {"order:audit", "order:price", "order:address"}
        ),
        "WAREHOUSE": sorted(
            with_menus(["dashboard:inventory", *ship_pages, *prod_pages])
            | {"shipment:batch_ship", "inventory:edit", "inventory:push", "inventory:share_edit", "inventory:alert_edit"}
        ),
        "FINANCE": sorted(
            with_menus(["dashboard:overview", "order:list", "order:detail", *fin_pages])
            | {"finance:import", "finance:confirm_diff"}
        ),
        "VIEWER": sorted(set(view_all) | set(dash)),
    }


def seed_role_permissions(session: Session, roles: dict[str, Role], code_map: dict[str, Permission], page_codes: list[str]) -> None:
    mapping = role_permission_codes(page_codes)
    for role_code, codes in mapping.items():
        role = roles[role_code]
        if codes == ["*"]:
            targets = list(code_map.values())
        else:
            targets = [code_map[c] for c in codes if c in code_map]
        for perm in targets:
            session.add(RolePermission(role_id=role.id, permission_id=perm.id))
    session.flush()


def seed_users(session: Session, roles: dict[str, Role]) -> dict[str, User]:
    result: dict[str, User] = {}
    pwd = hash_password(DEFAULT_PASSWORD)
    for username, real_name, role_code, status, created in USERS:
        user = User(
            username=username,
            password=pwd,
            real_name=real_name,
            email=f"{username}@order-hub.com",
            phone=f"1{random.choice(['3', '5', '8'])}{random.randint(100000000, 999999999)}",
            status=status,
            last_login_time=days_ago(random.randint(0, 15)) if status == 1 else None,
            created_at=days_ago(created),
        )
        session.add(user)
        session.flush()
        session.add(UserRole(user_id=user.id, role_id=roles[role_code].id))
        result[username] = user
    session.flush()
    return result


def seed_role_shops(session: Session, roles: dict[str, Role], shops: dict[str, Shop]) -> None:
    all_shop_ids = [s.id for s in shops.values()]
    # 客服仅可见部分店铺，其余角色可见全部店铺
    cs_shop_ids = [shops[c].id for c in ("TB001", "JD001", "PDD001") if c in shops]
    scope = {
        "SUPER_ADMIN": all_shop_ids,
        "OPERATION": all_shop_ids,
        "CUSTOMER_SERVICE": cs_shop_ids,
        "WAREHOUSE": all_shop_ids,
        "FINANCE": all_shop_ids,
        "VIEWER": all_shop_ids,
    }
    for role_code, shop_ids in scope.items():
        for sid in shop_ids:
            session.add(RoleShop(role_id=roles[role_code].id, shop_id=sid))
    session.flush()


def seed_sync_tasks(session: Session, shops: dict[str, Shop]) -> list[SyncTask]:
    # (shop_code, sync_type, cron_expr, status, remark)
    plan = [
        ("TB001", "ORDER", "*/10 * * * *", 1, "订单每 10 分钟增量同步"),
        ("TB001", "INVENTORY", "0 */2 * * *", 1, "库存每 2 小时同步"),
        ("JD001", "ORDER", "*/5 * * * *", 1, "订单每 5 分钟同步"),
        ("JD001", "AFTER_SALE", "0 */4 * * *", 0, "售后同步（暂停）"),
        ("PDD001", "ORDER", "*/15 * * * *", 1, "订单每 15 分钟同步"),
        ("DY001", "ORDER", "*/10 * * * *", 1, "直播订单同步"),
        ("DY001", "INVENTORY", "0 */6 * * *", 1, "库存同步"),
        ("SELF001", "AFTER_SALE", "0 */2 * * *", 1, "售后每 2 小时同步"),
        ("SELF002", "INVENTORY", "0 3 * * *", 0, "库存每日同步（暂停）"),
    ]
    tasks: list[SyncTask] = []
    for idx, (scode, stype, cron, status, remark) in enumerate(plan):
        task = SyncTask(
            shop_id=shops[scode].id,
            sync_type=stype,
            cron_expr=cron,
            start_time=days_ago(60 - idx),
            last_sync_time=days_ago(random.randint(0, 3)) if status == 1 else None,
            status=status,
            remark=remark,
            created_at=days_ago(60 - idx),
        )
        session.add(task)
        tasks.append(task)
    session.flush()
    return tasks


def seed_sync_logs(session: Session, tasks: list[SyncTask]) -> None:
    reasons = [
        "平台接口限流，部分订单未拉取",
        "店铺授权过期，请重新授权",
        "网络超时，服务端无响应",
    ]
    for task in tasks:
        for _ in range(random.randint(1, 3)):
            roll = random.random()
            if roll < 0.65:
                status, success, fail, reason = "成功", random.randint(10, 120), 0, None
            elif roll < 0.85:
                status, success, fail, reason = "部分失败", random.randint(5, 60), random.randint(1, 8), reasons[0]
            else:
                status, success, fail, reason = "失败", 0, random.randint(1, 5), random.choice(reasons[1:])
            start = days_ago(random.randint(0, 10))
            cost = random.randint(800, 12000)
            session.add(
                SyncLog(
                    task_id=task.id,
                    shop_id=task.shop_id,
                    sync_type=task.sync_type,
                    start_time=start,
                    end_time=start + timedelta(milliseconds=cost),
                    status=status,
                    success_count=success,
                    fail_count=fail,
                    cost_ms=cost,
                    fail_reason=reason,
                    trigger_type=random.choice(["定时", "手动"]),
                    created_at=start,
                )
            )
    session.flush()


def seed_operation_logs(session: Session, users: dict[str, User]) -> None:
    entries = [
        ("admin", "AUTH", "登录", "用户", "用户登录成功"),
        ("admin", "USER", "新增", "用户", "新增用户 ops01"),
        ("admin", "ROLE", "分配功能权限", "角色", "更新运营专员功能权限"),
        ("ops01", "SHOP", "编辑", "店铺", "编辑店铺 优选旗舰店"),
        ("fin01", "PLATFORM", "启停", "平台", "停用平台 拼多多"),
        ("wh01", "SYNC", "手动触发", "同步任务", "手动触发一次同步"),
        ("cs01", "USER", "重置密码", "用户", "重置用户 cs02 密码"),
        ("admin", "PERMISSION", "配置数据权限", "角色", "更新客服店铺范围"),
    ]
    for idx, (username, module, action, ttype, content) in enumerate(entries):
        user = users[username]
        session.add(
            OperationLog(
                user_id=user.id,
                username=user.username,
                module=module,
                action=action,
                target_type=ttype,
                target_id=str(random.randint(1, 20)),
                content=content,
                ip=f"192.168.1.{random.randint(2, 254)}",
                created_at=days_ago(random.randint(0, 30)),
            )
        )
    session.flush()


ORDER_SEED = 20260202
ANOMALY_REASONS = ["收货地址缺失", "金额校验不一致：商品金额与明细合计不符"]


def _platform_order_no(rng: random.Random, platform_code: str, dt: datetime) -> str:
    """生成各平台形态的原始订单号（贴近真实）。"""
    if platform_code == "TAOBAO":
        return str(rng.randint(10**14, 10**15 - 1))
    if platform_code == "JD":
        return str(rng.randint(10**9, 10**10 - 1))
    if platform_code == "PDD":
        return f"{dt:%y%m%d}-{rng.randint(10**11, 10**12 - 1)}"
    if platform_code == "DOUYIN":
        return str(rng.randint(10**17, 10**18 - 1))
    return f"SN{rng.randint(10**11, 10**12 - 1)}"


def _money(value: float) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"))


def seed_orders(session: Session, shops: dict, mapping_lookup: dict) -> int:
    """生成贴近真实的订单数据（约 300~500 单，覆盖全部平台与店铺，跨度约 60 天）。

    明细的 platform_sku_id 采用确定性编码，可与 sku_mapping 命中；未命中者 is_matched=0。
    mapping_lookup: {(shop_id, platform_sku_id): (sku_id, sku_code)}。
    """
    rng = random.Random(ORDER_SEED)
    now = now_utc()
    used_pnos: set[str] = set()
    seq = 0
    total = 0

    for shop in shops.values():
        platform_code = shop.platform_code
        status_map = ORDER_STATUS_MAP.get(platform_code, {})
        if not status_map:
            continue
        inverse = {v: k for k, v in status_map.items()}
        field_map = seed.ORDER_FIELD_MAP[platform_code]
        ext_fields = seed.EXT_FIELD_MAP[platform_code]
        status_codes = list(seed.STATUS_WEIGHTS)
        status_weights = [seed.STATUS_WEIGHTS[k] for k in status_codes]

        for _ in range(rng.randint(30, 45)):
            seq += 1
            order_time = now - timedelta(
                days=rng.randint(0, 59),
                hours=rng.randint(0, 23),
                minutes=rng.randint(0, 59),
                seconds=rng.randint(0, 59),
            )
            unified = rng.choices(status_codes, weights=status_weights, k=1)[0]
            raw_status = inverse.get(unified, "")
            account, nick = seed.random_buyer(rng, platform_code)
            recv = seed.random_receiver(rng)
            order_no = f"OH{order_time:%Y%m%d}{seq:05d}"

            while True:
                pno = _platform_order_no(rng, platform_code, order_time)
                if pno not in used_pnos:
                    used_pnos.add(pno)
                    break

            # 明细 1~3 条
            items = []
            goods = Decimal("0")
            disc = Decimal("0")
            for _ in range(rng.randint(1, 3)):
                detail = seed.random_product_detail(rng)
                qty = rng.randint(1, 3)
                line_total = _money(detail["price"] * qty)
                line_disc = _money(float(line_total) * rng.choice([0, 0, 0, 0.05, 0.1]))
                items.append(
                    {
                        "platform_sku_id": seed.platform_sku_code(shop.shop_code, detail["spu"], detail["spec_index"]),
                        "platform_sku_name": f"{detail['name']} {detail['spec']}",
                        "outer_sku_code": detail["sku_code"],
                        "product_name": detail["name"],
                        "spec_desc": detail["spec"],
                        "price": _money(detail["price"]),
                        "quantity": qty,
                        "total_amount": line_total,
                        "discount_amount": line_disc,
                        "pay_amount": (line_total - line_disc).quantize(Decimal("0.01")),
                        "local_sku_code": detail["sku_code"],
                    }
                )
                goods += line_total
                disc += line_disc
            freight = _money(rng.choice([0, 0, 0, 8, 12, 15]))
            pay_amount = (goods - disc + freight).quantize(Decimal("0.01"))

            # 异常单
            is_abnormal = 1 if rng.random() < 0.08 else 0
            abnormal_reason = rng.choice(ANOMALY_REASONS) if is_abnormal else None
            address_missing = abnormal_reason == "收货地址缺失"

            # 付款 / 发货 / 完成 / 关闭时间
            paid_at = None
            if unified != "PENDING_PAY":
                paid_at = order_time + timedelta(minutes=rng.randint(1, 180))
            shipped_at = None
            if unified in ("PART_SHIPPED", "SHIPPED", "FINISHED", "AFTER_SALE"):
                shipped_at = (paid_at or order_time) + timedelta(hours=rng.randint(6, 72))
            finished_at = (
                shipped_at + timedelta(days=rng.randint(1, 7))
                if unified == "FINISHED" and shipped_at
                else None
            )
            closed_at = order_time + timedelta(hours=rng.randint(1, 48)) if unified == "CLOSED" else None

            order = Order(
                order_no=order_no,
                platform_code=platform_code,
                shop_id=shop.id,
                platform_order_no=pno,
                buyer_account=account,
                buyer_nick=nick,
                receiver_name=None if address_missing else recv["name"],
                receiver_phone=None if address_missing else recv["phone"],
                receiver_province=None if address_missing else recv["province"],
                receiver_city=None if address_missing else recv["city"],
                receiver_district=None if address_missing else recv["district"],
                receiver_address=None if address_missing else recv["detail"],
                goods_amount=goods,
                discount_amount=disc,
                freight_amount=freight,
                pay_amount=pay_amount,
                status=unified,
                platform_status=raw_status,
                source="平台",
                is_abnormal=is_abnormal,
                abnormal_reason=abnormal_reason,
                merchant_remark=rng.choice([None, None, None, "客户要求尽快发货", "已备注不用发票"]),
                buyer_remark=rng.choice([None, None, "尽快发货，谢谢！", "需要发票", "不要放快递柜"]),
                tags=rng.choice([None, None, None, "加急", "大客户"]),
                order_time=order_time,
                paid_at=paid_at,
                shipped_at=shipped_at,
                finished_at=finished_at,
                closed_at=closed_at,
                sync_time=order_time + timedelta(minutes=rng.randint(1, 30)),
                created_at=order_time,
                updated_at=order_time,
            )
            session.add(order)
            session.flush()

            for item in items:
                matched = mapping_lookup.get((shop.id, item["platform_sku_id"]))
                session.add(
                    OrderItem(
                        order_id=order.id,
                        order_no=order_no,
                        platform_sku_id=item["platform_sku_id"],
                        platform_sku_name=item["platform_sku_name"],
                        outer_sku_code=item["outer_sku_code"],
                        sku_id=matched[0] if matched else None,
                        sku_code=matched[1] if matched else item["local_sku_code"],
                        product_name=item["product_name"],
                        spec_desc=item["spec_desc"],
                        price=item["price"],
                        quantity=item["quantity"],
                        total_amount=item["total_amount"],
                        discount_amount=item["discount_amount"],
                        pay_amount=item["pay_amount"],
                        shipped_quantity=item["quantity"] if shipped_at else 0,
                        refund_quantity=0,
                        is_matched=1 if matched else 0,
                        created_at=order_time,
                    )
                )

            # 平台扩展字段（约 60% 的订单）
            if rng.random() < 0.6:
                for raw_key, cn_name in ext_fields.items():
                    if raw_key == field_map["platform_status"]:
                        value = raw_status
                    elif raw_key == "seller_nick":
                        value = shop.shop_name
                    elif raw_key in ("venderId", "mall_id", "shop_id"):
                        value = str(shop.id)
                    elif raw_key in seed.EXT_VALUE_POOL:
                        value = rng.choice(seed.EXT_VALUE_POOL[raw_key])
                    elif raw_key in ("buyer_message", "buyerMessage", "buyer_remark"):
                        value = order.buyer_remark
                    else:
                        value = None
                    if value:
                        session.add(
                            OrderExt(
                                order_id=order.id,
                                ext_key=raw_key,
                                ext_name=cn_name,
                                ext_value=str(value),
                                created_at=order_time,
                            )
                        )

            # 操作日志：汇聚（全部）+ 异常（异常单）+ 数据变更（约 30%）
            session.add(
                OrderLog(
                    order_id=order.id,
                    order_no=order_no,
                    action="同步",
                    to_status=unified,
                    content="首次汇聚订单",
                    operator="系统",
                    source="系统",
                    created_at=order_time,
                )
            )
            if is_abnormal:
                session.add(
                    OrderLog(
                        order_id=order.id,
                        order_no=order_no,
                        action="同步异常",
                        to_status=unified,
                        content=f"同步校验失败：{abnormal_reason}",
                        operator="系统",
                        source="系统",
                        created_at=order_time + timedelta(minutes=rng.randint(1, 30)),
                    )
                )
            if rng.random() < 0.3:
                change_time = order_time + timedelta(hours=rng.randint(1, 24))
                old_pay = pay_amount
                new_pay = (pay_amount + _money(rng.choice([5, -5, 10]))).quantize(Decimal("0.01"))
                session.add(
                    OrderLog(
                        order_id=order.id,
                        order_no=order_no,
                        action="数据变更",
                        to_status=unified,
                        content="平台数据更新：实付金额",
                        operator="系统",
                        source="系统",
                        created_at=change_time,
                    )
                )
                session.add(
                    OrderChange(
                        order_id=order.id,
                        order_no=order_no,
                        change_type="改价",
                        field_name="pay_amount",
                        before_value=f"{old_pay:.2f}",
                        after_value=f"{new_pay:.2f}",
                        reason="平台侧买家改价",
                        operator="系统",
                        created_at=change_time,
                    )
                )

            total += 1

    session.flush()
    return total


# --------------------------------------------------------------------------- #
# 商品与库存域（M4 / M5）
# --------------------------------------------------------------------------- #
CATEGORY_POOL = [
    "服饰内衣", "服饰内衣", "手机数码", "手机数码", "家居家装", "家居家装", "个护清洁", "鞋靴箱包",
    "鞋靴箱包", "厨具水具", "家居家装", "厨具水具", "手机数码", "手机数码", "手机数码", "家用电器",
    "宠物用品", "个护清洁", "服饰内衣", "汽车用品",
]
BRAND_POOL = ["云选", "优选", "品质", "智选", "佳品"]
UNIT_POOL = [
    "件", "件", "个", "个", "个", "个", "支", "双", "个", "个", "个", "台", "个", "个", "台", "台",
    "袋", "瓶", "条", "个",
]
# 库存流水类型 → (来源类型, 明细标注)，覆盖 6 种变动类型
FLOW_PLAN = [
    ("PURCHASE_IN", "PURCHASE", "采购入库"),
    ("ORDER_OCCUPY", "ORDER", "订单占用"),
    ("ORDER_RELEASE", "ORDER", "订单释放"),
    ("SHIP_DEDUCT", "ORDER", "发货扣减"),
    ("RETURN_IN", "ORDER", "退货入库"),
    ("STOCKTAKE", "STOCKTAKE", "盘点调整"),
]


def seed_products(session: Session) -> tuple[dict[str, Product], dict[str, Sku], list[Sku]]:
    """基于商品池生成本地 SPU 与 SKU。"""
    products: dict[str, Product] = {}
    sku_by_code: dict[str, Sku] = {}
    skus: list[Sku] = []
    for idx, (name, spu, base, specs) in enumerate(seed.PRODUCTS):
        created = days_ago(200 - idx * 2)
        status = 0 if idx % 11 == 7 else 1
        product = Product(
            spu_code=spu,
            spu_name=name,
            category_name=CATEGORY_POOL[idx % len(CATEGORY_POOL)],
            brand=BRAND_POOL[idx % len(BRAND_POOL)],
            unit=UNIT_POOL[idx % len(UNIT_POOL)],
            status=status,
            remark=None,
            created_at=created,
            updated_at=created,
        )
        session.add(product)
        session.flush()
        products[spu] = product
        for si, (spec_desc, delta) in enumerate(specs, start=1):
            sale = _money(base + delta)
            sku = Sku(
                sku_code=seed.local_sku_code(spu, si),
                spu_id=product.id,
                sku_name=f"{name} {spec_desc}",
                spec_desc=spec_desc,
                cost_price=_money(float(sale) * 0.62),
                sale_price=sale,
                status=status,
                created_at=created,
                updated_at=created,
            )
            session.add(sku)
            session.flush()
            sku_by_code[sku.sku_code] = sku
            skus.append(sku)
    return products, sku_by_code, skus


def seed_platform_products(session: Session, shops: dict[str, Shop]) -> list[PlatformSku]:
    """按启用店铺派生平台商品与平台规格（约 15% 商品不上架）。"""
    platform_skus: list[PlatformSku] = []
    for shop in shops.values():
        if shop.status != 1:
            continue
        for idx, (name, spu, base, specs) in enumerate(seed.PRODUCTS):
            if random.random() < 0.15:
                continue
            created = days_ago(random.randint(15, 150))
            pp = PlatformProduct(
                shop_id=shop.id,
                platform_code=shop.platform_code,
                platform_product_id=f"{shop.shop_code}{spu}",
                product_title=name,
                category_name=CATEGORY_POOL[idx % len(CATEGORY_POOL)],
                status=random.choice(["在售", "在售", "在售", "下架"]),
                sync_time=days_ago(random.randint(0, 5)),
                created_at=created,
            )
            session.add(pp)
            session.flush()
            for si, (spec_desc, delta) in enumerate(specs, start=1):
                ps = PlatformSku(
                    platform_product_id=pp.id,
                    shop_id=shop.id,
                    platform_code=shop.platform_code,
                    platform_sku_id=seed.platform_sku_code(shop.shop_code, spu, si),
                    sku_name=f"{name} {spec_desc}",
                    spec_desc=spec_desc,
                    outer_sku_code=seed.local_sku_code(spu, si),
                    price=_money(base + delta),
                    platform_stock=random.choice([0, 5, 20, 80, 200, 500, 1200]),
                    is_matched=0,
                    sync_time=pp.sync_time,
                    created_at=created,
                )
                session.add(ps)
                platform_skus.append(ps)
    session.flush()
    return platform_skus


def seed_sku_mappings(
    session: Session, platform_skus: list[PlatformSku], sku_by_code: dict[str, Sku]
) -> dict[tuple[int, str], tuple[int, str]]:
    """建立平台规格→本地 SKU 映射（约 15% 保持未映射），并回写 is_matched。"""
    lookup: dict[tuple[int, str], tuple[int, str]] = {}
    for ps in platform_skus:
        if random.random() < 0.15:
            continue
        sku = sku_by_code.get(ps.outer_sku_code or "")
        if not sku:
            continue
        created = days_ago(random.randint(5, 120))
        session.add(
            SkuMapping(
                platform_code=ps.platform_code,
                shop_id=ps.shop_id,
                platform_sku_id=ps.platform_sku_id,
                platform_sku_name=ps.sku_name,
                sku_id=sku.id,
                sku_code=sku.sku_code,
                status=1,
                remark=None,
                created_at=created,
                updated_at=created,
            )
        )
        ps.is_matched = 1
        session.add(ps)
        lookup[(ps.shop_id, ps.platform_sku_id)] = (sku.id, sku.sku_code)
    session.flush()
    return lookup


def seed_inventory(session: Session, skus: list[Sku]) -> list[Inventory]:
    """每个 SKU 一条库存记录（约 25% 低库存）。"""
    rows: list[Inventory] = []
    for idx, sku in enumerate(skus):
        low = idx % 4 == 0
        main_qty = random.randint(0, 30) if low else random.randint(120, 900)
        occupied = random.randint(0, min(main_qty, 50))
        row = Inventory(
            sku_id=sku.id,
            sku_code=sku.sku_code,
            main_qty=main_qty,
            occupied_qty=occupied,
            status=1 if sku.status == 1 else 0,
            updated_at=days_ago(random.randint(0, 5)),
        )
        session.add(row)
        rows.append(row)
    session.flush()
    return rows


def seed_inventory_alerts(session: Session, inv_rows: list[Inventory]) -> int:
    """为约 80% SKU 配置预警阈值，低库存 SKU 保证触发。"""
    count = 0
    for row in inv_rows:
        if random.random() >= 0.8:
            continue
        available = row.main_qty - row.occupied_qty
        alert_qty = (available + random.randint(0, 20)) if available <= 30 else random.choice([10, 20, 30, 50])
        session.add(
            InventoryAlert(
                sku_id=row.sku_id,
                sku_code=row.sku_code,
                alert_qty=alert_qty,
                is_enabled=1 if random.random() < 0.85 else 0,
                updated_at=days_ago(random.randint(0, 10)),
            )
        )
        count += 1
    session.flush()
    return count


def seed_inventory_flows(session: Session, inv_rows: list[Inventory]) -> int:
    """生成库存流水，覆盖全部 6 种变动类型，含来源单号与时间跨度。"""
    count = 0
    for idx, inv in enumerate(inv_rows):
        if idx < len(FLOW_PLAN):
            chosen = [FLOW_PLAN[idx]]  # 前 6 个 SKU 各强制一种类型，确保全覆盖
        else:
            chosen = [random.choice(FLOW_PLAN) for _ in range(random.randint(0, 2))]
        if not chosen:
            continue
        deltas: list[int] = []
        for flow_type, _st, _cn in chosen:
            if flow_type in ("PURCHASE_IN", "RETURN_IN"):
                deltas.append(random.randint(10, 120))
            elif flow_type == "SHIP_DEDUCT":
                deltas.append(-random.randint(5, 60))
            elif flow_type == "STOCKTAKE":
                deltas.append(random.randint(-30, 30))
            else:  # ORDER_OCCUPY / ORDER_RELEASE：主库存不变
                deltas.append(0)
        cursor = max(inv.main_qty - sum(deltas), 0)
        flow_time = days_ago(random.randint(40, 100))
        for (flow_type, source_type, cn_name), delta in zip(chosen, deltas):
            before = cursor
            cursor = max(cursor + delta, 0)
            change = cursor - before
            if flow_type == "PURCHASE_IN":
                source_no = f"CG{flow_time:%Y%m%d}{random.randint(1000, 9999)}"
                remark = "采购入库"
            elif flow_type == "RETURN_IN":
                source_no = f"OH{flow_time:%Y%m%d}{random.randint(1000, 9999)}"
                remark = f"买家退货入库 {change} 件"
            elif flow_type == "ORDER_OCCUPY":
                source_no = f"OH{flow_time:%Y%m%d}{random.randint(1000, 9999)}"
                remark = f"订单占用 {random.randint(1, 5)} 件"
            elif flow_type == "ORDER_RELEASE":
                source_no = f"OH{flow_time:%Y%m%d}{random.randint(1000, 9999)}"
                remark = f"订单释放 {random.randint(1, 5)} 件"
            elif flow_type == "SHIP_DEDUCT":
                source_no = f"OH{flow_time:%Y%m%d}{random.randint(1000, 9999)}"
                remark = f"发货扣减 {-change} 件"
            else:  # STOCKTAKE
                source_no = f"PD{flow_time:%Y%m%d}{random.randint(1000, 9999)}"
                remark = cn_name
            session.add(
                InventoryFlow(
                    sku_id=inv.sku_id,
                    sku_code=inv.sku_code,
                    flow_type=flow_type,
                    change_qty=change,
                    before_qty=before,
                    after_qty=cursor,
                    source_type=source_type,
                    source_no=source_no,
                    remark=remark,
                    operator=random.choice(["admin", "ops01", "wh01", "系统"]),
                    created_at=flow_time,
                )
            )
            count += 1
            flow_time = flow_time + timedelta(days=random.randint(1, 15))
    session.flush()
    return count


def seed_inventory_shares(session: Session, skus: list[Sku], shops: dict[str, Shop]) -> int:
    """约一半 SKU 在多个店铺间共享同一盘库存。"""
    enabled = [s for s in shops.values() if s.status == 1]
    count = 0
    for idx, sku in enumerate(skus):
        if idx % 2 != 0 or not enabled:
            continue
        for shop in random.sample(enabled, min(len(enabled), random.randint(1, 3))):
            session.add(
                InventoryShare(
                    sku_id=sku.id,
                    sku_code=sku.sku_code,
                    shop_id=shop.id,
                    platform_code=shop.platform_code,
                    status=1,
                    created_at=days_ago(random.randint(5, 100)),
                )
            )
            count += 1
    session.flush()
    return count


def main() -> None:
    with Session(engine) as session:
        print("[seed] 清空本批次相关表 ...")
        clear_tables(session)

        platforms = seed_platforms(session)
        shops = seed_shops(session)
        roles = seed_roles(session)
        code_map, all_codes, page_codes = seed_permissions(session)
        seed_role_permissions(session, roles, code_map, page_codes)
        users = seed_users(session, roles)
        seed_role_shops(session, roles, shops)
        tasks = seed_sync_tasks(session, shops)
        seed_sync_logs(session, tasks)
        seed_operation_logs(session, users)
        products, sku_by_code, skus = seed_products(session)
        platform_skus = seed_platform_products(session, shops)
        mapping_lookup = seed_sku_mappings(session, platform_skus, sku_by_code)
        orders_count = seed_orders(session, shops, mapping_lookup)
        inv_rows = seed_inventory(session, skus)
        alert_count = seed_inventory_alerts(session, inv_rows)
        flow_count = seed_inventory_flows(session, inv_rows)
        share_count = seed_inventory_shares(session, skus, shops)

        session.commit()

        print(f"[seed] 平台 {len(platforms)} / 店铺 {len(shops)} / 角色 {len(roles)} / 权限 {len(all_codes)}")
        print(f"[seed] 用户 {len(users)} / 同步任务 {len(tasks)} / 订单 {orders_count}")
        print(
            f"[seed] 商品 {len(products)} / SKU {len(skus)} / 平台规格 {len(platform_skus)} / 映射 {len(mapping_lookup)}"
        )
        print(f"[seed] 库存 {len(inv_rows)} / 预警 {alert_count} / 流水 {flow_count} / 共享 {share_count}")
        print("[seed] 同步日志与操作日志已生成")
        print("[seed] 默认密码：123456")


if __name__ == "__main__":
    main()
