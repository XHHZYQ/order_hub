// 通用类型：统一响应体、分页、下拉选项

/** 统一响应体 */
export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}

/** 分页响应体 */
export interface PageResult<T> {
  list: T[]
  total: number
  page: number
  page_size: number
}

/** 分页查询参数 */
export interface PageQuery {
  page?: number
  page_size?: number
  [key: string]: unknown
}

/** 下拉选项 */
export interface Option {
  label: string
  value: string | number
  [key: string]: unknown
}

/** 后端平台下拉原始结构 */
export interface PlatformOptionRaw {
  platform_code: string
  platform_name: string
}

/** 后端店铺下拉原始结构 */
export interface ShopOptionRaw {
  id: number
  shop_name: string
  platform_code?: string
}
