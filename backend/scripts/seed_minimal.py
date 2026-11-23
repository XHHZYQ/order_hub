"""最小演示数据（幂等、可重复执行，固定随机种子）。

用法（在 backend 目录下）：
    uv run python scripts/seed_minimal.py

覆盖表：platform / shop / role / permission / role_permission / user / user_role /
role_shop / sync_task / sync_log / operation_log
"""

import pathlib
import random
import sys
from datetime import datetime, timedelta

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from sqlmodel import Session, delete  # noqa: E402

from app.core.database import engine  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models.platform import Platform, Shop, SyncLog, SyncTask  # noqa: E402
from app.models.system import (  # noqa: E402
    OperationLog,
    Permission,
    Role,
    RolePermission,
    RoleShop,
    User,
    UserRole,
)
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
    ("shipment:batch_ship", "批量发货", "shipment:ship", 1),
    ("inventory:edit", "库存调整", "inventory:list", 1),
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
                "shipment:batch_ship",
                "inventory:edit",
                "sync:trigger",
            }
        ),
        "CUSTOMER_SERVICE": sorted(
            with_menus(["dashboard:overview", "order:list", "order:detail", "order:after_sale", "shipment:list", "product:list"])
            | {"order:audit", "order:price", "order:address"}
        ),
        "WAREHOUSE": sorted(
            with_menus(["dashboard:inventory", *ship_pages, *prod_pages])
            | {"shipment:batch_ship", "inventory:edit"}
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

        session.commit()

        print(f"[seed] 平台 {len(platforms)} / 店铺 {len(shops)} / 角色 {len(roles)} / 权限 {len(all_codes)}")
        print(f"[seed] 用户 {len(users)} / 同步任务 {len(tasks)} / 同步日志与操作日志已生成")
        print("[seed] 默认密码：123456")


if __name__ == "__main__":
    main()
