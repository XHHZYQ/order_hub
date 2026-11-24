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
      <StatCard label="平台数" :text="String(data?.by_platform.length ?? 0)" unit="个" />
      <StatCard label="店铺数" :text="String(data?.by_shop.length ?? 0)" unit="家" />
      <StatCard label="订单数" :text="formatNumber(totalOrders)" unit="单" />
      <StatCard label="销售额" :value="totalSales" money />
    </div>

    <div class="dashboard__grid">
      <ChartCard title="平台销售对比" :option="platformOption" :height="320" />
      <ChartCard title="店铺销售 Top 10" :option="shopOption" :height="320" />
    </div>

    <div class="glass-card">
      <div class="dashboard__title">店铺明细</div>
      <el-table v-loading="loading" :data="data?.by_shop ?? []" stripe border>
        <el-table-column prop="shop_name" label="店铺" min-width="160" show-overflow-tooltip />
        <el-table-column prop="platform_name" label="平台" width="120" />
        <el-table-column prop="order_count" label="订单数" width="110" align="center" />
        <el-table-column label="销售额" width="140" align="right">
          <template #default="{ row }"><AmountText :value="row.sales_amount" /></template>
        </el-table-column>
        <el-table-column label="操作" width="110" align="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDrill(row.shop_id)">查看订单</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-drawer v-model="drillVisible" title="订单明细" size="900px" @open="fetchDrill">
      <el-table v-loading="drillLoading" :data="drillList" stripe border>
        <el-table-column prop="order_no" label="订单号" min-width="170" show-overflow-tooltip />
        <el-table-column prop="platform_order_no" label="平台订单号" min-width="170" show-overflow-tooltip />
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
// 数据看板 - 渠道与店铺：平台/店铺维度的销售对比与订单下钻
import { computed, onMounted, reactive, ref } from 'vue'
import type { EChartsOption } from 'echarts'
import QueryForm from '@/components/QueryForm.vue'
import DictSelect from '@/components/DictSelect.vue'
import StatCard from '@/components/StatCard.vue'
import ChartCard from '@/components/ChartCard.vue'
import StatusTag from '@/components/StatusTag.vue'
import AmountText from '@/components/AmountText.vue'
import { getDashboardChannels, drillDownOrders } from '@/api/dashboard'
import { formatNumber } from '@/utils/format'
import { formatDateTime } from '@/utils/datetime'
import type { DashboardChannels, DrillOrder } from '@/types/dashboard'

const loading = ref(false)
const data = ref<DashboardChannels | null>(null)
const timeRange = ref<[string, string] | null>(null)

const query = reactive({
  shop_id: undefined as number | undefined,
  platform_code: undefined as string | undefined,
})

const totalOrders = computed(() =>
  (data.value?.by_platform ?? []).reduce((sum, p) => sum + p.order_count, 0),
)
const totalSales = computed(() =>
  (data.value?.by_platform ?? []).reduce((sum, p) => sum + p.sales_amount, 0),
)

const platformOption = computed<EChartsOption>(() => {
  const rows = data.value?.by_platform ?? []
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 10, right: 20, bottom: 10, top: 30, containLabel: true },
    xAxis: { type: 'category', data: rows.map((r) => r.platform_name) },
    yAxis: { type: 'value', name: '销售额' },
    series: [
      {
        type: 'bar',
        barWidth: 38,
        itemStyle: { color: '#6366f1', borderRadius: [6, 6, 0, 0] },
        data: rows.map((r) => r.sales_amount),
      },
    ],
  }
})

const shopOption = computed<EChartsOption>(() => {
  const rows = [...(data.value?.by_shop ?? [])].slice(0, 10).reverse()
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 10, right: 30, bottom: 10, top: 20, containLabel: true },
    xAxis: { type: 'value', name: '销售额' },
    yAxis: { type: 'category', data: rows.map((r) => r.shop_name) },
    series: [
      {
        type: 'bar',
        barWidth: 14,
        itemStyle: { color: '#10b981', borderRadius: [0, 6, 6, 0] },
        data: rows.map((r) => r.sales_amount),
      },
    ],
  }
})

async function fetchData() {
  loading.value = true
  try {
    data.value = await getDashboardChannels({
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
const drillShopId = ref<number | undefined>(undefined)
const drillQuery = reactive({ page: 1, page_size: 10 })

function openDrill(shopId: number) {
  drillShopId.value = shopId
  drillQuery.page = 1
  drillVisible.value = true
}

async function fetchDrill() {
  drillLoading.value = true
  try {
    const res = await drillDownOrders({
      ...drillQuery,
      metric: 'order',
      shop_id: drillShopId.value,
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

  &__title {
    font-size: 16px;
    font-weight: 600;
    color: var(--color-text-base);
    margin-bottom: 12px;
  }

  &__pager {
    display: flex;
    justify-content: flex-end;
    margin-top: 16px;
  }
}
</style>
