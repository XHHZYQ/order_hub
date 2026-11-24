// M6 发货与物流接口
import request from './request'
import type { PageQuery, PageResult } from '@/types'
import type {
  LogisticsCompany,
  PendingOrder,
  FaceSheet,
  Shipment,
  ShipmentDetail,
  ShipmentAlert,
  ShipmentQuery,
  LogisticsTrace,
  WaybillForm,
  ShipmentForm,
  BatchShipmentForm,
  PrintForm,
  PrintResult,
  BatchShipResult,
  SyncTraceResult,
} from '@/types/fulfillment'

/** 物流公司字典 */
export function getLogisticsCompanies() {
  return request.get<LogisticsCompany[]>('/v1/logistics-companies')
}

/** 待发货订单列表 */
export function getPendingOrders(params: PageQuery) {
  return request.get<PageResult<PendingOrder>>('/v1/shipments/pending', params)
}

/** 获取电子面单（单个/批量） */
export function getWaybills(data: WaybillForm) {
  return request.post<FaceSheet[]>('/v1/shipments/waybill', data)
}

/** 批量打单 */
export function printShipments(data: PrintForm) {
  return request.post<PrintResult>('/v1/shipments/print', data)
}

/** 发货（单笔：创建发货单、回传平台、扣减库存） */
export function createShipment(data: ShipmentForm) {
  return request.post<ShipmentDetail>('/v1/shipments', data)
}

/** 批量发货 */
export function batchShip(data: BatchShipmentForm) {
  return request.post<BatchShipResult>('/v1/shipments/batch', data)
}

/** 发货单列表 */
export function getShipmentList(params: ShipmentQuery) {
  return request.get<PageResult<Shipment>>('/v1/shipments', params)
}

/** 发货单详情（含轨迹） */
export function getShipmentDetail(id: number) {
  return request.get<ShipmentDetail>(`/v1/shipments/${id}`)
}

/** 物流轨迹列表 */
export function getShipmentTraces(id: number) {
  return request.get<LogisticsTrace[]>(`/v1/shipments/${id}/traces`)
}

/** 拉取物流轨迹 */
export function syncShipmentTrace(id: number) {
  return request.post<SyncTraceResult>(`/v1/shipments/${id}/sync-trace`)
}

/** 物流异常预警列表 */
export function getShipmentAlerts(params: PageQuery) {
  return request.get<PageResult<ShipmentAlert>>('/v1/shipments/alerts', params)
}
