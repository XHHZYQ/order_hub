// M2 订单汇聚类型定义

/** 订单统一状态码（8 态，与《数据库设计》6.2 一致；后端以状态码存储） */
export type OrderStatus =
  | 'PENDING_PAY'
  | 'PENDING_AUDIT'
  | 'PENDING_SHIP'
  | 'PART_SHIPPED'
  | 'SHIPPED'
  | 'FINISHED'
  | 'CLOSED'
  | 'AFTER_SALE'

/** 订单来源 */
export type OrderSource = '平台' | '手工'

/** 订单列表项 / 详情（统一订单模型主信息） */
export interface Order {
  id: number
  order_no: string
  platform_code: string
  shop_id: number
  shop_name?: string
  platform_name?: string
  platform_order_no: string
  buyer_account: string
  receiver_name: string
  receiver_phone: string
  receiver_province?: string
  receiver_city?: string
  receiver_district?: string
  receiver_address: string
  goods_amount: number
  discount_amount: number
  freight_amount: number
  pay_amount: number
  status: string
  status_name?: string
  platform_status?: string
  source: string
  is_abnormal: number
  abnormal_reason?: string
  merchant_remark?: string
  buyer_remark?: string
  /** 标签（逗号分隔） */
  tags?: string
  order_time: string
  paid_at?: string
  shipped_at?: string
  sync_time?: string
  created_at?: string
  updated_at?: string
}

/** 订单商品明细 */
export interface OrderItem {
  id?: number
  platform_sku_id: string
  platform_sku_name: string
  outer_sku_code?: string
  sku_id?: number
  sku_code?: string
  product_name: string
  spec_desc?: string
  price: number
  quantity: number
  total_amount: number
  discount_amount: number
  pay_amount: number
  shipped_quantity: number
  refund_quantity: number
  is_matched: number
}

/** 订单平台扩展信息 */
export interface OrderExt {
  id?: number
  ext_key: string
  ext_name: string
  ext_value: string
}

/** 订单操作日志 */
export interface OrderLog {
  action: string
  from_status?: string
  to_status?: string
  content?: string
  operator?: string
  source?: string
  created_at: string
}

/** 订单变更记录 */
export interface OrderChange {
  change_type?: string
  field_name: string
  before_value?: string
  after_value?: string
  reason?: string
  operator?: string
  created_at: string
}

/** 订单日志与变更记录聚合结果 */
export interface OrderLogResult {
  logs: OrderLog[]
  changes: OrderChange[]
}

/** 手动同步 / 手动补单入参 */
export interface OrderSyncForm {
  shop_id: number | null
  start_time: string | null
  end_time: string | null
}

/** 手动同步 / 手动补单结果 */
export interface OrderSyncResult {
  total: number
  success_count: number
  fail_count: number
  log_id: number
  start_time: string
  end_time: string
}

/** 同步异常订单（字段同订单列表项，重点关注 abnormal_reason） */
export type SyncError = Order

/** 异常订单重试结果 */
export interface OrderRetryResult {
  order_id: number
  success: boolean
  abnormal: number
  abnormal_reason?: string
}

/** 订单列表查询参数 */
export interface OrderQuery {
  page?: number
  page_size?: number
  shop_id?: number
  platform_code?: string
  status?: string
  start_time?: string
  end_time?: string
  /** 订单号 / 平台订单号 / 买家账号 / 收件人 */
  keyword?: string
  /** 商品名 */
  goods_keyword?: string
}
