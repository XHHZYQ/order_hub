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
      <StatCard label="订单数" :text="formatNumber(data?.order_count ?? 0)" unit="单" clickable @click="openDrill('order')" />
      <StatCard label="销售额" :value="data?.sales_amount ?? 0" money />
      <StatCard label="客单价" :value="data?.avg_order_amount ?? 0" money />
      <StatCard label="买家数" :text="formatNumber(data?.buyer_count ?? 0)" unit="人" />
      <StatCard label="退款金额" :value="data?.refund_amount ?? 0" money />
      <StatCard label="退款单数" :text="formatNumber(data?.refund_count ?? 0)" unit="单" />
    </div>

    <ChartCard title="销售与订单趋势" :option="trendOption" :height="340">
      <template #extra>
        <span class="dashboard__range">{{ data?.start_time }} ~ {{ data?.end_time }}</span>
      </template>
    </ChartCard>

    <el-drawer v-model="drillVisible" title="订单明细" size="900px" @open="fetchDrill">
      <el-table v-loading="drillLoading" :data="drillList" stripe border>
        <el-table-column prop="order_no" label="订单号" min-width="170" show-overflow-tooltip />
        <el-table-column prop="platform_order_no" label="平台订单号" min-width="170" show-overflow-tooltip />
        <el-table-column prop="platform_name" label="平台" width="100" />
        <el-table-column prop="shop_name" label="店铺" min-width="140" show-overflow-tooltip />
        <el-table-column prop="buyer_account" label="买家" min-width="120" show-overflow-tooltip />
        <el-table-column label="应付金额" width="120" align="right">
          <template #default="{ row }"><AmountText :value="row.pay_amount" /></template>
        </el-table-column>
        <el-table-column label="状态" width="110" align="center">
          <template #default="{ row }"><StatusTag :value="row.status" scene="order" /></template>
        </el-table-column>
        <el-table-column label="下单时间" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.order_time) }}</template>
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
// 数据看板 - 经营总览：核心指标 + 销售趋势 + 订单下钻
import { computed, onMounted, reactive, ref } from 'vue'
import type { EChartsOption } from 'echarts'
import QueryForm from '@/components/QueryForm.vue'
import DictSelect from '@/components/DictSelect.vue'
import StatCard from '@/components/StatCard.vue'
import ChartCard from '@/components/ChartCard.vue'
import StatusTag from '@/components/StatusTag.vue'
import AmountText from '@/components/AmountText.vue'
import { getDashboardOverview, drillDownOrders } from '@/api/dashboard'
import { formatNumber } from '@/utils/format'
import { formatDateTime } from '@/utils/datetime'
import type { DashboardOverview, DrillOrder, DrillQuery } from '@/types/dashboard'

const loading = ref(false)
const data = ref<DashboardOverview | null>(null)
const timeRange = ref<[string, string] | null>(null)

const query = reactive({
  shop_id: undefined as number | undefined,
  platform_code: undefined as string | undefined,
})

const trendOption = computed<EChartsOption>(() => {
  const trend = data.value?.trend ?? []
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: ['销售额', '订单数'], right: 0 },
    grid: { left: 10, right: 20, bottom: 10, top: 40, containLabel: true },
    xAxis: { type: 'category', boundaryGap: false, data: trend.map((t) => t.date) },
    yAxis: [
      { type: 'value', name: '销售额' },
      { type: 'value', name: '订单数' },
    ],
    series: [
      {
        name: '销售额',
        type: 'line',
        smooth: true,
        areaStyle: { opacity: 0.15 },
        itemStyle: { color: '#6366f1' },
        data: trend.map((t) => t.sales_amount),
      },
      {
        name: '订单数',
        type: 'line',
        smooth: true,
        yAxisIndex: 1,
        itemStyle: { color: '#10b981' },
        data: trend.map((t) => t.order_count),
      },
    ],
  }
})

async function fetchData() {
  loading.value = true
  try {
    data.value = await getDashboardOverview({
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
const drillList = ref<DrillOrder[]>([])
const drillTotal = ref(0)
const drillQuery = reactive({
  page: 1,
  page_size: 10,
  metric: 'order' as DrillQuery['metric'],
})

function openDrill(metric: DrillQuery['metric']) {
  drillQuery.metric = metric
  drillQuery.page = 1
  drillVisible.value = true
}

async function fetchDrill() {
  drillLoading.value = true
  try {
    const res = await drillDownOrders({
      ...drillQuery,
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
    grid-template-columns: repeat(6, 1fr);
    gap: var(--padding-base);
  }

  &__range {
    font-size: 12px;
    color: var(--color-text-secondary);
  }

  &__pager {
    display: flex;
    justify-content: flex-end;
    margin-top: 16px;
  }
}
</style>
