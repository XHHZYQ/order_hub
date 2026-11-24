<template>
  <div class="page-container">
    <div class="profit glass-card">
      <QueryForm :loading="loading" @search="handleSearch" @reset="handleReset">
        <el-form-item label="店铺">
          <DictSelect v-model="query.shop_id" type="shop" width="180px" />
        </el-form-item>
        <el-form-item label="平台">
          <DictSelect v-model="query.platform_code" type="platform" width="150px" />
        </el-form-item>
        <el-form-item label="时间">
          <el-date-picker
            v-model="timeRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 360px"
          />
        </el-form-item>
        <el-form-item label="Top">
          <el-input-number v-model="query.limit" :min="5" :max="100" :step="5" style="width: 120px" />
        </el-form-item>
      </QueryForm>
    </div>

    <div class="profit__stats">
      <div v-for="card in cards" :key="card.label" class="stat-card glass-card">
        <div class="stat-card__label">{{ card.label }}</div>
        <div class="stat-card__value" :class="card.class">
          <AmountText v-if="card.money" :value="card.value" />
          <span v-else>{{ card.text }}</span>
        </div>
      </div>
    </div>

    <div class="profit__body glass-card">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="按订单" name="order">
          <el-table v-loading="loading" :data="data?.by_order ?? []" stripe border>
            <el-table-column type="index" label="#" width="60" align="center" />
            <el-table-column prop="order_no" label="订单号" min-width="170" show-overflow-tooltip />
            <el-table-column prop="platform_order_no" label="平台订单号" min-width="170" show-overflow-tooltip />
            <el-table-column prop="buyer_account" label="买家" min-width="120" show-overflow-tooltip>
              <template #default="{ row }">{{ row.buyer_account || '-' }}</template>
            </el-table-column>
            <el-table-column label="实收" width="120" align="right">
              <template #default="{ row }"><AmountText :value="row.settled" /></template>
            </el-table-column>
            <el-table-column label="成本" width="120" align="right">
              <template #default="{ row }"><AmountText :value="row.cost" /></template>
            </el-table-column>
            <el-table-column label="毛利" width="120" align="right">
              <template #default="{ row }">
                <span :class="{ 'profit__negative': row.profit < 0 }">
                  <AmountText :value="row.profit" />
                </span>
              </template>
            </el-table-column>
            <el-table-column label="毛利率" width="100" align="right">
              <template #default="{ row }">{{ formatPercent(row.profit_rate * 100) }}</template>
            </el-table-column>
            <el-table-column label="成交时间" min-width="170">
              <template #default="{ row }">{{ formatDateTime(row.trade_time) }}</template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="按商品" name="product">
          <el-table v-loading="loading" :data="data?.by_product ?? []" stripe border>
            <el-table-column type="index" label="#" width="60" align="center" />
            <el-table-column prop="sku_code" label="SKU 编码" min-width="140" show-overflow-tooltip />
            <el-table-column prop="product_name" label="商品名称" min-width="200" show-overflow-tooltip />
            <el-table-column prop="quantity" label="销量" width="100" align="center" />
            <el-table-column label="实收" width="130" align="right">
              <template #default="{ row }"><AmountText :value="row.settled" /></template>
            </el-table-column>
            <el-table-column label="成本" width="130" align="right">
              <template #default="{ row }"><AmountText :value="row.cost" /></template>
            </el-table-column>
            <el-table-column label="毛利" width="130" align="right">
              <template #default="{ row }">
                <span :class="{ 'profit__negative': row.profit < 0 }">
                  <AmountText :value="row.profit" />
                </span>
              </template>
            </el-table-column>
            <el-table-column label="毛利率" width="110" align="right">
              <template #default="{ row }">{{ formatPercent(row.profit_rate * 100) }}</template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
// 财务对账 - 毛利核算：实收 - 成本（Sku.cost_price），按订单 / 按商品两个维度
import { computed, onMounted, reactive, ref } from 'vue'
import QueryForm from '@/components/QueryForm.vue'
import DictSelect from '@/components/DictSelect.vue'
import AmountText from '@/components/AmountText.vue'
import { getProfits } from '@/api/bill'
import { formatPercent } from '@/utils/format'
import { formatDateTime } from '@/utils/datetime'
import type { ProfitSummary } from '@/types/finance'

const loading = ref(false)
const data = ref<ProfitSummary | null>(null)
const timeRange = ref<[string, string] | null>(null)
const activeTab = ref('order')

const query = reactive({
  shop_id: undefined as number | undefined,
  platform_code: undefined as string | undefined,
  limit: 20,
})

const cards = computed(() => [
  { label: '实收金额', value: data.value?.settled ?? 0, money: true, text: '', class: '' },
  { label: '成本金额', value: data.value?.cost ?? 0, money: true, text: '', class: '' },
  {
    label: '毛利',
    value: data.value?.profit ?? 0,
    money: true,
    text: '',
    class: (data.value?.profit ?? 0) < 0 ? 'profit__negative' : 'profit__positive',
  },
  {
    label: '毛利率',
    value: 0,
    money: false,
    text: formatPercent((data.value?.profit_rate ?? 0) * 100),
    class: '',
  },
  { label: '订单数', value: 0, money: false, text: String(data.value?.order_count ?? 0), class: '' },
])

async function fetchData() {
  loading.value = true
  try {
    data.value = await getProfits({
      shop_id: query.shop_id,
      platform_code: query.platform_code,
      limit: query.limit,
      start_time: timeRange.value?.[0],
      end_time: timeRange.value?.[1],
    })
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  fetchData()
}

function handleReset() {
  query.shop_id = undefined
  query.platform_code = undefined
  query.limit = 20
  timeRange.value = null
  fetchData()
}

onMounted(fetchData)
</script>

<style scoped lang="scss">
.profit {
  &__stats {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: var(--padding-base);
    margin: var(--padding-base) 0;
  }

  &__negative {
    color: var(--color-danger);
  }

  &__positive {
    color: var(--color-success);
  }
}

.stat-card {
  &__label {
    font-size: 13px;
    color: var(--color-text-secondary);
    margin-bottom: 8px;
  }

  &__value {
    font-size: 20px;
    font-weight: 600;
    color: var(--color-text-base);
  }
}
</style>
