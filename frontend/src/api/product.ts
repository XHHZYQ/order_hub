// M4 商品与 SKU 映射接口
import request from './request'
import type { PageQuery, PageResult } from '@/types'
import type {
  Product,
  ProductForm,
  Sku,
  SkuForm,
  PlatformProduct,
  SkuMapping,
  SkuMappingForm,
  SkuMappingBatchForm,
  UnmatchedSku,
  MappingImportResult,
} from '@/types/product'

// ---------- 本地商品（SPU）与 SKU ----------

/** 本地商品（SPU）列表 */
export function getProductList(params: PageQuery) {
  return request.get<PageResult<Product>>('/v1/products', params)
}

/** 商品详情（含 SKU） */
export function getProductDetail(id: number) {
  return request.get<Product>(`/v1/products/${id}`)
}

/** 新增本地商品 */
export function createProduct(data: ProductForm) {
  return request.post<Product>('/v1/products', data)
}

/** 编辑本地商品 */
export function updateProduct(id: number, data: ProductForm) {
  return request.put<Product>(`/v1/products/${id}`, data)
}

/** 删除本地商品 */
export function deleteProduct(id: number) {
  return request.delete<null>(`/v1/products/${id}`)
}

/** 商品下的 SKU 列表 */
export function getProductSkus(id: number, params?: PageQuery) {
  return request.get<Sku[]>(`/v1/products/${id}/skus`, params)
}

/** 新增 SKU */
export function createSku(spuId: number, data: SkuForm) {
  return request.post<Sku>(`/v1/products/${spuId}/skus`, data)
}

/** 编辑 SKU */
export function updateSku(id: number, data: SkuForm) {
  return request.put<Sku>(`/v1/skus/${id}`, data)
}

/** 删除 SKU */
export function deleteSku(id: number) {
  return request.delete<null>(`/v1/skus/${id}`)
}

// ---------- 平台商品与映射 ----------

/** 平台商品列表（按店铺/平台筛选） */
export function getPlatformProductList(params: PageQuery) {
  return request.get<PageResult<PlatformProduct>>('/v1/platform-products', params)
}

/** 平台商品详情（含平台规格） */
export function getPlatformProductDetail(id: number) {
  return request.get<PlatformProduct>(`/v1/platform-products/${id}`)
}

/** SKU 映射列表 */
export function getSkuMappingList(params: PageQuery) {
  return request.get<PageResult<SkuMapping>>('/v1/sku-mappings', params)
}

/** 新增映射（平台 SKU → 本地 SKU） */
export function createSkuMapping(data: SkuMappingForm) {
  return request.post<SkuMapping>('/v1/sku-mappings', data)
}

/** 修改映射 */
export function updateSkuMapping(id: number, data: SkuMappingForm) {
  return request.put<SkuMapping>(`/v1/sku-mappings/${id}`, data)
}

/** 删除映射 */
export function deleteSkuMapping(id: number) {
  return request.delete<null>(`/v1/sku-mappings/${id}`)
}

/** 批量维护映射 */
export function batchSkuMapping(data: SkuMappingBatchForm) {
  return request.post<MappingImportResult>('/v1/sku-mappings/batch', data)
}

/** 未匹配平台商品/规格列表 */
export function getUnmatchedMappings(params: PageQuery) {
  return request.get<PageResult<UnmatchedSku>>('/v1/sku-mappings/unmatched', params)
}

/** 导入映射文件 */
export function importSkuMappings(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  return request.post<MappingImportResult>('/v1/sku-mappings/import', formData)
}

/** 导出映射文件（返回文件流） */
export function exportSkuMappings(params: PageQuery) {
  return request.get<Blob>('/v1/sku-mappings/export', params, { responseType: 'blob' })
}
