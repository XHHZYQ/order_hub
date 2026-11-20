// M1 平台与店铺管理类型定义

/** 平台字典 */
export interface Platform {
  id: number
  platform_code: string
  platform_name: string
  icon?: string
  sort_no: number
  status: number
  remark?: string
  created_at: string
  updated_at?: string
}

/** 平台表单 */
export interface PlatformForm {
  id?: number
  platform_code: string
  platform_name: string
  icon?: string
  sort_no: number
  status: number
  remark?: string
}

/** 店铺 */
export interface Shop {
  id: number
  platform_code: string
  platform_name?: string
  shop_code: string
  shop_name: string
  seller_account: string
  auth_status: number
  auth_token?: string
  contact_name?: string
  contact_phone?: string
  status: number
  remark?: string
  created_at: string
  updated_at?: string
}

/** 店铺表单（新增时含模拟授权） */
export interface ShopForm {
  id?: number
  platform_code: string
  shop_code: string
  shop_name: string
  seller_account: string
  contact_name?: string
  contact_phone?: string
  status: number
  remark?: string
}

/** 同步任务 */
export interface SyncTask {
  id: number
  shop_id: number
  shop_name?: string
  platform_code?: string
  sync_type: string
  cron_expr: string
  start_time: string
  last_sync_time?: string
  status: number
  remark?: string
  created_at: string
  updated_at?: string
}

/** 同步任务表单 */
export interface SyncTaskForm {
  id?: number
  shop_id: number | undefined
  sync_type: string
  cron_expr: string
  start_time: string
  status: number
  remark?: string
}

/** 同步日志 */
export interface SyncLog {
  id: number
  task_id: number
  shop_id: number
  shop_name?: string
  sync_type: string
  start_time: string
  end_time: string
  status: string
  success_count: number
  fail_count: number
  cost_ms: number
  fail_reason?: string
  trigger_type: string
  created_at: string
}
