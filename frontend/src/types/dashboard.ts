// M9 数据看板类型定义

import type { PageQuery } from '@/types'

/** 看板通用查询参数（时间默认近 30 天） */
export interface DashboardQuery {
  start_time?: string
  end_time?: string
  platform_code?: string
  shop_id?: number
}

/** 商品/售后/库存分析附加 top 参数 */
export interface DashboardTopQuery extends DashboardQuery {
  top?: number
}

/** 趋势点（经营总览） */
export interface OverviewTrend {
  date: string
  order_count: number
  sales_amount: number
}

/** 经营总览结果 */
export interface DashboardOverview {
  start_time: string
  end_time: string
  order_count: number
  sales_amount: number
  avg_order_amount: number
  buyer_count: number
  refund_amount: number
  refund_count: number
  trend: OverviewTrend[]
}

/** 平台维度对比 */
export interface ChannelPlatform {
  platform_code: string
  platform_name: string
  order_count: number
  sales_amount: number
  avg_order_amount: number
}

/** 店铺维度对比 */
export interface ChannelShop {
  shop_id: number
  shop_name: string
  platform_code: string
  platform_name: string
  order_count: number
  sales_amount: number
}

/** 渠道与店铺对比结果 */
export interface DashboardChannels {
  by_platform: ChannelPlatform[]
  by_shop: ChannelShop[]
}

/** 热销商品 */
export interface ProductHot {
  sku_id: number | null
  sku_code?: string | null
  product_name: string
  quantity: number
  sales_amount: number
}

/** 品类分布 */
export interface ProductCategory {
  category_name: string
  quantity: number
  sales_amount: number
}

/** 商品销售趋势点 */
export interface ProductTrend {
  date: string
  quantity: number
  sales_amount: number
}

/** 商品销售分析结果 */
export interface DashboardProducts {
  total_quantity: number
  total_sales_amount: number
  sku_count: number
  hot: ProductHot[]
  categories: ProductCategory[]
  trend: ProductTrend[]
}

/** 状态分布通用项 */
export interface StatusCount {
  status: string
  status_name: string
  count: number
}

/** 订单与履约分析结果 */
export interface DashboardFulfillment {
  order_count: number
  finished_count: number
  shipment_count: number
  avg_ship_hours: number
  fulfillment_rate: number
  status_distribution: StatusCount[]
  shipment_distribution: StatusCount[]
}

/** 售后类型分布 */
export interface AfterSaleTypeCount {
  type: string
  type_name: string
  count: number
}

/** 售后原因分布 */
export interface AfterSaleReasonCount {
  reason: string
  count: number
}

/** 售后趋势点 */
export interface AfterSaleTrend {
  date: string
  count: number
}

/** 售后分析结果 */
export interface DashboardAfterSales {
  total: number
  refund_amount: number
  refund_success_count: number
  type_distribution: AfterSaleTypeCount[]
  status_distribution: StatusCount[]
  reason_distribution: AfterSaleReasonCount[]
  trend: AfterSaleTrend[]
  refund_status_names: Record<string, string>
}

/** 库存预警项 */
export interface InventoryAlertItem {
  sku_id: number
  sku_code: string
  sku_name: string
  available_qty: number
  alert_qty: number
  risk: string
}

/** 库存周转项 */
export interface InventoryTurnoverItem {
  sku_id: number
  sku_code: string
  sku_name: string
  sold_qty: number
  available_qty: number
  turnover_rate: number
}

/** 库存分析结果 */
export interface DashboardInventory {
  sku_count: number
  main_qty: number
  occupied_qty: number
  available_qty: number
  alert_count: number
  shortage_count: number
  alerts: InventoryAlertItem[]
  turnover: InventoryTurnoverItem[]
}

// --------------------------------------------------------------------------- //
// 下钻
// --------------------------------------------------------------------------- //

/** 下钻指标类型 */
export type DrillMetric = 'order' | 'product' | 'after_sale' | 'inventory_alert'

/** 下钻查询参数 */
export interface DrillQuery extends PageQuery {
  metric: DrillMetric
  start_time?: string
  end_time?: string
  platform_code?: string
  shop_id?: number
  sku_id?: number
}

/** 下钻：订单明细 */
export interface DrillOrder {
  id: number
  order_no: string
  platform_order_no: string
  platform_name: string
  shop_name: string
  buyer_account?: string | null
  pay_amount: number
  status: string
  status_name: string
  order_time: string
}

/** 下钻：商品明细 */
export interface DrillProduct {
  order_no: string
  platform_order_no: string
  sku_code?: string | null
  product_name: string
  quantity: number
  pay_amount: number
  order_time: string
  status: string
  status_name: string
}

/** 下钻：售后单明细 */
export interface DrillAfterSale {
  after_sale_no: string
  order_no?: string | null
  type: string
  type_name: string
  reason?: string | null
  status: string
  status_name: string
  refund_amount: number
  apply_time: string
}

/** 下钻：库存预警明细 */
export interface DrillInventoryAlert {
  sku_id: number
  sku_code: string
  main_qty: number
  occupied_qty: number
  available_qty: number
  alert_qty: number
}
