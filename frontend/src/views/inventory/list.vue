<template>
  <div class="page-container">
    <PageTable :total="total" :page="query.page" :page-size="query.page_size" @change="handlePageChange">
      <template #query>
        <QueryForm :loading="loading" @search="handleSearch" @reset="handleReset">
          <el-form-item label="SKU">
            <el-input
              v-model="query.keyword"
              placeholder="SKU 编码 / 名称"
              clearable
              style="width: 200px"
              @keyup.enter="handleSearch"
            />
          </el-form-item>
          <el-form-item label="状态">
            <DictSelect v-model="query.status" type="inventoryStatus" width="130px" />
          </el-form-item>
          <el-form-item label="预警">
            <el-checkbox v-model="query.alert_only">仅低于安全阈值</el-checkbox>
          </el-form-item>
        </QueryForm>
      </template>

      <el-table
        v-loading="loading"
        class="clickable-table"
        :data="list"
        stripe
        border
        @row-click="openEdit"
      >
        <el-table-column prop="sku_code" label="SKU 编码" min-width="150" show-overflow-tooltip />
        <el-table-column prop="sku_name" label="SKU 名称" min-width="170" show-overflow-tooltip />
        <el-table-column prop="spu_name" label="商品名称" min-width="170" show-overflow-tooltip />
        <el-table-column label="主库存" width="100" align="right">
          <template #default="{ row }">{{ formatNumber(row.main_qty) }}</template>
        </el-table-column>
        <el-table-column label="占用" width="100" align="right">
          <template #default="{ row }">{{ formatNumber(row.occupied_qty) }}</template>
        </el-table-column>
        <el-table-column label="可售" width="100" align="right">
          <template #default="{ row }">
            <span :class="{ 'text-warning': availableOf(row) < (row.alert_qty ?? 0) }">
              {{ formatNumber(availableOf(row)) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="安全阈值" width="100" align="right">
          <template #default="{ row }">{{ row.alert_qty != null ? formatNumber(row.alert_qty) : '-' }}</template>
        </el-table-column>
        <el-table-column label="库存水平" width="130" align="center">
          <template #default="{ row }">
            <StatusTag :value="levelOf(row)" scene="inventoryLevel" />
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <StatusTag :value="row.status" scene="common" />
          </template>
        </el-table-column>
        <el-table-column label="更新时间" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.updated_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="180" align="right" fixed="right">
          <template #default="{ row }">
            <el-button v-permission="'inventory:edit'" link type="primary" @click.stop="openEdit(row)">
              编辑
            </el-button>
            <el-button v-permission="'inventory:push'" link type="primary" @click.stop="handlePush(row)">
              回写平台
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </PageTable>

    <!-- 编辑主库存 -->
    <el-dialog v-model="dialogVisible" title="编辑主库存" width="500px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="SKU 编码">
          <span>{{ current?.sku_code }}</span>
        </el-form-item>
        <el-form-item label="SKU 名称">
          <span>{{ current?.sku_name || '-' }}</span>
        </el-form-item>
        <el-form-item label="当前主库存">
          <span>{{ formatNumber(current?.main_qty ?? 0) }}</span>
        </el-form-item>
        <el-form-item label="主库存" prop="main_qty">
          <el-input-number v-model="form.main_qty" :min="0" :step="1" style="width: 100%" />
        </el-form-item>
        <el-form-item label="调整备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" placeholder="请输入调整备注" />
        </el-form-item>
      </el-form>
      <el-alert
        class="mb-16"
        type="info"
        :closable="false"
        show-icon
        title="修改主库存会生成一条库存变动流水用于追溯"
      />
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
// 库存管理：主库存/占用/可售展示，编辑主库存（生成流水）与可售库存回写平台
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import PageTable from '@/components/PageTable.vue'
import QueryForm from '@/components/QueryForm.vue'
import StatusTag from '@/components/StatusTag.vue'
import DictSelect from '@/components/DictSelect.vue'
import { getInventoryList, updateInventory, pushInventory } from '@/api/inventory'
import { formatNumber } from '@/utils/format'
import { formatDateTime } from '@/utils/datetime'
import type { Inventory } from '@/types/inventory'

const loading = ref(false)
const submitting = ref(false)
const list = ref<Inventory[]>([])
const total = ref(0)

const query = reactive({
  page: 1,
  page_size: 10,
  keyword: '',
  status: undefined as number | undefined,
  alert_only: false,
})

async function fetchList() {
  loading.value = true
  try {
    const res = await getInventoryList({
      page: query.page,
      page_size: query.page_size,
      keyword: query.keyword || undefined,
      status: query.status,
      alert_only: query.alert_only || undefined,
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
  query.keyword = ''
  query.status = undefined
  query.alert_only = false
  query.page = 1
  fetchList()
}

function handlePageChange(payload: { page: number; pageSize: number }) {
  query.page = payload.page
  query.page_size = payload.pageSize
  fetchList()
}

/** 可售库存：优先用后端返回值，否则按 主库存 - 占用 计算 */
function availableOf(row: Inventory) {
  return row.available_qty ?? (row.main_qty ?? 0) - (row.occupied_qty ?? 0)
}

/** 库存水平：可售 <= 0 缺货 / 低于安全阈值 / 正常 */
function levelOf(row: Inventory) {
  const available = availableOf(row)
  if (available <= 0) return 'OUT'
  if (row.alert_qty != null && available < row.alert_qty) return 'LOW'
  return 'NORMAL'
}

// ---------- 编辑主库存 ----------
const dialogVisible = ref(false)
const formRef = ref<FormInstance>()
const current = ref<Inventory | null>(null)
const form = reactive({ main_qty: 0, remark: '' })
const rules: FormRules = {
  main_qty: [{ required: true, message: '请输入主库存', trigger: 'blur' }],
}

function openEdit(row: Inventory) {
  current.value = row
  form.main_qty = row.main_qty
  form.remark = ''
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!formRef.value || !current.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      await updateInventory(current.value!.sku_id, { main_qty: form.main_qty, remark: form.remark })
      ElMessage.success('保存成功')
      dialogVisible.value = false
      fetchList()
    } finally {
      submitting.value = false
    }
  })
}

async function handlePush(row: Inventory) {
  try {
    await ElMessageBox.confirm(
      `确定将 SKU「${row.sku_code}」的可售库存（${formatNumber(availableOf(row))}）回写到平台吗？`,
      '提示',
      { type: 'warning' },
    )
  } catch {
    return
  }
  await pushInventory(row.sku_id)
  ElMessage.success('回写平台成功')
}

onMounted(fetchList)
</script>

<style scoped lang="scss">
.mb-16 {
  margin-bottom: 16px;
}

/* 可点击行：鼠标悬浮手型 + 高亮，提示该行可编辑库存 */
.clickable-table {
  :deep(.el-table__row) {
    cursor: pointer;
    transition: background-color 0.2s ease;
  }

  :deep(.el-table__body tr:hover > td.el-table__cell) {
    background-color: var(--el-color-primary-light-9) !important;
  }
}
</style>
