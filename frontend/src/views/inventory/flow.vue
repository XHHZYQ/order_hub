<template>
  <div class="page-container">
    <PageTable :total="total" :page="query.page" :page-size="query.page_size" @change="handlePageChange">
      <template #query>
        <QueryForm :loading="loading" @search="handleSearch" @reset="handleReset">
          <el-form-item label="变动类型">
            <DictSelect v-model="query.flow_type" type="flowType" width="160px" />
          </el-form-item>
          <el-form-item label="SKU">
            <el-input
              v-model="query.keyword"
              placeholder="SKU 编码 / 名称"
              clearable
              style="width: 180px"
              @keyup.enter="handleSearch"
            />
          </el-form-item>
          <el-form-item label="来源单号">
            <el-input
              v-model="query.source_no"
              placeholder="来源单号"
              clearable
              style="width: 180px"
              @keyup.enter="handleSearch"
            />
          </el-form-item>
          <el-form-item label="变动时间">
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
      </template>

      <el-table v-loading="loading" class="hover-table" :data="list" stripe border>
        <el-table-column prop="sku_code" label="SKU 编码" min-width="150" show-overflow-tooltip />
        <el-table-column prop="sku_name" label="SKU 名称" min-width="170" show-overflow-tooltip />
        <el-table-column label="变动类型" width="120" align="center">
          <template #default="{ row }">{{ dictLabel(INVENTORY_FLOW_TYPE_DICT, row.flow_type) }}</template>
        </el-table-column>
        <el-table-column label="变动数量" width="110" align="right">
          <template #default="{ row }">
            <span :class="row.change_qty >= 0 ? 'text-success' : 'text-danger'">
              {{ row.change_qty > 0 ? `+${formatNumber(row.change_qty)}` : formatNumber(row.change_qty) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="变动前" width="100" align="right">
          <template #default="{ row }">{{ formatNumber(row.before_qty) }}</template>
        </el-table-column>
        <el-table-column label="变动后" width="100" align="right">
          <template #default="{ row }">{{ formatNumber(row.after_qty) }}</template>
        </el-table-column>
        <el-table-column label="来源类型" width="110" align="center">
          <template #default="{ row }">{{ row.source_type || '-' }}</template>
        </el-table-column>
        <el-table-column prop="source_no" label="来源单号" min-width="160" show-overflow-tooltip />
        <el-table-column prop="operator" label="操作人" min-width="120" />
        <el-table-column prop="remark" label="备注" min-width="160" show-overflow-tooltip />
        <el-table-column label="变动时间" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
      </el-table>
    </PageTable>
  </div>
</template>

<script setup lang="ts">
// 库存流水：按变动类型/来源单号/时间筛选，展示每次库存变动明细
import { onMounted, reactive, ref } from 'vue'
import PageTable from '@/components/PageTable.vue'
import QueryForm from '@/components/QueryForm.vue'
import DictSelect from '@/components/DictSelect.vue'
import { getInventoryFlows } from '@/api/inventory'
import { INVENTORY_FLOW_TYPE_DICT, dictLabel } from '@/store/dict'
import { formatNumber } from '@/utils/format'
import { formatDateTime } from '@/utils/datetime'
import type { InventoryFlow } from '@/types/inventory'

const loading = ref(false)
const list = ref<InventoryFlow[]>([])
const total = ref(0)
const timeRange = ref<[string, string] | null>(null)

const query = reactive({
  page: 1,
  page_size: 10,
  flow_type: undefined as string | undefined,
  keyword: '',
  source_no: '',
})

async function fetchList() {
  loading.value = true
  try {
    const res = await getInventoryFlows({
      page: query.page,
      page_size: query.page_size,
      flow_type: query.flow_type,
      keyword: query.keyword || undefined,
      source_no: query.source_no || undefined,
      start_time: timeRange.value?.[0],
      end_time: timeRange.value?.[1],
    })
    list.value = res.list ?? []
    total.value = res.total ?? 0
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  query.page = 1
  fetchList()
}

function handleReset() {
  query.flow_type = undefined
  query.keyword = ''
  query.source_no = ''
  timeRange.value = null
  query.page = 1
  fetchList()
}

function handlePageChange(payload: { page: number; pageSize: number }) {
  query.page = payload.page
  query.page_size = payload.pageSize
  fetchList()
}

onMounted(fetchList)
</script>

<style scoped lang="scss">
/* 主表格行 hover 高亮（该页行不可点击，仅高亮，不显示手型） */
.hover-table {
  :deep(.el-table__body tr:hover > td.el-table__cell) {
    background-color: var(--el-color-primary-light-9) !important;
  }
}
</style>
