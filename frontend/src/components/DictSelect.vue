<template>
  <el-select
    :model-value="modelValue"
    :placeholder="placeholder"
    :clearable="clearable"
    :filterable="filterable"
    :multiple="multiple"
    :disabled="disabled"
    :loading="loading"
    :style="{ width }"
    @update:model-value="handleChange"
    @visible-change="handleVisible"
  >
    <el-option
      v-for="opt in options"
      :key="opt.value"
      :label="opt.label"
      :value="opt.value"
    />
  </el-select>
</template>

<script setup lang="ts">
// 字典下拉：平台 / 店铺 / 状态 / 同步类型等
import { computed, ref, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import {
  useDictStore,
  SYNC_TYPE_DICT,
  SYNC_STATUS_DICT,
  TRIGGER_TYPE_DICT,
  ENABLE_STATUS_DICT,
  AUTH_STATUS_DICT,
  ORDER_STATUS_DICT,
  ORDER_SOURCE_DICT,
  INVENTORY_FLOW_TYPE_DICT,
  INVENTORY_SOURCE_TYPE_DICT,
  INVENTORY_STATUS_DICT,
  INVENTORY_LEVEL_DICT,
  MATCH_STATUS_DICT,
  ABNORMAL_TYPE_DICT,
  SHIPMENT_STATUS_DICT,
  PUSH_STATUS_DICT,
  TRACE_STATUS_DICT,
  AFTER_SALE_TYPE_DICT,
  AFTER_SALE_STATUS_DICT,
  REFUND_STATUS_DICT,
} from '@/store/dict'
import type { Option } from '@/types'

type DictType =
  | 'platform'
  | 'shop'
  | 'enableStatus'
  | 'authStatus'
  | 'syncType'
  | 'syncStatus'
  | 'trigger'
  | 'orderStatus'
  | 'orderSource'
  | 'flowType'
  | 'sourceType'
  | 'inventoryStatus'
  | 'inventoryLevel'
  | 'matchStatus'
  | 'abnormalType'
  | 'shipmentStatus'
  | 'pushStatus'
  | 'traceStatus'
  | 'afterSaleType'
  | 'afterSaleStatus'
  | 'refundStatus'

interface Props {
  modelValue?: string | number | (string | number)[] | null
  type: DictType
  placeholder?: string
  clearable?: boolean
  filterable?: boolean
  multiple?: boolean
  disabled?: boolean
  width?: string
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: undefined,
  placeholder: '请选择',
  clearable: true,
  filterable: true,
  multiple: false,
  disabled: false,
  width: '180px',
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: any): void
}>()

const dictStore = useDictStore()
const { platformOptions, shopOptions } = storeToRefs(dictStore)
const loading = ref(false)

const options = computed<Option[]>(() => {
  switch (props.type) {
    case 'platform':
      return platformOptions.value
    case 'shop':
      return shopOptions.value
    case 'enableStatus':
      return ENABLE_STATUS_DICT
    case 'authStatus':
      return AUTH_STATUS_DICT
    case 'syncType':
      return SYNC_TYPE_DICT
    case 'syncStatus':
      return SYNC_STATUS_DICT
    case 'trigger':
      return TRIGGER_TYPE_DICT
    case 'orderStatus':
      return ORDER_STATUS_DICT
    case 'orderSource':
      return ORDER_SOURCE_DICT
    case 'flowType':
      return INVENTORY_FLOW_TYPE_DICT
    case 'sourceType':
      return INVENTORY_SOURCE_TYPE_DICT
    case 'inventoryStatus':
      return INVENTORY_STATUS_DICT
    case 'inventoryLevel':
      return INVENTORY_LEVEL_DICT
    case 'matchStatus':
      return MATCH_STATUS_DICT
    case 'abnormalType':
      return ABNORMAL_TYPE_DICT
    case 'shipmentStatus':
      return SHIPMENT_STATUS_DICT
    case 'pushStatus':
      return PUSH_STATUS_DICT
    case 'traceStatus':
      return TRACE_STATUS_DICT
    case 'afterSaleType':
      return AFTER_SALE_TYPE_DICT
    case 'afterSaleStatus':
      return AFTER_SALE_STATUS_DICT
    case 'refundStatus':
      return REFUND_STATUS_DICT
    default:
      return []
  }
})

function handleChange(value: any) {
  emit('update:modelValue', value)
}

async function loadRemote() {
  try {
    if (props.type === 'platform' && !dictStore.platformLoaded) {
      loading.value = true
      await dictStore.loadPlatformOptions()
    } else if (props.type === 'shop' && !dictStore.shopLoaded) {
      loading.value = true
      await dictStore.loadShopOptions()
    }
  } finally {
    loading.value = false
  }
}

function handleVisible(visible: boolean) {
  if (visible) loadRemote()
}

onMounted(() => {
  if (props.type === 'platform' || props.type === 'shop') loadRemote()
})
</script>
