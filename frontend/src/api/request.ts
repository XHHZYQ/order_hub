// axios 封装：注入 Token、统一解包响应体、统一错误提示、分页参数约束
import axios, {
  type AxiosInstance,
  type AxiosRequestConfig,
  type AxiosResponse,
  type InternalAxiosRequestConfig,
} from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'
import { getToken, removeToken } from '@/utils/auth'
import type { ApiResponse } from '@/types'

/** 业务错误码 */
export const BizCode = {
  SUCCESS: 0,
  PARAM_ERROR: 1001,
  UNAUTHORIZED: 1002,
  NO_PERMISSION: 1003,
  NOT_FOUND: 1004,
} as const

/** page_size 上限（前后端双重限制） */
export const MAX_PAGE_SIZE = 100

const service: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// 请求拦截：注入 Token、约束分页参数
service.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    if (config.params && typeof config.params === 'object') {
      const params = config.params as Record<string, unknown>
      if (typeof params.page_size === 'number' && params.page_size > MAX_PAGE_SIZE) {
        params.page_size = MAX_PAGE_SIZE
      }
    }
    return config
  },
  (error) => Promise.reject(error),
)

// 响应拦截：统一解包 { code, message, data }
service.interceptors.response.use(
  (response: AxiosResponse<ApiResponse>) => {
    const res = response.data
    // 非 JSON 响应（如文件流）直接返回
    if (res === undefined || res === null || typeof res !== 'object' || !('code' in res)) {
      return response.data
    }
    if (res.code === BizCode.SUCCESS) {
      return res.data
    }
    if (res.code === BizCode.UNAUTHORIZED) {
      removeToken()
      ElMessage.error(res.message || '登录已失效，请重新登录')
      if (router.currentRoute.value.path !== '/login') {
        router.push({ path: '/login', query: { redirect: router.currentRoute.value.fullPath } })
      }
    } else {
      ElMessage.error(res.message || '请求失败')
    }
    return Promise.reject(new Error(res.message || 'Error'))
  },
  (error) => {
    const status = error?.response?.status
    let message = error?.message || '网络异常'
    if (status === 401) {
      removeToken()
      message = '登录已失效，请重新登录'
      if (router.currentRoute.value.path !== '/login') {
        router.push({ path: '/login' })
      }
    } else if (status === 403) {
      message = '无操作权限'
    } else if (status === 404) {
      message = '请求的资源不存在'
    } else if (status === 500) {
      message = '服务内部错误'
    } else if (error?.response?.data?.message) {
      message = error.response.data.message
    }
    ElMessage.error(message)
    return Promise.reject(error)
  },
)

/** 请求方法封装：返回值已解包为业务 data */
const request = {
  get<T = unknown>(url: string, params?: Record<string, unknown>, config?: AxiosRequestConfig) {
    return service.get<unknown, T>(url, { params, ...config })
  },
  post<T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig) {
    return service.post<unknown, T>(url, data, config)
  },
  put<T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig) {
    return service.put<unknown, T>(url, data, config)
  },
  patch<T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig) {
    return service.patch<unknown, T>(url, data, config)
  },
  delete<T = unknown>(url: string, params?: Record<string, unknown>, config?: AxiosRequestConfig) {
    return service.delete<unknown, T>(url, { params, ...config })
  },
}

export default request
export { service as axiosInstance }
