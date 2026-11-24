// M7 售后管理类型定义

import type { PageQuery } from '@/types'

/** 售后单 */
export interface AfterSale {
  id: number
  after_sale_no: string
  platform_code: string
  platform_name?: string | null
  shop_id: number
  shop_name?: string | null
  platform_after_sale_no: string
  order_id?: number | null
  order_no?: string | null
  order_status?: string | null
  order_status_name?: string | null
  buyer_account?: string | null
  type: string
  type_name?: string
  reason?: string | null
  status: string
  status_name?: string
  platform_status?: string | null
  refund_amount: number
  refund_status: string
  refund_status_name?: string
  goods_returned: number
  apply_time: string
  handle_deadline?: string | null
  finish_time?: string | null
  operator?: string | null
  remark?: string | null
  created_at?: string | null
  updated_at?: string | null
}

/** 售后处理记录 */
export interface AfterSaleLog {
  id: number
  after_sale_id: number
  after_sale_no: string
  action: string
  content?: string | null
  operator?: string | null
  created_at?: string | null
}

/** 售后单详情 */
export interface AfterSaleDetail extends AfterSale {
  order_pay_amount?: number | null
  logs: AfterSaleLog[]
}

/** 售后超时预警项 */
export interface AfterSaleAlert extends AfterSale {
  overdue_hours?: number | null
  alert_reason?: string
}

/** 售后原因分析结果 */
export interface AfterSaleAnalysis {
  total: number
  refund_amount: number
  by_type: { type: string; type_name: string; count: number; amount: number }[]
  by_reason: { reason: string; count: number }[]
  by_shop: { shop_id: number; shop_name: string; count: number; amount: number }[]
}

/** 售后单查询参数 */
export interface AfterSaleQuery extends PageQuery {
  shop_id?: number
  platform_code?: string
  status?: string
  type?: string
  refund_status?: string
  keyword?: string
  start_time?: string
  end_time?: string
}

/** 同步售后申请入参 */
export interface AfterSaleSyncForm {
  shop_id?: number | null
}

/** 同步售后结果 */
export interface AfterSaleSyncResult {
  created: number
}

/** 售后处理入参 */
export interface AfterSaleHandleForm {
  action: '同意' | '拒绝' | '协商' | '备注' | '退货入库'
  content?: string | null
  refund_amount?: number | null
  goods_returned?: boolean | null
}

/** 退款同步入参 */
export interface AfterSaleRefundForm {
  refund_amount?: number | null
  refund_status?: string | null
  remark?: string | null
}
