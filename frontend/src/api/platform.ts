// M1 平台字典接口
import request from './request'
import type { PageQuery, PageResult, PlatformOptionRaw } from '@/types'
import type { Platform, PlatformForm } from '@/types/platform'

/** 平台列表 */
export function getPlatformList(params: PageQuery) {
  return request.get<PageResult<Platform>>('/v1/platforms', params)
}

/** 平台详情 */
export function getPlatformDetail(id: number) {
  return request.get<Platform>(`/v1/platforms/${id}`)
}

/** 新增平台 */
export function createPlatform(data: PlatformForm) {
  return request.post<Platform>('/v1/platforms', data)
}

/** 编辑平台 */
export function updatePlatform(id: number, data: PlatformForm) {
  return request.put<Platform>(`/v1/platforms/${id}`, data)
}

/** 删除平台 */
export function deletePlatform(id: number) {
  return request.delete<null>(`/v1/platforms/${id}`)
}

/** 启用/停用平台 */
export function updatePlatformStatus(id: number, status: number) {
  return request.patch<null>(`/v1/platforms/${id}/status`, { status })
}

/** 平台下拉选项（编码 + 名称） */
export function getPlatformOptions() {
  return request.get<PlatformOptionRaw[]>('/v1/platforms/options')
}
