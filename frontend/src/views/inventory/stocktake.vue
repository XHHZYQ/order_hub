<template>
  <div class="page-container">
    <div class="glass-card stocktake-form">
      <div class="stocktake-form__title">选择 SKU 录入实盘数量</div>
      <el-form inline>
        <el-form-item label="SKU">
          <el-select
            v-model="selectedSkuId"
            filterable
            remote
            reserve-keyword
            :remote-method="remoteSearch"
            :loading="skuLoading"
            placeholder="输入 SKU 编码 / 名称搜索"
            style="width: 300px"
          >
            <el-option
              v-for="item in skuOptions"
              :key="item.sku_id"
              :label="`${item.sku_code} ${item.sku_name || ''}`"
              :value="item.sku_id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="实盘数量">
          <el-input-number v-model="actualQty" :min="0" :step="1" style="width: 160px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Plus" @click="handleAdd">添加</el-button>
        </el-form-item>
        <el-form-item label="盘点备注">
          <el-input v-model="remark" placeholder="选填" style="width: 220px" />
        </el-form-item>
        <el-form-item>
          <el-button
            v-permission="'inventory:stocktake'"
            type="success"
            :loading="submitting"
            :disabled="!rows.length"
            @click="handleSubmit"
          >
            提交盘点
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="glass-card stocktake-table">
      <div class="stocktake-table__title">盘点明细</div>
      <el-table class="hover-table" :data="rows" stripe border>
        <el-table-column type="index" label="#" width="60" align="center" />
        <el-table-column prop="sku_code" label="SKU 编码" min-width="150" show-overflow-tooltip />
        <el-table-column prop="sku_name" label="SKU 名称" min-width="170" show-overflow-tooltip />
        <el-table-column label="系统库存" width="110" align="right">
          <template #default="{ row }">{{ formatNumber(row.system_qty) }}</template>
        </el-table-column>
        <el-table-column label="实盘数量" width="180" align="center">
          <template #default="{ row }">
            <el-input-number v-model="row.actual_qty" :min="0" :step="1" size="small" />
          </template>
        </el-table-column>
        <el-table-column label="差异" width="110" align="right">
          <template #default="{ row }">
            <span :class="diffOf(row) >= 0 ? 'text-success' : 'text-danger'">
              {{ diffOf(row) > 0 ? `+${formatNumber(diffOf(row))}` : formatNumber(diffOf(row)) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="90" align="right" fixed="right">
          <template #default="{ $index }">
            <el-button link type="danger" @click="handleRemove($index)">移除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 盘点结果 -->
    <div v-if="result" class="glass-card stocktake-result">
      <div class="stocktake-result__title">盘点结果</div>
      <el-descriptions :column="3" border>
        <el-descriptions-item label="盘点总数">{{ result.total }}</el-descriptions-item>
        <el-descriptions-item label="盘盈数量">{{ result.gain_count }}</el-descriptions-item>
        <el-descriptions-item label="盘亏数量">{{ result.loss_count }}</el-descriptions-item>
      </el-descriptions>
      <el-table class="hover-table mt-16" :data="result.items" stripe border max-height="320">
        <el-table-column prop="sku_code" label="SKU 编码" min-width="150" show-overflow-tooltip />
        <el-table-column prop="sku_name" label="SKU 名称" min-width="170" show-overflow-tooltip />
        <el-table-column label="盘点前" width="110" align="right">
          <template #default="{ row }">{{ formatNumber(row.before_qty) }}</template>
        </el-table-column>
        <el-table-column label="实盘数量" width="110" align="right">
          <template #default="{ row }">{{ formatNumber(row.actual_qty) }}</template>
        </el-table-column>
        <el-table-column label="调整数量" width="120" align="right">
          <template #default="{ row }">
            <span :class="row.change_qty >= 0 ? 'text-success' : 'text-danger'">
              {{ row.change_qty > 0 ? `+${formatNumber(row.change_qty)}` : formatNumber(row.change_qty) }}
            </span>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
// 库存盘点：选择 SKU 录入实盘数量，提交后生成盘盈/盘亏调整流水并展示结果
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { getInventoryList, submitStocktake } from '@/api/inventory'
import { formatNumber } from '@/utils/format'
import type { Inventory, StocktakeResult, StocktakeItemForm } from '@/types/inventory'

interface StocktakeRow {
  sku_id: number
  sku_code: string
  sku_name?: string
  system_qty: number
  actual_qty: number
}

const skuOptions = ref<Inventory[]>([])
const skuLoading = ref(false)
const selectedSkuId = ref<number | undefined>(undefined)
const actualQty = ref<number>(0)
const remark = ref('')
const rows = ref<StocktakeRow[]>([])
const submitting = ref(false)
const result = ref<StocktakeResult | null>(null)

async function remoteSearch(keyword: string) {
  skuLoading.value = true
  try {
    const res = await getInventoryList({ page: 1, page_size: 20, keyword: keyword || undefined })
    skuOptions.value = res.list ?? []
  } finally {
    skuLoading.value = false
  }
}

function handleAdd() {
  if (selectedSkuId.value == null) {
    ElMessage.warning('请先选择 SKU')
    return
  }
  const opt = skuOptions.value.find((item) => item.sku_id === selectedSkuId.value)
  if (!opt) {
    ElMessage.warning('未找到该 SKU 的库存信息')
    return
  }
  if (rows.value.some((row) => row.sku_id === opt.sku_id)) {
    ElMessage.warning('该 SKU 已在盘点明细中')
    return
  }
  rows.value.push({
    sku_id: opt.sku_id,
    sku_code: opt.sku_code,
    sku_name: opt.sku_name,
    system_qty: opt.main_qty ?? 0,
    actual_qty: actualQty.value,
  })
  selectedSkuId.value = undefined
  actualQty.value = 0
}

function handleRemove(index: number) {
  rows.value.splice(index, 1)
}

function diffOf(row: StocktakeRow) {
  return (row.actual_qty ?? 0) - (row.system_qty ?? 0)
}

async function handleSubmit() {
  if (!rows.value.length) return
  const hasDiff = rows.value.some((row) => diffOf(row) !== 0)
  const tip = hasDiff
    ? '提交后将按差异生成盘盈/盘亏调整流水，确定继续吗？'
    : '所选 SKU 实盘与账面一致，确定提交吗？'
  try {
    await ElMessageBox.confirm(tip, '提交盘点', { type: 'warning' })
  } catch {
    return
  }
  const items: StocktakeItemForm[] = rows.value.map((row) => ({
    sku_id: row.sku_id,
    actual_qty: row.actual_qty,
  }))
  submitting.value = true
  try {
    const res = await submitStocktake({ remark: remark.value || undefined, items })
    result.value = res
    ElMessage.success(`盘点完成：共 ${res.total} 条，盘盈 ${res.gain_count}，盘亏 ${res.loss_count}`)
    rows.value = []
    remark.value = ''
    remoteSearch('')
  } finally {
    submitting.value = false
  }
}

onMounted(() => remoteSearch(''))
</script>

<style scoped lang="scss">
.stocktake-form {
  padding-bottom: 8px;
}

.stocktake-form__title,
.stocktake-table__title,
.stocktake-result__title {
  margin-bottom: 12px;
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-base);
}

.stocktake-table,
.stocktake-result {
  margin-top: var(--padding-base);
}

.mt-16 {
  margin-top: 16px;
}

/* 主表格行 hover 高亮（该页行不可点击，仅高亮，不显示手型） */
.hover-table {
  :deep(.el-table__body tr:hover > td.el-table__cell) {
    background-color: var(--el-color-primary-light-9) !important;
  }
}
</style>
