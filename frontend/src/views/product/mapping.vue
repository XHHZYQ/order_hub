<template>
  <div class="page-container">
    <PageTable :total="total" :page="query.page" :page-size="query.page_size" @change="handlePageChange">
      <template #query>
        <QueryForm :loading="loading" @search="handleSearch" @reset="handleReset">
          <el-form-item label="店铺">
            <DictSelect v-model="query.shop_id" type="shop" width="180px" />
          </el-form-item>
          <el-form-item label="平台">
            <DictSelect v-model="query.platform_code" type="platform" width="160px" />
          </el-form-item>
          <el-form-item label="关键字">
            <el-input
              v-model="query.keyword"
              placeholder="平台规格 ID / 本地 SKU 编码"
              clearable
              style="width: 220px"
              @keyup.enter="handleSearch"
            />
          </el-form-item>
        </QueryForm>
      </template>

      <template #tips>
        <el-alert
          v-if="unmatchedTotal > 0"
          type="warning"
          show-icon
          :closable="false"
          title="存在未匹配的平台规格"
        >
          <template #default>
            当前有 <b class="text-warning">{{ unmatchedTotal }}</b> 个平台规格未匹配本地 SKU，可能影响库存同步与防超卖，请及时维护映射。
            <el-button link type="primary" @click="openUnmatched">前往处理</el-button>
          </template>
        </el-alert>
      </template>

      <template #toolbar>
        <el-button v-permission="'mapping:create'" type="primary" :icon="Plus" @click="openCreate">
          新增映射
        </el-button>
        <el-button v-permission="'mapping:create'" :icon="Operation" @click="openBatch">批量维护</el-button>
        <el-upload
          ref="uploadRef"
          :show-file-list="false"
          :auto-upload="false"
          accept=".csv"
          :on-change="handleImportFile"
        >
          <el-button v-permission="'mapping:import'" :icon="Upload">导入映射</el-button>
        </el-upload>
        <el-button v-permission="'mapping:export'" :icon="Download" @click="handleExport">导出映射</el-button>
      </template>

      <el-table v-loading="loading" class="hover-table" :data="list" stripe border>
        <el-table-column type="index" label="#" width="60" align="center" />
        <el-table-column prop="platform_code" label="平台编码" min-width="110" />
        <el-table-column prop="shop_name" label="店铺" min-width="150" show-overflow-tooltip />
        <el-table-column prop="platform_sku_id" label="平台规格 ID" min-width="150" show-overflow-tooltip />
        <el-table-column prop="platform_sku_name" label="平台规格名称" min-width="180" show-overflow-tooltip />
        <el-table-column prop="sku_code" label="本地 SKU 编码" min-width="150" show-overflow-tooltip />
        <el-table-column prop="sku_name" label="本地 SKU 名称" min-width="160" show-overflow-tooltip />
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <StatusTag :value="row.status" scene="common" />
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="140" show-overflow-tooltip />
        <el-table-column label="操作" width="150" align="right" fixed="right">
          <template #default="{ row }">
            <el-button v-permission="'mapping:edit'" link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button v-permission="'mapping:delete'" link type="danger" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </PageTable>

    <!-- 新增/编辑映射 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑映射' : '新增映射'" width="540px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="110px">
        <el-form-item label="店铺" prop="shop_id">
          <DictSelect
            v-model="form.shop_id"
            type="shop"
            :disabled="isEdit"
            width="100%"
            @update:model-value="handleShopChange"
          />
        </el-form-item>
        <el-form-item label="平台规格 ID" prop="platform_sku_id">
          <el-input v-model="form.platform_sku_id" :disabled="isEdit" placeholder="如 平台规格 ID" />
        </el-form-item>
        <el-form-item label="平台规格名称">
          <el-input v-model="form.platform_sku_name" placeholder="选填" />
        </el-form-item>
        <el-form-item label="本地 SKU 编码" prop="sku_code">
          <el-input v-model="form.sku_code" placeholder="请输入本地 SKU 编码" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" placeholder="请输入备注" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.status" :active-value="1" :inactive-value="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 批量维护 -->
    <el-dialog v-model="batchVisible" title="批量维护映射" width="600px" destroy-on-close>
      <el-alert
        class="mb-16"
        type="info"
        :closable="false"
        show-icon
        title="每行一条，格式：平台规格 ID,本地 SKU 编码（英文逗号分隔）"
      />
      <el-form label-width="110px">
        <el-form-item label="店铺">
          <DictSelect v-model="batchForm.shop_id" type="shop" width="100%" />
        </el-form-item>
        <el-form-item label="映射数据">
          <el-input
            v-model="batchText"
            type="textarea"
            :rows="10"
            placeholder="例如：&#10;P-SKU-1001,SKU0001001&#10;P-SKU-1002,SKU0001002"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="batchVisible = false">取消</el-button>
        <el-button type="primary" :loading="batchSubmitting" @click="handleBatchSubmit">提交</el-button>
      </template>
    </el-dialog>

    <!-- 未匹配列表 -->
    <el-drawer v-model="unmatchedVisible" title="未匹配平台规格" size="60%" @open="fetchUnmatched">
      <el-alert
        class="mb-16"
        type="warning"
        show-icon
        :closable="false"
        title="以下平台规格尚未映射本地 SKU，请尽快维护"
      />
      <el-table v-loading="unmatchedLoading" :data="unmatchedList" stripe border height="calc(100vh - 260px)">
        <el-table-column prop="platform_code" label="平台编码" width="110" />
        <el-table-column prop="shop_name" label="店铺" min-width="150" show-overflow-tooltip />
        <el-table-column prop="platform_sku_id" label="平台规格 ID" min-width="150" show-overflow-tooltip />
        <el-table-column label="平台规格名称" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">{{ row.platform_sku_name || row.sku_name || '-' }}</template>
        </el-table-column>
        <el-table-column prop="outer_sku_code" label="商家编码" min-width="130" show-overflow-tooltip />
        <el-table-column label="操作" width="120" align="right" fixed="right">
          <template #default="{ row }">
            <el-button v-permission="'mapping:create'" link type="primary" @click="openMappingFromUnmatched(row)">
              建立映射
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pager">
        <el-pagination
          :current-page="unmatchedQuery.page"
          :page-size="unmatchedQuery.page_size"
          :total="unmatchedTotal"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          background
          @current-change="handleUnmatchedPageChange"
          @size-change="handleUnmatchedSizeChange"
        />
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
// SKU 映射：映射列表增改删 + 批量维护 + 导入/导出 + 未匹配提示与处理
import { onMounted, reactive, ref } from 'vue'
import {
  ElMessage,
  ElMessageBox,
  type FormInstance,
  type FormRules,
  type UploadFile,
  type UploadInstance,
} from 'element-plus'
import { Plus, Upload, Download, Operation } from '@element-plus/icons-vue'
import PageTable from '@/components/PageTable.vue'
import QueryForm from '@/components/QueryForm.vue'
import StatusTag from '@/components/StatusTag.vue'
import DictSelect from '@/components/DictSelect.vue'
import {
  getSkuMappingList,
  createSkuMapping,
  updateSkuMapping,
  deleteSkuMapping,
  batchSkuMapping,
  getUnmatchedMappings,
  importSkuMappings,
  exportSkuMappings,
} from '@/api/product'
import type { SkuMapping, SkuMappingForm, UnmatchedSku } from '@/types/product'

const loading = ref(false)
const submitting = ref(false)
const list = ref<SkuMapping[]>([])
const total = ref(0)
const uploadRef = ref<UploadInstance>()

const query = reactive({
  page: 1,
  page_size: 10,
  shop_id: undefined as number | undefined,
  platform_code: undefined as string | undefined,
  keyword: '',
})

async function fetchList() {
  loading.value = true
  try {
    const res = await getSkuMappingList({
      page: query.page,
      page_size: query.page_size,
      shop_id: query.shop_id,
      platform_code: query.platform_code,
      keyword: query.keyword || undefined,
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
  query.shop_id = undefined
  query.platform_code = undefined
  query.keyword = ''
  query.page = 1
  fetchList()
}

function handlePageChange(payload: { page: number; pageSize: number }) {
  query.page = payload.page
  query.page_size = payload.pageSize
  fetchList()
}

// ---------- 未匹配数量提示 ----------
const unmatchedTotal = ref(0)

async function fetchUnmatchedCount() {
  try {
    const res = await getUnmatchedMappings({ page: 1, page_size: 1 })
    unmatchedTotal.value = res.total ?? 0
  } catch {
    unmatchedTotal.value = 0
  }
}

// ---------- 新增/编辑 ----------
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref<FormInstance>()
const form = reactive<SkuMappingForm>({
  shop_id: undefined,
  platform_sku_id: '',
  platform_sku_name: '',
  sku_id: undefined,
  sku_code: '',
  status: 1,
  remark: '',
})

const rules: FormRules = {
  shop_id: [{ required: true, message: '请选择店铺', trigger: 'change' }],
  platform_sku_id: [{ required: true, message: '请输入平台规格 ID', trigger: 'blur' }],
  sku_code: [{ required: true, message: '请输入本地 SKU 编码', trigger: 'blur' }],
}

function handleShopChange() {
  form.platform_code = undefined
}

function resetForm() {
  form.id = undefined
  form.shop_id = undefined
  form.platform_code = undefined
  form.platform_sku_id = ''
  form.platform_sku_name = ''
  form.sku_id = undefined
  form.sku_code = ''
  form.status = 1
  form.remark = ''
}

function openCreate() {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

function openEdit(row: SkuMapping) {
  isEdit.value = true
  form.id = row.id
  form.shop_id = row.shop_id
  form.platform_code = row.platform_code
  form.platform_sku_id = row.platform_sku_id
  form.platform_sku_name = row.platform_sku_name
  form.sku_id = row.sku_id
  form.sku_code = row.sku_code
  form.status = row.status
  form.remark = row.remark
  dialogVisible.value = true
}

function openMappingFromUnmatched(row: UnmatchedSku) {
  isEdit.value = false
  resetForm()
  form.shop_id = row.shop_id
  form.platform_code = row.platform_code
  form.platform_sku_id = row.platform_sku_id
  form.platform_sku_name = row.platform_sku_name || row.sku_name
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      if (isEdit.value && form.id) {
        await updateSkuMapping(form.id, { ...form })
        ElMessage.success('保存成功')
      } else {
        await createSkuMapping({ ...form })
        ElMessage.success('新增成功')
      }
      dialogVisible.value = false
      fetchList()
      fetchUnmatchedCount()
      if (unmatchedVisible.value) fetchUnmatched()
    } finally {
      submitting.value = false
    }
  })
}

async function handleDelete(row: SkuMapping) {
  try {
    await ElMessageBox.confirm(
      `确定要删除平台规格「${row.platform_sku_id}」与本地 SKU「${row.sku_code}」的映射吗？`,
      '提示',
      { type: 'warning' },
    )
  } catch {
    return
  }
  await deleteSkuMapping(row.id)
  ElMessage.success('删除成功')
  fetchList()
  fetchUnmatchedCount()
}

// ---------- 批量维护 ----------
const batchVisible = ref(false)
const batchSubmitting = ref(false)
const batchText = ref('')
const batchForm = reactive({ shop_id: undefined as number | undefined })

function openBatch() {
  batchForm.shop_id = undefined
  batchText.value = ''
  batchVisible.value = true
}

async function handleBatchSubmit() {
  if (!batchForm.shop_id) {
    ElMessage.warning('请选择店铺')
    return
  }
  const items = batchText.value
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line)
    .map((line) => {
      const [platform_sku_id, sku_code] = line.split(',').map((s) => s.trim())
      return { platform_sku_id, sku_code }
    })
    .filter((item) => item.platform_sku_id && item.sku_code)
  if (!items.length) {
    ElMessage.warning('请按「平台规格 ID,本地 SKU 编码」格式录入至少一条数据')
    return
  }
  batchSubmitting.value = true
  try {
    const res = await batchSkuMapping({ shop_id: batchForm.shop_id, items })
    ElMessage.success(`批量维护完成：成功 ${res.success_count} 条，失败 ${res.fail_count} 条`)
    batchVisible.value = false
    fetchList()
    fetchUnmatchedCount()
  } finally {
    batchSubmitting.value = false
  }
}

// ---------- 导入 / 导出 ----------
async function handleImportFile(uploadFile: UploadFile) {
  const file = uploadFile.raw
  if (!file) return
  try {
    const res = await importSkuMappings(file)
    ElMessage.success(`导入完成：共 ${res.total} 条，成功 ${res.success_count} 条，失败 ${res.fail_count} 条`)
    fetchList()
    fetchUnmatchedCount()
  } finally {
    uploadRef.value?.clearFiles()
  }
}

async function handleExport() {
  const blob = await exportSkuMappings({
    shop_id: query.shop_id,
    platform_code: query.platform_code,
    keyword: query.keyword || undefined,
  })
  const url = URL.createObjectURL(blob as Blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'sku-mappings.xlsx'
  link.click()
  URL.revokeObjectURL(url)
}

// ---------- 未匹配列表 ----------
const unmatchedVisible = ref(false)
const unmatchedLoading = ref(false)
const unmatchedList = ref<UnmatchedSku[]>([])
const unmatchedQuery = reactive({ page: 1, page_size: 10 })

async function fetchUnmatched() {
  unmatchedLoading.value = true
  try {
    const res = await getUnmatchedMappings({
      page: unmatchedQuery.page,
      page_size: unmatchedQuery.page_size,
      platform_code: query.platform_code,
      shop_id: query.shop_id,
    })
    unmatchedList.value = res.list ?? []
    unmatchedTotal.value = res.total ?? 0
  } finally {
    unmatchedLoading.value = false
  }
}

function openUnmatched() {
  unmatchedQuery.page = 1
  unmatchedVisible.value = true
}

function handleUnmatchedPageChange(page: number) {
  unmatchedQuery.page = page
  fetchUnmatched()
}

function handleUnmatchedSizeChange(pageSize: number) {
  unmatchedQuery.page = 1
  unmatchedQuery.page_size = pageSize
  fetchUnmatched()
}

onMounted(() => {
  fetchList()
  fetchUnmatchedCount()
})
</script>

<style scoped lang="scss">
.mb-16 {
  margin-bottom: 16px;
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

/* 主表格行 hover 高亮（该页行不可点击，仅高亮，不显示手型） */
.hover-table {
  :deep(.el-table__body tr:hover > td.el-table__cell) {
    background-color: var(--el-color-primary-light-9) !important;
  }
}
</style>
