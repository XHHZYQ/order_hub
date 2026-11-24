<template>
  <div
    class="stat-card glass-card"
    :class="{ 'stat-card--clickable': clickable }"
    @click="clickable && emit('click')"
  >
    <div class="stat-card__label">{{ label }}</div>
    <div class="stat-card__value" :style="color ? { color } : undefined">
      <AmountText v-if="money" :value="value" />
      <template v-else>{{ text }}</template>
      <span v-if="unit" class="stat-card__unit">{{ unit }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
// 指标卡：用于看板/汇总页的核心指标展示，支持金额与文本两种形态
import AmountText from '@/components/AmountText.vue'

interface Props {
  label: string
  /** 金额型取该值（与 AmountText 配合） */
  value?: number
  /** 文本型直接展示 */
  text?: string
  /** 是否为金额 */
  money?: boolean
  /** 单位后缀（如 小时、%） */
  unit?: string
  /** 数值颜色 */
  color?: string
  /** 是否可点击下钻 */
  clickable?: boolean
}

withDefaults(defineProps<Props>(), {
  value: 0,
  text: '0',
  money: false,
  unit: '',
  color: '',
  clickable: false,
})

const emit = defineEmits<{ click: [] }>()
</script>

<style scoped lang="scss">
.stat-card {
  &--clickable {
    cursor: pointer;
    transition: box-shadow 0.2s;

    &:hover {
      box-shadow: var(--shadow-hover);
    }
  }

  &__label {
    font-size: 13px;
    color: var(--color-text-secondary);
    margin-bottom: 8px;
  }

  &__value {
    font-size: 22px;
    font-weight: 600;
    color: var(--color-text-base);
    display: flex;
    align-items: baseline;
    gap: 4px;
  }

  &__unit {
    font-size: 13px;
    font-weight: 400;
    color: var(--color-text-secondary);
  }
}
</style>
