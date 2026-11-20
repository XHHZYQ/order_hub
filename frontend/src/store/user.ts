// 用户状态：用户信息、角色、功能权限码、店铺范围
import { defineStore } from 'pinia'
import { getCurrentUser, login as loginApi, logout as logoutApi } from '@/api/auth'
import { getToken, setToken, removeToken } from '@/utils/auth'
import type { LoginParams, UserInfo } from '@/types/system'

interface UserState {
  token: string
  userInfo: UserInfo | null
  permissions: string[]
  shopIds: number[]
  loaded: boolean
}

export const useUserStore = defineStore('user', {
  state: (): UserState => ({
    token: getToken(),
    userInfo: null,
    permissions: [],
    shopIds: [],
    loaded: false,
  }),

  getters: {
    roles: (state) => state.userInfo?.roles ?? [],
    username: (state) => state.userInfo?.username ?? '',
    realName: (state) => state.userInfo?.real_name ?? '',
  },

  actions: {
    /** 登录并保存 Token */
    async login(params: LoginParams) {
      const res = await loginApi(params)
      this.token = res.token
      setToken(res.token)
      return res
    },

    /** 拉取当前用户信息（角色/权限码/店铺范围） */
    async fetchUserInfo() {
      const info = await getCurrentUser()
      this.userInfo = info
      this.permissions = info.permissions ?? []
      this.shopIds = info.shop_ids ?? []
      this.loaded = true
      return info
    },

    /** 登出：清空本地状态 */
    async logout() {
      try {
        await logoutApi()
      } catch {
        // 忽略登出接口异常，本地状态照常清理
      }
      this.reset()
    },

    reset() {
      this.token = ''
      this.userInfo = null
      this.permissions = []
      this.shopIds = []
      this.loaded = false
      removeToken()
    },

    /** 是否拥有指定功能权限（无权限码要求视为通过） */
    hasPermission(perm?: string) {
      if (!perm) return true
      // 超级管理员以 "*" 表示拥有全部权限
      return this.permissions.includes('*') || this.permissions.includes(perm)
    },
  },
})
