<template>
  <div class="page-container ship-workbench">
    <!-- 左：待发货订单 -->
    <div class="ship-workbench__list glass-card">
      <div class="ship-workbench__head">
        <el-input
          v-model="keyword"
          placeholder="订单号 / 买家 / 收件人"
          clearable
          @keyup.enter="fetchOrders"
        >
          <template #append>
            <el-button :icon="Search" @click="fetchOrders" />
          </template>
        </el-input>
      </div>
      <el-table
        v-loading="loading"
        :data="orders"
        highlight-current-row
        height="calc(100vh - 260px)"
        @current-change="handleCurrentChange"
      >
        <el-table-column prop="order_no" label="订单号" min-width="170" show-overflow-tooltip />
        <el-table-column prop="shop_name" label="店铺" min-width="130" show-overflow-tooltip />
        <el-table-column prop="receiver_name" label="收件人" min-width="90" />
        <el-table-column label="未发数量" width="90" align="center">
          <template #default="{ row }">{{ row.total_qty }}</template>
        </el-table-column>
      </el-table>
      <div class="pager">
        <el-pagination
          :current-page="query.page"
          :page-size="query.page_size"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, prev, pager, next"
          background
          @current-change="handlePageChange"
        />
      </div>
    </div>

    <!-- 右：发货操作 -->
    <div class="ship-workbench__panel glass-card">
      <div class="panel-title">打单发货</div>
      <el-empty v-if="!current" description="请从左侧选择一笔待发货订单" />
      <el-form v-else label-width="100px">
        <el-form-item label="订单号">
          <span>{{ current.order_no }}</span>
        </el-form-item>
        <el-form-item label="收件信息">
          <div class="receiver">
            <div>{{ current.receiver_name }} {{ current.receiver_phone }}</div>
            <div class="text-secondary">
              {{ current.receiver_province }}{{ current.receiver_city }}{{ current.receiver_district
              }}{{ current.receiver_address }}
            </div>
          </div>
        </el-form-item>
        <el-form-item label="物流公司">
          <el-select v-model="form.logistics_company_code" placeholder="请选择" style="width: 100%">
            <el-option
              v-for="c in companies"
              :key="c.company_code"
              :label="c.company_name"
              :value="c.company_code"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="物流单号">
          <el-input v-model="form.waybill_no" placeholder="点击获取面单自动填入" />
        </el-form-item>
        <el-form-item label="面单号">
          <el-input v-model="form.face_sheet_no" placeholder="自动生成" />
        </el-form-item>

        <div v-if="sheet" class="face-sheet">
          <div class="face-sheet__head">
            <span class="face-sheet__company">{{ sheet.logistics_company_name }}</span>
            <span class="face-sheet__no">{{ sheet.waybill_no }}</span>
          </div>
          <div class="face-sheet__body">
            <p><span class="label">收件人：</span>{{ sheet.receiver_name }} {{ sheet.receiver_phone }}</p>
            <p><span class="label">地址：</span>{{ sheet.receiver_address }}</p>
            <p><span class="label">订单号：</span>{{ sheet.order_no }}</p>
          </div>
        </div>

        <div class="panel-actions">
          <el-button v-permission="'shipment:ship'" :icon="Document" @click="handleWaybill">
            获取面单
          </el-button>
          <el-button v-permission="'shipment:ship'" :icon="Printer" :disabled="!sheet" @click="doPrint">
            打印
          </el-button>
          <el-button
            v-permission="'shipment:ship'"
            type="primary"
            :icon="Van"
            :loading="submitting"
            @click="handleShip"
          >
            确认发货
          </el-button>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
// 打单发货台：左侧选单，右侧获取面单、打印、确认发货
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Document, Printer, Van } from '@element-plus/icons-vue'
import {
  getPendingOrders,
  getLogisticsCompanies,
  getWaybills,
  createShipment,
} from '@/api/shipment'
import type { PendingOrder, LogisticsCompany, FaceSheet } from '@/types/fulfillment'

const loading = ref(false)
const submitting = ref(false)
const orders = ref<PendingOrder[]>([])
const total = ref(0)
const keyword = ref('')
const companies = ref<LogisticsCompany[]>([])
const current = ref<PendingOrder | null>(null)
const sheet = ref<FaceSheet | null>(null)

const query = reactive({ page: 1, page_size: 10 })
const form = reactive({ logistics_company_code: '', waybill_no: '', face_sheet_no: '' })

async function fetchOrders() {
  loading.value = true
  try {
    const res = await getPendingOrders({
      page: query.page,
      page_size: query.page_size,
      keyword: keyword.value || undefined,
    })
    orders.value = res.list ?? []
    total.value = res.total ?? 0
  } finally {
    loading.value = false
  }
}

function handlePageChange(page: number) {
  query.page = page
  fetchOrders()
}

function handleCurrentChange(row: PendingOrder | null) {
  current.value = row
  sheet.value = null
  form.logistics_company_code = companies.value[0]?.company_code ?? ''
  form.waybill_no = ''
  form.face_sheet_no = ''
}

async function handleWaybill() {
  if (!current.value) return
  if (!form.logistics_company_code) {
    ElMessage.warning('请选择物流公司')
    return
  }
  const res = await getWaybills({
    order_id: current.value.id,
    logistics_company_code: form.logistics_company_code,
  })
  const first = res?.[0]
  if (!first) {
    ElMessage.warning('未获取到面单')
    return
  }
  sheet.value = first
  form.waybill_no = first.waybill_no
  form.face_sheet_no = first.face_sheet_no
}

async function handleShip() {
  if (!current.value) return
  if (!form.logistics_company_code) {
    ElMessage.warning('请选择物流公司')
    return
  }
  submitting.value = true
  try {
    await createShipment({
      order_id: current.value.id,
      logistics_company_code: form.logistics_company_code,
      waybill_no: form.waybill_no || null,
      face_sheet_no: form.face_sheet_no || null,
    })
    ElMessage.success('发货成功')
    current.value = null
    sheet.value = null
    fetchOrders()
  } finally {
    submitting.value = false
  }
}

function doPrint() {
  if (!sheet.value) return
  const s = sheet.value
  const html = `
    <div style="border:1px dashed #999;padding:16px;border-radius:6px;max-width:420px">
      <div style="display:flex;justify-content:space-between;font-weight:600;border-bottom:1px solid #eee;padding-bottom:8px;margin-bottom:8px">
        <span>${s.logistics_company_name}</span><span>${s.waybill_no}</span>
      </div>
      <p>收件人：${s.receiver_name ?? ''} ${s.receiver_phone ?? ''}</p>
      <p>地址：${s.receiver_address ?? ''}</p>
      <p>订单号：${s.order_no}</p>
      <p>面单号：${s.face_sheet_no}</p>
    </div>`
  const win = window.open('', '_blank', 'width=520,height=640')
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
  fetchOrders()
})
</script>

<style scoped lang="scss">
.ship-workbench {
  display: flex;
  gap: var(--padding-base);
  align-items: flex-start;

  &__list {
    flex: 1 1 58%;
    min-width: 0;
    padding: var(--padding-base);
  }

  &__panel {
    flex: 0 0 380px;
    padding: var(--padding-base);
  }

  &__head {
    margin-bottom: 12px;
  }
}

.panel-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
  color: var(--color-text-base);
}

.receiver {
  line-height: 1.7;
  font-size: 13px;
}

.panel-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}

.face-sheet {
  border: 1px dashed var(--color-border);
  border-radius: 6px;
  padding: 12px 16px;
  margin: 4px 0 16px;
  font-size: 13px;

  &__head {
    display: flex;
    justify-content: space-between;
    font-weight: 600;
    padding-bottom: 8px;
    margin-bottom: 8px;
    border-bottom: 1px solid var(--color-border);
  }

  &__body {
    line-height: 1.9;

    .label {
      color: var(--color-text-secondary);
    }
  }
}
</style>
