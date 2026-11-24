<template>
  <el-tag :type="tag.type" :effect="effect" size="default" round>
    {{ tag.label }}
  </el-tag>
</template>

<script setup lang="ts">
// 状态标签：按场景统一配色（见《项目结构》7.4 状态配色约定）
import { computed } from 'vue'

type TagType = 'primary' | 'success' | 'warning' | 'danger' | 'info'

interface StatusOption {
  label: string
  type: TagType
}

interface Props {
  value: string | number | null | undefined
  /** 场景：common 通用启停 / auth 授权 / syncStatus 同步状态 / trigger 触发方式 / syncType 同步类型 / order 订单状态 / match 匹配状态 / inventoryLevel 库存水平 / shipment 发货单状态 / trace 轨迹节点 / push 回写状态 / afterSale 售后状态 / afterSaleType 售后类型 / refund 退款状态 / abnormal 异常类型 / billReconcile 账单对账状态 / billMatch 账单明细匹配 / diffType 对账差异类型 / diffHandle 差异处理状态 / custom */
  scene?: 'common' | 'auth' | 'syncStatus' | 'trigger' | 'syncType' | 'order' | 'match' | 'inventoryLevel' | 'shipment' | 'trace' | 'push' | 'afterSale' | 'afterSaleType' | 'refund' | 'abnormal' | 'billReconcile' | 'billMatch' | 'diffType' | 'diffHandle' | 'custom'
  /** 自定义映射（scene=custom 时使用） */
  options?: Record<string | number, StatusOption>
  effect?: 'light' | 'dark' | 'plain'
}

const props = withDefaults(defineProps<Props>(), {
  value: '',
  scene: 'common',
  options: undefined,
  effect: 'light',
})

const SCENE_MAP: Record<string, Record<string | number, StatusOption>> = {
  common: {
    1: { label: '启用', type: 'success' },
    0: { label: '停用', type: 'info' },
  },
  auth: {
    1: { label: '已授权', type: 'success' },
    0: { label: '未授权', type: 'warning' },
  },
  syncStatus: {
    待执行: { label: '待执行', type: 'info' },
    执行中: { label: '执行中', type: 'primary' },
    成功: { label: '成功', type: 'success' },
    部分失败: { label: '部分失败', type: 'warning' },
    失败: { label: '失败', type: 'danger' },
  },
  trigger: {
    定时: { label: '定时', type: 'info' },
    手动: { label: '手动', type: 'primary' },
  },
  syncType: {
    ORDER: { label: '订单', type: 'primary' },
    INVENTORY: { label: '库存', type: 'success' },
    AFTER_SALE: { label: '售后', type: 'warning' },
  },
  // 订单状态配色（见《项目结构》7.4；键为后端状态码）
  order: {
    PENDING_PAY: { label: '待付款', type: 'info' },
    PENDING_AUDIT: { label: '待审核', type: 'warning' },
    PENDING_SHIP: { label: '待发货', type: 'primary' },
    PART_SHIPPED: { label: '部分发货', type: 'warning' },
    SHIPPED: { label: '已发货', type: 'primary' },
    FINISHED: { label: '已完成', type: 'success' },
    CLOSED: { label: '已关闭', type: 'info' },
    AFTER_SALE: { label: '售后中', type: 'danger' },
  },
  // 匹配状态（是否已映射本地 SKU）
  match: {
    1: { label: '已匹配', type: 'success' },
    0: { label: '未匹配', type: 'warning' },
  },
  // 库存水平（见《项目结构》7.4：正常=成功、低于安全库存=警告、缺货=危险）
  inventoryLevel: {
    NORMAL: { label: '正常', type: 'success' },
    LOW: { label: '低于安全库存', type: 'warning' },
    OUT: { label: '缺货', type: 'danger' },
  },
  // 发货单物流状态
  shipment: {
    SHIPPED: { label: '已发货', type: 'primary' },
    IN_TRANSIT: { label: '运输中', type: 'primary' },
    SIGNED: { label: '已签收', type: 'success' },
    ABNORMAL: { label: '异常', type: 'danger' },
  },
  // 物流轨迹节点
  trace: {
    COLLECTED: { label: '已揽收', type: 'info' },
    IN_TRANSIT: { label: '运输中', type: 'primary' },
    ARRIVED: { label: '到达网点', type: 'primary' },
    DELIVERING: { label: '派送中', type: 'warning' },
    SIGNED: { label: '已签收', type: 'success' },
    ABNORMAL: { label: '异常', type: 'danger' },
  },
  // 回写平台状态
  push: {
    0: { label: '待回写', type: 'info' },
    1: { label: '成功', type: 'success' },
    2: { label: '失败', type: 'danger' },
  },
  // 售后状态
  afterSale: {
    PENDING: { label: '待处理', type: 'warning' },
    PROCESSING: { label: '处理中', type: 'primary' },
    WAIT_BUYER: { label: '等待买家', type: 'info' },
    WAIT_SELLER: { label: '等待商家', type: 'warning' },
    FINISHED: { label: '已完成', type: 'success' },
    CLOSED: { label: '已关闭', type: 'info' },
  },
  // 售后类型
  afterSaleType: {
    REFUND: { label: '退款', type: 'warning' },
    RETURN_REFUND: { label: '退货退款', type: 'danger' },
    EXCHANGE: { label: '换货', type: 'primary' },
  },
  // 退款状态
  refund: {
    NONE: { label: '无需退款', type: 'info' },
    PENDING: { label: '退款中', type: 'warning' },
    SUCCESS: { label: '退款成功', type: 'success' },
    FAILED: { label: '退款失败', type: 'danger' },
  },
  // 异常订单类型
  abnormal: {
    SYNC: { label: '同步异常', type: 'danger' },
    ADDRESS: { label: '地址异常', type: 'warning' },
    AMOUNT: { label: '金额异常', type: 'warning' },
    TIMEOUT: { label: '长时间未付/未发', type: 'info' },
  },
  // 账单对账状态（M8）
  billReconcile: {
    PENDING: { label: '待对账', type: 'warning' },
    MATCHING: { label: '对账中', type: 'primary' },
    RECONCILED: { label: '已对账', type: 'success' },
    CLOSED: { label: '已封账', type: 'info' },
  },
  // 账单明细匹配状态
  billMatch: {
    MATCHED: { label: '已匹配', type: 'success' },
    AMOUNT_DIFF: { label: '金额不一致', type: 'warning' },
    UNMATCHED: { label: '未匹配', type: 'danger' },
  },
  // 对账差异类型
  diffType: {
    LOCAL_MISSING: { label: '本地无单', type: 'danger' },
    BILL_MISSING: { label: '账单无单', type: 'warning' },
    AMOUNT_DIFF: { label: '金额不一致', type: 'warning' },
  },
  // 差异处理状态
  diffHandle: {
    PENDING: { label: '待处理', type: 'warning' },
    HANDLED: { label: '已处理', type: 'success' },
  },
}

const tag = computed<StatusOption>(() => {
  const map = props.scene === 'custom' ? props.options ?? {} : SCENE_MAP[props.scene] ?? {}
  const key = props.value as string | number
  if (map[key]) return map[key]
  // 兜底：直接展示原值
  return { label: props.value === '' || props.value === null || props.value === undefined ? '-' : String(props.value), type: 'info' }
})
</script>
