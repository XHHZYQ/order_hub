"""模拟数据字典：商品池、买家池、真实感地址池、平台字段映射与扩展字段模板。

设计说明
--------
- 本模块只放"纯数据 + 纯函数"，不导入任何 ORM/服务，避免循环依赖。
- 订单原始字段名（见《数据库设计》7.1 平台字段映射对照表）集中在此，
  `app/adapters` 的适配器直接引用，保证"生成方"与"解析方"字段口径一致。
"""

from __future__ import annotations

import random

# --------------------------------------------------------------------------- #
# 平台原始字段映射：{统一字段: 平台原始字段}（见《数据库设计》7.1）
# --------------------------------------------------------------------------- #
ORDER_FIELD_MAP: dict[str, dict[str, str]] = {
    "TAOBAO": {
        "platform_order_no": "tid",
        "buyer_account": "buyer_nick",
        "buyer_nick": "buyer_nick",
        "receiver_name": "receiver_name",
        "receiver_phone": "receiver_mobile",
        "receiver_province": "receiver_state",
        "receiver_city": "receiver_city",
        "receiver_district": "receiver_district",
        "receiver_address": "receiver_address",
        "goods_amount": "total_fee",
        "discount_amount": "discount_fee",
        "freight_amount": "post_fee",
        "pay_amount": "payment",
        "platform_status": "status",
        "order_time": "created",
        "paid_at": "pay_time",
        "shipped_at": "consign_time",
        "buyer_remark": "buyer_message",
    },
    "JD": {
        "platform_order_no": "orderId",
        "buyer_account": "pin",
        "buyer_nick": "buyerNick",
        "receiver_name": "consignee",
        "receiver_phone": "mobile",
        "receiver_province": "province",
        "receiver_city": "city",
        "receiver_district": "county",
        "receiver_address": "address",
        "goods_amount": "orderTotalPrice",
        "discount_amount": "discountAmount",
        "freight_amount": "freightPrice",
        "pay_amount": "orderPayment",
        "platform_status": "orderState",
        "order_time": "orderTime",
        "paid_at": "paymentTime",
        "shipped_at": "shipTime",
        "buyer_remark": "buyerMessage",
    },
    "PDD": {
        "platform_order_no": "order_sn",
        "buyer_account": "buyer_user",
        "buyer_nick": "buyer_nick",
        "receiver_name": "receiver_name",
        "receiver_phone": "receiver_phone",
        "receiver_province": "province",
        "receiver_city": "city",
        "receiver_district": "town",
        "receiver_address": "receiver_address",
        "goods_amount": "goods_amount",
        "discount_amount": "discount_amount",
        "freight_amount": "postage",
        "pay_amount": "pay_amount",
        "platform_status": "order_status",
        "order_time": "create_time",
        "paid_at": "pay_time",
        "shipped_at": "shipping_time",
        "buyer_remark": "buyer_message",
    },
    "DOUYIN": {
        "platform_order_no": "order_id",
        "buyer_account": "open_id",
        "buyer_nick": "buyer_nick",
        "receiver_name": "receiver_name",
        "receiver_phone": "receiver_phone",
        "receiver_province": "province",
        "receiver_city": "city",
        "receiver_district": "district",
        "receiver_address": "receiver_address",
        "goods_amount": "goods_amount",
        "discount_amount": "discount_amount",
        "freight_amount": "post_amount",
        "pay_amount": "pay_amount",
        "platform_status": "order_status",
        "order_time": "create_time",
        "paid_at": "pay_time",
        "shipped_at": "ship_time",
        "buyer_remark": "buyer_message",
    },
    "SELF": {
        "platform_order_no": "order_sn",
        "buyer_account": "user_id",
        "buyer_nick": "buyer_nick",
        "receiver_name": "receiver_name",
        "receiver_phone": "receiver_phone",
        "receiver_province": "receiver_province",
        "receiver_city": "receiver_city",
        "receiver_district": "receiver_district",
        "receiver_address": "receiver_address",
        "goods_amount": "goods_amount",
        "discount_amount": "discount_amount",
        "freight_amount": "freight_amount",
        "pay_amount": "pay_amount",
        "platform_status": "status",
        "order_time": "create_time",
        "paid_at": "pay_time",
        "shipped_at": "ship_time",
        "buyer_remark": "buyer_remark",
    },
}

# --------------------------------------------------------------------------- #
# 订单明细原始字段映射：{统一字段: 平台原始字段}
# --------------------------------------------------------------------------- #
ITEM_FIELD_MAP: dict[str, dict[str, str]] = {
    "TAOBAO": {
        "platform_sku_id": "sku_id",
        "platform_sku_name": "sku_properties_name",
        "outer_sku_code": "outer_sku_id",
        "product_name": "title",
        "spec_desc": "sku_properties_name",
        "price": "price",
        "quantity": "num",
        "total_amount": "total_fee",
        "discount_amount": "discount_fee",
        "pay_amount": "payment",
    },
    "JD": {
        "platform_sku_id": "skuId",
        "platform_sku_name": "skuName",
        "outer_sku_code": "outerSkuId",
        "product_name": "skuName",
        "spec_desc": "skuSpec",
        "price": "jdPrice",
        "quantity": "itemNum",
        "total_amount": "itemTotalPrice",
        "discount_amount": "couponDiscount",
        "pay_amount": "itemPayment",
    },
    "PDD": {
        "platform_sku_id": "sku_id",
        "platform_sku_name": "goods_name",
        "outer_sku_code": "outer_id",
        "product_name": "goods_name",
        "spec_desc": "goods_spec",
        "price": "goods_price",
        "quantity": "goods_count",
        "total_amount": "goods_total",
        "discount_amount": "goods_discount",
        "pay_amount": "goods_payment",
    },
    "DOUYIN": {
        "platform_sku_id": "sku_id",
        "platform_sku_name": "product_name",
        "outer_sku_code": "outer_sku_id",
        "product_name": "product_name",
        "spec_desc": "spec_desc",
        "price": "price",
        "quantity": "item_num",
        "total_amount": "goods_amount",
        "discount_amount": "discount_amount",
        "pay_amount": "pay_amount",
    },
    "SELF": {
        "platform_sku_id": "sku_id",
        "platform_sku_name": "sku_name",
        "outer_sku_code": "sku_code",
        "product_name": "product_name",
        "spec_desc": "spec_desc",
        "price": "price",
        "quantity": "quantity",
        "total_amount": "total_amount",
        "discount_amount": "discount_amount",
        "pay_amount": "pay_amount",
    },
}

# 订单明细列表在原始报文中的键名
ITEM_LIST_KEY: dict[str, str] = {
    "TAOBAO": "orders",
    "JD": "orderItems",
    "PDD": "goods_list",
    "DOUYIN": "sku_order_list",
    "SELF": "items",
}

# 平台扩展字段：{平台原始字段: 中文名}（用于 order_ext 落库与展示）
EXT_FIELD_MAP: dict[str, dict[str, str]] = {
    "TAOBAO": {
        "status": "平台原始状态",
        "seller_nick": "卖家昵称",
        "trade_from": "交易来源",
        "buyer_message": "买家留言",
    },
    "JD": {
        "orderState": "平台原始状态",
        "venderId": "商家编号",
        "orderSource": "订单来源",
        "buyerMessage": "买家留言",
    },
    "PDD": {
        "order_status": "平台原始状态",
        "mall_id": "店铺ID",
        "order_tag": "订单标签",
        "buyer_message": "买家留言",
    },
    "DOUYIN": {
        "order_status": "平台原始状态",
        "shop_id": "店铺ID",
        "channel": "下单渠道",
        "buyer_message": "买家留言",
    },
    "SELF": {
        "status": "平台原始状态",
        "channel": "下单渠道",
        "coupon_code": "优惠券码",
        "buyer_remark": "买家备注",
    },
}

# 各平台买家账号前缀 / 订单号形态标识
PLATFORM_PREFIX: dict[str, str] = {
    "TAOBAO": "tb",
    "JD": "jd",
    "PDD": "pdd",
    "DOUYIN": "dy",
    "SELF": "self",
}

# 统一状态分布权重（生成订单时使用）
STATUS_WEIGHTS: dict[str, int] = {
    "PENDING_PAY": 12,
    "PENDING_AUDIT": 8,
    "PENDING_SHIP": 20,
    "PART_SHIPPED": 5,
    "SHIPPED": 20,
    "FINISHED": 28,
    "CLOSED": 5,
    "AFTER_SALE": 2,
}

# --------------------------------------------------------------------------- #
# 商品池：(商品名, SPU 编码, 基础价, [(规格描述, 加价), ...])
# --------------------------------------------------------------------------- #
PRODUCTS: list[tuple[str, str, float, list[tuple[str, float]]]] = [
    ("纯棉圆领短袖T恤", "SPU10001", 79.0, [("白色 M", 0.0), ("黑色 L", 0.0), ("藏青 XL", 10.0), ("灰色 2XL", 15.0)]),
    ("轻薄羽绒服", "SPU10002", 399.0, [("黑色 L", 0.0), ("酒红 M", 0.0), ("米白 XL", 20.0)]),
    ("真无线蓝牙耳机", "SPU10003", 249.0, [("星空黑", 0.0), ("陶瓷白", 0.0), ("晨曦金", 30.0)]),
    ("智能手环 Pro", "SPU10004", 199.0, [("曜石黑", 0.0), ("薄荷绿", 10.0)]),
    ("保温杯 500ml", "SPU10005", 129.0, [("磨砂黑", 0.0), ("奶白", 0.0), ("樱花粉", 5.0)]),
    ("天然乳胶枕", "SPU10006", 159.0, [("标准款", 0.0), ("加高款", 20.0)]),
    ("电动牙刷", "SPU10007", 189.0, [("USB 充电款", 0.0), ("便携旅行款", 25.0)]),
    ("运动跑鞋", "SPU10008", 329.0, [("黑色 41", 0.0), ("白色 42", 0.0), ("灰色 40", 0.0), ("蓝色 43", 10.0)]),
    ("双肩背包", "SPU10009", 219.0, [("商务黑", 0.0), ("雾霾蓝", 0.0)]),
    ("不锈钢炒锅", "SPU10010", 279.0, [("32cm", 0.0), ("30cm", -20.0)]),
    ("智能台灯", "SPU10011", 149.0, [("白色", 0.0), ("灰色", 0.0)]),
    ("空气炸锅 4.5L", "SPU10012", 359.0, [("象牙白", 0.0), ("曜石黑", 0.0)]),
    ("无线鼠标", "SPU10013", 99.0, [("静音黑", 0.0), ("樱花粉", 5.0)]),
    ("机械键盘 87 键", "SPU10014", 289.0, [("青轴", 0.0), ("红轴", 20.0), ("茶轴", 20.0)]),
    ("护眼显示器 27 寸", "SPU10015", 1099.0, [("标准版", 0.0), ("高刷版", 200.0)]),
    ("扫地机器人", "SPU10016", 1599.0, [("标准版", 0.0), ("激光导航版", 300.0)]),
    ("猫粮 2kg", "SPU10017", 118.0, [("成猫鸡肉味", 0.0), ("幼猫三文鱼味", 12.0)]),
    ("手工皂礼盒", "SPU10018", 88.0, [("玫瑰味", 0.0), ("薰衣草味", 0.0)]),
    ("羊毛围巾", "SPU10019", 168.0, [("驼色", 0.0), ("酒红", 0.0)]),
    ("车载手机支架", "SPU10020", 59.0, [("出风口款", 0.0), ("吸盘款", 5.0)]),
]

# 买家昵称池
BUYER_NICKS: list[str] = [
    "清风拂柳",
    "山间小路",
    "爱吃橘子的猫",
    "追风少年",
    "柠檬不酸",
    "海阔天空",
    "阳光下午茶",
    "认真生活",
    "小鹿乱撞",
    "秋天的第一杯",
    "慢慢来比较快",
    "极简主义者",
    "会飞的鱼",
    "咖啡因依赖",
    "旅行青蛙",
    "深夜书房",
    "云淡风轻",
    "拾光者",
    "半糖主义",
    "无名之辈",
    "木木林",
    "南方有嘉木",
    "冬日暖阳",
    "奔跑的蜗牛",
    "一叶知秋",
    "爱笑的人",
    "简单快乐",
    "天涯浪子",
    "岁月静好",
    "小确幸",
]

# 收货地址池：(省, 市, 区, 详细地址)
ADDRESS_POOL: list[tuple[str, str, str, str]] = [
    ("广东省", "广州市", "天河区", "科韵路 16 号信息港大厦 B 座 1201"),
    ("广东省", "深圳市", "南山区", "科技园南区高新南七道 18 号 A 栋 802"),
    ("广东省", "东莞市", "南城街道", "鸿福路 200 号第一国际商务大厦 1508"),
    ("北京市", "北京市", "朝阳区", "建国路 88 号 SOHO 现代城 C 座 2705"),
    ("北京市", "北京市", "海淀区", "中关村大街 27 号中关村大厦 1608"),
    ("上海市", "上海市", "浦东新区", "张江高科技园区博云路 2 号 506"),
    ("上海市", "上海市", "徐汇区", "漕溪北路 331 号汇智大厦 3201"),
    ("浙江省", "杭州市", "西湖区", "文一西路 969 号数娱大厦 1102"),
    ("浙江省", "杭州市", "滨江区", "江南大道 3588 号恒鑫大厦 2309"),
    ("江苏省", "南京市", "鼓楼区", "中山北路 105 号中环国际广场 1706"),
    ("江苏省", "苏州市", "工业园区", "星湖街 328 号协鑫广场 908"),
    ("四川省", "成都市", "武侯区", "天府大道北段 1700 号环球中心 E2 1808"),
    ("四川省", "成都市", "高新区", "盛和一路 88 号新希望国际大厦 B 座 1503"),
    ("湖北省", "武汉市", "洪山区", "光谷大道 77 号金融港 B 区 1206"),
    ("湖南省", "长沙市", "岳麓区", "麓谷大道 627 号麓谷科技园 802"),
    ("陕西省", "西安市", "雁塔区", "高新四路 3 号爵士大厦 1509"),
    ("山东省", "青岛市", "市南区", "香港中路 8 号世界贸易中心 2001"),
    ("福建省", "厦门市", "思明区", "软件园二期观日路 26 号 501"),
    ("重庆市", "重庆市", "渝北区", "金开大道 99 号协信中心 1807"),
    ("河南省", "郑州市", "金水区", "农业路 100 号国际企业中心 A 座 1208"),
    ("辽宁省", "沈阳市", "和平区", "南京南街 121 号朗勤大厦 1906"),
    ("云南省", "昆明市", "盘龙区", "北京路 155 号白塔路商务大厦 1005"),
]

# 收货人姓氏与名字，用于拼接收货人
SURNAMES: list[str] = ["王", "李", "张", "刘", "陈", "杨", "赵", "黄", "周", "吴", "徐", "孙", "马", "朱", "胡"]
GIVEN_NAMES: list[str] = ["伟", "芳", "娜", "敏", "静", "磊", "强", "军", "洋", "勇", "艳", "杰", "涛", "明", "超"]

# 扩展字段取值候选（按原始字段名）
EXT_VALUE_POOL: dict[str, list[str]] = {
    "trade_from": ["WAP", "PC", "APP"],
    "orderSource": ["PC", "APP", "MINI"],
    "order_tag": ["普通订单", "拼团订单", "秒杀订单", "百亿补贴"],
    "channel": ["直播间", "商品橱窗", "商城搜索", "小程序", "短视频"],
    "coupon_code": ["CPN202611", "SUMMER10", "VIP2026", ""],
}


def random_product(rng: random.Random) -> tuple[str, str, str, float]:
    """随机取一个商品规格，返回 (商品名, SPU 编码, 规格描述, 单价)。"""
    name, spu, base, specs = rng.choice(PRODUCTS)
    spec_desc, delta = rng.choice(specs)
    price = round(base + delta, 2)
    return name, spu, spec_desc, price


def random_buyer(rng: random.Random, platform_code: str) -> tuple[str, str]:
    """随机买家，返回 (账号, 昵称)。"""
    prefix = PLATFORM_PREFIX.get(platform_code, "u")
    account = f"{prefix}_{rng.randint(100000, 999999)}"
    return account, rng.choice(BUYER_NICKS)


def random_receiver(rng: random.Random) -> dict[str, str]:
    """随机收货信息（省/市/区/详细地址/收货人/手机号）。"""
    province, city, district, detail = rng.choice(ADDRESS_POOL)
    name = rng.choice(SURNAMES) + rng.choice(GIVEN_NAMES)
    phone = f"1{rng.choice(['3', '5', '7', '8', '9'])}{rng.randint(100000000, 999999999)}"
    return {
        "province": province,
        "city": city,
        "district": district,
        "detail": detail,
        "name": name,
        "phone": phone,
    }
