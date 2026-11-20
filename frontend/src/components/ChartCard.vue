<template>
  <div class="chart-card glass-card">
    <div class="chart-card__header">
      <div class="chart-card__title">{{ title }}</div>
      <div class="chart-card__extra">
        <slot name="extra" />
      </div>
    </div>
    <div ref="chartRef" class="chart-card__chart" :style="{ height: `${height}px` }" />
  </div>
</template>

<script setup lang="ts">
// ECharts 图表卡片封装（标题 + 工具栏 + 图表），基础实现
import { onBeforeUnmount, onMounted, ref, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

interface Props {
  title?: string
  /** 图表高度（px） */
  height?: number
  /** ECharts option */
  option?: echarts.EChartsOption
}

const props = withDefaults(defineProps<Props>(), {
  title: '',
  height: 320,
  option: undefined,
})

const chartRef = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null

function render() {
  if (!chart) return
  if (props.option) chart.setOption(props.option, true)
}

function init() {
  if (!chartRef.value) return
  chart = echarts.init(chartRef.value)
  render()
}

function resize() {
  chart?.resize()
}

watch(
  () => props.option,
  () => {
    nextTick(render)
  },
  { deep: true },
)

onMounted(() => {
  init()
  window.addEventListener('resize', resize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resize)
  chart?.dispose()
  chart = null
})

defineExpose({ resize, getInstance: () => chart })
</script>

<style scoped lang="scss">
.chart-card {
  &__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
  }

  &__title {
    font-size: 16px;
    font-weight: 600;
    color: var(--color-text-base);
  }

  &__chart {
    width: 100%;
  }
}
</style>
