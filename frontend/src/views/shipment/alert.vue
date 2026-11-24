<template>
  <div class="page-container">
    <PageTable :total="total" :page="query.page" :page-size="query.page_size" @change="handlePageChange">
      <template #toolbar>
        <el-button :icon="Refresh" @click="fetchList">刷新</el-button>
      </template>

      <template #tips>
        <el-alert
          type="warning"
          :closable="false"
          show-icon
          title="长期无物流更新的发货单（停滞超过 48 小时）会出现在此，可点击「拉取轨迹」刷新最新物流"
        />
      </template>

      <el-table v-loading="loading" :data="list" stripe border>
        <el-table-column prop="shipment_no" label="发货单号" min-width="180" show-overflow-tooltip />
        <el-table-column prop="order_no" label="订单号" min-width="180" show-overflow-tooltip />
        <el-table-column prop="shop_name" label="店铺" min-width="140" show-overflow-tooltip />
        <el-table-column prop="logistics_company_name" label="物流公司" min-width="120" />
        <el-table-column prop="waybill_no" label="运单号" min-width="160" show-overflow-tooltip />
        <el-table-column label="物流状态" width="110" align="center">
          <template #default="{ row }">
            <StatusTag :value="row.status" scene="shipment" />
          </template>
        </el-table-column>
        <el-table-column label="最后轨迹时间" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.last_trace_time) }}</template>
        </el-table-column>
        <el-table-column prop="stale_hours" label="停滞(小时)" width="110" align="center" />
        <el-table-column prop="alert_reason" label="预警原因" min-width="220" show-overflow-tooltip />
        <el-table-column label="操作" width="160" align="right" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleSyncTrace(row)">拉取轨迹</el-button>
          </template>
        </el-table-column>
      </el-table>
    </PageTable>
  </div>
</template>

<script setup lang="ts">
// 物流异常预警：长期无轨迹更新的发货单
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import PageTable from '@/components/PageTable.vue'
import StatusTag from '@/components/StatusTag.vue'
import { getShipmentAlerts, syncShipmentTrace } from '@/api/shipment'
import { formatDateTime } from '@/utils/datetime'
import type { ShipmentAlert } from '@/types/fulfillment'

const loading = ref(false)
const list = ref<ShipmentAlert[]>([])
const total = ref(0)

const query = reactive({ page: 1, page_size: 10 })

async function fetchList() {
  loading.value = true
  try {
    const res = await getShipmentAlerts({ page: query.page, page_size: query.page_size })
    list.value = res.list ?? []
    total.value = res.total ?? 0
  } finally {
    loading.value = false
  }
}

function handlePageChange(payload: { page: number; pageSize: number }) {
  query.page = payload.page
  query.page_size = payload.pageSize
  fetchList()
}

async function handleSyncTrace(row: ShipmentAlert) {
  const res = await syncShipmentTrace(row.id)
  ElMessage.success(`轨迹已更新，新增 ${res.added} 条`)
  fetchList()
}

onMounted(fetchList)
</script>
