<template>
  <div class="page-container">
    <div class="settlement glass-card">
      <QueryForm :loading="loading" @search="handleSearch" @reset="handleReset">
        <el-form-item label="分组维度">
          <el-radio-group v-model="query.group_by" @change="handleSearch">
            <el-radio-button value="platform">按平台</el-radio-button>
            <el-radio-button value="shop">按店铺</el-radio-button>
          </el-radio-group>
        </el-form-item>
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
      </QueryForm>
    </div>

    <div class="settlement__stats">
      <div v-for="card in cards" :key="card.label" class="stat-card glass-card">
        <div class="stat-card__label">{{ card.label }}</div>
        <div class="stat-card__value">
          <AmountText v-if="card.money" :value="card.value" />
          <span v-else>{{ formatNumber(card.value) }}</span>
        </div>
      </div>
    </div>

    <div class="settlement__body glass-card">
      <div class="settlement__toolbar">
        <div class="settlement__title">结算汇总明细</div>
        <el-button :icon="Download" @click="handleExport">导出汇总</el-button>
      </div>

      <el-table v-loading="loading" :data="data?.rows ?? []" stripe border show-summary :summary-method="summaryMethod">
        <el-table-column prop="name" :label="query.group_by === 'shop' ? '店铺' : '平台'" min-width="160" show-overflow-tooltip />
        <el-table-column prop="order_count" label="订单数" width="100" align="center" />
        <el-table-column label="应收货款" width="140" align="right">
          <template #default="{ row }"><AmountText :value="row.receivable" /></template>
        </el-table-column>
        <el-table-column label="平台费用" width="130" align="right">
          <template #default="{ row }"><AmountText :value="row.platform_fee" /></template>
        </el-table-column>
        <el-table-column label="平台补贴" width="130" align="right">
          <template #default="{ row }"><AmountText :value="row.subsidy" /></template>
        </el-table-column>
        <el-table-column label="退款金额" width="130" align="right">
          <template #default="{ row }"><AmountText :value="row.refund" /></template>
        </el-table-column>
        <el-table-column label="实收金额" width="140" align="right">
          <template #default="{ row }">
            <span class="settlement__settled"><AmountText :value="row.settled" /></span>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
// 财务对账 - 结算汇总：按平台/店铺汇总应收、平台费用、补贴、退款与实收
import { computed, onMounted, reactive, ref } from 'vue'
import type { TableColumnCtx } from 'element-plus'
import { Download } from '@element-plus/icons-vue'
import QueryForm from '@/components/QueryForm.vue'
import DictSelect from '@/components/DictSelect.vue'
import AmountText from '@/components/AmountText.vue'
import { getSettlements, exportReconciliation } from '@/api/bill'
import { formatNumber } from '@/utils/format'
import type { SettlementSummary, SettlementRow } from '@/types/finance'

const loading = ref(false)
const data = ref<SettlementSummary | null>(null)
const timeRange = ref<[string, string] | null>(null)

const query = reactive({
  group_by: 'platform' as 'platform' | 'shop',
  shop_id: undefined as number | undefined,
  platform_code: undefined as string | undefined,
})

const cards = computed(() => [
  { label: '应收货款', value: data.value?.receivable ?? 0, money: true },
  { label: '平台费用', value: data.value?.platform_fee ?? 0, money: true },
  { label: '平台补贴', value: data.value?.subsidy ?? 0, money: true },
  { label: '退款金额', value: data.value?.refund ?? 0, money: true },
  { label: '实收金额', value: data.value?.settled ?? 0, money: true },
  { label: '订单数', value: data.value?.order_count ?? 0, money: false },
])

async function fetchData() {
  loading.value = true
  try {
    data.value = await getSettlements({
      group_by: query.group_by,
      shop_id: query.shop_id,
      platform_code: query.platform_code,
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
  query.group_by = 'platform'
  query.shop_id = undefined
  query.platform_code = undefined
  timeRange.value = null
  fetchData()
}

function summaryMethod(param: { columns: TableColumnCtx<SettlementRow>[] }) {
  const { columns } = param
  const sums: string[] = []
  const total = data.value
  columns.forEach((column, index) => {
    if (index === 0) {
      sums[index] = '合计'
      return
    }
    const key = column.property as keyof SettlementSummary
    const value = total ? (total[key] as number) : 0
    if (column.property === 'order_count') {
      sums[index] = formatNumber(value)
    } else if (column.property) {
      sums[index] = formatNumber(value, 2)
    } else {
      sums[index] = ''
    }
  })
  return sums
}

async function handleExport() {
  const blob = await exportReconciliation({
    export_type: 'settlement',
    shop_id: query.shop_id,
    platform_code: query.platform_code,
    start_time: timeRange.value?.[0],
    end_time: timeRange.value?.[1],
  })
  const url = URL.createObjectURL(blob as Blob)
  const link = document.createElement('a')
  link.href = url
  link.download = '结算汇总.csv'
  link.click()
  URL.revokeObjectURL(url)
}

onMounted(fetchData)
</script>

<style scoped lang="scss">
.settlement {
  display: flex;
  flex-direction: column;
  gap: var(--padding-base);

  &__stats {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: var(--padding-base);
  }

  &__toolbar {
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

  &__settled {
    font-weight: 600;
    color: var(--color-primary);
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
