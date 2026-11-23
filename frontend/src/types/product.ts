// M4 商品与 SKU 映射类型定义（字段名与《数据库设计》4.3 一致）

/** 本地商品（SPU） */
export interface Product {
  id: number
  spu_code: string
  spu_name: string
  category_name?: string
  brand?: string
  unit?: string
  status: number
  remark?: string
  /** 该 SPU 下 SKU 数量（列表冗余展示） */
  sku_count?: number
  created_at: string
  updated_at?: string
}

/** 本地商品表单 */
export interface ProductForm {
  id?: number
  spu_code: string
  spu_name: string
  category_name?: string
  brand?: string
  unit?: string
  status: number
  remark?: string
}

/** 本地 SKU */
export interface Sku {
  id: number
  sku_code: string
  spu_id: number
  sku_name: string
  spec_desc?: string
  cost_price?: number
  sale_price?: number
  status: number
  created_at?: string
  updated_at?: string
}

/** 本地 SKU 表单 */
export interface SkuForm {
  id?: number
  sku_code: string
  sku_name: string
  spec_desc?: string
  cost_price?: number
  sale_price?: number
  status: number
}

/** 平台商品 */
export interface PlatformProduct {
  id: number
  shop_id: number
  shop_name?: string
  platform_code: string
  platform_name?: string
  platform_product_id: string
  product_title: string
  category_name?: string
  status?: string
  sku_count?: number
  matched_count?: number
  sync_time?: string
  created_at?: string
  /** 详情接口返回的平台规格 */
  skus?: PlatformSku[]
}

/** 平台商品规格 */
export interface PlatformSku {
  id: number
  platform_product_id: number
  shop_id: number
  platform_code?: string
  platform_sku_id: string
  sku_name: string
  spec_desc?: string
  outer_sku_code?: string
  price?: number
  platform_stock?: number
  is_matched: number
  sync_time?: string
}

/** SKU 映射 */
export interface SkuMapping {
  id: number
  platform_code: string
  platform_name?: string
  shop_id: number
  shop_name?: string
  platform_sku_id: string
  platform_sku_name?: string
  sku_id: number
  sku_code: string
  sku_name?: string
  status: number
  remark?: string
  created_at?: string
  updated_at?: string
}

/** SKU 映射表单 */
export interface SkuMappingForm {
  id?: number
  platform_code?: string
  shop_id: number | undefined
  platform_sku_id: string
  platform_sku_name?: string
  sku_id: number | undefined
  sku_code?: string
  status: number
  remark?: string
}

/** 未匹配平台商品/规格 */
export interface UnmatchedSku {
  id: number
  platform_code: string
  shop_id: number
  shop_name?: string
  platform_sku_id: string
  platform_sku_name?: string
  sku_name?: string
  outer_sku_code?: string
  product_title?: string
}

/** 批量维护映射单行（平台规格 ID → 本地 SKU 编码） */
export interface SkuMappingBatchItem {
  platform_sku_id: string
  sku_code: string
}

/** 批量维护映射入参 */
export interface SkuMappingBatchForm {
  shop_id: number | undefined
  platform_code?: string
  items: SkuMappingBatchItem[]
}

/** 映射导入结果 */
export interface MappingImportResult {
  total: number
  success_count: number
  fail_count: number
  fail_reasons?: string[]
}
