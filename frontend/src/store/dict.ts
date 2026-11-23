// 字典缓存：平台、店铺下拉与静态状态字典
import { defineStore } from 'pinia'
import { getPlatformOptions } from '@/api/platform'
import { getShopOptions } from '@/api/shop'
import type { Option } from '@/types'

// 静态字典（与《数据库设计》6 节字典保持一致）
export const SYNC_TYPE_DICT: Option[] = [
  { label: '订单', value: 'ORDER' },
  { label: '库存', value: 'INVENTORY' },
  { label: '售后', value: 'AFTER_SALE' },
]

export const SYNC_STATUS_DICT: Option[] = [
  { label: '待执行', value: '待执行' },
  { label: '执行中', value: '执行中' },
  { label: '成功', value: '成功' },
  { label: '部分失败', value: '部分失败' },
  { label: '失败', value: '失败' },
]

export const TRIGGER_TYPE_DICT: Option[] = [
  { label: '定时', value: '定时' },
  { label: '手动', value: '手动' },
]

export const ENABLE_STATUS_DICT: Option[] = [
  { label: '启用', value: 1 },
  { label: '停用', value: 0 },
]

export const AUTH_STATUS_DICT: Option[] = [
  { label: '已授权', value: 1 },
  { label: '未授权', value: 0 },
]

// 订单统一状态（8 态，与《数据库设计》6.2 一致；后端以状态码存储，前端映射中文展示）
export const ORDER_STATUS_DICT: Option[] = [
  { label: '待付款', value: 'PENDING_PAY' },
  { label: '待审核', value: 'PENDING_AUDIT' },
  { label: '待发货', value: 'PENDING_SHIP' },
  { label: '部分发货', value: 'PART_SHIPPED' },
  { label: '已发货', value: 'SHIPPED' },
  { label: '已完成', value: 'FINISHED' },
  { label: '已关闭', value: 'CLOSED' },
  { label: '售后中', value: 'AFTER_SALE' },
]

// 订单来源
export const ORDER_SOURCE_DICT: Option[] = [
  { label: '平台', value: '平台' },
  { label: '手工', value: '手工' },
]

// 库存变动类型（inventory_flow.flow_type，见《数据库设计》6.3；后端以类型码存储）
export const INVENTORY_FLOW_TYPE_DICT: Option[] = [
  { label: '采购入库', value: 'PURCHASE_IN' },
  { label: '订单占用', value: 'ORDER_OCCUPY' },
  { label: '订单释放', value: 'ORDER_RELEASE' },
  { label: '发货扣减', value: 'SHIP_DEDUCT' },
  { label: '退货入库', value: 'RETURN_IN' },
  { label: '盘点调整', value: 'STOCKTAKE' },
]

// 库存流水来源类型（inventory_flow.source_type）
export const INVENTORY_SOURCE_TYPE_DICT: Option[] = [
  { label: '订单', value: '订单' },
  { label: '盘点', value: '盘点' },
  { label: '采购', value: '采购' },
]

// 库存状态（inventory.status：1 正常 / 0 停用）
export const INVENTORY_STATUS_DICT: Option[] = [
  { label: '正常', value: 1 },
  { label: '停用', value: 0 },
]

// 库存水平（预警场景：正常 / 低于安全库存 / 缺货）
export const INVENTORY_LEVEL_DICT: Option[] = [
  { label: '正常', value: 'NORMAL' },
  { label: '低于安全库存', value: 'LOW' },
  { label: '缺货', value: 'OUT' },
]

// 匹配状态（is_matched）
export const MATCH_STATUS_DICT: Option[] = [
  { label: '已匹配', value: 1 },
  { label: '未匹配', value: 0 },
]

/** 按字典取中文标签（找不到返回原值，空值返回 '-'） */
export function dictLabel(dict: Option[], value: unknown): string {
  if (value === undefined || value === null || value === '') return '-'
  const hit = dict.find((item) => item.value === value)
  return hit ? hit.label : String(value)
}

interface DictState {
  platformOptions: Option[]
  shopOptions: Option[]
  platformLoaded: boolean
  shopLoaded: boolean
}

export const useDictStore = defineStore('dict', {
  state: (): DictState => ({
    platformOptions: [],
    shopOptions: [],
    platformLoaded: false,
    shopLoaded: false,
  }),

  actions: {
    /** 加载平台下拉（带缓存） */
    async loadPlatformOptions(force = false) {
      if (this.platformLoaded && !force) return this.platformOptions
      const list = await getPlatformOptions()
      this.platformOptions = (list ?? []).map((item) => ({
        label: item.platform_name,
        value: item.platform_code,
      }))
      this.platformLoaded = true
      return this.platformOptions
    },

    /** 加载店铺下拉（带缓存，受当前用户数据权限过滤） */
    async loadShopOptions(force = false) {
      if (this.shopLoaded && !force) return this.shopOptions
      const list = await getShopOptions()
      this.shopOptions = (list ?? []).map((item) => ({
        label: item.shop_name,
        value: item.id,
      }))
      this.shopLoaded = true
      return this.shopOptions
    },
  },
})
