// M8 财务对账接口
import request from './request'
import type { PageResult } from '@/types'
import type {
  Bill,
  BillDetail,
  BillMatchResult,
  BillQuery,
  BillDetailQuery,
  DiffQuery,
  DiffHandleForm,
  ReconcileDiff,
  SettlementQuery,
  SettlementSummary,
  ProfitQuery,
  ProfitSummary,
  ExportQuery,
  BillImportForm,
  MockFileQuery,
} from '@/types/finance'

// ------------------------------ 账单 ------------------------------ //

/** 账单批次列表 */
export function getBillList(params: BillQuery) {
  return request.get<PageResult<Bill>>('/v1/bills', params)
}

/** 账单批次详情 */
export function getBillDetail(id: number) {
  return request.get<Bill>(`/v1/bills/${id}`)
}

/** 账单明细列表 */
export function getBillDetails(id: number, params: BillDetailQuery) {
  return request.get<PageResult<BillDetail>>(`/v1/bills/${id}/details`, params)
}

/** 导入平台账单文件（multipart，file 与 auto_generate 二选一） */
export function importBill(form: BillImportForm) {
  const formData = new FormData()
  formData.append('platform_code', form.platform_code)
  formData.append('shop_id', String(form.shop_id))
  formData.append('bill_period', form.bill_period)
  formData.append('auto_generate', String(form.auto_generate ?? false))
  if (form.file) formData.append('file', form.file)
  return request.post<Bill>('/v1/bills/import', formData)
}

/** 生成并下载模拟账单文件（演示用，返回文件流） */
export function downloadMockBillFile(params: MockFileQuery) {
  return request.get<Blob>('/v1/bills/mock-file', params as unknown as Record<string, unknown>, {
    responseType: 'blob',
  })
}

/** 触发账单与订单匹配 */
export function matchBill(id: number) {
  return request.post<BillMatchResult>(`/v1/bills/${id}/match`)
}

/** 对账期封账 */
export function closeBill(id: number) {
  return request.post<Bill>(`/v1/bills/${id}/close`)
}

// ------------------------------ 差异 / 结算 / 毛利 / 导出 ------------------------------ //

/** 对账差异列表 */
export function getDifferences(params: DiffQuery) {
  return request.get<PageResult<ReconcileDiff>>('/v1/reconciliations/differences', params)
}

/** 处理对账差异 */
export function handleDifference(id: number, data: DiffHandleForm) {
  return request.post<{ id: number; handle_status: string; handle_remark: string }>(
    `/v1/reconciliations/differences/${id}/handle`,
    data,
  )
}

/** 结算汇总（应收/平台费用/实收，按平台或店铺分组） */
export function getSettlements(params: SettlementQuery) {
  return request.get<SettlementSummary>('/v1/reconciliations/settlements', params as Record<string, unknown>)
}

/** 毛利核算（订单/商品两个维度） */
export function getProfits(params: ProfitQuery) {
  return request.get<ProfitSummary>('/v1/reconciliations/profits', params as Record<string, unknown>)
}

/** 导出对账明细/差异/汇总（返回文件流） */
export function exportReconciliation(params: ExportQuery) {
  return request.get<Blob>('/v1/reconciliations/export', params as unknown as Record<string, unknown>, {
    responseType: 'blob',
  })
}
