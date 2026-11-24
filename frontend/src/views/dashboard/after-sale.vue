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
      <StatCard label="售后单数" :text="formatNumber(data?.total ?? 0)" unit="单" clickable @click="openDrill" />
      <StatCard label="退款金额" :value="data?.refund_amount ?? 0" money />
      <StatCard label="退款成功" :text="formatNumber(data?.refund_success_count ?? 0)" unit="单" />
      <StatCard label="售后类型数" :text="String(data?.type_distribution.length ?? 0)" unit="类" />
    </div>

    <div class="dashboard__grid">
      <ChartCard title="售后类型分布" :option="typeOption" :height="320" />
      <ChartCard title="售后状态分布" :option="statusOption" :height="320" />
    </div>

    <div class="dashboard__grid">
      <ChartCard title="退款原因 Top" :option="reasonOption" :height="320" />
      <ChartCard title="售后趋势" :option="trendOption" :height="320" />
    </div>

    <el-drawer v-model="drillVisible" title="售后单明细" size="900px" @open="fetchDrill">
      <el-table v-loading="drillLoading" :data="drillList" stripe border>
        <el-table-column prop="after_sale_no" label="售后单号" min-width="170" show-overflow-tooltip />
        <el-table-column prop="order_no" label="订单号" min-width="170" show-overflow-tooltip>
          <template #default="{ row }">{{ row.order_no || '-' }}</template>
        </el-table-column>
        <el-table-column prop="type_name" label="类型" width="100" />
        <el-table-column prop="reason" label="原因" min-width="140" show-overflow-tooltip>
          <template #default="{ row }">{{ row.reason || '-' }}</template>
        </el-table-column>
        <el-table-column prop="status_name" label="状态" width="110" />
        <el-table-column label="退款金额" width="120" align="right">
          <template #default="{ row }"><AmountText :value="row.refund_amount" /></template>
        </el-table-column>
        <el-table-column label="申请时间" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.apply_time) }}</template>
        </el-table-column>
      </el-table>
      <div class="dashboard__pager">
        <el-pagination
          :current-page="drillQuery.page"
          :page-size="drillQuery.page_size"
          :total="drillTotal"
          layout="total, prev, pager, next"
          background
          @current-change="handleDrillPage"
        />
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
// 数据看板 - 售后分析：售后类型/状态/原因分布、退款与售后趋势、售后单下钻
import { computed, onMounted, reactive, ref } from 'vue'
import type { EChartsOption } from 'echarts'
import QueryForm from '@/components/QueryForm.vue'
import DictSelect from '@/components/DictSelect.vue'
import StatCard from '@/components/StatCard.vue'
import ChartCard from '@/components/ChartCard.vue'
import AmountText from '@/components/AmountText.vue'
import { getDashboardAfterSales, drillDownAfterSales } from '@/api/dashboard'
import { formatNumber } from '@/utils/format'
import { formatDateTime } from '@/utils/datetime'
import type { DashboardAfterSales, DrillAfterSale } from '@/types/dashboard'

const loading = ref(false)
const data = ref<DashboardAfterSales | null>(null)
const timeRange = ref<[string, string] | null>(null)

const query = reactive({
  shop_id: undefined as number | undefined,
  platform_code: undefined as string | undefined,
})

const typeOption = computed<EChartsOption>(() => {
  const rows = data.value?.type_distribution ?? []
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 0 },
    series: [
      {
        type: 'pie',
        radius: ['45%', '68%'],
        center: ['50%', '45%'],
        data: rows.map((r) => ({ name: r.type_name, value: r.count })),
      },
    ],
  }
})

const statusOption = computed<EChartsOption>(() => {
  const names = data.value?.refund_status_names ?? {}
  const rows = data.value?.status_distribution ?? []
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 10, right: 20, bottom: 10, top: 30, containLabel: true },
    xAxis: { type: 'category', data: rows.map((r) => r.status_name || names[r.status] || r.status) },
    yAxis: { type: 'value', name: '数量' },
    series: [
      {
        type: 'bar',
        barWidth: 38,
        itemStyle: { color: '#10b981', borderRadius: [6, 6, 0, 0] },
        data: rows.map((r) => r.count),
      },
    ],
  }
})

const reasonOption = computed<EChartsOption>(() => {
  const rows = [...(data.value?.reason_distribution ?? [])].slice(0, 8).reverse()
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 10, right: 30, bottom: 10, top: 20, containLabel: true },
    xAxis: { type: 'value', name: '数量' },
    yAxis: { type: 'category', data: rows.map((r) => r.reason) },
    series: [
      {
        type: 'bar',
        barWidth: 14,
        itemStyle: { color: '#f59e0b', borderRadius: [0, 6, 6, 0] },
        data: rows.map((r) => r.count),
      },
    ],
  }
})

const trendOption = computed<EChartsOption>(() => {
  const trend = data.value?.trend ?? []
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 10, right: 20, bottom: 10, top: 30, containLabel: true },
    xAxis: { type: 'category', boundaryGap: false, data: trend.map((t) => t.date) },
    yAxis: { type: 'value', name: '售后单数' },
    series: [
      {
        type: 'line',
        smooth: true,
        areaStyle: { opacity: 0.15 },
        itemStyle: { color: '#ef4444' },
        data: trend.map((t) => t.count),
      },
    ],
  }
})

async function fetchData() {
  loading.value = true
  try {
    data.value = await getDashboardAfterSales({
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

// ---------- 下钻 ----------
const drillVisible = ref(false)
const drillLoading = ref(false)
const drillList = ref<DrillAfterSale[]>([])
const drillTotal = ref(0)
const drillQuery = reactive({ page: 1, page_size: 10 })

function openDrill() {
  drillQuery.page = 1
  drillVisible.value = true
}

async function fetchDrill() {
  drillLoading.value = true
  try {
    const res = await drillDownAfterSales({
      ...drillQuery,
      metric: 'after_sale',
      shop_id: query.shop_id,
      platform_code: query.platform_code,
      start_time: timeRange.value?.[0],
      end_time: timeRange.value?.[1],
    })
    drillList.value = res.list ?? []
    drillTotal.value = res.total ?? 0
  } finally {
    drillLoading.value = false
  }
}

function handleDrillPage(page: number) {
  drillQuery.page = page
  fetchDrill()
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
    grid-template-columns: repeat(4, 1fr);
    gap: var(--padding-base);
  }

  &__grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: var(--padding-base);
  }

  &__pager {
    display: flex;
    justify-content: flex-end;
    margin-top: 16px;
  }
}
</style>
