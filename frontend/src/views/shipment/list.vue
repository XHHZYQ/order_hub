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
          <el-form-item label="物流状态">
            <DictSelect v-model="query.status" type="shipmentStatus" width="140px" />
          </el-form-item>
          <el-form-item label="发货时间">
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
              placeholder="发货单号 / 订单号 / 运单号"
              clearable
              style="width: 210px"
              @keyup.enter="handleSearch"
            />
          </el-form-item>
        </QueryForm>
      </template>

      <el-table v-loading="loading" :data="list" stripe border>
        <el-table-column prop="shipment_no" label="发货单号" min-width="180" show-overflow-tooltip />
        <el-table-column prop="order_no" label="订单号" min-width="180" show-overflow-tooltip />
        <el-table-column prop="shop_name" label="店铺" min-width="140" show-overflow-tooltip />
        <el-table-column prop="logistics_company_name" label="物流公司" min-width="120" />
        <el-table-column prop="waybill_no" label="运单号" min-width="160" show-overflow-tooltip />
        <el-table-column label="发货数量" width="100" align="center">
          <template #default="{ row }">{{ row.ship_qty }}</template>
        </el-table-column>
        <el-table-column label="物流状态" width="110" align="center">
          <template #default="{ row }">
            <StatusTag :value="row.status" scene="shipment" />
          </template>
        </el-table-column>
        <el-table-column label="回写平台" width="110" align="center">
          <template #default="{ row }">
            <StatusTag :value="row.push_status" scene="push" />
          </template>
        </el-table-column>
        <el-table-column label="发货时间" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.shipped_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="180" align="right" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)">详情</el-button>
            <el-button v-permission="'shipment:list'" link type="primary" @click="handleSyncTrace(row)">
              拉取轨迹
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </PageTable>

    <!-- 发货单详情 -->
    <el-drawer v-model="detailVisible" title="发货单详情" size="560px">
      <div v-loading="detailLoading">
        <el-descriptions v-if="detail" :column="1" border>
          <el-descriptions-item label="发货单号">{{ detail.shipment_no }}</el-descriptions-item>
          <el-descriptions-item label="订单号">{{ detail.order_no }}</el-descriptions-item>
          <el-descriptions-item label="店铺 / 平台">
            {{ detail.shop_name }} / {{ detail.platform_name }}
          </el-descriptions-item>
          <el-descriptions-item label="物流公司">{{ detail.logistics_company_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="运单号">{{ detail.waybill_no || '-' }}</el-descriptions-item>
          <el-descriptions-item label="面单号">{{ detail.face_sheet_no || '-' }}</el-descriptions-item>
          <el-descriptions-item label="发货数量">{{ detail.ship_qty }}</el-descriptions-item>
          <el-descriptions-item label="物流状态">
            <StatusTag :value="detail.status" scene="shipment" />
          </el-descriptions-item>
          <el-descriptions-item label="回写平台">
            <StatusTag :value="detail.push_status" scene="push" />
          </el-descriptions-item>
          <el-descriptions-item v-if="detail.push_fail_reason" label="回写失败原因">
            <span class="text-danger">{{ detail.push_fail_reason }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="收件信息">
            {{ detail.receiver_name }} {{ detail.receiver_phone }}
          </el-descriptions-item>
          <el-descriptions-item label="发货时间">{{ formatDateTime(detail.shipped_at) }}</el-descriptions-item>
        </el-descriptions>

        <div class="trace-title">物流轨迹</div>
        <el-timeline v-if="detail?.traces?.length">
          <el-timeline-item
            v-for="t in detail.traces"
            :key="t.id"
            :timestamp="formatDateTime(t.trace_time)"
            placement="top"
          >
            <div class="trace-item">
              <StatusTag :value="t.trace_status" scene="trace" />
              <span class="trace-desc">{{ t.trace_desc }}</span>
            </div>
          </el-timeline-item>
        </el-timeline>
        <el-empty v-else description="暂无轨迹" :image-size="80" />
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
// 发货记录：发货单查询 + 详情（含轨迹）+ 拉取轨迹
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import PageTable from '@/components/PageTable.vue'
import QueryForm from '@/components/QueryForm.vue'
import DictSelect from '@/components/DictSelect.vue'
import StatusTag from '@/components/StatusTag.vue'
import { getShipmentList, getShipmentDetail, syncShipmentTrace } from '@/api/shipment'
import { formatDateTime } from '@/utils/datetime'
import type { Shipment, ShipmentDetail } from '@/types/fulfillment'

const loading = ref(false)
const list = ref<Shipment[]>([])
const total = ref(0)
const timeRange = ref<[string, string] | null>(null)

const query = reactive({
  page: 1,
  page_size: 10,
  shop_id: undefined as number | undefined,
  platform_code: undefined as string | undefined,
  status: undefined as string | undefined,
  keyword: '',
})

async function fetchList() {
  loading.value = true
  try {
    const res = await getShipmentList({
      page: query.page,
      page_size: query.page_size,
      shop_id: query.shop_id,
      platform_code: query.platform_code,
      status: query.status,
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

// ---------- 详情 ----------
const detailVisible = ref(false)
const detailLoading = ref(false)
const detail = ref<ShipmentDetail | null>(null)

async function openDetail(row: Shipment) {
  detail.value = null
  detailVisible.value = true
  detailLoading.value = true
  try {
    detail.value = await getShipmentDetail(row.id)
  } finally {
    detailLoading.value = false
  }
}

async function handleSyncTrace(row: Shipment) {
  const res = await syncShipmentTrace(row.id)
  ElMessage.success(`轨迹已更新，新增 ${res.added} 条`)
  fetchList()
}

onMounted(fetchList)
</script>

<style scoped lang="scss">
.trace-title {
  font-size: 15px;
  font-weight: 600;
  margin: 20px 0 16px;
  color: var(--color-text-base);
}

.trace-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.trace-desc {
  font-size: 13px;
  color: var(--color-text-secondary);
}
</style>
