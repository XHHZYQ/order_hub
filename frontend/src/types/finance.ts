// M8 财务对账类型定义

import type { PageQuery } from '@/types'

/** 账单对账状态 */
export type BillReconcileStatus = 'PENDING' | 'MATCHING' | 'RECONCILED' | 'CLOSED'

/** 账单明细匹配状态 */
export type BillMatchStatus = 'MATCHED' | 'AMOUNT_DIFF' | 'UNMATCHED'

/** 对账差异类型 */
export type ReconcileDiffType = 'LOCAL_MISSING' | 'BILL_MISSING' | 'AMOUNT_DIFF'

/** 差异处理状态 */
export type DiffHandleStatus = 'PENDING' | 'HANDLED'

/** 账单批次 */
export interface Bill {
  id: number
  bill_no: string
  platform_code: string
  platform_name?: string | null
  shop_id: number
  shop_name?: string | null
  /** 账期，如 2026-10 */
  bill_period: string
  file_name?: string | null
  total_count: number
  total_amount: number
  reconcile_status: string
  reconcile_status_name?: string
  import_time: string
  operator?: string | null
  created_at?: string
  /** 详情接口附加：差异条数 */
  diff_count?: number
  /** 详情接口附加：待处理差异条数 */
  pending_diff_count?: number
}

/** 账单明细 */
export interface BillDetail {
  id: number
  bill_id: number
  platform_code: string
  shop_id: number
  platform_order_no: string
  /** 匹配到的本地订单号（未匹配为空） */
  order_no?: string | null
  order_id?: number | null
  trade_time?: string | null
  goods_amount: number
  freight_amount: number
  commission_amount: number
  subsidy_amount: number
  refund_amount: number
  settled_amount: number
  match_status: string
  match_status_name?: string
  created_at?: string
}

/** 对账差异 */
export interface ReconcileDiff {
  id: number
  bill_id: number
  bill_no?: string | null
  bill_detail_id?: number | null
  platform_code: string
  platform_name?: string | null
  shop_id: number
  shop_name?: string | null
  platform_order_no: string
  order_no?: string | null
  diff_type: string
  diff_type_name?: string
  local_amount: number
  bill_amount: number
  diff_amount: number
  handle_status: string
  handle_status_name?: string
  handle_remark?: string | null
  operator?: string | null
  handle_time?: string | null
  created_at?: string
}

/** 账单列表查询参数 */
export interface BillQuery extends PageQuery {
  shop_id?: number
  platform_code?: string
  reconcile_status?: string
  bill_period?: string
  keyword?: string
  start_time?: string
  end_time?: string
}

/** 账单明细查询参数 */
export interface BillDetailQuery extends PageQuery {
  match_status?: string
  keyword?: string
}

/** 差异查询参数 */
export interface DiffQuery extends PageQuery {
  bill_id?: number
  diff_type?: string
  handle_status?: string
  shop_id?: number
  platform_code?: string
  keyword?: string
  start_time?: string
  end_time?: string
}

/** 账单导入入参 */
export interface BillImportForm {
  platform_code: string
  shop_id: number
  bill_period: string
  /** 为真时按本地订单生成模拟账单（演示用） */
  auto_generate?: boolean
  file?: File | null
}

/** 模拟账单文件下载参数 */
export interface MockFileQuery {
  platform_code: string
  shop_id: number
  bill_period: string
  file_type?: 'csv' | 'xlsx'
}

/** 对账匹配结果 */
export interface BillMatchResult {
  bill_id: number
  matched: number
  amount_diff: number
  unmatched: number
  bill_missing: number
  diff_count: number
}

/** 差异处理入参 */
export interface DiffHandleForm {
  action?: string | null
  handle_remark?: string | null
}

/** 结算汇总查询参数 */
export interface SettlementQuery {
  start_time?: string
  end_time?: string
  platform_code?: string
  shop_id?: number
  group_by?: 'platform' | 'shop'
}

/** 结算汇总分组行 */
export interface SettlementRow {
  key: string | number
  name: string
  receivable: number
  platform_fee: number
  subsidy: number
  refund: number
  settled: number
  order_count: number
}

/** 结算汇总结果 */
export interface SettlementSummary {
  receivable: number
  platform_fee: number
  subsidy: number
  refund: number
  settled: number
  order_count: number
  rows: SettlementRow[]
}

/** 毛利查询参数 */
export interface ProfitQuery {
  start_time?: string
  end_time?: string
  platform_code?: string
  shop_id?: number
  limit?: number
}

/** 按订单毛利 */
export interface ProfitOrder {
  order_id: number
  order_no: string
  platform_order_no: string
  buyer_account?: string | null
  settled: number
  cost: number
  profit: number
  profit_rate: number
  trade_time?: string | null
}

/** 按商品毛利 */
export interface ProfitProduct {
  sku_id: number
  sku_code: string
  product_name: string
  quantity: number
  settled: number
  cost: number
  profit: number
  profit_rate: number
}

/** 毛利核算结果 */
export interface ProfitSummary {
  settled: number
  cost: number
  profit: number
  profit_rate: number
  order_count: number
  by_order: ProfitOrder[]
  by_product: ProfitProduct[]
}

/** 报表导出类型 */
export type ExportType = 'detail' | 'difference' | 'settlement'

/** 报表导出查询参数 */
export interface ExportQuery {
  export_type: ExportType
  start_time?: string
  end_time?: string
  platform_code?: string
  shop_id?: number
  bill_id?: number
}
