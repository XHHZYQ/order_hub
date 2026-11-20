// M10 登录认证接口
import request from './request'
import type { LoginParams, LoginResult, UserInfo } from '@/types/system'

/** 登录 */
export function login(data: LoginParams) {
  return request.post<LoginResult>('/v1/auth/login', data)
}

/** 登出 */
export function logout() {
  return request.post<null>('/v1/auth/logout')
}

/** 当前用户信息（角色、功能权限码、店铺范围） */
export function getCurrentUser() {
  return request.get<UserInfo>('/v1/auth/me')
}
