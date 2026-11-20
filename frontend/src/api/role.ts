// M10 角色与权限接口
import request from './request'
import type { PageQuery, PageResult } from '@/types'
import type { RoleItem, RoleForm, PermissionNode, RolePermissionsResult, RoleDataScopeResult } from '@/types/system'

/** 角色列表 */
export function getRoleList(params?: PageQuery) {
  return request.get<PageResult<RoleItem>>('/v1/roles', params)
}

/** 角色详情 */
export function getRoleDetail(id: number) {
  return request.get<RoleItem>(`/v1/roles/${id}`)
}

/** 新增角色 */
export function createRole(data: RoleForm) {
  return request.post<RoleItem>('/v1/roles', data)
}

/** 编辑角色 */
export function updateRole(id: number, data: RoleForm) {
  return request.put<RoleItem>(`/v1/roles/${id}`, data)
}

/** 删除角色 */
export function deleteRole(id: number) {
  return request.delete<null>(`/v1/roles/${id}`)
}

/** 功能权限树（菜单 + 按钮） */
export function getPermissionTree() {
  return request.get<PermissionNode[]>('/v1/permissions/tree')
}

/** 查询角色功能权限（已选权限 ID 集合） */
export function getRolePermissions(id: number) {
  return request.get<RolePermissionsResult>(`/v1/roles/${id}/permissions`)
}

/** 分配角色功能权限 */
export function updateRolePermissions(id: number, permissionIds: number[]) {
  return request.put<null>(`/v1/roles/${id}/permissions`, { permission_ids: permissionIds })
}

/** 查询角色数据权限（店铺 ID 集合） */
export function getRoleDataScope(id: number) {
  return request.get<RoleDataScopeResult>(`/v1/roles/${id}/data-scope`)
}

/** 配置角色数据权限（店铺范围） */
export function updateRoleDataScope(id: number, shopIds: number[]) {
  return request.put<null>(`/v1/roles/${id}/data-scope`, { shop_ids: shopIds })
}
