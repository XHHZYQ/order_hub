<template>
  <div class="page-container">
    <PageTable :total="total" :page="query.page" :page-size="query.page_size" @change="handlePageChange">
      <template #query>
        <QueryForm :loading="loading" @search="handleSearch" @reset="handleReset">
          <el-form-item label="关键字">
            <el-input
              v-model="query.keyword"
              placeholder="SPU 编码 / 名称"
              clearable
              style="width: 200px"
              @keyup.enter="handleSearch"
            />
          </el-form-item>
          <el-form-item label="类目">
            <el-input
              v-model="query.category_name"
              placeholder="按类目筛选"
              clearable
              style="width: 160px"
              @keyup.enter="handleSearch"
            />
          </el-form-item>
          <el-form-item label="状态">
            <DictSelect v-model="query.status" type="enableStatus" width="130px" />
          </el-form-item>
        </QueryForm>
      </template>

      <template #toolbar>
        <el-button v-permission="'product:create'" type="primary" :icon="Plus" @click="openCreate">
          新增商品
        </el-button>
      </template>

      <el-table
        v-loading="loading"
        class="clickable-table"
        :data="list"
        stripe
        border
        @row-click="openSkuDrawer"
      >
        <el-table-column type="index" label="#" width="60" align="center" />
        <el-table-column prop="spu_code" label="SPU 编码" min-width="140" show-overflow-tooltip />
        <el-table-column prop="spu_name" label="商品名称" min-width="200" show-overflow-tooltip />
        <el-table-column prop="category_name" label="类目" min-width="120" show-overflow-tooltip />
        <el-table-column prop="brand" label="品牌" min-width="110" show-overflow-tooltip />
        <el-table-column prop="unit" label="单位" width="80" align="center" />
        <el-table-column label="SKU 数量" width="100" align="center">
          <template #default="{ row }">{{ row.sku_count ?? '-' }}</template>
        </el-table-column>
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <StatusTag :value="row.status" scene="common" />
          </template>
        </el-table-column>
        <el-table-column label="创建时间" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="210" align="right" fixed="right">
          <template #default="{ row }">
            <el-button v-permission="'product:edit'" link type="primary" @click.stop="openEdit(row)">
              编辑
            </el-button>
            <el-button link type="primary" @click.stop="openSkuDrawer(row)">SKU</el-button>
            <el-button v-permission="'product:delete'" link type="danger" @click.stop="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </PageTable>

    <!-- 新增/编辑 SPU -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑商品' : '新增商品'" width="560px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="SPU 编码" prop="spu_code">
          <el-input v-model="form.spu_code" :disabled="isEdit" placeholder="如 SPU0001" />
        </el-form-item>
        <el-form-item label="商品名称" prop="spu_name">
          <el-input v-model="form.spu_name" placeholder="请输入商品名称" />
        </el-form-item>
        <el-form-item label="类目">
          <el-input v-model="form.category_name" placeholder="如 服饰 / 数码" />
        </el-form-item>
        <el-form-item label="品牌">
          <el-input v-model="form.brand" placeholder="请输入品牌" />
        </el-form-item>
        <el-form-item label="单位">
          <el-input v-model="form.unit" placeholder="如 件 / 个" />
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

    <!-- SKU 抽屉 -->
    <el-drawer v-model="skuDrawerVisible" :title="`SKU 列表 - ${currentSpu?.spu_name || ''}`" size="62%">
      <div class="drawer-toolbar">
        <div class="drawer-toolbar__info">
          <span class="text-secondary">SPU 编码：{{ currentSpu?.spu_code || '-' }}</span>
          <span class="text-secondary">类目：{{ currentSpu?.category_name || '-' }}</span>
        </div>
        <el-button v-permission="'product:create'" type="primary" :icon="Plus" @click="openSkuCreate">
          新增 SKU
        </el-button>
      </div>

      <el-table v-loading="skuLoading" :data="skus" stripe border height="calc(100vh - 220px)">
        <el-table-column type="index" label="#" width="60" align="center" />
        <el-table-column prop="sku_code" label="SKU 编码" min-width="150" show-overflow-tooltip />
        <el-table-column prop="sku_name" label="SKU 名称" min-width="180" show-overflow-tooltip />
        <el-table-column prop="spec_desc" label="规格" min-width="150" show-overflow-tooltip />
        <el-table-column label="成本价" width="120" align="right">
          <template #default="{ row }"><AmountText :value="row.cost_price" /></template>
        </el-table-column>
        <el-table-column label="售价" width="120" align="right">
          <template #default="{ row }"><AmountText :value="row.sale_price" /></template>
        </el-table-column>
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <StatusTag :value="row.status" scene="common" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" align="right" fixed="right">
          <template #default="{ row }">
            <el-button v-permission="'product:edit'" link type="primary" @click="openSkuEdit(row)">
              编辑
            </el-button>
            <el-button v-permission="'product:delete'" link type="danger" @click="handleSkuDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-drawer>

    <!-- 新增/编辑 SKU -->
    <el-dialog v-model="skuDialogVisible" :title="skuIsEdit ? '编辑 SKU' : '新增 SKU'" width="520px" destroy-on-close>
      <el-form ref="skuFormRef" :model="skuForm" :rules="skuRules" label-width="90px">
        <el-form-item label="SKU 编码" prop="sku_code">
          <el-input v-model="skuForm.sku_code" :disabled="skuIsEdit" placeholder="如 SKU0001001" />
        </el-form-item>
        <el-form-item label="SKU 名称" prop="sku_name">
          <el-input v-model="skuForm.sku_name" placeholder="请输入 SKU 名称" />
        </el-form-item>
        <el-form-item label="规格">
          <el-input v-model="skuForm.spec_desc" placeholder="如 红色 / XL" />
        </el-form-item>
        <el-form-item label="成本价">
          <el-input-number v-model="skuForm.cost_price" :min="0" :precision="2" :step="1" style="width: 100%" />
        </el-form-item>
        <el-form-item label="售价">
          <el-input-number v-model="skuForm.sale_price" :min="0" :precision="2" :step="1" style="width: 100%" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="skuForm.status" :active-value="1" :inactive-value="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="skuDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="skuSubmitting" @click="handleSkuSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
// 本地商品：SPU 增改删 + 抽屉维护 SKU（单击行打开 SKU 抽屉）
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import PageTable from '@/components/PageTable.vue'
import QueryForm from '@/components/QueryForm.vue'
import StatusTag from '@/components/StatusTag.vue'
import DictSelect from '@/components/DictSelect.vue'
import AmountText from '@/components/AmountText.vue'
import {
  getProductList,
  createProduct,
  updateProduct,
  deleteProduct,
  getProductSkus,
  createSku,
  updateSku,
  deleteSku,
} from '@/api/product'
import { formatDateTime } from '@/utils/datetime'
import type { Product, ProductForm, Sku, SkuForm } from '@/types/product'

const loading = ref(false)
const submitting = ref(false)
const list = ref<Product[]>([])
const total = ref(0)

const query = reactive({
  page: 1,
  page_size: 10,
  keyword: '',
  category_name: '',
  status: undefined as number | undefined,
})

async function fetchList() {
  loading.value = true
  try {
    const res = await getProductList({
      page: query.page,
      page_size: query.page_size,
      keyword: query.keyword || undefined,
      category_name: query.category_name || undefined,
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
  query.category_name = ''
  query.status = undefined
  query.page = 1
  fetchList()
}

function handlePageChange(payload: { page: number; pageSize: number }) {
  query.page = payload.page
  query.page_size = payload.pageSize
  fetchList()
}

// ---------- SPU 新增/编辑 ----------
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref<FormInstance>()
const form = reactive<ProductForm>({
  spu_code: '',
  spu_name: '',
  category_name: '',
  brand: '',
  unit: '',
  status: 1,
  remark: '',
})

const rules: FormRules = {
  spu_code: [{ required: true, message: '请输入 SPU 编码', trigger: 'blur' }],
  spu_name: [{ required: true, message: '请输入商品名称', trigger: 'blur' }],
}

function resetForm() {
  form.id = undefined
  form.spu_code = ''
  form.spu_name = ''
  form.category_name = ''
  form.brand = ''
  form.unit = ''
  form.status = 1
  form.remark = ''
}

function openCreate() {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

function openEdit(row: Product) {
  isEdit.value = true
  form.id = row.id
  form.spu_code = row.spu_code
  form.spu_name = row.spu_name
  form.category_name = row.category_name
  form.brand = row.brand
  form.unit = row.unit
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
        await updateProduct(form.id, { ...form })
        ElMessage.success('保存成功')
      } else {
        await createProduct({ ...form })
        ElMessage.success('新增成功')
      }
      dialogVisible.value = false
      fetchList()
    } finally {
      submitting.value = false
    }
  })
}

async function handleDelete(row: Product) {
  try {
    await ElMessageBox.confirm(`确定要删除商品「${row.spu_name}」吗？其下 SKU 将一并失效。`, '提示', {
      type: 'warning',
    })
  } catch {
    return
  }
  await deleteProduct(row.id)
  ElMessage.success('删除成功')
  fetchList()
}

// ---------- SKU 抽屉 ----------
const skuDrawerVisible = ref(false)
const skuLoading = ref(false)
const skus = ref<Sku[]>([])
const currentSpu = ref<Product | null>(null)

async function openSkuDrawer(row: Product) {
  currentSpu.value = row
  skuDrawerVisible.value = true
  await fetchSkus()
}

async function fetchSkus() {
  if (!currentSpu.value) return
  skuLoading.value = true
  try {
    const res = await getProductSkus(currentSpu.value.id)
    skus.value = res ?? []
  } finally {
    skuLoading.value = false
  }
}

const skuDialogVisible = ref(false)
const skuIsEdit = ref(false)
const skuSubmitting = ref(false)
const skuFormRef = ref<FormInstance>()
const skuForm = reactive<SkuForm>({
  sku_code: '',
  sku_name: '',
  spec_desc: '',
  cost_price: 0,
  sale_price: 0,
  status: 1,
})

const skuRules: FormRules = {
  sku_code: [{ required: true, message: '请输入 SKU 编码', trigger: 'blur' }],
  sku_name: [{ required: true, message: '请输入 SKU 名称', trigger: 'blur' }],
}

function resetSkuForm() {
  skuForm.id = undefined
  skuForm.sku_code = ''
  skuForm.sku_name = ''
  skuForm.spec_desc = ''
  skuForm.cost_price = 0
  skuForm.sale_price = 0
  skuForm.status = 1
}

function openSkuCreate() {
  skuIsEdit.value = false
  resetSkuForm()
  skuDialogVisible.value = true
}

function openSkuEdit(row: Sku) {
  skuIsEdit.value = true
  skuForm.id = row.id
  skuForm.sku_code = row.sku_code
  skuForm.sku_name = row.sku_name
  skuForm.spec_desc = row.spec_desc
  skuForm.cost_price = row.cost_price
  skuForm.sale_price = row.sale_price
  skuForm.status = row.status
  skuDialogVisible.value = true
}

async function handleSkuSubmit() {
  if (!skuFormRef.value || !currentSpu.value) return
  await skuFormRef.value.validate(async (valid) => {
    if (!valid) return
    skuSubmitting.value = true
    try {
      if (skuIsEdit.value && skuForm.id) {
        await updateSku(skuForm.id, { ...skuForm })
        ElMessage.success('保存成功')
      } else {
        await createSku(currentSpu.value!.id, { ...skuForm })
        ElMessage.success('新增成功')
      }
      skuDialogVisible.value = false
      fetchSkus()
      fetchList()
    } finally {
      skuSubmitting.value = false
    }
  })
}

async function handleSkuDelete(row: Sku) {
  try {
    await ElMessageBox.confirm(`确定要删除 SKU「${row.sku_name}」吗？`, '提示', { type: 'warning' })
  } catch {
    return
  }
  await deleteSku(row.id)
  ElMessage.success('删除成功')
  fetchSkus()
  fetchList()
}

onMounted(fetchList)
</script>

<style scoped lang="scss">
.drawer-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;

  &__info {
    display: flex;
    align-items: center;
    gap: 20px;
  }
}

/* 可点击行：鼠标悬浮手型 + 高亮，提示该行可查看 SKU */
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
