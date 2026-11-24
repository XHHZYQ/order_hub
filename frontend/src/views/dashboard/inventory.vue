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
      <StatCard label="SKU 数" :text="formatNumber(data?.sku_count ?? 0)" unit="个" />
      <StatCard label="主仓库存" :text="formatNumber(data?.main_qty ?? 0)" unit="件" />
      <StatCard label="占用库存" :text="formatNumber(data?.occupied_qty ?? 0)" unit="件" />
      <StatCard label="可用库存" :text="formatNumber(data?.available_qty ?? 0)" unit="件" />
      <StatCard
        label="预警 SKU"
        :text="formatNumber(data?.alert_count ?? 0)"
        unit="个"
        color="var(--color-warning)"
        clickable
        @click="openDrill"
      />
      <StatCard
        label="缺货 SKU"
        :text="formatNumber(data?.shortage_count ?? 0)"
        unit="个"
        color="var(--color-danger)"
      />
    </div>

    <ChartCard title="库存预警 Top" :option="alertOption" :height="320" />

    <div class="dashboard__grid">
      <div class="glass-card">
        <div class="dashboard__title">库存预警明细</div>
        <el-table v-loading="loading" :data="data?.alerts ?? []" stripe border>
          <el-table-column prop="sku_code" label="SKU 编码" min-width="140" show-overflow-tooltip />
          <el-table-column prop="sku_name" label="商品名称" min-width="180" show-overflow-tooltip />
          <el-table-column prop="available_qty" label="可用库存" width="110" align="center" />
          <el-table-column prop="alert_qty" label="预警阈值" width="110" align="center" />
          <el-table-column label="风险" width="110" align="center">
            <template #default="{ row }">
              <el-tag :type="row.available_qty <= 0 ? 'danger' : 'warning'" effect="light" round>
                {{ row.risk }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div class="glass-card">
        <div class="dashboard__title">库存周转 Top</div>
        <el-table v-loading="loading" :data="data?.turnover ?? []" stripe border>
          <el-table-column prop="sku_code" label="SKU 编码" min-width="140" show-overflow-tooltip />
          <el-table-column prop="sku_name" label="商品名称" min-width="180" show-overflow-tooltip />
          <el-table-column prop="sold_qty" label="销量" width="100" align="center" />
          <el-table-column prop="available_qty" label="可用库存" width="110" align="center" />
          <el-table-column label="周转率" width="110" align="right">
            <template #default="{ row }">{{ formatNumber(row.turnover_rate, 2) }}</template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <el-drawer v-model="drillVisible" title="库存预警明细" size="880px" @open="fetchDrill">
      <el-table v-loading="drillLoading" :data="drillList" stripe border>
        <el-table-column prop="sku_code" label="SKU 编码" min-width="150" show-overflow-tooltip />
        <el-table-column prop="main_qty" label="主仓库存" width="120" align="center" />
        <el-table-column prop="occupied_qty" label="占用库存" width="120" align="center" />
        <el-table-column prop="available_qty" label="可用库存" width="120" align="center" />
        <el-table-column prop="alert_qty" label="预警阈值" width="120" align="center" />
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
// 数据看板 - 库存分析：库存总览、预警与周转 Top、库存预警下钻
import { computed, onMounted, reactive, ref } from 'vue'
import type { EChartsOption } from 'echarts'
import QueryForm from '@/components/QueryForm.vue'
import DictSelect from '@/components/DictSelect.vue'
import StatCard from '@/components/StatCard.vue'
import ChartCard from '@/components/ChartCard.vue'
import { getDashboardInventory, drillDownInventoryAlerts } from '@/api/dashboard'
import { formatNumber } from '@/utils/format'
import type { DashboardInventory, DrillInventoryAlert } from '@/types/dashboard'

const loading = ref(false)
const data = ref<DashboardInventory | null>(null)
const timeRange = ref<[string, string] | null>(null)

const query = reactive({
  shop_id: undefined as number | undefined,
  platform_code: undefined as string | undefined,
})

const alertOption = computed<EChartsOption>(() => {
  const rows = [...(data.value?.alerts ?? [])].slice(0, 10).reverse()
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 10, right: 30, bottom: 10, top: 20, containLabel: true },
    xAxis: { type: 'value', name: '可用库存' },
    yAxis: { type: 'category', data: rows.map((r) => r.sku_name.slice(0, 12)) },
    series: [
      {
        type: 'bar',
        barWidth: 14,
        itemStyle: {
          color: (params: { dataIndex: number }) => {
            const item = rows[params.dataIndex]
            return item && item.available_qty <= 0 ? '#ef4444' : '#f59e0b'
          },
          borderRadius: [0, 6, 6, 0],
        },
        data: rows.map((r) => r.available_qty),
      },
    ],
  }
})

async function fetchData() {
  loading.value = true
  try {
    data.value = await getDashboardInventory({
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
const drillList = ref<DrillInventoryAlert[]>([])
const drillTotal = ref(0)
const drillQuery = reactive({ page: 1, page_size: 10 })

function openDrill() {
  drillQuery.page = 1
  drillVisible.value = true
}

async function fetchDrill() {
  drillLoading.value = true
  try {
    const res = await drillDownInventoryAlerts({
      ...drillQuery,
      metric: 'inventory_alert',
      shop_id: query.shop_id,
      platform_code: query.platform_code,
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
