<template>
  <div class="page-container">
    <PageTable :total="total" :page="query.page" :page-size="query.page_size" @change="handlePageChange">
      <template #query>
        <QueryForm :loading="loading" @search="handleSearch" @reset="handleReset">
          <el-form-item label="店铺">
            <DictSelect v-model="query.shop_id" type="shop" width="180px" />
          </el-form-item>
          <el-form-item label="平台">
            <DictSelect v-model="query.platform_code" type="platform" width="150px" />
          </el-form-item>
          <el-form-item label="差异类型">
            <DictSelect v-model="query.diff_type" type="diffType" width="140px" />
          </el-form-item>
          <el-form-item label="处理状态">
            <DictSelect v-model="query.handle_status" type="diffHandle" width="130px" />
          </el-form-item>
          <el-form-item label="时间">
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
              placeholder="平台订单号 / 本地订单号"
              clearable
              style="width: 210px"
              @keyup.enter="handleSearch"
            />
          </el-form-item>
        </QueryForm>
      </template>

      <template #toolbar>
        <el-button :icon="Refresh" @click="fetchList">刷新</el-button>
        <el-button :icon="Download" @click="handleExport">导出差异</el-button>
      </template>

      <el-table v-loading="loading" :data="list" stripe border>
        <el-table-column prop="platform_order_no" label="平台订单号" min-width="170" show-overflow-tooltip />
        <el-table-column prop="order_no" label="本地订单号" min-width="170" show-overflow-tooltip>
          <template #default="{ row }">{{ row.order_no || '-' }}</template>
        </el-table-column>
        <el-table-column prop="platform_name" label="平台" width="100" />
        <el-table-column prop="shop_name" label="店铺" min-width="140" show-overflow-tooltip />
        <el-table-column label="差异类型" width="120" align="center">
          <template #default="{ row }">
            <StatusTag :value="row.diff_type" scene="diffType" />
          </template>
        </el-table-column>
        <el-table-column label="本地金额" width="120" align="right">
          <template #default="{ row }"><AmountText :value="row.local_amount" /></template>
        </el-table-column>
        <el-table-column label="账单金额" width="120" align="right">
          <template #default="{ row }"><AmountText :value="row.bill_amount" /></template>
        </el-table-column>
        <el-table-column label="差异金额" width="120" align="right">
          <template #default="{ row }"><AmountText :value="row.diff_amount" /></template>
        </el-table-column>
        <el-table-column label="处理状态" width="110" align="center">
          <template #default="{ row }">
            <StatusTag :value="row.handle_status" scene="diffHandle" />
          </template>
        </el-table-column>
        <el-table-column prop="handle_remark" label="处理备注" min-width="140" show-overflow-tooltip>
          <template #default="{ row }">{{ row.handle_remark || '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="110" align="right" fixed="right">
          <template #default="{ row }">
            <el-button
              v-permission="'finance:difference'"
              link
              type="primary"
              :disabled="row.handle_status === 'HANDLED'"
              @click="openHandle(row)"
            >
              处理
            </el-button>
            <el-button link type="primary" @click="openDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </PageTable>

    <!-- 处理差异 -->
    <el-dialog v-model="handleVisible" title="处理对账差异" width="520px" destroy-on-close>
      <el-form label-width="100px">
        <el-form-item label="平台订单号">
          <span>{{ currentRow?.platform_order_no }}</span>
        </el-form-item>
        <el-form-item label="差异类型">
          <StatusTag v-if="currentRow" :value="currentRow.diff_type" scene="diffType" />
        </el-form-item>
        <el-form-item label="差异金额">
          <AmountText :value="currentRow?.diff_amount ?? 0" />
        </el-form-item>
        <el-form-item label="处理动作">
          <el-select v-model="handleForm.action" placeholder="请选择处理动作" style="width: 100%">
            <el-option v-for="a in ACTIONS" :key="a.value" :label="a.label" :value="a.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="处理备注">
          <el-input v-model="handleForm.handle_remark" type="textarea" :rows="3" placeholder="请输入处理说明" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="handleVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitHandle">确定</el-button>
      </template>
    </el-dialog>

    <!-- 差异详情 -->
    <el-drawer v-model="detailVisible" title="差异详情" size="480px">
      <el-descriptions v-if="currentRow" :column="1" border>
        <el-descriptions-item label="平台订单号">{{ currentRow.platform_order_no }}</el-descriptions-item>
        <el-descriptions-item label="本地订单号">{{ currentRow.order_no || '-' }}</el-descriptions-item>
        <el-descriptions-item label="平台 / 店铺">
          {{ currentRow.platform_name }} / {{ currentRow.shop_name }}
        </el-descriptions-item>
        <el-descriptions-item label="关联账单">{{ currentRow.bill_no || '-' }}</el-descriptions-item>
        <el-descriptions-item label="差异类型">
          <StatusTag :value="currentRow.diff_type" scene="diffType" />
        </el-descriptions-item>
        <el-descriptions-item label="本地金额">
          <AmountText :value="currentRow.local_amount" />
        </el-descriptions-item>
        <el-descriptions-item label="账单金额">
          <AmountText :value="currentRow.bill_amount" />
        </el-descriptions-item>
        <el-descriptions-item label="差异金额">
          <AmountText :value="currentRow.diff_amount" />
        </el-descriptions-item>
        <el-descriptions-item label="处理状态">
          <StatusTag :value="currentRow.handle_status" scene="diffHandle" />
        </el-descriptions-item>
        <el-descriptions-item label="处理备注">{{ currentRow.handle_remark || '-' }}</el-descriptions-item>
        <el-descriptions-item label="操作人">{{ currentRow.operator || '-' }}</el-descriptions-item>
        <el-descriptions-item label="处理时间">{{ formatDateTime(currentRow.handle_time) }}</el-descriptions-item>
      </el-descriptions>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
// 财务对账 - 对账差异：差异列表 + 处理 + 导出 + 详情
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Download } from '@element-plus/icons-vue'
import PageTable from '@/components/PageTable.vue'
import QueryForm from '@/components/QueryForm.vue'
import DictSelect from '@/components/DictSelect.vue'
import StatusTag from '@/components/StatusTag.vue'
import AmountText from '@/components/AmountText.vue'
import { getDifferences, handleDifference, exportReconciliation } from '@/api/bill'
import { formatDateTime } from '@/utils/datetime'
import type { ReconcileDiff } from '@/types/finance'

const ACTIONS = [
  { label: '人工核销', value: '核销' },
  { label: '挂账待查', value: '挂账' },
  { label: '调整账单', value: '调整' },
  { label: '忽略差异', value: '忽略' },
]

const loading = ref(false)
const submitting = ref(false)
const list = ref<ReconcileDiff[]>([])
const total = ref(0)
const timeRange = ref<[string, string] | null>(null)

const query = reactive({
  page: 1,
  page_size: 10,
  shop_id: undefined as number | undefined,
  platform_code: undefined as string | undefined,
  diff_type: undefined as string | undefined,
  handle_status: undefined as string | undefined,
  keyword: '',
})

async function fetchList() {
  loading.value = true
  try {
    const res = await getDifferences({
      page: query.page,
      page_size: query.page_size,
      shop_id: query.shop_id,
      platform_code: query.platform_code,
      diff_type: query.diff_type,
      handle_status: query.handle_status,
      keyword: query.keyword || undefined,
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
  query.diff_type = undefined
  query.handle_status = undefined
  query.keyword = ''
  timeRange.value = null
  query.page = 1
  fetchList()
}

function handlePageChange(payload: { page: number; pageSize: number }) {
  query.page = payload.page
  query.page_size = payload.pageSize
  fetchList()
}

async function handleExport() {
  const blob = await exportReconciliation({
    export_type: 'difference',
    shop_id: query.shop_id,
    platform_code: query.platform_code,
    start_time: timeRange.value?.[0],
    end_time: timeRange.value?.[1],
  })
  const url = URL.createObjectURL(blob as Blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'reconcile-differences.csv'
  link.click()
  URL.revokeObjectURL(url)
}

// ---------- 处理 ----------
const handleVisible = ref(false)
const currentRow = ref<ReconcileDiff | null>(null)
const handleForm = reactive({
  action: '核销' as string | undefined,
  handle_remark: '',
})

function openHandle(row: ReconcileDiff) {
  currentRow.value = row
  handleForm.action = '核销'
  handleForm.handle_remark = ''
  handleVisible.value = true
}

async function submitHandle() {
  if (!currentRow.value) return
  submitting.value = true
  try {
    await handleDifference(currentRow.value.id, {
      action: handleForm.action,
      handle_remark: handleForm.handle_remark || null,
    })
    ElMessage.success('处理成功')
    handleVisible.value = false
    fetchList()
  } finally {
    submitting.value = false
  }
}

// ---------- 详情 ----------
const detailVisible = ref(false)

function openDetail(row: ReconcileDiff) {
  currentRow.value = row
  detailVisible.value = true
}

onMounted(fetchList)
</script>
