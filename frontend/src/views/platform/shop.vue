<template>
  <div class="page-container">
    <PageTable :total="total" :page="query.page" :page-size="query.page_size" @change="handlePageChange">
      <template #query>
        <QueryForm :loading="loading" @search="handleSearch" @reset="handleReset">
          <el-form-item label="平台">
            <DictSelect v-model="query.platform_code" type="platform" width="160px" />
          </el-form-item>
          <el-form-item label="关键字">
            <el-input
              v-model="query.keyword"
              placeholder="店铺名称 / 编码"
              clearable
              style="width: 180px"
              @keyup.enter="handleSearch"
            />
          </el-form-item>
          <el-form-item label="授权状态">
            <DictSelect v-model="query.auth_status" type="authStatus" width="130px" />
          </el-form-item>
          <el-form-item label="状态">
            <DictSelect v-model="query.status" type="enableStatus" width="130px" />
          </el-form-item>
        </QueryForm>
      </template>

      <template #toolbar>
        <el-button v-permission="'shop:create'" type="primary" :icon="Plus" @click="openCreate">
          新增店铺
        </el-button>
      </template>

      <el-table v-loading="loading" :data="list" stripe border>
        <el-table-column type="index" label="#" width="60" align="center" />
        <el-table-column prop="shop_name" label="店铺名称" min-width="170" show-overflow-tooltip />
        <el-table-column prop="platform_name" label="所属平台" min-width="130" />
        <el-table-column prop="shop_code" label="店铺编码" min-width="130" show-overflow-tooltip />
        <el-table-column prop="seller_account" label="卖家账号" min-width="140" show-overflow-tooltip />
        <el-table-column prop="contact_name" label="联系人" min-width="100" />
        <el-table-column prop="contact_phone" label="联系电话" min-width="130" />
        <el-table-column label="授权状态" width="100" align="center">
          <template #default="{ row }">
            <StatusTag :value="row.auth_status" scene="auth" />
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <StatusTag :value="row.status" scene="common" />
          </template>
        </el-table-column>
        <el-table-column label="创建时间" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="260" align="right" fixed="right">
          <template #default="{ row }">
            <el-button v-permission="'shop:edit'" link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button v-permission="'shop:authorize'" link type="primary" @click="handleAuthorize(row)">
              授权
            </el-button>
            <el-button
              v-permission="'shop:status'"
              link
              :type="row.status === 1 ? 'warning' : 'success'"
              @click="handleToggleStatus(row)"
            >
              {{ row.status === 1 ? '停用' : '启用' }}
            </el-button>
            <el-button v-permission="'shop:delete'" link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </PageTable>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑店铺' : '新增店铺'" width="560px" destroy-on-close>
      <el-alert
        v-if="!isEdit"
        class="mb-16"
        type="info"
        :closable="false"
        title="新增店铺后将自动进行模拟授权（生成访问凭证）"
        show-icon
      />
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="所属平台" prop="platform_code">
          <DictSelect v-model="form.platform_code" type="platform" :disabled="isEdit" width="100%" />
        </el-form-item>
        <el-form-item label="店铺名称" prop="shop_name">
          <el-input v-model="form.shop_name" placeholder="请输入店铺名称" />
        </el-form-item>
        <el-form-item label="店铺编码" prop="shop_code">
          <el-input v-model="form.shop_code" :disabled="isEdit" placeholder="请输入店铺编码" />
        </el-form-item>
        <el-form-item label="卖家账号" prop="seller_account">
          <el-input v-model="form.seller_account" placeholder="请输入卖家账号" />
        </el-form-item>
        <el-form-item label="联系人">
          <el-input v-model="form.contact_name" placeholder="请输入联系人" />
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input v-model="form.contact_phone" placeholder="请输入联系电话" />
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
// 店铺管理：列表/筛选/新增（含模拟授权）/编辑/启停/重新授权
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import PageTable from '@/components/PageTable.vue'
import QueryForm from '@/components/QueryForm.vue'
import StatusTag from '@/components/StatusTag.vue'
import DictSelect from '@/components/DictSelect.vue'
import {
  getShopList,
  createShop,
  updateShop,
  deleteShop,
  updateShopStatus,
  authorizeShop,
} from '@/api/shop'
import { useDictStore } from '@/store/dict'
import { formatDateTime } from '@/utils/datetime'
import type { Shop, ShopForm } from '@/types/platform'

const loading = ref(false)
const submitting = ref(false)
const list = ref<Shop[]>([])
const total = ref(0)
const dictStore = useDictStore()

const query = reactive({
  page: 1,
  page_size: 10,
  platform_code: undefined as string | undefined,
  keyword: '',
  auth_status: undefined as number | undefined,
  status: undefined as number | undefined,
})

async function fetchList() {
  loading.value = true
  try {
    const res = await getShopList({
      page: query.page,
      page_size: query.page_size,
      platform_code: query.platform_code,
      keyword: query.keyword || undefined,
      auth_status: query.auth_status,
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
  query.platform_code = undefined
  query.keyword = ''
  query.auth_status = undefined
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
const form = reactive<ShopForm>({
  platform_code: '',
  shop_code: '',
  shop_name: '',
  seller_account: '',
  contact_name: '',
  contact_phone: '',
  status: 1,
  remark: '',
})

const rules: FormRules = {
  platform_code: [{ required: true, message: '请选择所属平台', trigger: 'change' }],
  shop_name: [{ required: true, message: '请输入店铺名称', trigger: 'blur' }],
  shop_code: [{ required: true, message: '请输入店铺编码', trigger: 'blur' }],
  seller_account: [{ required: true, message: '请输入卖家账号', trigger: 'blur' }],
}

function resetForm() {
  form.id = undefined
  form.platform_code = ''
  form.shop_code = ''
  form.shop_name = ''
  form.seller_account = ''
  form.contact_name = ''
  form.contact_phone = ''
  form.status = 1
  form.remark = ''
}

function openCreate() {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

function openEdit(row: Shop) {
  isEdit.value = true
  form.id = row.id
  form.platform_code = row.platform_code
  form.shop_code = row.shop_code
  form.shop_name = row.shop_name
  form.seller_account = row.seller_account
  form.contact_name = row.contact_name
  form.contact_phone = row.contact_phone
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
        await updateShop(form.id, { ...form })
        ElMessage.success('保存成功')
      } else {
        await createShop({ ...form })
        ElMessage.success('新增成功，已完成模拟授权')
      }
      dialogVisible.value = false
      dictStore.shopLoaded = false
      fetchList()
    } finally {
      submitting.value = false
    }
  })
}

async function handleAuthorize(row: Shop) {
  try {
    await ElMessageBox.confirm(`确定要重新授权店铺「${row.shop_name}」吗？`, '提示', { type: 'warning' })
  } catch {
    return
  }
  await authorizeShop(row.id)
  ElMessage.success('重新授权成功')
  fetchList()
}

async function handleToggleStatus(row: Shop) {
  const next = row.status === 1 ? 0 : 1
  const action = next === 1 ? '启用' : '停用'
  try {
    await ElMessageBox.confirm(`确定要${action}店铺「${row.shop_name}」吗？`, '提示', { type: 'warning' })
  } catch {
    return
  }
  await updateShopStatus(row.id, next)
  ElMessage.success(`${action}成功`)
  dictStore.shopLoaded = false
  fetchList()
}

async function handleDelete(row: Shop) {
  try {
    await ElMessageBox.confirm(`确定要删除店铺「${row.shop_name}」吗？`, '提示', { type: 'warning' })
  } catch {
    return
  }
  await deleteShop(row.id)
  ElMessage.success('删除成功')
  dictStore.shopLoaded = false
  fetchList()
}

onMounted(fetchList)
</script>

<style scoped lang="scss">
.mb-16 {
  margin-bottom: 16px;
}
</style>
