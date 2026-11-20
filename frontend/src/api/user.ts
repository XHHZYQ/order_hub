// M10 用户管理接口
import request from './request'
import type { PageQuery, PageResult } from '@/types'
import type { UserItem, UserForm } from '@/types/system'

/** 用户列表 */
export function getUserList(params: PageQuery) {
  return request.get<PageResult<UserItem>>('/v1/users', params)
}

/** 用户详情 */
export function getUserDetail(id: number) {
  return request.get<UserItem>(`/v1/users/${id}`)
}

/** 新增用户 */
export function createUser(data: UserForm) {
  return request.post<UserItem>('/v1/users', data)
}

/** 编辑用户 */
export function updateUser(id: number, data: UserForm) {
  return request.put<UserItem>(`/v1/users/${id}`, data)
}

/** 删除用户 */
export function deleteUser(id: number) {
  return request.delete<null>(`/v1/users/${id}`)
}

/** 启用/停用用户 */
export function updateUserStatus(id: number, status: number) {
  return request.patch<null>(`/v1/users/${id}/status`, { status })
}

/** 重置密码 */
export function resetUserPassword(id: number, password: string) {
  return request.post<null>(`/v1/users/${id}/reset-password`, { password })
}
