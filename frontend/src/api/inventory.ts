// M5 库存同步与防超卖接口
import request from './request'
import type { PageQuery, PageResult } from '@/types'
import type {
  Inventory,
  InventoryForm,
  InventoryFlow,
  InventoryShare,
  InventoryShareForm,
  InventoryAlert,
  InventoryAlertConfig,
  InventoryAlertConfigForm,
  StocktakeForm,
  StocktakeResult,
} from '@/types/inventory'

// ---------- 库存 ----------

/** 库存列表（主库存/占用/可售） */
export function getInventoryList(params: PageQuery) {
  return request.get<PageResult<Inventory>>('/v1/inventory', params)
}

/** 单个 SKU 库存详情 */
export function getInventoryDetail(skuId: number) {
  return request.get<Inventory>(`/v1/inventory/${skuId}`)
}

/** 编辑主库存（生成流水） */
export function updateInventory(skuId: number, data: InventoryForm) {
  return request.put<Inventory>(`/v1/inventory/${skuId}`, data)
}

/** 可售库存回写平台 */
export function pushInventory(skuId: number) {
  return request.post<{ success: boolean; message?: string }>(`/v1/inventory/${skuId}/push`)
}

// ---------- 库存流水 ----------

/** 库存流水列表（类型/来源单号/时间） */
export function getInventoryFlows(params: PageQuery) {
  return request.get<PageResult<InventoryFlow>>('/v1/inventory/flows', params)
}

// ---------- 库存共享 ----------

/** 库存共享配置列表 */
export function getInventoryShares(params: PageQuery) {
  return request.get<PageResult<InventoryShare>>('/v1/inventory/shares', params)
}

/** 新增共享配置（SKU + 店铺范围） */
export function createInventoryShare(data: InventoryShareForm) {
  return request.post<InventoryShare>('/v1/inventory/shares', data)
}

/** 修改共享配置 */
export function updateInventoryShare(id: number, data: InventoryShareForm) {
  return request.put<InventoryShare>(`/v1/inventory/shares/${id}`, data)
}

/** 删除共享配置 */
export function deleteInventoryShare(id: number) {
  return request.delete<null>(`/v1/inventory/shares/${id}`)
}

// ---------- 库存预警 ----------

/** 库存预警列表（低于安全阈值的 SKU） */
export function getInventoryAlerts(params: PageQuery) {
  return request.get<PageResult<InventoryAlert>>('/v1/inventory/alerts', params)
}

/** 库存预警配置列表 */
export function getInventoryAlertConfigs(params: PageQuery) {
  return request.get<PageResult<InventoryAlertConfig>>('/v1/inventory/alert-configs', params)
}

/** 编辑安全库存阈值 */
export function updateInventoryAlertConfig(id: number, data: InventoryAlertConfigForm) {
  return request.put<InventoryAlertConfig>(`/v1/inventory/alert-configs/${id}`, data)
}

// ---------- 库存盘点 ----------

/** 库存盘点（录入实盘，生成调整流水） */
export function submitStocktake(data: StocktakeForm) {
  return request.post<StocktakeResult>('/v1/inventory/stocktake', data)
}
