<template>
  <div class="page-container">
    <el-tabs v-model="activeTab">
      <!-- 预警列表 -->
      <el-tab-pane label="预警列表" name="alert">
        <PageTable :total="alertTotal" :page="alertQuery.page" :page-size="alertQuery.page_size" @change="handleAlertPageChange">
          <template #query>
            <QueryForm :loading="alertLoading" @search="handleAlertSearch" @reset="handleAlertReset">
              <el-form-item label="SKU">
                <el-input
                  v-model="alertQuery.keyword"
                  placeholder="SKU 编码 / 名称"
                  clearable
                  style="width: 200px"
                  @keyup.enter="handleAlertSearch"
                />
              </el-form-item>
            </QueryForm>
          </template>

          <el-table v-loading="alertLoading" class="hover-table" :data="alertList" stripe border>
            <el-table-column prop="sku_code" label="SKU 编码" min-width="150" show-overflow-tooltip />
            <el-table-column prop="sku_name" label="SKU 名称" min-width="170" show-overflow-tooltip />
            <el-table-column label="主库存" width="100" align="right">
              <template #default="{ row }">{{ formatNumber(row.main_qty) }}</template>
            </el-table-column>
            <el-table-column label="占用" width="100" align="right">
              <template #default="{ row }">{{ formatNumber(row.occupied_qty) }}</template>
            </el-table-column>
            <el-table-column label="可售" width="100" align="right">
              <template #default="{ row }">
                <span class="text-warning">{{ formatNumber(availableOf(row)) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="安全阈值" width="110" align="right">
              <template #default="{ row }">{{ formatNumber(row.alert_qty) }}</template>
            </el-table-column>
            <el-table-column label="库存水平" width="130" align="center">
              <template #default="{ row }">
                <StatusTag :value="levelOf(row)" scene="inventoryLevel" />
              </template>
            </el-table-column>
            <el-table-column label="更新时间" min-width="170">
              <template #default="{ row }">{{ formatDateTime(row.updated_at) }}</template>
            </el-table-column>
          </el-table>
        </PageTable>
      </el-tab-pane>

      <!-- 预警配置 -->
      <el-tab-pane label="预警配置" name="config">
        <PageTable :total="configTotal" :page="configQuery.page" :page-size="configQuery.page_size" @change="handleConfigPageChange">
          <template #query>
            <QueryForm :loading="configLoading" @search="handleConfigSearch" @reset="handleConfigReset">
              <el-form-item label="SKU">
                <el-input
                  v-model="configQuery.keyword"
                  placeholder="SKU 编码 / 名称"
                  clearable
                  style="width: 200px"
                  @keyup.enter="handleConfigSearch"
                />
              </el-form-item>
              <el-form-item label="是否启用">
                <DictSelect v-model="configQuery.is_enabled" type="enableStatus" width="130px" />
              </el-form-item>
            </QueryForm>
          </template>

          <el-table v-loading="configLoading" class="hover-table" :data="configList" stripe border>
            <el-table-column prop="sku_code" label="SKU 编码" min-width="150" show-overflow-tooltip />
            <el-table-column prop="sku_name" label="SKU 名称" min-width="170" show-overflow-tooltip />
            <el-table-column label="安全阈值" width="120" align="right">
              <template #default="{ row }">{{ formatNumber(row.alert_qty) }}</template>
            </el-table-column>
            <el-table-column label="是否启用" width="110" align="center">
              <template #default="{ row }">
                <StatusTag :value="row.is_enabled" scene="common" />
              </template>
            </el-table-column>
            <el-table-column label="更新时间" min-width="170">
              <template #default="{ row }">{{ formatDateTime(row.updated_at) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="130" align="right" fixed="right">
              <template #default="{ row }">
                <el-button v-permission="'inventory:alert_edit'" link type="primary" @click="openEdit(row)">
                  编辑阈值
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </PageTable>
      </el-tab-pane>
    </el-tabs>

    <!-- 编辑安全库存阈值 -->
    <el-dialog v-model="dialogVisible" title="编辑预警配置" width="480px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="110px">
        <el-form-item label="SKU 编码">
          <span>{{ current?.sku_code }}</span>
        </el-form-item>
        <el-form-item label="SKU 名称">
          <span>{{ current?.sku_name || '-' }}</span>
        </el-form-item>
        <el-form-item label="安全阈值" prop="alert_qty">
          <el-input-number v-model="form.alert_qty" :min="0" :step="1" style="width: 100%" />
        </el-form-item>
        <el-form-item label="是否启用">
          <el-switch v-model="form.is_enabled" :active-value="1" :inactive-value="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
// 库存预警：预警列表（低于安全阈值的 SKU）+ 预警配置（安全阈值/启用），编辑阈值
import { onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import PageTable from '@/components/PageTable.vue'
import QueryForm from '@/components/QueryForm.vue'
import StatusTag from '@/components/StatusTag.vue'
import DictSelect from '@/components/DictSelect.vue'
import {
  getInventoryAlerts,
  getInventoryAlertConfigs,
  updateInventoryAlertConfig,
} from '@/api/inventory'
import { formatNumber } from '@/utils/format'
import { formatDateTime } from '@/utils/datetime'
import type { InventoryAlert, InventoryAlertConfig, InventoryAlertConfigForm } from '@/types/inventory'

const activeTab = ref<'alert' | 'config'>('alert')

// ---------- 预警列表 ----------
const alertLoading = ref(false)
const alertList = ref<InventoryAlert[]>([])
const alertTotal = ref(0)
const alertQuery = reactive({ page: 1, page_size: 10, keyword: '' })

async function fetchAlerts() {
  alertLoading.value = true
  try {
    const res = await getInventoryAlerts({
      page: alertQuery.page,
      page_size: alertQuery.page_size,
      keyword: alertQuery.keyword || undefined,
    })
    alertList.value = res.list ?? []
    alertTotal.value = res.total ?? 0
  } finally {
    alertLoading.value = false
  }
}

function handleAlertSearch() {
  alertQuery.page = 1
  fetchAlerts()
}

function handleAlertReset() {
  alertQuery.keyword = ''
  alertQuery.page = 1
  fetchAlerts()
}

function handleAlertPageChange(payload: { page: number; pageSize: number }) {
  alertQuery.page = payload.page
  alertQuery.page_size = payload.pageSize
  fetchAlerts()
}

function availableOf(row: InventoryAlert) {
  return row.available_qty ?? (row.main_qty ?? 0) - (row.occupied_qty ?? 0)
}

function levelOf(row: InventoryAlert) {
  if (row.stock_status) return row.stock_status
  const available = availableOf(row)
  if (available <= 0) return 'OUT'
  return 'LOW'
}

// ---------- 预警配置 ----------
const configLoading = ref(false)
const configList = ref<InventoryAlertConfig[]>([])
const configTotal = ref(0)
const configQuery = reactive({
  page: 1,
  page_size: 10,
  keyword: '',
  is_enabled: undefined as number | undefined,
})
const configLoaded = ref(false)

async function fetchConfigs() {
  configLoading.value = true
  try {
    const res = await getInventoryAlertConfigs({
      page: configQuery.page,
      page_size: configQuery.page_size,
      keyword: configQuery.keyword || undefined,
      is_enabled: configQuery.is_enabled,
    })
    configList.value = res.list ?? []
    configTotal.value = res.total ?? 0
    configLoaded.value = true
  } finally {
    configLoading.value = false
  }
}

function handleConfigSearch() {
  configQuery.page = 1
  fetchConfigs()
}

function handleConfigReset() {
  configQuery.keyword = ''
  configQuery.is_enabled = undefined
  configQuery.page = 1
  fetchConfigs()
}

function handleConfigPageChange(payload: { page: number; pageSize: number }) {
  configQuery.page = payload.page
  configQuery.page_size = payload.pageSize
  fetchConfigs()
}

// 首次切换到配置页时懒加载
watch(activeTab, (tab) => {
  if (tab === 'config' && !configLoaded.value) fetchConfigs()
})

// ---------- 编辑阈值 ----------
const dialogVisible = ref(false)
const submitting = ref(false)
const formRef = ref<FormInstance>()
const current = ref<InventoryAlertConfig | null>(null)
const form = reactive<InventoryAlertConfigForm>({ alert_qty: 0, is_enabled: 1 })
const rules: FormRules = {
  alert_qty: [{ required: true, message: '请输入安全阈值', trigger: 'blur' }],
}

function openEdit(row: InventoryAlertConfig) {
  current.value = row
  form.id = row.id
  form.alert_qty = row.alert_qty
  form.is_enabled = row.is_enabled
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!formRef.value || !current.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      await updateInventoryAlertConfig(current.value!.id, { alert_qty: form.alert_qty, is_enabled: form.is_enabled })
      ElMessage.success('保存成功')
      dialogVisible.value = false
      fetchConfigs()
      fetchAlerts()
    } finally {
      submitting.value = false
    }
  })
}

onMounted(fetchAlerts)
</script>

<style scoped lang="scss">
/* 主表格行 hover 高亮（该页行不可点击，仅高亮，不显示手型） */
.hover-table {
  :deep(.el-table__body tr:hover > td.el-table__cell) {
    background-color: var(--el-color-primary-light-9) !important;
  }
}
</style>
