// M2 订单汇聚类型定义
import type { PageQuery } from '@/types'

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
export interface OrderQuery extends PageQuery {
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

// --------------------------------------------------------------------------- //
// M3 订单处理
// --------------------------------------------------------------------------- //

/** 异常订单池列表项（在订单列表项上附带异常类型） */
export interface AbnormalOrder extends Order {
  abnormal_types?: string[]
  abnormal_type_names?: string[]
}

/** 异常订单池查询参数 */
export interface AbnormalQuery extends OrderQuery {
  /** 异常类型：SYNC / ADDRESS / AMOUNT / TIMEOUT */
  abnormal_type?: string
}

/** 可流转的下一状态项 */
export interface StatusOption {
  status: string
  status_name: string
}

/** 状态流转可选项结果 */
export interface OrderStatusOptions {
  order_id: number
  current_status: string
  current_status_name: string
  options: StatusOption[]
}

/** 单条审核入参（action：PASS 通过 / REJECT 驳回） */
export interface OrderAuditForm {
  action: 'PASS' | 'REJECT'
  reason?: string | null
}

/** 批量审核入参 */
export interface OrderBatchAuditForm {
  order_ids: number[]
  action: 'PASS' | 'REJECT'
  reason?: string | null
}

/** 改价入参（仅传需要修改的金额字段） */
export interface OrderPriceForm {
  goods_amount?: number
  discount_amount?: number
  freight_amount?: number
  pay_amount?: number
  reason?: string | null
}

/** 改址入参（仅传需要修改的字段） */
export interface OrderAddressForm {
  receiver_name?: string
  receiver_phone?: string
  receiver_province?: string
  receiver_city?: string
  receiver_district?: string
  receiver_address?: string
  reason?: string | null
}

/** 备注/打标入参 */
export interface OrderRemarkForm {
  merchant_remark?: string | null
  buyer_remark?: string | null
  /** 标签列表（整体覆盖） */
  tags?: string[] | null
  /** 商家备注是否追加 */
  append?: boolean
}

/** 批量备注/打标入参 */
export interface OrderBatchRemarkForm extends OrderRemarkForm {
  order_ids: number[]
}

/** 合并/批量转发货等仅需订单 ID 的批量入参 */
export interface OrderBatchIdsForm {
  order_ids: number[]
  remark?: string | null
}

/** 合并结果 */
export interface OrderMergeResult {
  merge_group_no: string
  order_count: number
  order_nos: string[]
}

/** 拆分方案明细 */
export interface OrderSplitItem {
  item_id: number
  quantity: number
}

/** 拆分方案的一个子单 */
export interface OrderSplitPart {
  items: OrderSplitItem[]
}

/** 拆单入参（≥2 个部分） */
export interface OrderSplitForm {
  parts: OrderSplitPart[]
  remark?: string | null
}

/** 拆单结果 */
export interface OrderSplitResult {
  parent_order_no: string
  child_count: number
  child_order_nos: string[]
}

/** 状态流转入参 */
export interface OrderStatusChangeForm {
  to_status: string
  remark?: string | null
}

/** 批量操作结果 */
export interface OrderBatchResult {
  success_count: number
  fail_count: number
  success_ids: number[]
  failed: { id: number; reason: string }[]
}
