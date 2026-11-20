<template>
  <div class="page-container">
    <PageTable :total="total" :page="query.page" :page-size="query.page_size" @change="handlePageChange">
      <template #query>
        <QueryForm :loading="loading" @search="handleSearch" @reset="handleReset">
          <el-form-item label="关键字">
            <el-input
              v-model="query.keyword"
              placeholder="平台编码 / 名称"
              clearable
              style="width: 200px"
              @keyup.enter="handleSearch"
            />
          </el-form-item>
          <el-form-item label="状态">
            <DictSelect v-model="query.status" type="enableStatus" width="140px" />
          </el-form-item>
        </QueryForm>
      </template>

      <template #toolbar>
        <el-button v-permission="'platform:create'" type="primary" :icon="Plus" @click="openCreate">
          新增平台
        </el-button>
      </template>

      <el-table v-loading="loading" :data="list" stripe border>
        <el-table-column type="index" label="#" width="60" align="center" />
        <el-table-column prop="platform_code" label="平台编码" min-width="130" />
        <el-table-column prop="platform_name" label="平台名称" min-width="140" />
        <el-table-column prop="sort_no" label="排序" width="90" align="center" />
        <el-table-column prop="remark" label="备注" min-width="200" show-overflow-tooltip />
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <StatusTag :value="row.status" scene="common" />
          </template>
        </el-table-column>
        <el-table-column label="创建时间" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="190" align="right" fixed="right">
          <template #default="{ row }">
            <el-button v-permission="'platform:edit'" link type="primary" @click="openEdit(row)">
              编辑
            </el-button>
            <el-button
              v-permission="'platform:status'"
              link
              :type="row.status === 1 ? 'warning' : 'success'"
              @click="handleToggleStatus(row)"
            >
              {{ row.status === 1 ? '停用' : '启用' }}
            </el-button>
            <el-button v-permission="'platform:delete'" link type="danger" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </PageTable>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑平台' : '新增平台'" width="480px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="平台编码" prop="platform_code">
          <el-input v-model="form.platform_code" :disabled="isEdit" placeholder="如 TAOBAO" />
        </el-form-item>
        <el-form-item label="平台名称" prop="platform_name">
          <el-input v-model="form.platform_name" placeholder="如 淘宝/天猫" />
        </el-form-item>
        <el-form-item label="图标地址">
          <el-input v-model="form.icon" placeholder="图标地址（可选）" />
        </el-form-item>
        <el-form-item label="排序号" prop="sort_no">
          <el-input-number v-model="form.sort_no" :min="0" :max="9999" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="3" placeholder="请输入备注" />
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
// 平台管理：平台字典增改删 + 启停
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import PageTable from '@/components/PageTable.vue'
import QueryForm from '@/components/QueryForm.vue'
import StatusTag from '@/components/StatusTag.vue'
import DictSelect from '@/components/DictSelect.vue'
import {
  getPlatformList,
  createPlatform,
  updatePlatform,
  deletePlatform,
  updatePlatformStatus,
} from '@/api/platform'
import { useDictStore } from '@/store/dict'
import { formatDateTime } from '@/utils/datetime'
import type { Platform, PlatformForm } from '@/types/platform'

const loading = ref(false)
const submitting = ref(false)
const list = ref<Platform[]>([])
const total = ref(0)
const dictStore = useDictStore()

const query = reactive({
  page: 1,
  page_size: 10,
  keyword: '',
  status: undefined as number | undefined,
})

async function fetchList() {
  loading.value = true
  try {
    const res = await getPlatformList({
      page: query.page,
      page_size: query.page_size,
      keyword: query.keyword || undefined,
      status: query.status,
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
const form = reactive<PlatformForm>({
  platform_code: '',
  platform_name: '',
  icon: '',
  sort_no: 0,
  status: 1,
  remark: '',
})

const rules: FormRules = {
  platform_code: [{ required: true, message: '请输入平台编码', trigger: 'blur' }],
  platform_name: [{ required: true, message: '请输入平台名称', trigger: 'blur' }],
}

function resetForm() {
  form.id = undefined
  form.platform_code = ''
  form.platform_name = ''
  form.icon = ''
  form.sort_no = 0
  form.status = 1
  form.remark = ''
}

function openCreate() {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

function openEdit(row: Platform) {
  isEdit.value = true
  form.id = row.id
  form.platform_code = row.platform_code
  form.platform_name = row.platform_name
  form.icon = row.icon
  form.sort_no = row.sort_no
  form.status = row.status
  form.remark = row.remark
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      if (isEdit.value && form.id) {
        await updatePlatform(form.id, { ...form })
        ElMessage.success('保存成功')
      } else {
        await createPlatform({ ...form })
        ElMessage.success('新增成功')
      }
      dialogVisible.value = false
      dictStore.platformLoaded = false
      fetchList()
    } finally {
      submitting.value = false
    }
  })
}

async function handleToggleStatus(row: Platform) {
  const next = row.status === 1 ? 0 : 1
  const action = next === 1 ? '启用' : '停用'
  try {
    await ElMessageBox.confirm(`确定要${action}平台「${row.platform_name}」吗？`, '提示', { type: 'warning' })
  } catch {
    return
  }
  await updatePlatformStatus(row.id, next)
  ElMessage.success(`${action}成功`)
  dictStore.platformLoaded = false
  fetchList()
}

async function handleDelete(row: Platform) {
  try {
    await ElMessageBox.confirm(`确定要删除平台「${row.platform_name}」吗？`, '提示', { type: 'warning' })
  } catch {
    return
  }
  await deletePlatform(row.id)
  ElMessage.success('删除成功')
  dictStore.platformLoaded = false
  fetchList()
}

onMounted(fetchList)
</script>
