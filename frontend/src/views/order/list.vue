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
          <el-form-item label="订单状态">
            <DictSelect v-model="query.status" type="orderStatus" width="140px" />
          </el-form-item>
          <el-form-item label="下单时间">
            <el-date-picker
              v-model="timeRange"
              type="datetimerange"
              range-separator="至"
              start-placeholder="开始时间"
              end-placeholder="结束时间"
              value-format="YYYY-MM-DD HH:mm:ss"
              style="width: 360px"
            />
          </el-form-item>
          <el-form-item label="关键字">
            <el-input
              v-model="query.keyword"
              placeholder="订单号 / 买家 / 收件人"
              clearable
              style="width: 200px"
              @keyup.enter="handleSearch"
            />
          </el-form-item>
          <el-form-item label="商品名">
            <el-input
              v-model="query.goods_keyword"
              placeholder="按商品名筛选"
              clearable
              style="width: 180px"
              @keyup.enter="handleSearch"
            />
          </el-form-item>
        </QueryForm>
      </template>

      <template #toolbar>
        <el-button v-permission="'order:sync'" type="primary" :icon="Refresh" @click="openSync('sync')">
          手动同步
        </el-button>
        <el-button v-permission="'order:sync'" :icon="DocumentAdd" @click="openSync('supplement')">
          手动补单
        </el-button>
        <el-button v-permission="'order:sync'" :icon="Warning" @click="openErrors">同步异常</el-button>
      </template>

      <el-table
        v-loading="loading"
        class="clickable-table"
        :data="list"
        stripe
        border
        @row-click="handleRowClick"
      >
        <el-table-column prop="order_no" label="订单号" min-width="180" show-overflow-tooltip />
        <el-table-column prop="platform_name" label="平台" min-width="110" />
        <el-table-column prop="shop_name" label="店铺" min-width="150" show-overflow-tooltip />
        <el-table-column prop="buyer_account" label="买家" min-width="130" show-overflow-tooltip />
        <el-table-column prop="receiver_name" label="收件人" min-width="100" />
        <el-table-column label="实付金额" width="130" align="right">
          <template #default="{ row }">
            <AmountText :value="row.pay_amount" />
          </template>
        </el-table-column>
        <el-table-column label="订单状态" width="110" align="center">
          <template #default="{ row }">
            <StatusTag :value="row.status" scene="order" />
          </template>
        </el-table-column>
        <el-table-column label="是否异常" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.is_abnormal === 1" type="danger" effect="light" round>异常</el-tag>
            <span v-else class="text-secondary">-</span>
          </template>
        </el-table-column>
        <el-table-column label="下单时间" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.order_time) }}</template>
        </el-table-column>
      </el-table>
    </PageTable>

    <!-- 手动同步 / 手动补单 -->
    <el-dialog
      v-model="syncVisible"
      :title="syncMode === 'sync' ? '手动同步订单' : '手动补单'"
      width="520px"
      destroy-on-close
    >
      <el-alert
        class="mb-16"
        type="info"
        :closable="false"
        :title="
          syncMode === 'sync'
            ? '按所选店铺与时间范围拉取平台订单，未指定店铺时同步全部授权店铺'
            : '按所选店铺与时间范围补拉缺失订单（补单）'
        "
        show-icon
      />
      <el-form label-width="90px">
        <el-form-item label="店铺">
          <DictSelect v-model="syncForm.shop_id" type="shop" width="100%" placeholder="全部店铺" />
        </el-form-item>
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="syncForm.timeRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="syncVisible = false">取消</el-button>
        <el-button type="primary" :loading="syncing" @click="handleSync">确定</el-button>
      </template>
    </el-dialog>

    <!-- 同步异常抽屉 -->
    <el-drawer v-model="errorsVisible" title="同步异常订单" size="60%" @open="fetchErrors">
      <el-table v-loading="errorsLoading" :data="errors" stripe border height="calc(100vh - 200px)">
        <el-table-column prop="order_no" label="订单号" min-width="170" show-overflow-tooltip />
        <el-table-column prop="shop_name" label="店铺" min-width="130" show-overflow-tooltip />
        <el-table-column prop="platform_name" label="平台" min-width="100" />
        <el-table-column prop="abnormal_reason" label="异常原因" min-width="220" show-overflow-tooltip />
        <el-table-column label="下单时间" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.order_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="150" align="right" fixed="right">
          <template #default="{ row }">
            <el-button v-permission="'order:sync'" link type="primary" @click="handleRetry(row)">重试</el-button>
            <el-button v-permission="'order:sync'" link type="primary" @click="openHandle(row)">处理</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pager">
        <el-pagination
          :current-page="errorQuery.page"
          :page-size="errorQuery.page_size"
          :total="errorTotal"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          background
          @current-change="handleErrorPageChange"
          @size-change="handleErrorSizeChange"
        />
      </div>
    </el-drawer>

    <!-- 人工处理异常 -->
    <el-dialog v-model="handleVisible" title="处理异常订单" width="480px" destroy-on-close>
      <el-form label-width="90px">
        <el-form-item label="订单号">
          <span>{{ currentError?.order_no }}</span>
        </el-form-item>
        <el-form-item label="异常原因">
          <span class="text-danger">{{ currentError?.abnormal_reason || '-' }}</span>
        </el-form-item>
        <el-form-item label="处理备注">
          <el-input v-model="handleNote" type="textarea" :rows="3" placeholder="请输入处理备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="handleVisible = false">取消</el-button>
        <el-button type="primary" :loading="handling" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
// 订单列表：筛选 + 分页 + 手动同步/补单 + 同步异常抽屉（重试/处理），单击行进入详情
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, DocumentAdd, Warning } from '@element-plus/icons-vue'
import PageTable from '@/components/PageTable.vue'
import QueryForm from '@/components/QueryForm.vue'
import StatusTag from '@/components/StatusTag.vue'
import DictSelect from '@/components/DictSelect.vue'
import AmountText from '@/components/AmountText.vue'
import {
  getOrderList,
  getSyncErrors,
  orderSync,
  orderSupplement,
  retrySyncError,
  handleSyncError,
} from '@/api/order'
import { formatDateTime } from '@/utils/datetime'
import type { Order, OrderSyncForm, SyncError } from '@/types/order'

const router = useRouter()
const loading = ref(false)
const list = ref<Order[]>([])
const total = ref(0)
const timeRange = ref<[string, string] | null>(null)

const query = reactive({
  page: 1,
  page_size: 10,
  shop_id: undefined as number | undefined,
  platform_code: undefined as string | undefined,
  status: undefined as string | undefined,
  keyword: '',
  goods_keyword: '',
})

async function fetchList() {
  loading.value = true
  try {
    const res = await getOrderList({
      page: query.page,
      page_size: query.page_size,
      shop_id: query.shop_id,
      platform_code: query.platform_code,
      status: query.status,
      keyword: query.keyword || undefined,
      goods_keyword: query.goods_keyword || undefined,
      start_time: timeRange.value?.[0],
      end_time: timeRange.value?.[1],
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
  query.status = undefined
  query.keyword = ''
  query.goods_keyword = ''
  timeRange.value = null
  query.page = 1
  fetchList()
}

function handlePageChange(payload: { page: number; pageSize: number }) {
  query.page = payload.page
  query.page_size = payload.pageSize
  fetchList()
}

function handleRowClick(row: Order) {
  router.push(`/order/detail/${row.id}`)
}

// ---------- 手动同步 / 手动补单 ----------
const syncVisible = ref(false)
const syncing = ref(false)
const syncMode = ref<'sync' | 'supplement'>('sync')
const syncForm = reactive({
  shop_id: undefined as number | undefined,
  timeRange: null as [string, string] | null,
})

function openSync(mode: 'sync' | 'supplement') {
  syncMode.value = mode
  syncForm.shop_id = undefined
  syncForm.timeRange = null
  syncVisible.value = true
}

async function handleSync() {
  const payload: OrderSyncForm = {
    shop_id: syncForm.shop_id ?? null,
    start_time: syncForm.timeRange?.[0] ?? null,
    end_time: syncForm.timeRange?.[1] ?? null,
  }
  syncing.value = true
  try {
    const res = syncMode.value === 'sync' ? await orderSync(payload) : await orderSupplement(payload)
    ElMessage.success(`同步完成：共 ${res.total} 条，成功 ${res.success_count} 条，失败 ${res.fail_count} 条`)
    syncVisible.value = false
    fetchList()
  } finally {
    syncing.value = false
  }
}

// ---------- 同步异常 ----------
const errorsVisible = ref(false)
const errorsLoading = ref(false)
const errors = ref<SyncError[]>([])
const errorTotal = ref(0)
const errorQuery = reactive({ page: 1, page_size: 10 })

async function fetchErrors() {
  errorsLoading.value = true
  try {
    const res = await getSyncErrors({ page: errorQuery.page, page_size: errorQuery.page_size })
    errors.value = res.list ?? []
    errorTotal.value = res.total ?? 0
  } finally {
    errorsLoading.value = false
  }
}

function openErrors() {
  errorQuery.page = 1
  errorsVisible.value = true
}

function handleErrorPageChange(page: number) {
  errorQuery.page = page
  fetchErrors()
}

function handleErrorSizeChange(pageSize: number) {
  errorQuery.page = 1
  errorQuery.page_size = pageSize
  fetchErrors()
}

async function handleRetry(row: SyncError) {
  try {
    await ElMessageBox.confirm(`确定要重试订单「${row.order_no}」的同步吗？`, '提示', { type: 'warning' })
  } catch {
    return
  }
  const res = await retrySyncError(row.id)
  if (res.success && res.abnormal !== 1) {
    ElMessage.success('重试成功')
  } else {
    ElMessage.warning(`重试后仍异常：${res.abnormal_reason || '未知原因'}`)
  }
  fetchErrors()
  fetchList()
}

const handleVisible = ref(false)
const handling = ref(false)
const handleNote = ref('')
const currentError = ref<SyncError | null>(null)

function openHandle(row: SyncError) {
  currentError.value = row
  handleNote.value = ''
  handleVisible.value = true
}

async function handleSubmit() {
  if (!currentError.value) return
  handling.value = true
  try {
    await handleSyncError(currentError.value.id, handleNote.value || null)
    ElMessage.success('处理成功')
    handleVisible.value = false
    fetchErrors()
    fetchList()
  } finally {
    handling.value = false
  }
}

onMounted(fetchList)
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

/* 可点击行：鼠标悬浮手型 + 高亮，提示该行可进入详情 */
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
