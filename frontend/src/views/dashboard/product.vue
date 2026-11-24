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
        <el-form-item label="Top">
          <el-input-number v-model="query.top" :min="5" :max="50" :step="5" style="width: 120px" />
        </el-form-item>
      </QueryForm>
    </div>

    <div class="dashboard__stats">
      <StatCard label="销售件数" :text="formatNumber(data?.total_quantity ?? 0)" unit="件" />
      <StatCard label="销售额" :value="data?.total_sales_amount ?? 0" money />
      <StatCard label="SKU 数" :text="formatNumber(data?.sku_count ?? 0)" unit="个" />
      <StatCard label="热销商品数" :text="String(data?.hot.length ?? 0)" unit="款" />
    </div>

    <div class="dashboard__grid">
      <ChartCard title="热销商品 Top" :option="hotOption" :height="320" />
      <ChartCard title="品类销售分布" :option="categoryOption" :height="320" />
    </div>

    <ChartCard title="商品销售趋势" :option="trendOption" :height="300" />

    <div class="glass-card">
      <div class="dashboard__title">热销商品明细</div>
      <el-table v-loading="loading" :data="data?.hot ?? []" stripe border @row-click="openDrill">
        <el-table-column type="index" label="#" width="60" align="center" />
        <el-table-column prop="sku_code" label="SKU 编码" min-width="140" show-overflow-tooltip>
          <template #default="{ row }">{{ row.sku_code || '-' }}</template>
        </el-table-column>
        <el-table-column prop="product_name" label="商品名称" min-width="200" show-overflow-tooltip />
        <el-table-column prop="quantity" label="销量" width="110" align="center" />
        <el-table-column label="销售额" width="140" align="right">
          <template #default="{ row }"><AmountText :value="row.sales_amount" /></template>
        </el-table-column>
        <el-table-column label="操作" width="110" align="right">
          <template #default="{ row }">
            <el-button link type="primary" :disabled="!row.sku_id" @click.stop="openDrill(row)">查看明细</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-drawer v-model="drillVisible" title="商品销售明细" size="900px" @open="fetchDrill">
      <el-table v-loading="drillLoading" :data="drillList" stripe border>
        <el-table-column prop="order_no" label="订单号" min-width="170" show-overflow-tooltip />
        <el-table-column prop="platform_order_no" label="平台订单号" min-width="170" show-overflow-tooltip />
        <el-table-column prop="product_name" label="商品名称" min-width="200" show-overflow-tooltip />
        <el-table-column prop="quantity" label="数量" width="90" align="center" />
        <el-table-column label="金额" width="120" align="right">
          <template #default="{ row }"><AmountText :value="row.pay_amount" /></template>
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
// 数据看板 - 商品销售：热销商品、品类分布、销售趋势与明细下钻
import { computed, onMounted, reactive, ref } from 'vue'
import type { EChartsOption } from 'echarts'
import QueryForm from '@/components/QueryForm.vue'
import DictSelect from '@/components/DictSelect.vue'
import StatCard from '@/components/StatCard.vue'
import ChartCard from '@/components/ChartCard.vue'
import AmountText from '@/components/AmountText.vue'
import { getDashboardProducts, drillDownProducts } from '@/api/dashboard'
import { formatNumber } from '@/utils/format'
import { formatDateTime } from '@/utils/datetime'
import type { DashboardProducts, DrillProduct, ProductHot } from '@/types/dashboard'

const loading = ref(false)
const data = ref<DashboardProducts | null>(null)
const timeRange = ref<[string, string] | null>(null)

const query = reactive({
  shop_id: undefined as number | undefined,
  platform_code: undefined as string | undefined,
  top: 10,
})

const hotOption = computed<EChartsOption>(() => {
  const rows = [...(data.value?.hot ?? [])].reverse()
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 10, right: 30, bottom: 10, top: 20, containLabel: true },
    xAxis: { type: 'value', name: '销量' },
    yAxis: {
      type: 'category',
      data: rows.map((r) => r.product_name.slice(0, 12)),
    },
    series: [
      {
        type: 'bar',
        barWidth: 14,
        itemStyle: { color: '#6366f1', borderRadius: [0, 6, 6, 0] },
        data: rows.map((r) => r.quantity),
      },
    ],
  }
})

const categoryOption = computed<EChartsOption>(() => {
  const rows = data.value?.categories ?? []
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 0, type: 'scroll' },
    series: [
      {
        type: 'pie',
        radius: ['45%', '68%'],
        center: ['50%', '45%'],
        data: rows.map((r) => ({ name: r.category_name, value: r.quantity })),
      },
    ],
  }
})

const trendOption = computed<EChartsOption>(() => {
  const trend = data.value?.trend ?? []
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: ['销售额', '销量'], right: 0 },
    grid: { left: 10, right: 20, bottom: 10, top: 40, containLabel: true },
    xAxis: { type: 'category', boundaryGap: false, data: trend.map((t) => t.date) },
    yAxis: [
      { type: 'value', name: '销售额' },
      { type: 'value', name: '销量' },
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
        name: '销量',
        type: 'line',
        smooth: true,
        yAxisIndex: 1,
        itemStyle: { color: '#f59e0b' },
        data: trend.map((t) => t.quantity),
      },
    ],
  }
})

async function fetchData() {
  loading.value = true
  try {
    data.value = await getDashboardProducts({
      shop_id: query.shop_id,
      platform_code: query.platform_code,
      top: query.top,
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
  query.top = 10
  timeRange.value = null
  fetchData()
}

// ---------- 下钻 ----------
const drillVisible = ref(false)
const drillLoading = ref(false)
const drillList = ref<DrillProduct[]>([])
const drillTotal = ref(0)
const drillSkuId = ref<number | undefined>(undefined)
const drillQuery = reactive({ page: 1, page_size: 10 })

function openDrill(row: ProductHot) {
  if (!row.sku_id) return
  drillSkuId.value = row.sku_id
  drillQuery.page = 1
  drillVisible.value = true
}

async function fetchDrill() {
  drillLoading.value = true
  try {
    const res = await drillDownProducts({
      ...drillQuery,
      metric: 'product',
      sku_id: drillSkuId.value,
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
