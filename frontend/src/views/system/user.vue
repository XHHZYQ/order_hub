<template>
  <div class="page-container">
    <PageTable
      :total="total"
      :page="query.page"
      :page-size="query.page_size"
      @change="handlePageChange"
    >
      <template #query>
        <QueryForm :loading="loading" @search="handleSearch" @reset="handleReset">
          <el-form-item label="关键字">
            <el-input
              v-model="query.keyword"
              placeholder="账号 / 姓名 / 手机号"
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
        <el-button v-permission="'user:create'" type="primary" :icon="Plus" @click="openCreate">
          新增用户
        </el-button>
      </template>

      <el-table v-loading="loading" :data="list" stripe border>
        <el-table-column type="index" label="#" width="60" align="center" />
        <el-table-column prop="username" label="账号" min-width="130" show-overflow-tooltip />
        <el-table-column prop="real_name" label="姓名" min-width="110" show-overflow-tooltip />
        <el-table-column prop="phone" label="手机号" min-width="130" />
        <el-table-column prop="email" label="邮箱" min-width="180" show-overflow-tooltip />
        <el-table-column label="角色" min-width="200">
          <template #default="{ row }">
            <el-tag
              v-for="role in row.roles"
              :key="role.id"
              class="role-tag"
              type="primary"
              effect="light"
            >
              {{ role.role_name }}
            </el-tag>
            <span v-if="!row.roles || row.roles.length === 0" class="text-secondary">-</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <StatusTag :value="row.status" scene="common" />
          </template>
        </el-table-column>
        <el-table-column label="最近登录" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.last_login_time) }}</template>
        </el-table-column>
        <el-table-column label="创建时间" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="200" align="right" fixed="right">
          <template #default="{ row }">
            <el-button v-permission="'user:edit'" link type="primary" @click="openEdit(row)">
              编辑
            </el-button>
            <el-button
              v-permission="'user:status'"
              link
              :type="row.status === 1 ? 'warning' : 'success'"
              @click="handleToggleStatus(row)"
            >
              {{ row.status === 1 ? '停用' : '启用' }}
            </el-button>
            <el-dropdown
              v-permission="'user:edit'"
              trigger="click"
              @command="(cmd: string) => handleMoreCommand(cmd, row)"
            >
              <el-button link type="primary">
                更多<el-icon><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="role">分配角色</el-dropdown-item>
                  <el-dropdown-item command="reset">重置密码</el-dropdown-item>
                  <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>
    </PageTable>

    <!-- 新增/编辑用户 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑用户' : '新增用户'"
      width="520px"
      destroy-on-close
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="账号" prop="username">
          <el-input v-model="form.username" :disabled="isEdit" placeholder="请输入登录账号" />
        </el-form-item>
        <el-form-item label="姓名" prop="real_name">
          <el-input v-model="form.real_name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item v-if="!isEdit" label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="请输入初始密码" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="form.phone" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="角色" prop="role_ids">
          <el-select v-model="form.role_ids" multiple placeholder="请选择角色" style="width: 100%">
            <el-option
              v-for="role in roleOptions"
              :key="role.id"
              :label="role.role_name"
              :value="role.id"
            />
          </el-select>
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

    <!-- 分配角色 -->
    <el-dialog v-model="roleDialogVisible" title="分配角色" width="480px" destroy-on-close>
      <el-form label-width="90px">
        <el-form-item label="用户">
          <span>{{ currentRow?.username }}</span>
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="assignRoleIds" multiple placeholder="请选择角色" style="width: 100%">
            <el-option
              v-for="role in roleOptions"
              :key="role.id"
              :label="role.role_name"
              :value="role.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="roleDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleAssignRoles">确定</el-button>
      </template>
    </el-dialog>

    <!-- 重置密码 -->
    <el-dialog v-model="pwdDialogVisible" title="重置密码" width="440px" destroy-on-close>
      <el-form ref="pwdFormRef" :model="pwdForm" :rules="pwdRules" label-width="90px">
        <el-form-item label="用户">
          <span>{{ currentRow?.username }}</span>
        </el-form-item>
        <el-form-item label="新密码" prop="password">
          <el-input v-model="pwdForm.password" type="password" show-password placeholder="请输入新密码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pwdDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleResetPassword">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
// 用户管理：列表 + 增改删 + 启停 + 重置密码 + 分配角色
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, ArrowDown } from '@element-plus/icons-vue'
import PageTable from '@/components/PageTable.vue'
import QueryForm from '@/components/QueryForm.vue'
import StatusTag from '@/components/StatusTag.vue'
import DictSelect from '@/components/DictSelect.vue'
import {
  getUserList,
  createUser,
  updateUser,
  deleteUser,
  updateUserStatus,
  resetUserPassword,
} from '@/api/user'
import { getRoleList } from '@/api/role'
import { formatDateTime } from '@/utils/datetime'
import type { RoleItem, UserForm, UserItem } from '@/types/system'

const loading = ref(false)
const submitting = ref(false)
const list = ref<UserItem[]>([])
const total = ref(0)
const roleOptions = ref<RoleItem[]>([])

const query = reactive({
  page: 1,
  page_size: 10,
  keyword: '',
  status: undefined as number | undefined,
})

async function fetchList() {
  loading.value = true
  try {
    const res = await getUserList({
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

async function fetchRoles() {
  const res = await getRoleList({ page: 1, page_size: 100 })
  roleOptions.value = res.list ?? []
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
const currentRow = ref<UserItem | null>(null)
const form = reactive<UserForm>({
  username: '',
  real_name: '',
  phone: '',
  email: '',
  status: 1,
  password: '',
  role_ids: [],
})

const rules: FormRules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  real_name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入初始密码', trigger: 'blur' }],
}

function resetForm() {
  form.id = undefined
  form.username = ''
  form.real_name = ''
  form.phone = ''
  form.email = ''
  form.status = 1
  form.password = ''
  form.role_ids = []
}

function openCreate() {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

function openEdit(row: UserItem) {
  isEdit.value = true
  resetForm()
  form.id = row.id
  form.username = row.username
  form.real_name = row.real_name
  form.phone = row.phone
  form.email = row.email
  form.status = row.status
  form.role_ids = (row.roles ?? []).map((r) => r.id)
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      if (isEdit.value && form.id) {
        await updateUser(form.id, { ...form })
        ElMessage.success('保存成功')
      } else {
        await createUser({ ...form })
        ElMessage.success('新增成功')
      }
      dialogVisible.value = false
      fetchList()
    } finally {
      submitting.value = false
    }
  })
}

// ---------- 启停 ----------
async function handleToggleStatus(row: UserItem) {
  const next = row.status === 1 ? 0 : 1
  const action = next === 1 ? '启用' : '停用'
  try {
    await ElMessageBox.confirm(`确定要${action}用户「${row.username}」吗？`, '提示', {
      type: 'warning',
    })
  } catch {
    return
  }
  await updateUserStatus(row.id, next)
  ElMessage.success(`${action}成功`)
  fetchList()
}

// ---------- 更多操作 ----------
function handleMoreCommand(cmd: string, row: UserItem) {
  currentRow.value = row
  if (cmd === 'role') openAssignRole(row)
  else if (cmd === 'reset') pwdDialogVisible.value = true
  else if (cmd === 'delete') handleDelete(row)
}

async function handleDelete(row: UserItem) {
  try {
    await ElMessageBox.confirm(`确定要删除用户「${row.username}」吗？`, '提示', { type: 'warning' })
  } catch {
    return
  }
  await deleteUser(row.id)
  ElMessage.success('删除成功')
  fetchList()
}

// ---------- 分配角色 ----------
const roleDialogVisible = ref(false)
const assignRoleIds = ref<number[]>([])

function openAssignRole(row: UserItem) {
  assignRoleIds.value = (row.roles ?? []).map((r) => r.id)
  roleDialogVisible.value = true
}

async function handleAssignRoles() {
  if (!currentRow.value) return
  submitting.value = true
  try {
    const row = currentRow.value
    await updateUser(row.id, {
      username: row.username,
      real_name: row.real_name,
      phone: row.phone,
      email: row.email,
      status: row.status,
      role_ids: assignRoleIds.value,
    })
    ElMessage.success('分配成功')
    roleDialogVisible.value = false
    fetchList()
  } finally {
    submitting.value = false
  }
}

// ---------- 重置密码 ----------
const pwdDialogVisible = ref(false)
const pwdFormRef = ref<FormInstance>()
const pwdForm = reactive({ password: '' })
const pwdRules: FormRules = {
  password: [{ required: true, message: '请输入新密码', trigger: 'blur' }],
}

async function handleResetPassword() {
  if (!pwdFormRef.value || !currentRow.value) return
  await pwdFormRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      await resetUserPassword(currentRow.value!.id, pwdForm.password)
      ElMessage.success('密码已重置')
      pwdDialogVisible.value = false
      pwdForm.password = ''
    } finally {
      submitting.value = false
    }
  })
}

onMounted(() => {
  fetchList()
  fetchRoles()
})
</script>

<style scoped lang="scss">
.role-tag {
  margin: 2px 4px 2px 0;
}
</style>
