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
          <el-form-item label="店铺">
            <DictSelect v-model="query.shop_id" type="shop" width="180px" />
          </el-form-item>
          <el-form-item label="平台">
            <DictSelect v-model="query.platform_code" type="platform" width="160px" />
          </el-form-item>
        </QueryForm>
      </template>

      <template #toolbar>
        <el-button v-permission="'inventory:share_edit'" type="primary" :icon="Plus" @click="openCreate">
          新增共享配置
        </el-button>
      </template>

      <el-table v-loading="loading" class="hover-table" :data="list" stripe border>
        <el-table-column type="index" label="#" width="60" align="center" />
        <el-table-column prop="sku_code" label="SKU 编码" min-width="150" show-overflow-tooltip />
        <el-table-column prop="sku_name" label="SKU 名称" min-width="170" show-overflow-tooltip />
        <el-table-column prop="platform_name" label="平台" min-width="110" />
        <el-table-column prop="shop_name" label="参与共享店铺" min-width="160" show-overflow-tooltip />
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <StatusTag :value="row.status" scene="common" />
          </template>
        </el-table-column>
        <el-table-column label="创建时间" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="150" align="right" fixed="right">
          <template #default="{ row }">
            <el-button v-permission="'inventory:share_edit'" link type="primary" @click="openEdit(row)">
              编辑
            </el-button>
            <el-button v-permission="'inventory:share_edit'" link type="danger" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </PageTable>

    <!-- 新增/编辑共享配置 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑共享配置' : '新增共享配置'" width="520px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
        <el-form-item label="本地 SKU 编码" prop="sku_code">
          <el-input v-model="form.sku_code" :disabled="isEdit" placeholder="请输入本地 SKU 编码" />
        </el-form-item>
        <el-form-item label="参与共享店铺" prop="shop_id">
          <DictSelect v-model="form.shop_id" type="shop" width="100%" />
        </el-form-item>
        <el-form-item label="平台">
          <DictSelect v-model="form.platform_code" type="platform" width="100%" />
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
  </div>
</template>

<script setup lang="ts">
// 库存共享：配置 SKU 的共享店铺范围，支持新增/修改/删除
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import PageTable from '@/components/PageTable.vue'
import QueryForm from '@/components/QueryForm.vue'
import StatusTag from '@/components/StatusTag.vue'
import DictSelect from '@/components/DictSelect.vue'
import {
  getInventoryShares,
  createInventoryShare,
  updateInventoryShare,
  deleteInventoryShare,
} from '@/api/inventory'
import { formatDateTime } from '@/utils/datetime'
import type { InventoryShare, InventoryShareForm } from '@/types/inventory'

const loading = ref(false)
const submitting = ref(false)
const list = ref<InventoryShare[]>([])
const total = ref(0)

const query = reactive({
  page: 1,
  page_size: 10,
  keyword: '',
  shop_id: undefined as number | undefined,
  platform_code: undefined as string | undefined,
})

async function fetchList() {
  loading.value = true
  try {
    const res = await getInventoryShares({
      page: query.page,
      page_size: query.page_size,
      keyword: query.keyword || undefined,
      shop_id: query.shop_id,
      platform_code: query.platform_code,
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
  query.shop_id = undefined
  query.platform_code = undefined
  query.page = 1
  fetchList()
}

function handlePageChange(payload: { page: number; pageSize: number }) {
  query.page = payload.page
  query.page_size = payload.pageSize
  fetchList()
}

// ---------- 新增/编辑 ----------
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref<FormInstance>()
const form = reactive<InventoryShareForm & { sku_code?: string }>({
  sku_id: undefined,
  shop_id: undefined,
  platform_code: undefined,
  status: 1,
  sku_code: '',
})

const rules: FormRules = {
  sku_code: [{ required: true, message: '请输入本地 SKU 编码', trigger: 'blur' }],
  shop_id: [{ required: true, message: '请选择参与共享店铺', trigger: 'change' }],
}

function openCreate() {
  isEdit.value = false
  form.id = undefined
  form.sku_id = undefined
  form.sku_code = ''
  form.shop_id = undefined
  form.platform_code = undefined
  form.status = 1
  dialogVisible.value = true
}

function openEdit(row: InventoryShare) {
  isEdit.value = true
  form.id = row.id
  form.sku_id = row.sku_id
  form.sku_code = row.sku_code
  form.shop_id = row.shop_id
  form.platform_code = row.platform_code
  form.status = row.status
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      const payload: InventoryShareForm = {
        id: form.id,
        sku_id: form.sku_id,
        shop_id: form.shop_id,
        platform_code: form.platform_code,
        status: form.status,
      }
      if (isEdit.value && form.id) {
        await updateInventoryShare(form.id, payload)
        ElMessage.success('保存成功')
      } else {
        await createInventoryShare(payload)
        ElMessage.success('新增成功')
      }
      dialogVisible.value = false
      fetchList()
    } finally {
      submitting.value = false
    }
  })
}

async function handleDelete(row: InventoryShare) {
  try {
    await ElMessageBox.confirm(
      `确定要删除 SKU「${row.sku_code}」在店铺「${row.shop_name || row.shop_id}」的共享配置吗？`,
      '提示',
      { type: 'warning' },
    )
  } catch {
    return
  }
  await deleteInventoryShare(row.id)
  ElMessage.success('删除成功')
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
