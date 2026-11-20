// M1 同步任务与日志接口
import request from './request'
import type { PageQuery, PageResult } from '@/types'
import type { SyncTask, SyncTaskForm, SyncLog } from '@/types/platform'

/** 同步任务列表 */
export function getSyncTaskList(params: PageQuery) {
  return request.get<PageResult<SyncTask>>('/v1/sync-tasks', params)
}

/** 新增同步任务 */
export function createSyncTask(data: SyncTaskForm) {
  return request.post<SyncTask>('/v1/sync-tasks', data)
}

/** 编辑同步任务 */
export function updateSyncTask(id: number, data: SyncTaskForm) {
  return request.put<SyncTask>(`/v1/sync-tasks/${id}`, data)
}

/** 删除同步任务 */
export function deleteSyncTask(id: number) {
  return request.delete<null>(`/v1/sync-tasks/${id}`)
}

/** 启用/停用同步任务 */
export function updateSyncTaskStatus(id: number, status: number) {
  return request.patch<null>(`/v1/sync-tasks/${id}/status`, { status })
}

/** 手动触发一次同步 */
export function triggerSyncTask(id: number) {
  return request.post<null>(`/v1/sync-tasks/${id}/trigger`)
}

/** 同步日志列表 */
export function getSyncLogList(params: PageQuery) {
  return request.get<PageResult<SyncLog>>('/v1/sync-logs', params)
}

/** 同步日志详情 */
export function getSyncLogDetail(id: number) {
  return request.get<SyncLog>(`/v1/sync-logs/${id}`)
}

/** 按失败日志重新触发同步 */
export function retrySyncLog(id: number) {
  return request.post<null>(`/v1/sync-logs/${id}/retry`)
}
