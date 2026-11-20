// M1 店铺接口
import request from './request'
import type { PageQuery, PageResult, ShopOptionRaw } from '@/types'
import type { Shop, ShopForm } from '@/types/platform'

/** 店铺列表 */
export function getShopList(params: PageQuery) {
  return request.get<PageResult<Shop>>('/v1/shops', params)
}

/** 店铺详情 */
export function getShopDetail(id: number) {
  return request.get<Shop>(`/v1/shops/${id}`)
}

/** 新增店铺（含模拟授权） */
export function createShop(data: ShopForm) {
  return request.post<Shop>('/v1/shops', data)
}

/** 编辑店铺 */
export function updateShop(id: number, data: ShopForm) {
  return request.put<Shop>(`/v1/shops/${id}`, data)
}

/** 删除店铺 */
export function deleteShop(id: number) {
  return request.delete<null>(`/v1/shops/${id}`)
}

/** 启用/停用店铺 */
export function updateShopStatus(id: number, status: number) {
  return request.patch<null>(`/v1/shops/${id}/status`, { status })
}

/** 重新授权（模拟生成访问凭证） */
export function authorizeShop(id: number) {
  return request.post<Shop>(`/v1/shops/${id}/authorize`)
}

/** 店铺下拉选项（按当前用户数据权限过滤） */
export function getShopOptions() {
  return request.get<ShopOptionRaw[]>('/v1/shops/options')
}
