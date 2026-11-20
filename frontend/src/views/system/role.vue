<template>
  <div class="page-container">
    <PageTable :total="total" :page="query.page" :page-size="query.page_size" @change="handlePageChange">
      <template #query>
        <QueryForm :loading="loading" @search="handleSearch" @reset="handleReset">
          <el-form-item label="关键字">
            <el-input
              v-model="query.keyword"
              placeholder="角色编码 / 名称"
              clearable
              style="width: 200px"
              @keyup.enter="handleSearch"
            />
          </el-form-item>
        </QueryForm>
      </template>

      <template #toolbar>
        <el-button v-permission="'role:create'" type="primary" :icon="Plus" @click="openCreate">
          新增角色
        </el-button>
      </template>

      <el-table v-loading="loading" :data="list" stripe border>
        <el-table-column prop="role_code" label="角色编码" min-width="140" />
        <el-table-column prop="role_name" label="角色名称" min-width="150" />
        <el-table-column prop="remark" label="备注" min-width="200" show-overflow-tooltip />
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
            <el-button v-permission="'role:edit'" link type="primary" @click="openEdit(row)">
              编辑
            </el-button>
            <el-button v-permission="'role:permission'" link type="primary" @click="openPermission(row)">
              功能权限
            </el-button>
            <el-button v-permission="'role:data_scope'" link type="primary" @click="openDataScope(row)">
              数据权限
            </el-button>
            <el-button v-permission="'role:delete'" link type="danger" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </PageTable>

    <!-- 新增/编辑角色 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑角色' : '新增角色'" width="480px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="角色编码" prop="role_code">
          <el-input v-model="form.role_code" :disabled="isEdit" placeholder="如 SUPER_ADMIN" />
        </el-form-item>
        <el-form-item label="角色名称" prop="role_name">
          <el-input v-model="form.role_name" placeholder="请输入角色名称" />
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

    <!-- 分配功能权限 -->
    <el-dialog v-model="permDialogVisible" title="分配功能权限" width="520px" destroy-on-close>
      <div class="perm-dialog__head">
        <span>角色：{{ currentRole?.role_name }}</span>
        <el-checkbox v-model="permExpandAll" @change="handleExpandAll">展开/折叠</el-checkbox>
      </div>
      <el-tree
        ref="permTreeRef"
        v-loading="permLoading"
        :data="permTree"
        node-key="id"
        show-checkbox
        :check-strictly="permCheckStrictly"
        :props="{ label: 'perm_name', children: 'children' }"
        :default-expand-all="permExpandAll"
        style="max-height: 420px; overflow: auto"
      />
      <template #footer>
        <el-button @click="permDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSavePermission">确定</el-button>
      </template>
    </el-dialog>

    <!-- 配置数据权限 -->
    <el-dialog v-model="dataDialogVisible" title="配置数据权限（店铺范围）" width="720px" destroy-on-close>
      <el-transfer
        v-model="selectedShopIds"
        :data="shopTransferData"
        :titles="['未授权店铺', '已授权店铺']"
        filterable
        filter-placeholder="搜索店铺"
      />
      <template #footer>
        <el-button @click="dataDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSaveDataScope">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
// 角色管理：列表 + 增改删 + 分配功能权限树 + 配置数据权限店铺范围
import { nextTick, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import PageTable from '@/components/PageTable.vue'
import QueryForm from '@/components/QueryForm.vue'
import StatusTag from '@/components/StatusTag.vue'
import {
  getRoleList,
  createRole,
  updateRole,
  deleteRole,
  getPermissionTree,
  getRolePermissions,
  updateRolePermissions,
  getRoleDataScope,
  updateRoleDataScope,
} from '@/api/role'
import { getShopOptions } from '@/api/shop'
import { useDictStore } from '@/store/dict'
import { formatDateTime } from '@/utils/datetime'
import type { PermissionNode, RoleForm, RoleItem } from '@/types/system'

const loading = ref(false)
const submitting = ref(false)
const list = ref<RoleItem[]>([])
const total = ref(0)

const query = reactive({
  page: 1,
  page_size: 10,
  keyword: '',
})

async function fetchList() {
  loading.value = true
  try {
    const res = await getRoleList({
      page: query.page,
      page_size: query.page_size,
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
  query.keyword = ''
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
const form = reactive<RoleForm>({ role_code: '', role_name: '', remark: '', status: 1 })

const rules: FormRules = {
  role_code: [{ required: true, message: '请输入角色编码', trigger: 'blur' }],
  role_name: [{ required: true, message: '请输入角色名称', trigger: 'blur' }],
}

function resetForm() {
  form.id = undefined
  form.role_code = ''
  form.role_name = ''
  form.remark = ''
  form.status = 1
}

function openCreate() {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

function openEdit(row: RoleItem) {
  isEdit.value = true
  form.id = row.id
  form.role_code = row.role_code
  form.role_name = row.role_name
  form.remark = row.remark
  form.status = row.status
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      if (isEdit.value && form.id) {
        await updateRole(form.id, { ...form })
        ElMessage.success('保存成功')
      } else {
        await createRole({ ...form })
        ElMessage.success('新增成功')
      }
      dialogVisible.value = false
      fetchList()
    } finally {
      submitting.value = false
    }
  })
}

async function handleDelete(row: RoleItem) {
  try {
    await ElMessageBox.confirm(`确定要删除角色「${row.role_name}」吗？`, '提示', { type: 'warning' })
  } catch {
    return
  }
  await deleteRole(row.id)
  ElMessage.success('删除成功')
  fetchList()
}

// ---------- 功能权限 ----------
interface TreeExposed {
  setCheckedKeys: (keys: (string | number)[], leafOnly?: boolean) => void
  getCheckedKeys: (leafOnly?: boolean) => (string | number)[]
  getHalfCheckedKeys: () => (string | number)[]
  store: { nodesMap: Record<string, { expanded: boolean }> }
}

const permDialogVisible = ref(false)
const permLoading = ref(false)
const permTree = ref<PermissionNode[]>([])
const permTreeRef = ref<TreeExposed | null>(null)
const permExpandAll = ref(true)
const permCheckStrictly = ref(false)
const currentRole = ref<RoleItem | null>(null)

async function openPermission(row: RoleItem) {
  currentRole.value = row
  permDialogVisible.value = true
  permLoading.value = true
  try {
    const [tree, perm] = await Promise.all([getPermissionTree(), getRolePermissions(row.id)])
    permTree.value = tree ?? []
    await nextTick()
    // 先以严格模式回填，避免父节点自动级联导致全选
    permCheckStrictly.value = true
    await nextTick()
    permTreeRef.value?.setCheckedKeys(perm?.permission_ids ?? [])
    permCheckStrictly.value = false
  } finally {
    permLoading.value = false
  }
}

function handleExpandAll(val: boolean) {
  const nodes = permTreeRef.value?.store.nodesMap ?? {}
  Object.values(nodes).forEach((node: { expanded: boolean }) => {
    node.expanded = val
  })
}

async function handleSavePermission() {
  if (!currentRole.value || !permTreeRef.value) return
  const checked = permTreeRef.value.getCheckedKeys(false) as number[]
  const halfChecked = permTreeRef.value.getHalfCheckedKeys() as number[]
  submitting.value = true
  try {
    await updateRolePermissions(currentRole.value.id, [...checked, ...halfChecked])
    ElMessage.success('权限已保存')
    permDialogVisible.value = false
  } finally {
    submitting.value = false
  }
}

// ---------- 数据权限 ----------
const dataDialogVisible = ref(false)
const selectedShopIds = ref<number[]>([])
const shopTransferData = ref<{ key: number; label: string }[]>([])
const dictStore = useDictStore()

async function openDataScope(row: RoleItem) {
  currentRole.value = row
  dataDialogVisible.value = true
  const [shops, scope] = await Promise.all([getShopOptions(), getRoleDataScope(row.id)])
  shopTransferData.value = (shops ?? []).map((s) => ({ key: s.id, label: s.shop_name }))
  selectedShopIds.value = scope?.shop_ids ?? []
}

async function handleSaveDataScope() {
  if (!currentRole.value) return
  submitting.value = true
  try {
    await updateRoleDataScope(currentRole.value.id, selectedShopIds.value)
    ElMessage.success('数据权限已保存')
    dataDialogVisible.value = false
    dictStore.shopLoaded = false // 数据权限变化后使店铺缓存失效
  } finally {
    submitting.value = false
  }
}

onMounted(fetchList)
</script>

<style scoped lang="scss">
.perm-dialog__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  color: var(--color-text-secondary);
}
</style>
