// M6 发货与物流类型定义

import type { PageQuery } from '@/types'
import type { Order } from './order'

/** 物流公司字典项 */
export interface LogisticsCompany {
  company_code: string
  company_name: string
}

/** 待发货订单（在订单列表项上附加商品统计） */
export interface PendingOrder extends Order {
  /** 已匹配本地 SKU 的明细数 */
  item_count: number
  /** 未发货总数量 */
  total_qty: number
  /** 未匹配 SKU 的明细数 */
  unmatched_count: number
}

/** 电子面单数据 */
export interface FaceSheet {
  order_id: number
  order_no: string
  platform_code: string
  logistics_company_code: string
  logistics_company_name: string
  waybill_no: string
  face_sheet_no: string
  package_no: string
  receiver_name?: string | null
  receiver_phone?: string | null
  receiver_address?: string | null
}

/** 发货单 */
export interface Shipment {
  id: number
  shipment_no: string
  order_id: number
  order_no: string
  shop_id: number
  platform_code: string
  logistics_company_code?: string | null
  logistics_company_name?: string | null
  waybill_no?: string | null
  face_sheet_no?: string | null
  package_no?: string | null
  ship_qty: number
  print_status: number
  push_status: number
  push_status_name?: string
  push_fail_reason?: string | null
  status: string
  status_name?: string
  shipped_at?: string | null
  operator?: string | null
  created_at?: string | null
  shop_name?: string | null
  platform_name?: string | null
  receiver_name?: string | null
  receiver_phone?: string | null
  receiver_address?: string | null
}

/** 物流轨迹节点 */
export interface LogisticsTrace {
  id: number
  shipment_id: number
  waybill_no?: string | null
  trace_time: string
  trace_desc?: string | null
  trace_status?: string | null
  trace_status_name?: string
  created_at?: string | null
}

/** 发货单详情（含订单状态与轨迹） */
export interface ShipmentDetail extends Shipment {
  order_status?: string | null
  order_status_name?: string | null
  traces: LogisticsTrace[]
}

/** 物流异常预警项 */
export interface ShipmentAlert extends Shipment {
  last_trace_time?: string | null
  stale_hours?: number | null
  alert_reason?: string
}

/** 获取电子面单入参（单个传 order_id，批量传 order_ids） */
export interface WaybillForm {
  order_id?: number
  order_ids?: number[]
  logistics_company_code?: string | null
}

/** 发货明细 */
export interface ShipmentItemForm {
  item_id: number
  quantity: number
}

/** 发货入参 */
export interface ShipmentForm {
  order_id: number
  logistics_company_code?: string | null
  waybill_no?: string | null
  face_sheet_no?: string | null
  package_no?: string | null
  items?: ShipmentItemForm[] | null
}

/** 批量发货入参 */
export interface BatchShipmentForm {
  order_ids: number[]
  logistics_company_code?: string | null
}

/** 批量打单入参 */
export interface PrintForm {
  order_ids: number[]
  logistics_company_code?: string | null
}

/** 批量打单结果 */
export interface PrintResult {
  count: number
  sheets: FaceSheet[]
}

/** 批量发货结果 */
export interface BatchShipResult {
  success_count: number
  fail_count: number
  success: { order_id: number; shipment_no: string }[]
  failed: { order_id: number; reason: string }[]
}

/** 拉取轨迹结果 */
export interface SyncTraceResult {
  shipment_id: number
  added: number
  status: string
  status_name?: string
  traces: LogisticsTrace[]
}

/** 发货单查询参数 */
export interface ShipmentQuery extends PageQuery {
  shop_id?: number
  platform_code?: string
  status?: string
  keyword?: string
  start_time?: string
  end_time?: string
}
