// M9 数据看板接口
import request from './request'
import type { PageResult } from '@/types'
import type {
  DashboardQuery,
  DashboardTopQuery,
  DashboardOverview,
  DashboardChannels,
  DashboardProducts,
  DashboardFulfillment,
  DashboardAfterSales,
  DashboardInventory,
  DrillQuery,
  DrillOrder,
  DrillProduct,
  DrillAfterSale,
  DrillInventoryAlert,
} from '@/types/dashboard'

/** 经营总览 */
export function getDashboardOverview(params: DashboardQuery) {
  return request.get<DashboardOverview>('/v1/dashboard/overview', params as Record<string, unknown>)
}

/** 渠道与店铺对比 */
export function getDashboardChannels(params: DashboardQuery) {
  return request.get<DashboardChannels>('/v1/dashboard/channels', params as Record<string, unknown>)
}

/** 商品销售分析 */
export function getDashboardProducts(params: DashboardTopQuery) {
  return request.get<DashboardProducts>('/v1/dashboard/products', params as Record<string, unknown>)
}

/** 订单与履约分析 */
export function getDashboardFulfillment(params: DashboardQuery) {
  return request.get<DashboardFulfillment>('/v1/dashboard/fulfillment', params as Record<string, unknown>)
}

/** 售后分析 */
export function getDashboardAfterSales(params: DashboardTopQuery) {
  return request.get<DashboardAfterSales>('/v1/dashboard/after-sales', params as Record<string, unknown>)
}

/** 库存分析 */
export function getDashboardInventory(params: DashboardTopQuery) {
  return request.get<DashboardInventory>('/v1/dashboard/inventory', params as Record<string, unknown>)
}

/** 下钻：订单明细 */
export function drillDownOrders(params: DrillQuery) {
  return request.get<PageResult<DrillOrder>>('/v1/dashboard/drill-down', {
    ...params,
    metric: 'order',
  })
}

/** 下钻：商品明细 */
export function drillDownProducts(params: DrillQuery) {
  return request.get<PageResult<DrillProduct>>('/v1/dashboard/drill-down', {
    ...params,
    metric: 'product',
  })
}

/** 下钻：售后单明细 */
export function drillDownAfterSales(params: DrillQuery) {
  return request.get<PageResult<DrillAfterSale>>('/v1/dashboard/drill-down', {
    ...params,
    metric: 'after_sale',
  })
}

/** 下钻：库存预警明细 */
export function drillDownInventoryAlerts(params: DrillQuery) {
  return request.get<PageResult<DrillInventoryAlert>>('/v1/dashboard/drill-down', {
    ...params,
    metric: 'inventory_alert',
  })
}
