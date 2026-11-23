// M5 库存同步与防超卖类型定义（字段名与《数据库设计》4.3 一致）

/** 库存（主库存 / 占用 / 可售） */
export interface Inventory {
  id: number
  sku_id: number
  sku_code: string
  sku_name?: string
  spu_name?: string
  spec_desc?: string
  /** 主库存 */
  main_qty: number
  /** 占用库存 */
  occupied_qty: number
  /** 可售库存（后端返回或前端按 main_qty - occupied_qty 计算） */
  available_qty?: number
  /** 安全库存阈值 */
  alert_qty?: number
  status: number
  updated_at?: string
}

/** 编辑主库存入参 */
export interface InventoryForm {
  main_qty: number
  remark?: string
}

/** 库存流水 */
export interface InventoryFlow {
  id: number
  sku_id: number
  sku_code: string
  sku_name?: string
  /** 变动类型码：PURCHASE_IN / ORDER_OCCUPY / ... */
  flow_type: string
  /** 变动数量（正负） */
  change_qty: number
  before_qty: number
  after_qty: number
  source_type?: string
  source_no?: string
  remark?: string
  operator?: string
  created_at: string
}

/** 库存共享配置 */
export interface InventoryShare {
  id: number
  sku_id: number
  sku_code: string
  sku_name?: string
  shop_id: number
  shop_name?: string
  platform_code?: string
  platform_name?: string
  status: number
  created_at?: string
}

/** 库存共享配置表单 */
export interface InventoryShareForm {
  id?: number
  sku_id: number | undefined
  shop_id: number | undefined
  platform_code?: string
  status: number
}

/** 库存预警（低于安全阈值的 SKU） */
export interface InventoryAlert {
  id: number
  sku_id: number
  sku_code: string
  sku_name?: string
  main_qty?: number
  occupied_qty?: number
  available_qty?: number
  alert_qty: number
  is_enabled: number
  /** 库存状态码：NORMAL / LOW / OUT */
  stock_status?: string
  updated_at?: string
}

/** 库存预警配置 */
export interface InventoryAlertConfig {
  id: number
  sku_id: number
  sku_code: string
  sku_name?: string
  alert_qty: number
  is_enabled: number
  updated_at?: string
}

/** 库存预警配置表单 */
export interface InventoryAlertConfigForm {
  id?: number
  alert_qty: number
  is_enabled: number
}

/** 盘点单行录入 */
export interface StocktakeItemForm {
  sku_id: number
  sku_code?: string
  actual_qty: number
}

/** 盘点提交入参 */
export interface StocktakeForm {
  remark?: string
  items: StocktakeItemForm[]
}

/** 盘点结果单行 */
export interface StocktakeResultItem {
  sku_id: number
  sku_code: string
  sku_name?: string
  before_qty: number
  actual_qty: number
  change_qty: number
}

/** 盘点结果 */
export interface StocktakeResult {
  total: number
  gain_count: number
  loss_count: number
  items: StocktakeResultItem[]
}
