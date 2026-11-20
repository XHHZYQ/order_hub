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
  /** 场景：common 通用启停 / auth 授权 / syncStatus 同步状态 / trigger 触发方式 / syncType 同步类型 */
  scene?: 'common' | 'auth' | 'syncStatus' | 'trigger' | 'syncType' | 'custom'
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
}

const tag = computed<StatusOption>(() => {
  const map = props.scene === 'custom' ? props.options ?? {} : SCENE_MAP[props.scene] ?? {}
  const key = props.value as string | number
  if (map[key]) return map[key]
  // 兜底：直接展示原值
  return { label: props.value === '' || props.value === null || props.value === undefined ? '-' : String(props.value), type: 'info' }
})
</script>
