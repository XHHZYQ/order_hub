<template>
  <div class="dashboard">
    <div class="dashboard__filter glass-card">
      <QueryForm :loading="loading" @search="fetchData" @reset="handleReset">
        <el-form-item label="店铺">
          <DictSelect v-model="query.shop_id" type="shop" width="180px" />
        </el-form-item>
        <el-form-item label="平台">
          <DictSelect v-model="query.platform_code" type="platform" width="150px" />
        </el-form-item>
        <el-form-item label="时间">
          <el-date-picker
            v-model="timeRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 280px"
          />
        </el-form-item>
      </QueryForm>
    </div>

    <div class="dashboard__stats">
      <StatCard label="订单数" :text="formatNumber(data?.order_count ?? 0)" unit="单" />
      <StatCard label="已完成订单" :text="formatNumber(data?.finished_count ?? 0)" unit="单" />
      <StatCard label="发货单数" :text="formatNumber(data?.shipment_count ?? 0)" unit="单" />
      <StatCard label="平均发货时长" :text="formatNumber(data?.avg_ship_hours ?? 0, 1)" unit="小时" />
      <StatCard
        label="履约率"
        :text="formatPercent((data?.fulfillment_rate ?? 0) * 100, 1)"
        :color="'var(--color-success)'"
      />
    </div>

    <div class="dashboard__grid">
      <ChartCard title="订单状态分布" :option="statusOption" :height="320" />
      <ChartCard title="发货单状态分布" :option="shipmentOption" :height="320" />
    </div>

    <div class="dashboard__grid">
      <div class="glass-card">
        <div class="dashboard__title">订单状态明细</div>
        <el-table v-loading="loading" :data="data?.status_distribution ?? []" stripe border>
          <el-table-column prop="status_name" label="状态" min-width="140" />
          <el-table-column prop="count" label="订单数" width="120" align="center" />
          <el-table-column label="占比" min-width="160">
            <template #default="{ row }">
              <el-progress :percentage="ratio(row.count, orderTotal)" :stroke-width="10" />
            </template>
          </el-table-column>
        </el-table>
      </div>
      <div class="glass-card">
        <div class="dashboard__title">发货单状态明细</div>
        <el-table v-loading="loading" :data="data?.shipment_distribution ?? []" stripe border>
          <el-table-column prop="status_name" label="状态" min-width="140" />
          <el-table-column prop="count" label="发货单数" width="120" align="center" />
          <el-table-column label="占比" min-width="160">
            <template #default="{ row }">
              <el-progress :percentage="ratio(row.count, shipmentTotal)" :stroke-width="10" />
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// 数据看板 - 订单与履约：订单/发货单状态分布与履约率
import { computed, onMounted, reactive, ref } from 'vue'
import type { EChartsOption } from 'echarts'
import QueryForm from '@/components/QueryForm.vue'
import DictSelect from '@/components/DictSelect.vue'
import StatCard from '@/components/StatCard.vue'
import ChartCard from '@/components/ChartCard.vue'
import { getDashboardFulfillment } from '@/api/dashboard'
import { formatNumber, formatPercent } from '@/utils/format'
import type { DashboardFulfillment } from '@/types/dashboard'

const loading = ref(false)
const data = ref<DashboardFulfillment | null>(null)
const timeRange = ref<[string, string] | null>(null)

const query = reactive({
  shop_id: undefined as number | undefined,
  platform_code: undefined as string | undefined,
})

const orderTotal = computed(() =>
  (data.value?.status_distribution ?? []).reduce((sum, s) => sum + s.count, 0),
)
const shipmentTotal = computed(() =>
  (data.value?.shipment_distribution ?? []).reduce((sum, s) => sum + s.count, 0),
)

const statusOption = computed<EChartsOption>(() => {
  const rows = data.value?.status_distribution ?? []
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 0, type: 'scroll' },
    series: [
      {
        type: 'pie',
        radius: ['45%', '68%'],
        center: ['50%', '45%'],
        data: rows.map((r) => ({ name: r.status_name, value: r.count })),
      },
    ],
  }
})

const shipmentOption = computed<EChartsOption>(() => {
  const rows = data.value?.shipment_distribution ?? []
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 10, right: 20, bottom: 10, top: 30, containLabel: true },
    xAxis: { type: 'category', data: rows.map((r) => r.status_name) },
    yAxis: { type: 'value', name: '数量' },
    series: [
      {
        type: 'bar',
        barWidth: 38,
        itemStyle: { color: '#6366f1', borderRadius: [6, 6, 0, 0] },
        data: rows.map((r) => r.count),
      },
    ],
  }
})

function ratio(count: number, total: number) {
  if (!total) return 0
  return Number(((count / total) * 100).toFixed(1))
}

async function fetchData() {
  loading.value = true
  try {
    data.value = await getDashboardFulfillment({
      shop_id: query.shop_id,
      platform_code: query.platform_code,
      start_time: timeRange.value?.[0],
      end_time: timeRange.value?.[1],
    })
  } finally {
    loading.value = false
  }
}

function handleReset() {
  query.shop_id = undefined
  query.platform_code = undefined
  timeRange.value = null
  fetchData()
}

onMounted(fetchData)
</script>

<style scoped lang="scss">
.dashboard {
  display: flex;
  flex-direction: column;
  gap: var(--padding-base);
  padding: var(--padding-base);

  &__stats {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: var(--padding-base);
  }

  &__grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: var(--padding-base);
  }

  &__title {
    font-size: 16px;
    font-weight: 600;
    color: var(--color-text-base);
    margin-bottom: 12px;
  }
}
</style>
