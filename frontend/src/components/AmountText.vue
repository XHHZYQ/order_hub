<template>
  <span :class="['amount-text', { 'amount-text--negative': isNegative }]">{{ text }}</span>
</template>

<script setup lang="ts">
// 金额展示：千分位 + 两位小数 + ¥ 前缀
import { computed } from 'vue'
import { formatAmount } from '@/utils/format'

interface Props {
  value?: number | string | null
  symbol?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  value: 0,
  symbol: true,
})

const text = computed(() => formatAmount(props.value, props.symbol))
const isNegative = computed(() => {
  const num = typeof props.value === 'string' ? Number(props.value) : props.value ?? 0
  return num < 0
})
</script>

<style scoped lang="scss">
.amount-text {
  font-variant-numeric: tabular-nums;
  font-feature-settings: 'tnum';

  &--negative {
    color: var(--color-danger);
  }
}
</style>
