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
          <el-form-item label="对账状态">
            <DictSelect v-model="query.reconcile_status" type="billReconcile" width="140px" />
          </el-form-item>
          <el-form-item label="账期">
            <el-date-picker
              v-model="query.bill_period"
              type="month"
              placeholder="选择账期"
              value-format="YYYY-MM"
              style="width: 160px"
            />
          </el-form-item>
          <el-form-item label="关键字">
            <el-input
              v-model="query.keyword"
              placeholder="账单号 / 文件名"
              clearable
              style="width: 200px"
              @keyup.enter="handleSearch"
            />
          </el-form-item>
        </QueryForm>
      </template>

      <template #toolbar>
        <el-button :icon="Refresh" @click="fetchList">刷新</el-button>
        <el-button :icon="Download" @click="openMock">生成模拟账单</el-button>
        <el-button v-permission="'finance:bill'" type="primary" :icon="Upload" @click="openImport">
          导入账单
        </el-button>
      </template>

      <el-table v-loading="loading" :data="list" stripe border>
        <el-table-column prop="bill_no" label="账单号" min-width="180" show-overflow-tooltip />
        <el-table-column prop="platform_name" label="平台" min-width="100" />
        <el-table-column prop="shop_name" label="店铺" min-width="140" show-overflow-tooltip />
        <el-table-column prop="bill_period" label="账期" width="100" align="center" />
        <el-table-column prop="file_name" label="账单文件" min-width="160" show-overflow-tooltip />
        <el-table-column prop="total_count" label="明细数" width="90" align="center" />
        <el-table-column label="账单金额" width="130" align="right">
          <template #default="{ row }"><AmountText :value="row.total_amount" /></template>
        </el-table-column>
        <el-table-column label="对账状态" width="110" align="center">
          <template #default="{ row }">
            <StatusTag :value="row.reconcile_status" scene="billReconcile" />
          </template>
        </el-table-column>
        <el-table-column label="导入时间" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.import_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="200" align="right" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)">明细</el-button>
            <el-button
              v-permission="'finance:bill'"
              link
              type="primary"
              :disabled="row.reconcile_status === 'CLOSED'"
              @click="handleMatch(row)"
            >
              对账
            </el-button>
            <el-button
              v-permission="'finance:bill'"
              link
              type="primary"
              :disabled="row.reconcile_status === 'CLOSED'"
              @click="handleClose(row)"
            >
              封账
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </PageTable>

    <!-- 导入账单 -->
    <el-dialog v-model="importVisible" title="导入平台账单" width="520px" destroy-on-close>
      <el-alert
        class="mb-16"
        type="info"
        :closable="false"
        show-icon
        title="支持 CSV / XLSX 账单文件；也可开启“按本地订单生成模拟账单”用于演示"
      />
      <el-form label-width="100px">
        <el-form-item label="平台" required>
          <DictSelect v-model="importForm.platform_code" type="platform" width="100%" />
        </el-form-item>
        <el-form-item label="店铺" required>
          <DictSelect v-model="importForm.shop_id" type="shop" width="100%" />
        </el-form-item>
        <el-form-item label="账期" required>
          <el-date-picker
            v-model="importForm.bill_period"
            type="month"
            placeholder="选择账期"
            value-format="YYYY-MM"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="生成方式">
          <el-switch v-model="importForm.auto_generate" active-text="按本地订单自动生成" />
        </el-form-item>
        <el-form-item v-if="!importForm.auto_generate" label="账单文件" required>
          <el-upload
            :auto-upload="false"
            :limit="1"
            accept=".csv,.xlsx"
            :on-change="onFileChange"
            :on-remove="onFileRemove"
          >
            <el-button :icon="Upload">选择文件</el-button>
            <template #tip>
              <div class="el-upload__tip">仅支持 .csv / .xlsx</div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="importVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitImport">确定</el-button>
      </template>
    </el-dialog>

    <!-- 生成模拟账单 -->
    <el-dialog v-model="mockVisible" title="生成模拟账单文件" width="480px" destroy-on-close>
      <el-form label-width="100px">
        <el-form-item label="平台" required>
          <DictSelect v-model="mockForm.platform_code" type="platform" width="100%" />
        </el-form-item>
        <el-form-item label="店铺" required>
          <DictSelect v-model="mockForm.shop_id" type="shop" width="100%" />
        </el-form-item>
        <el-form-item label="账期" required>
          <el-date-picker
            v-model="mockForm.bill_period"
            type="month"
            placeholder="选择账期"
            value-format="YYYY-MM"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="文件格式">
          <el-radio-group v-model="mockForm.file_type">
            <el-radio value="csv">CSV</el-radio>
            <el-radio value="xlsx">XLSX</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="mockVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitMock">下载</el-button>
      </template>
    </el-dialog>

    <!-- 账单明细抽屉 -->
    <el-drawer v-model="detailVisible" title="账单明细" size="880px" @open="fetchDetails">
      <el-descriptions v-if="currentBill" :column="3" border class="mb-16">
        <el-descriptions-item label="账单号">{{ currentBill.bill_no }}</el-descriptions-item>
        <el-descriptions-item label="平台 / 店铺">
          {{ currentBill.platform_name }} / {{ currentBill.shop_name }}
        </el-descriptions-item>
        <el-descriptions-item label="账期">{{ currentBill.bill_period }}</el-descriptions-item>
        <el-descriptions-item label="明细数">{{ currentBill.total_count }}</el-descriptions-item>
        <el-descriptions-item label="账单金额">
          <AmountText :value="currentBill.total_amount" />
        </el-descriptions-item>
        <el-descriptions-item label="对账状态">
          <StatusTag :value="currentBill.reconcile_status" scene="billReconcile" />
        </el-descriptions-item>
      </el-descriptions>

      <div class="detail-toolbar">
        <DictSelect
          v-model="detailQuery.match_status"
          type="billMatch"
          width="150px"
          placeholder="匹配状态"
        />
        <el-input
          v-model="detailQuery.keyword"
          placeholder="平台订单号 / 本地订单号"
          clearable
          style="width: 240px"
          @keyup.enter="handleDetailSearch"
        />
        <el-button type="primary" :icon="Search" @click="handleDetailSearch">查询</el-button>
      </div>

      <el-table v-loading="detailLoading" :data="details" stripe border>
        <el-table-column prop="platform_order_no" label="平台订单号" min-width="170" show-overflow-tooltip />
        <el-table-column prop="order_no" label="本地订单号" min-width="170" show-overflow-tooltip>
          <template #default="{ row }">{{ row.order_no || '-' }}</template>
        </el-table-column>
        <el-table-column label="货款" width="110" align="right">
          <template #default="{ row }"><AmountText :value="row.goods_amount" /></template>
        </el-table-column>
        <el-table-column label="佣金" width="110" align="right">
          <template #default="{ row }"><AmountText :value="row.commission_amount" /></template>
        </el-table-column>
        <el-table-column label="补贴" width="110" align="right">
          <template #default="{ row }"><AmountText :value="row.subsidy_amount" /></template>
        </el-table-column>
        <el-table-column label="退款" width="110" align="right">
          <template #default="{ row }"><AmountText :value="row.refund_amount" /></template>
        </el-table-column>
        <el-table-column label="实收" width="120" align="right">
          <template #default="{ row }"><AmountText :value="row.settled_amount" /></template>
        </el-table-column>
        <el-table-column label="匹配状态" width="110" align="center">
          <template #default="{ row }">
            <StatusTag :value="row.match_status" scene="billMatch" />
          </template>
        </el-table-column>
      </el-table>

      <div class="detail-pager">
        <el-pagination
          :current-page="detailQuery.page"
          :page-size="detailQuery.page_size"
          :total="detailTotal"
          layout="total, prev, pager, next"
          background
          @current-change="handleDetailPageChange"
        />
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
// 财务对账 - 账单管理：导入账单 + 明细查看 + 对账/封账 + 生成模拟账单
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type UploadFile } from 'element-plus'
import { Refresh, Upload, Download, Search } from '@element-plus/icons-vue'
import PageTable from '@/components/PageTable.vue'
import QueryForm from '@/components/QueryForm.vue'
import DictSelect from '@/components/DictSelect.vue'
import StatusTag from '@/components/StatusTag.vue'
import AmountText from '@/components/AmountText.vue'
import {
  getBillList,
  getBillDetails,
  importBill,
  matchBill,
  closeBill,
  downloadMockBillFile,
} from '@/api/bill'
import { formatDateTime } from '@/utils/datetime'
import type { Bill, BillDetail } from '@/types/finance'

const loading = ref(false)
const submitting = ref(false)
const list = ref<Bill[]>([])
const total = ref(0)

const query = reactive({
  page: 1,
  page_size: 10,
  shop_id: undefined as number | undefined,
  platform_code: undefined as string | undefined,
  reconcile_status: undefined as string | undefined,
  bill_period: undefined as string | undefined,
  keyword: '',
})

async function fetchList() {
  loading.value = true
  try {
    const res = await getBillList({
      page: query.page,
      page_size: query.page_size,
      shop_id: query.shop_id,
      platform_code: query.platform_code,
      reconcile_status: query.reconcile_status,
      bill_period: query.bill_period,
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
  query.reconcile_status = undefined
  query.bill_period = undefined
  query.keyword = ''
  query.page = 1
  fetchList()
}

function handlePageChange(payload: { page: number; pageSize: number }) {
  query.page = payload.page
  query.page_size = payload.pageSize
  fetchList()
}

// ---------- 导入账单 ----------
const importVisible = ref(false)
const importForm = reactive({
  platform_code: undefined as string | undefined,
  shop_id: undefined as number | undefined,
  bill_period: undefined as string | undefined,
  auto_generate: false,
})
const uploadFile = ref<File | null>(null)

function openImport() {
  importForm.platform_code = undefined
  importForm.shop_id = undefined
  importForm.bill_period = undefined
  importForm.auto_generate = false
  uploadFile.value = null
  importVisible.value = true
}

function onFileChange(file: UploadFile) {
  uploadFile.value = (file.raw as File) ?? null
}

function onFileRemove() {
  uploadFile.value = null
}

async function submitImport() {
  if (!importForm.platform_code || !importForm.shop_id || !importForm.bill_period) {
    ElMessage.warning('请选择平台、店铺与账期')
    return
  }
  if (!importForm.auto_generate && !uploadFile.value) {
    ElMessage.warning('请上传账单文件，或开启“按本地订单自动生成”')
    return
  }
  submitting.value = true
  try {
    const bill = await importBill({
      platform_code: importForm.platform_code,
      shop_id: importForm.shop_id,
      bill_period: importForm.bill_period,
      auto_generate: importForm.auto_generate,
      file: uploadFile.value,
    })
    ElMessage.success(`导入成功，共 ${bill.total_count} 条明细`)
    importVisible.value = false
    fetchList()
  } finally {
    submitting.value = false
  }
}

// ---------- 生成模拟账单 ----------
const mockVisible = ref(false)
const mockForm = reactive({
  platform_code: undefined as string | undefined,
  shop_id: undefined as number | undefined,
  bill_period: undefined as string | undefined,
  file_type: 'csv' as 'csv' | 'xlsx',
})

function openMock() {
  mockForm.platform_code = undefined
  mockForm.shop_id = undefined
  mockForm.bill_period = undefined
  mockForm.file_type = 'csv'
  mockVisible.value = true
}

async function submitMock() {
  if (!mockForm.platform_code || !mockForm.shop_id || !mockForm.bill_period) {
    ElMessage.warning('请选择平台、店铺与账期')
    return
  }
  submitting.value = true
  try {
    const blob = await downloadMockBillFile({
      platform_code: mockForm.platform_code,
      shop_id: mockForm.shop_id,
      bill_period: mockForm.bill_period,
      file_type: mockForm.file_type,
    })
    const url = URL.createObjectURL(blob as Blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `bill-${mockForm.platform_code}-${mockForm.shop_id}-${mockForm.bill_period}.${mockForm.file_type}`
    link.click()
    URL.revokeObjectURL(url)
    mockVisible.value = false
    ElMessage.success('模拟账单已下载')
  } finally {
    submitting.value = false
  }
}

// ---------- 对账 / 封账 ----------
async function handleMatch(row: Bill) {
  await ElMessageBox.confirm(`确定对账单「${row.bill_no}」执行对账匹配吗？`, '对账确认', { type: 'info' })
  const res = await matchBill(row.id)
  ElMessage.success(
    `对账完成：匹配 ${res.matched}，金额不一致 ${res.amount_diff}，未匹配 ${res.unmatched}，账单无单 ${res.bill_missing}`,
  )
  fetchList()
}

async function handleClose(row: Bill) {
  await ElMessageBox.confirm(`封账后不可再对账，确定封账「${row.bill_no}」吗？`, '封账确认', { type: 'warning' })
  await closeBill(row.id)
  ElMessage.success('封账成功')
  fetchList()
}

// ---------- 明细 ----------
const detailVisible = ref(false)
const detailLoading = ref(false)
const details = ref<BillDetail[]>([])
const detailTotal = ref(0)
const currentBill = ref<Bill | null>(null)
const detailQuery = reactive({
  page: 1,
  page_size: 10,
  match_status: undefined as string | undefined,
  keyword: '',
})

function openDetail(row: Bill) {
  currentBill.value = row
  detailQuery.page = 1
  detailQuery.match_status = undefined
  detailQuery.keyword = ''
  detailVisible.value = true
}

async function fetchDetails() {
  if (!currentBill.value) return
  detailLoading.value = true
  try {
    const res = await getBillDetails(currentBill.value.id, {
      page: detailQuery.page,
      page_size: detailQuery.page_size,
      match_status: detailQuery.match_status,
      keyword: detailQuery.keyword || undefined,
    })
    details.value = res.list ?? []
    detailTotal.value = res.total ?? 0
  } finally {
    detailLoading.value = false
  }
}

function handleDetailSearch() {
  detailQuery.page = 1
  fetchDetails()
}

function handleDetailPageChange(page: number) {
  detailQuery.page = page
  fetchDetails()
}

onMounted(fetchList)
</script>

<style scoped lang="scss">
.mb-16 {
  margin-bottom: 16px;
}

.detail-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.detail-pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
