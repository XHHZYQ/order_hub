// M7 售后管理接口
import request from './request'
import type { PageQuery, PageResult } from '@/types'
import type {
  AfterSale,
  AfterSaleDetail,
  AfterSaleAlert,
  AfterSaleAnalysis,
  AfterSaleQuery,
  AfterSaleSyncForm,
  AfterSaleSyncResult,
  AfterSaleHandleForm,
  AfterSaleRefundForm,
} from '@/types/afterSale'

/** 售后单列表 */
export function getAfterSaleList(params: AfterSaleQuery) {
  return request.get<PageResult<AfterSale>>('/v1/after-sales', params)
}

/** 同步售后申请 */
export function syncAfterSales(data: AfterSaleSyncForm) {
  return request.post<AfterSaleSyncResult>('/v1/after-sales/sync', data)
}

/** 售后超时预警 */
export function getAfterSaleAlerts(params: PageQuery) {
  return request.get<PageResult<AfterSaleAlert>>('/v1/after-sales/alerts', params)
}

/** 售后原因分析 */
export function getAfterSaleAnalysis(params: { shop_id?: number }) {
  return request.get<AfterSaleAnalysis>('/v1/after-sales/analysis', params)
}

/** 售后单详情 */
export function getAfterSaleDetail(id: number) {
  return request.get<AfterSaleDetail>(`/v1/after-sales/${id}`)
}

/** 售后处理（同意/拒绝/协商/备注/退货入库） */
export function handleAfterSale(id: number, data: AfterSaleHandleForm) {
  return request.post<AfterSaleDetail>(`/v1/after-sales/${id}/handle`, data)
}

/** 退款同步 */
export function syncAfterSaleRefund(id: number, data: AfterSaleRefundForm) {
  return request.post<AfterSaleDetail>(`/v1/after-sales/${id}/refund`, data)
}
