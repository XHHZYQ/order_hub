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
          <el-form-item label="售后状态">
            <DictSelect v-model="query.status" type="afterSaleStatus" width="140px" />
          </el-form-item>
          <el-form-item label="售后类型">
            <DictSelect v-model="query.type" type="afterSaleType" width="140px" />
          </el-form-item>
          <el-form-item label="申请时间">
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
              placeholder="售后单号 / 订单号 / 买家"
              clearable
              style="width: 210px"
              @keyup.enter="handleSearch"
            />
          </el-form-item>
        </QueryForm>
      </template>

      <template #toolbar>
        <el-button :icon="Refresh" @click="fetchList">刷新</el-button>
        <el-button v-permission="'order:after_sale'" type="primary" :icon="RefreshRight" @click="openSync">
          同步售后
        </el-button>
        <el-button :icon="Warning" @click="openAlerts">超时预警</el-button>
        <el-button :icon="PieChart" @click="openAnalysis">原因分析</el-button>
      </template>

      <el-table v-loading="loading" :data="list" stripe border>
        <el-table-column prop="after_sale_no" label="售后单号" min-width="180" show-overflow-tooltip />
        <el-table-column prop="platform_name" label="平台" min-width="100" />
        <el-table-column prop="shop_name" label="店铺" min-width="140" show-overflow-tooltip />
        <el-table-column prop="order_no" label="订单号" min-width="170" show-overflow-tooltip />
        <el-table-column prop="buyer_account" label="买家" min-width="120" show-overflow-tooltip />
        <el-table-column label="类型" width="100" align="center">
          <template #default="{ row }">
            <StatusTag :value="row.type" scene="afterSaleType" />
          </template>
        </el-table-column>
        <el-table-column prop="reason" label="原因" min-width="130" show-overflow-tooltip />
        <el-table-column label="退款金额" width="120" align="right">
          <template #default="{ row }">
            <AmountText :value="row.refund_amount" />
          </template>
        </el-table-column>
        <el-table-column label="售后状态" width="110" align="center">
          <template #default="{ row }">
            <StatusTag :value="row.status" scene="afterSale" />
          </template>
        </el-table-column>
        <el-table-column label="退款状态" width="110" align="center">
          <template #default="{ row }">
            <StatusTag :value="row.refund_status" scene="refund" />
          </template>
        </el-table-column>
        <el-table-column label="申请时间" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.apply_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="170" align="right" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)">详情</el-button>
            <el-button v-permission="'order:after_sale'" link type="primary" @click="openHandle(row)">
              处理
            </el-button>
            <el-button v-permission="'order:after_sale'" link type="primary" @click="openRefund(row)">
              退款
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </PageTable>

    <!-- 同步售后 -->
    <el-dialog v-model="syncVisible" title="同步售后申请" width="480px" destroy-on-close>
      <el-alert
        class="mb-16"
        type="info"
        :closable="false"
        title="从平台拉取新增售后申请；未指定店铺时同步全部授权店铺"
        show-icon
      />
      <el-form label-width="90px">
        <el-form-item label="店铺">
          <DictSelect v-model="syncShopId" type="shop" width="100%" placeholder="全部店铺" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="syncVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitSync">确定</el-button>
      </template>
    </el-dialog>

    <!-- 售后处理 -->
    <el-dialog v-model="handleVisible" title="售后处理" width="540px" destroy-on-close>
      <el-form label-width="100px">
        <el-form-item label="售后单号">
          <span>{{ currentRow?.after_sale_no }}</span>
        </el-form-item>
        <el-form-item label="处理动作">
          <el-select v-model="handleForm.action" style="width: 100%">
            <el-option v-for="a in ACTIONS" :key="a" :label="a" :value="a" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="handleForm.action === '退货入库'" label="退货入库">
          <el-switch v-model="handleForm.goods_returned" active-text="货已退回并入库" />
        </el-form-item>
        <el-form-item v-if="handleForm.action === '同意'" label="退款金额">
          <el-input-number v-model="handleForm.refund_amount" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="处理说明">
          <el-input v-model="handleForm.content" type="textarea" :rows="3" placeholder="请输入处理说明" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="handleVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitHandle">确定</el-button>
      </template>
    </el-dialog>

    <!-- 退款同步 -->
    <el-dialog v-model="refundVisible" title="退款同步" width="480px" destroy-on-close>
      <el-form label-width="100px">
        <el-form-item label="售后单号">
          <span>{{ currentRow?.after_sale_no }}</span>
        </el-form-item>
        <el-form-item label="退款金额">
          <el-input-number v-model="refundForm.refund_amount" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="退款状态">
          <DictSelect v-model="refundForm.refund_status" type="refundStatus" width="100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="refundForm.remark" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="refundVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitRefund">确定</el-button>
      </template>
    </el-dialog>

    <!-- 详情抽屉 -->
    <el-drawer v-model="detailVisible" title="售后单详情" size="560px">
      <div v-loading="detailLoading">
        <el-descriptions v-if="detail" :column="1" border>
          <el-descriptions-item label="售后单号">{{ detail.after_sale_no }}</el-descriptions-item>
          <el-descriptions-item label="平台售后单号">{{ detail.platform_after_sale_no }}</el-descriptions-item>
          <el-descriptions-item label="店铺 / 平台">
            {{ detail.shop_name }} / {{ detail.platform_name }}
          </el-descriptions-item>
          <el-descriptions-item label="订单号">{{ detail.order_no || '-' }}</el-descriptions-item>
          <el-descriptions-item label="订单实付">
            <AmountText :value="detail.order_pay_amount" />
          </el-descriptions-item>
          <el-descriptions-item label="买家">{{ detail.buyer_account }}</el-descriptions-item>
          <el-descriptions-item label="售后类型">
            <StatusTag :value="detail.type" scene="afterSaleType" />
          </el-descriptions-item>
          <el-descriptions-item label="售后原因">{{ detail.reason || '-' }}</el-descriptions-item>
          <el-descriptions-item label="退款金额">
            <AmountText :value="detail.refund_amount" />
          </el-descriptions-item>
          <el-descriptions-item label="售后状态">
            <StatusTag :value="detail.status" scene="afterSale" />
          </el-descriptions-item>
          <el-descriptions-item label="退款状态">
            <StatusTag :value="detail.refund_status" scene="refund" />
          </el-descriptions-item>
          <el-descriptions-item label="是否退货">{{ detail.goods_returned ? '是' : '否' }}</el-descriptions-item>
          <el-descriptions-item label="申请时间">{{ formatDateTime(detail.apply_time) }}</el-descriptions-item>
          <el-descriptions-item label="处理截止">{{ formatDateTime(detail.handle_deadline) }}</el-descriptions-item>
          <el-descriptions-item label="完成时间">{{ formatDateTime(detail.finish_time) }}</el-descriptions-item>
        </el-descriptions>

        <div class="log-title">处理记录</div>
        <el-timeline v-if="detail?.logs?.length">
          <el-timeline-item
            v-for="l in detail.logs"
            :key="l.id"
            :timestamp="formatDateTime(l.created_at)"
            placement="top"
          >
            <div class="log-item">
              <el-tag size="small" effect="plain">{{ l.action }}</el-tag>
              <span class="log-content">{{ l.content }}</span>
            </div>
            <div class="log-operator">操作人：{{ l.operator || '-' }}</div>
          </el-timeline-item>
        </el-timeline>
        <el-empty v-else description="暂无处理记录" :image-size="80" />
      </div>
    </el-drawer>

    <!-- 超时预警 -->
    <el-drawer v-model="alertsVisible" title="售后超时预警" size="640px" @open="fetchAlerts">
      <el-table v-loading="alertsLoading" :data="alerts" stripe border height="calc(100vh - 180px)">
        <el-table-column prop="after_sale_no" label="售后单号" min-width="170" show-overflow-tooltip />
        <el-table-column prop="shop_name" label="店铺" min-width="130" show-overflow-tooltip />
        <el-table-column label="售后状态" width="110" align="center">
          <template #default="{ row }">
            <StatusTag :value="row.status" scene="afterSale" />
          </template>
        </el-table-column>
        <el-table-column prop="overdue_hours" label="超时(小时)" width="110" align="center" />
        <el-table-column prop="alert_reason" label="预警原因" min-width="200" show-overflow-tooltip />
      </el-table>
    </el-drawer>

    <!-- 原因分析 -->
    <el-dialog v-model="analysisVisible" title="售后原因分析" width="720px" destroy-on-close>
      <div v-loading="analysisLoading">
        <el-row :gutter="16" class="mb-16">
          <el-col :span="8">
            <div class="stat-card">
              <div class="stat-card__label">售后总数</div>
              <div class="stat-card__value">{{ analysis?.total ?? 0 }}</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="stat-card">
              <div class="stat-card__label">退款总额</div>
              <div class="stat-card__value">
                <AmountText :value="analysis?.refund_amount ?? 0" />
              </div>
            </div>
          </el-col>
        </el-row>

        <el-divider content-position="left">按类型</el-divider>
        <el-table :data="analysis?.by_type ?? []" stripe border size="small">
          <el-table-column label="类型" min-width="120">
            <template #default="{ row }">
              <StatusTag :value="row.type" scene="afterSaleType" />
            </template>
          </el-table-column>
          <el-table-column prop="count" label="数量" width="100" align="center" />
          <el-table-column label="退款金额" width="140" align="right">
            <template #default="{ row }"><AmountText :value="row.amount" /></template>
          </el-table-column>
        </el-table>

        <el-divider content-position="left">按原因</el-divider>
        <el-table :data="analysis?.by_reason ?? []" stripe border size="small">
          <el-table-column prop="reason" label="原因" min-width="220" show-overflow-tooltip />
          <el-table-column prop="count" label="数量" width="100" align="center" />
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
// 售后管理：列表 + 同步 + 处理 + 退款 + 详情 + 超时预警 + 原因分析
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, RefreshRight, Warning, PieChart } from '@element-plus/icons-vue'
import PageTable from '@/components/PageTable.vue'
import QueryForm from '@/components/QueryForm.vue'
import DictSelect from '@/components/DictSelect.vue'
import StatusTag from '@/components/StatusTag.vue'
import AmountText from '@/components/AmountText.vue'
import {
  getAfterSaleList,
  syncAfterSales,
  getAfterSaleAlerts,
  getAfterSaleAnalysis,
  getAfterSaleDetail,
  handleAfterSale,
  syncAfterSaleRefund,
} from '@/api/afterSale'
import { formatDateTime } from '@/utils/datetime'
import type {
  AfterSale,
  AfterSaleDetail,
  AfterSaleAlert,
  AfterSaleAnalysis,
  AfterSaleHandleForm,
} from '@/types/afterSale'

const ACTIONS: AfterSaleHandleForm['action'][] = ['同意', '拒绝', '协商', '备注', '退货入库']

const loading = ref(false)
const submitting = ref(false)
const list = ref<AfterSale[]>([])
const total = ref(0)
const timeRange = ref<[string, string] | null>(null)

const query = reactive({
  page: 1,
  page_size: 10,
  shop_id: undefined as number | undefined,
  platform_code: undefined as string | undefined,
  status: undefined as string | undefined,
  type: undefined as string | undefined,
  keyword: '',
})

async function fetchList() {
  loading.value = true
  try {
    const res = await getAfterSaleList({
      page: query.page,
      page_size: query.page_size,
      shop_id: query.shop_id,
      platform_code: query.platform_code,
      status: query.status,
      type: query.type,
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
  query.status = undefined
  query.type = undefined
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

// ---------- 同步 ----------
const syncVisible = ref(false)
const syncShopId = ref<number | undefined>(undefined)

function openSync() {
  syncShopId.value = undefined
  syncVisible.value = true
}

async function submitSync() {
  submitting.value = true
  try {
    const res = await syncAfterSales({ shop_id: syncShopId.value ?? null })
    ElMessage.success(`同步完成，新增 ${res.created} 条售后单`)
    syncVisible.value = false
    fetchList()
  } finally {
    submitting.value = false
  }
}

// ---------- 处理 / 退款 ----------
const currentRow = ref<AfterSale | null>(null)
const handleVisible = ref(false)
const refundVisible = ref(false)
const handleForm = reactive({
  action: '同意' as AfterSaleHandleForm['action'],
  content: '',
  refund_amount: 0,
  goods_returned: true,
})
const refundForm = reactive({
  refund_amount: 0,
  refund_status: 'SUCCESS' as string | undefined,
  remark: '',
})

function openHandle(row: AfterSale) {
  currentRow.value = row
  handleForm.action = '同意'
  handleForm.content = ''
  handleForm.refund_amount = row.refund_amount
  handleForm.goods_returned = true
  handleVisible.value = true
}

async function submitHandle() {
  if (!currentRow.value) return
  submitting.value = true
  try {
    await handleAfterSale(currentRow.value.id, {
      action: handleForm.action,
      content: handleForm.content || null,
      refund_amount: handleForm.action === '同意' ? handleForm.refund_amount : null,
      goods_returned: handleForm.action === '退货入库' ? handleForm.goods_returned : null,
    })
    ElMessage.success('处理成功')
    handleVisible.value = false
    fetchList()
  } finally {
    submitting.value = false
  }
}

function openRefund(row: AfterSale) {
  currentRow.value = row
  refundForm.refund_amount = row.refund_amount
  refundForm.refund_status = 'SUCCESS'
  refundForm.remark = ''
  refundVisible.value = true
}

async function submitRefund() {
  if (!currentRow.value) return
  submitting.value = true
  try {
    await syncAfterSaleRefund(currentRow.value.id, {
      refund_amount: refundForm.refund_amount,
      refund_status: refundForm.refund_status ?? null,
      remark: refundForm.remark || null,
    })
    ElMessage.success('退款同步成功')
    refundVisible.value = false
    fetchList()
  } finally {
    submitting.value = false
  }
}

// ---------- 详情 ----------
const detailVisible = ref(false)
const detailLoading = ref(false)
const detail = ref<AfterSaleDetail | null>(null)

async function openDetail(row: AfterSale) {
  detail.value = null
  detailVisible.value = true
  detailLoading.value = true
  try {
    detail.value = await getAfterSaleDetail(row.id)
  } finally {
    detailLoading.value = false
  }
}

// ---------- 超时预警 ----------
const alertsVisible = ref(false)
const alertsLoading = ref(false)
const alerts = ref<AfterSaleAlert[]>([])

function openAlerts() {
  alertsVisible.value = true
}

async function fetchAlerts() {
  alertsLoading.value = true
  try {
    const res = await getAfterSaleAlerts({ page: 1, page_size: 100 })
    alerts.value = res.list ?? []
  } finally {
    alertsLoading.value = false
  }
}

// ---------- 原因分析 ----------
const analysisVisible = ref(false)
const analysisLoading = ref(false)
const analysis = ref<AfterSaleAnalysis | null>(null)

async function openAnalysis() {
  analysisVisible.value = true
  analysisLoading.value = true
  try {
    analysis.value = await getAfterSaleAnalysis({ shop_id: query.shop_id })
  } finally {
    analysisLoading.value = false
  }
}

onMounted(fetchList)
</script>

<style scoped lang="scss">
.mb-16 {
  margin-bottom: 16px;
}

.log-title {
  font-size: 15px;
  font-weight: 600;
  margin: 20px 0 16px;
  color: var(--color-text-base);
}

.log-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.log-content {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.log-operator {
  margin-top: 4px;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.stat-card {
  padding: 16px;
  border-radius: 8px;
  background: var(--el-color-primary-light-9);

  &__label {
    font-size: 13px;
    color: var(--color-text-secondary);
    margin-bottom: 8px;
  }

  &__value {
    font-size: 22px;
    font-weight: 600;
    color: var(--color-text-base);
  }
}
</style>
