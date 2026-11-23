// M2 订单汇聚接口
import request from './request'
import type { PageQuery, PageResult } from '@/types'
import type {
  Order,
  OrderItem,
  OrderExt,
  OrderLogResult,
  OrderSyncForm,
  OrderSyncResult,
  SyncError,
  OrderRetryResult,
} from '@/types/order'

/** 订单列表（店铺/平台/状态/时间/关键字/商品筛选） */
export function getOrderList(params: PageQuery) {
  return request.get<PageResult<Order>>('/v1/orders', params)
}

/** 订单详情（主信息 + 金额 + 状态） */
export function getOrderDetail(id: number) {
  return request.get<Order>(`/v1/orders/${id}`)
}

/** 订单商品明细 */
export function getOrderItems(id: number) {
  return request.get<OrderItem[]>(`/v1/orders/${id}/items`)
}

/** 订单平台扩展信息 */
export function getOrderExt(id: number) {
  return request.get<OrderExt[]>(`/v1/orders/${id}/ext`)
}

/** 订单操作日志与变更记录 */
export function getOrderLogs(id: number) {
  return request.get<OrderLogResult>(`/v1/orders/${id}/logs`)
}

/** 同步异常订单列表 */
export function getSyncErrors(params: PageQuery) {
  return request.get<PageResult<SyncError>>('/v1/orders/sync-errors', params)
}

/** 手动触发订单同步 */
export function orderSync(data: OrderSyncForm) {
  return request.post<OrderSyncResult>('/v1/orders/sync', data)
}

/** 手动补单（指定时间范围补拉） */
export function orderSupplement(data: OrderSyncForm) {
  return request.post<OrderSyncResult>('/v1/orders/supplement', data)
}

/** 重试单条异常订单 */
export function retrySyncError(id: number) {
  return request.post<OrderRetryResult>(`/v1/orders/sync-errors/${id}/retry`)
}

/** 人工处理异常订单 */
export function handleSyncError(id: number, note: string | null) {
  return request.post<Order>(`/v1/orders/sync-errors/${id}/handle`, { note })
}
