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
  AbnormalOrder,
  AbnormalQuery,
  OrderStatusOptions,
  OrderAuditForm,
  OrderBatchAuditForm,
  OrderPriceForm,
  OrderAddressForm,
  OrderRemarkForm,
  OrderBatchRemarkForm,
  OrderBatchIdsForm,
  OrderMergeResult,
  OrderSplitForm,
  OrderSplitResult,
  OrderStatusChangeForm,
  OrderBatchResult,
} from '@/types/order'
import type { AfterSale } from '@/types/afterSale'

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

// ------------------------------ M3 订单处理 ------------------------------ //

/** 异常订单池（同步/地址/金额/超时异常） */
export function getAbnormalOrders(params: AbnormalQuery) {
  return request.get<PageResult<AbnormalOrder>>('/v1/orders/abnormal', params)
}

/** 单条订单审核（PASS 通过 / REJECT 驳回） */
export function auditOrder(id: number, data: OrderAuditForm) {
  return request.post<Order>(`/v1/orders/${id}/audit`, data)
}

/** 批量审核 */
export function batchAuditOrders(data: OrderBatchAuditForm) {
  return request.post<OrderBatchResult>('/v1/orders/batch/audit', data)
}

/** 订单改价 */
export function changeOrderPrice(id: number, data: OrderPriceForm) {
  return request.post<Order>(`/v1/orders/${id}/price`, data)
}

/** 修改收货地址 */
export function changeOrderAddress(id: number, data: OrderAddressForm) {
  return request.post<Order>(`/v1/orders/${id}/address`, data)
}

/** 订单备注/打标 */
export function addOrderRemark(id: number, data: OrderRemarkForm) {
  return request.post<Order>(`/v1/orders/${id}/remark`, data)
}

/** 批量备注/打标 */
export function batchOrderRemark(data: OrderBatchRemarkForm) {
  return request.post<OrderBatchResult>('/v1/orders/batch/remark', data)
}

/** 批量转发货 */
export function batchForwardShip(data: OrderBatchIdsForm) {
  return request.post<OrderBatchResult>('/v1/orders/batch/forward', data)
}

/** 订单合并 */
export function mergeOrders(data: OrderBatchIdsForm) {
  return request.post<OrderMergeResult>('/v1/orders/merge', data)
}

/** 订单拆分 */
export function splitOrder(id: number, data: OrderSplitForm) {
  return request.post<OrderSplitResult>(`/v1/orders/${id}/split`, data)
}

/** 订单状态流转（合法流转由状态机校验） */
export function changeOrderStatus(id: number, data: OrderStatusChangeForm) {
  return request.patch<Order>(`/v1/orders/${id}/status`, data)
}

/** 当前订单可流转的下一状态 */
export function getOrderStatusOptions(id: number) {
  return request.get<OrderStatusOptions>(`/v1/orders/${id}/status-options`)
}

/** 订单关联的售后单 */
export function getOrderAfterSales(id: number) {
  return request.get<AfterSale[]>(`/v1/orders/${id}/after-sales`)
}
