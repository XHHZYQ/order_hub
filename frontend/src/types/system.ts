// M10 系统管理类型定义

/** 登录参数 */
export interface LoginParams {
  username: string
  password: string
}

/** 登录结果 */
export interface LoginResult {
  token: string
}

/** 角色简要信息 */
export interface RoleBrief {
  id: number
  role_code: string
  role_name: string
}

/** 当前用户信息（/auth/me） */
export interface UserInfo {
  id: number
  username: string
  real_name: string
  phone?: string
  email?: string
  status: number
  last_login_time?: string
  roles: RoleBrief[]
  /** 功能权限码集合 */
  permissions: string[]
  /** 可访问店铺 ID 集合（数据权限） */
  shop_ids: number[]
}

/** 用户列表项 */
export interface UserItem {
  id: number
  username: string
  real_name: string
  phone?: string
  email?: string
  status: number
  last_login_time?: string
  roles: RoleBrief[]
  created_at: string
  updated_at?: string
}

/** 用户新增/编辑表单 */
export interface UserForm {
  id?: number
  username: string
  real_name: string
  phone?: string
  email?: string
  status: number
  password?: string
  role_ids: number[]
}

/** 角色列表项 */
export interface RoleItem {
  id: number
  role_code: string
  role_name: string
  remark?: string
  status: number
  created_at: string
  updated_at?: string
}

/** 角色表单 */
export interface RoleForm {
  id?: number
  role_code: string
  role_name: string
  remark?: string
  status: number
}

/** 功能权限节点（树） */
export interface PermissionNode {
  id: number
  parent_id: number
  perm_code: string
  perm_name: string
  perm_type: string
  route_path?: string
  icon?: string
  sort_no?: number
  children?: PermissionNode[]
}

/** 角色功能权限查询结果 */
export interface RolePermissionsResult {
  role_id: number
  permission_ids: number[]
}

/** 角色数据权限（店铺范围）查询结果 */
export interface RoleDataScopeResult {
  role_id: number
  shop_ids: number[]
}

/** 操作日志 */
export interface OperationLogItem {
  id: number
  user_id: number
  username: string
  module: string
  action: string
  target_type?: string
  target_id?: string
  content?: string
  ip?: string
  created_at: string
}
