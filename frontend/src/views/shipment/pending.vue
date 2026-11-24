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
          <el-form-item label="关键字">
            <el-input
              v-model="query.keyword"
              placeholder="订单号 / 买家 / 收件人"
              clearable
              style="width: 200px"
              @keyup.enter="handleSearch"
            />
          </el-form-item>
        </QueryForm>
      </template>

      <template #toolbar>
        <el-button :icon="Refresh" @click="fetchList">刷新</el-button>
        <el-button
          v-permission="'shipment:ship'"
          :icon="Printer"
          :disabled="!selectedIds.length"
          @click="openPrint(selectedIds)"
        >
          批量打单（{{ selectedIds.length }}）
        </el-button>
        <el-button
          v-permission="'shipment:batch_ship'"
          type="primary"
          :icon="Van"
          :disabled="!selectedIds.length"
          @click="openBatchShip"
        >
          批量发货（{{ selectedIds.length }}）
        </el-button>
      </template>

      <el-table
        v-loading="loading"
        :data="list"
        row-key="id"
        stripe
        border
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="46" reserve-selection />
        <el-table-column prop="order_no" label="订单号" min-width="180" show-overflow-tooltip />
        <el-table-column prop="platform_name" label="平台" min-width="110" />
        <el-table-column prop="shop_name" label="店铺" min-width="150" show-overflow-tooltip />
        <el-table-column prop="receiver_name" label="收件人" min-width="100" />
        <el-table-column prop="receiver_city" label="收件城市" min-width="110" />
        <el-table-column label="商品数" width="90" align="center">
          <template #default="{ row }">{{ row.item_count }}</template>
        </el-table-column>
        <el-table-column label="未发数量" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.total_qty > 0 ? 'warning' : 'success'" effect="light">
              {{ row.total_qty }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="下单时间" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.order_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="140" align="right" fixed="right">
          <template #default="{ row }">
            <el-button v-permission="'shipment:ship'" link type="primary" @click="openPrint([row.id])">
              打单
            </el-button>
            <el-button v-permission="'shipment:ship'" link type="primary" @click="openShip(row)">
              发货
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </PageTable>

    <!-- 发货（单笔） -->
    <el-dialog v-model="shipVisible" title="订单发货" width="560px" destroy-on-close>
      <el-form label-width="100px">
        <el-form-item label="订单号">
          <span>{{ currentOrder?.order_no }}</span>
        </el-form-item>
        <el-form-item label="物流公司">
          <el-select v-model="shipForm.logistics_company_code" placeholder="请选择物流公司" style="width: 100%">
            <el-option
              v-for="c in companies"
              :key="c.company_code"
              :label="c.company_name"
              :value="c.company_code"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="物流单号">
          <el-input v-model="shipForm.waybill_no" placeholder="留空则自动生成运单号" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="shipVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitShip">确认发货</el-button>
      </template>
    </el-dialog>

    <!-- 批量发货 -->
    <el-dialog v-model="batchVisible" title="批量发货" width="520px" destroy-on-close>
      <el-alert
        class="mb-16"
        type="info"
        :closable="false"
        :title="`将对已选中的 ${selectedIds.length} 笔订单创建发货单、回传平台并扣减库存`"
        show-icon
      />
      <el-form label-width="100px">
        <el-form-item label="物流公司">
          <el-select v-model="batchForm.logistics_company_code" placeholder="请选择物流公司" style="width: 100%">
            <el-option
              v-for="c in companies"
              :key="c.company_code"
              :label="c.company_name"
              :value="c.company_code"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="batchVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitBatch">确认发货</el-button>
      </template>
    </el-dialog>

    <!-- 电子面单 -->
    <el-dialog v-model="printVisible" title="电子面单" width="820px" destroy-on-close>
      <div id="face-sheet-print">
        <div v-for="s in sheets" :key="s.waybill_no" class="face-sheet">
          <div class="face-sheet__head">
            <span class="face-sheet__company">{{ s.logistics_company_name }}</span>
            <span class="face-sheet__no">{{ s.waybill_no }}</span>
          </div>
          <div class="face-sheet__body">
            <p><span class="label">收件人：</span>{{ s.receiver_name }} {{ s.receiver_phone }}</p>
            <p><span class="label">地址：</span>{{ s.receiver_address }}</p>
            <p><span class="label">订单号：</span>{{ s.order_no }}</p>
            <p><span class="label">面单号：</span>{{ s.face_sheet_no }}</p>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="printVisible = false">关闭</el-button>
        <el-button type="primary" :icon="Printer" @click="doPrint">打印面单</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
// 待发货：列出待发货订单，支持批量打单（电子面单）与单笔/批量发货
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Printer, Van } from '@element-plus/icons-vue'
import PageTable from '@/components/PageTable.vue'
import QueryForm from '@/components/QueryForm.vue'
import DictSelect from '@/components/DictSelect.vue'
import {
  getPendingOrders,
  getLogisticsCompanies,
  getWaybills,
  printShipments,
  createShipment,
  batchShip,
} from '@/api/shipment'
import { formatDateTime } from '@/utils/datetime'
import type {
  PendingOrder,
  LogisticsCompany,
  FaceSheet,
} from '@/types/fulfillment'

const loading = ref(false)
const submitting = ref(false)
const list = ref<PendingOrder[]>([])
const total = ref(0)
const companies = ref<LogisticsCompany[]>([])
const selectedIds = ref<number[]>([])

const query = reactive({
  page: 1,
  page_size: 10,
  shop_id: undefined as number | undefined,
  platform_code: undefined as string | undefined,
  keyword: '',
})

async function fetchList() {
  loading.value = true
  try {
    const res = await getPendingOrders({
      page: query.page,
      page_size: query.page_size,
      shop_id: query.shop_id,
      platform_code: query.platform_code,
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
  query.keyword = ''
  query.page = 1
  fetchList()
}

function handlePageChange(payload: { page: number; pageSize: number }) {
  query.page = payload.page
  query.page_size = payload.pageSize
  fetchList()
}

function handleSelectionChange(rows: PendingOrder[]) {
  selectedIds.value = rows.map((r) => r.id)
}

// ---------- 发货（单笔） ----------
const shipVisible = ref(false)
const currentOrder = ref<PendingOrder | null>(null)
const shipForm = reactive({ logistics_company_code: '', waybill_no: '' })

function openShip(row: PendingOrder) {
  currentOrder.value = row
  shipForm.logistics_company_code = companies.value[0]?.company_code ?? ''
  shipForm.waybill_no = ''
  shipVisible.value = true
}

async function submitShip() {
  if (!currentOrder.value) return
  if (!shipForm.logistics_company_code) {
    ElMessage.warning('请选择物流公司')
    return
  }
  submitting.value = true
  try {
    await createShipment({
      order_id: currentOrder.value.id,
      logistics_company_code: shipForm.logistics_company_code,
      waybill_no: shipForm.waybill_no || null,
    })
    ElMessage.success('发货成功')
    shipVisible.value = false
    fetchList()
  } finally {
    submitting.value = false
  }
}

// ---------- 批量发货 ----------
const batchVisible = ref(false)
const batchForm = reactive({ logistics_company_code: '' })

function openBatchShip() {
  batchForm.logistics_company_code = companies.value[0]?.company_code ?? ''
  batchVisible.value = true
}

async function submitBatch() {
  if (!batchForm.logistics_company_code) {
    ElMessage.warning('请选择物流公司')
    return
  }
  submitting.value = true
  try {
    const res = await batchShip({
      order_ids: selectedIds.value,
      logistics_company_code: batchForm.logistics_company_code,
    })
    ElMessage.success(`发货完成：成功 ${res.success_count} 笔，失败 ${res.fail_count} 笔`)
    batchVisible.value = false
    fetchList()
  } finally {
    submitting.value = false
  }
}

// ---------- 电子面单 ----------
const printVisible = ref(false)
const sheets = ref<FaceSheet[]>([])

async function openPrint(orderIds: number[]) {
  if (!orderIds.length) return
  const companyCode = companies.value[0]?.company_code ?? null
  // 单笔：获取面单并展示；批量：调用批量打单接口
  if (orderIds.length === 1) {
    sheets.value = await getWaybills({ order_id: orderIds[0], logistics_company_code: companyCode })
  } else {
    const res = await printShipments({ order_ids: orderIds, logistics_company_code: companyCode })
    sheets.value = res.sheets ?? []
  }
  if (!sheets.value.length) {
    ElMessage.warning('未获取到面单')
    return
  }
  printVisible.value = true
}

function doPrint() {
  const html = document.getElementById('face-sheet-print')?.innerHTML ?? ''
  const win = window.open('', '_blank', 'width=820,height=900')
  if (!win) {
    ElMessage.warning('打印窗口被浏览器拦截')
    return
  }
  win.document.write(`<html><head><title>电子面单</title></head><body>${html}</body></html>`)
  win.document.close()
  win.focus()
  win.print()
}

onMounted(async () => {
  companies.value = await getLogisticsCompanies()
  fetchList()
})
</script>

<style scoped lang="scss">
.mb-16 {
  margin-bottom: 16px;
}

.face-sheet {
  border: 1px dashed var(--color-border);
  border-radius: 6px;
  padding: 12px 16px;
  margin-bottom: 12px;

  &__head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-weight: 600;
    padding-bottom: 8px;
    margin-bottom: 8px;
    border-bottom: 1px solid var(--color-border);
  }

  &__company {
    font-size: 16px;
  }

  &__no {
    font-family: var(--font-family-mono, monospace);
    letter-spacing: 1px;
  }

  &__body {
    font-size: 13px;
    line-height: 1.9;

    .label {
      color: var(--color-text-secondary);
    }
  }
}
</style>
