<template>
  <div class="page-container">
    <PageTable :total="total" :page="query.page" :page-size="query.page_size" @change="handlePageChange">
      <template #query>
        <QueryForm :loading="loading" @search="handleSearch" @reset="handleReset">
          <el-form-item label="店铺">
            <DictSelect v-model="query.shop_id" type="shop" width="180px" />
          </el-form-item>
          <el-form-item label="同步类型">
            <DictSelect v-model="query.sync_type" type="syncType" width="130px" />
          </el-form-item>
          <el-form-item label="状态">
            <DictSelect v-model="query.status" type="enableStatus" width="130px" />
          </el-form-item>
        </QueryForm>
      </template>

      <template #toolbar>
        <el-button v-permission="'sync:task_create'" type="primary" :icon="Plus" @click="openCreate">
          新增任务
        </el-button>
      </template>

      <el-table v-loading="loading" :data="list" stripe border>
        <el-table-column type="index" label="#" width="60" align="center" />
        <el-table-column prop="shop_name" label="店铺" min-width="160" show-overflow-tooltip />
        <el-table-column label="同步类型" width="110" align="center">
          <template #default="{ row }">
            <StatusTag :value="row.sync_type" scene="syncType" />
          </template>
        </el-table-column>
        <el-table-column prop="cron_expr" label="Cron 表达式" min-width="150" />
        <el-table-column prop="start_time" label="开始时间" min-width="160">
          <template #default="{ row }">{{ formatDateTime(row.start_time) }}</template>
        </el-table-column>
        <el-table-column label="最近同步" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.last_sync_time) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <StatusTag :value="row.status" scene="common" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" align="right" fixed="right">
          <template #default="{ row }">
            <el-button v-permission="'sync:trigger'" link type="primary" @click="handleTrigger(row)">
              触发
            </el-button>
            <el-button v-permission="'sync:task_edit'" link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button
              v-permission="'sync:task_status'"
              link
              :type="row.status === 1 ? 'warning' : 'success'"
              @click="handleToggleStatus(row)"
            >
              {{ row.status === 1 ? '停用' : '启用' }}
            </el-button>
            <el-button v-permission="'sync:task_delete'" link type="danger" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </PageTable>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑同步任务' : '新增同步任务'" width="520px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="店铺" prop="shop_id">
          <DictSelect v-model="form.shop_id" type="shop" width="100%" />
        </el-form-item>
        <el-form-item label="同步类型" prop="sync_type">
          <DictSelect v-model="form.sync_type" type="syncType" width="100%" />
        </el-form-item>
        <el-form-item label="Cron 表达式" prop="cron_expr">
          <el-input v-model="form.cron_expr" placeholder="如 0 */1 * * *" />
        </el-form-item>
        <el-form-item label="开始时间" prop="start_time">
          <el-date-picker
            v-model="form.start_time"
            type="datetime"
            placeholder="选择开始时间"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 100%"
          />
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
  </div>
</template>

<script setup lang="ts">
// 同步任务：列表 + 新增/编辑/删除/启停 + 手动触发一次
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import PageTable from '@/components/PageTable.vue'
import QueryForm from '@/components/QueryForm.vue'
import StatusTag from '@/components/StatusTag.vue'
import DictSelect from '@/components/DictSelect.vue'
import {
  getSyncTaskList,
  createSyncTask,
  updateSyncTask,
  deleteSyncTask,
  updateSyncTaskStatus,
  triggerSyncTask,
} from '@/api/sync'
import { formatDateTime } from '@/utils/datetime'
import type { SyncTask, SyncTaskForm } from '@/types/platform'

const loading = ref(false)
const submitting = ref(false)
const list = ref<SyncTask[]>([])
const total = ref(0)

const query = reactive({
  page: 1,
  page_size: 10,
  shop_id: undefined as number | undefined,
  sync_type: undefined as string | undefined,
  status: undefined as number | undefined,
})

async function fetchList() {
  loading.value = true
  try {
    const res = await getSyncTaskList({
      page: query.page,
      page_size: query.page_size,
      shop_id: query.shop_id,
      sync_type: query.sync_type,
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
  query.shop_id = undefined
  query.sync_type = undefined
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
const form = reactive<SyncTaskForm>({
  shop_id: undefined,
  sync_type: '',
  cron_expr: '',
  start_time: '',
  status: 1,
  remark: '',
})

const rules: FormRules = {
  shop_id: [{ required: true, message: '请选择店铺', trigger: 'change' }],
  sync_type: [{ required: true, message: '请选择同步类型', trigger: 'change' }],
  cron_expr: [{ required: true, message: '请输入 Cron 表达式', trigger: 'blur' }],
  start_time: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
}

function resetForm() {
  form.id = undefined
  form.shop_id = undefined
  form.sync_type = ''
  form.cron_expr = ''
  form.start_time = ''
  form.status = 1
  form.remark = ''
}

function openCreate() {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

function openEdit(row: SyncTask) {
  isEdit.value = true
  form.id = row.id
  form.shop_id = row.shop_id
  form.sync_type = row.sync_type
  form.cron_expr = row.cron_expr
  form.start_time = row.start_time
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
        await updateSyncTask(form.id, { ...form })
        ElMessage.success('保存成功')
      } else {
        await createSyncTask({ ...form })
        ElMessage.success('新增成功')
      }
      dialogVisible.value = false
      fetchList()
    } finally {
      submitting.value = false
    }
  })
}

async function handleTrigger(row: SyncTask) {
  try {
    await ElMessageBox.confirm(`确定要立即触发店铺「${row.shop_name}」的同步任务吗？`, '提示', { type: 'warning' })
  } catch {
    return
  }
  await triggerSyncTask(row.id)
  ElMessage.success('已触发同步，请稍后在同步日志中查看结果')
  fetchList()
}

async function handleToggleStatus(row: SyncTask) {
  const next = row.status === 1 ? 0 : 1
  const action = next === 1 ? '启用' : '停用'
  try {
    await ElMessageBox.confirm(`确定要${action}该同步任务吗？`, '提示', { type: 'warning' })
  } catch {
    return
  }
  await updateSyncTaskStatus(row.id, next)
  ElMessage.success(`${action}成功`)
  fetchList()
}

async function handleDelete(row: SyncTask) {
  try {
    await ElMessageBox.confirm('确定要删除该同步任务吗？', '提示', { type: 'warning' })
  } catch {
    return
  }
  await deleteSyncTask(row.id)
  ElMessage.success('删除成功')
  fetchList()
}

onMounted(fetchList)
</script>
