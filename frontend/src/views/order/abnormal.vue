<template>
  <div class="page-container">
    <PageTable :total="total" :page="query.page" :page-size="query.page_size" @change="handlePageChange">
      <template #query>
        <QueryForm :loading="loading" @search="handleSearch" @reset="handleReset">
          <el-form-item label="异常类型">
            <DictSelect v-model="query.abnormal_type" type="abnormalType" width="160px" />
          </el-form-item>
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
        <el-table-column label="异常类型" min-width="200">
          <template #default="{ row }">
            <el-tag
              v-for="t in row.abnormal_types"
              :key="t"
              type="danger"
              effect="light"
              size="small"
              class="mr-6"
            >
              {{ abnormalLabel(t) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="下单时间" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.order_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="90" align="right" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click.stop="handleRowClick(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </PageTable>
  </div>
</template>

<script setup lang="ts">
// 异常订单池：同步异常 / 地址异常 / 金额异常 / 长时间未付未发
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Refresh } from '@element-plus/icons-vue'
import PageTable from '@/components/PageTable.vue'
import QueryForm from '@/components/QueryForm.vue'
import DictSelect from '@/components/DictSelect.vue'
import StatusTag from '@/components/StatusTag.vue'
import AmountText from '@/components/AmountText.vue'
import { getAbnormalOrders } from '@/api/order'
import { formatDateTime } from '@/utils/datetime'
import { ABNORMAL_TYPE_DICT } from '@/store/dict'
import type { AbnormalOrder } from '@/types/order'

const router = useRouter()
const loading = ref(false)
const list = ref<AbnormalOrder[]>([])
const total = ref(0)

const query = reactive({
  page: 1,
  page_size: 10,
  abnormal_type: undefined as string | undefined,
  shop_id: undefined as number | undefined,
  platform_code: undefined as string | undefined,
  keyword: '',
})

function abnormalLabel(code: string) {
  return ABNORMAL_TYPE_DICT.find((o) => o.value === code)?.label ?? code
}

async function fetchList() {
  loading.value = true
  try {
    const res = await getAbnormalOrders({
      page: query.page,
      page_size: query.page_size,
      abnormal_type: query.abnormal_type,
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
  query.abnormal_type = undefined
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

function handleRowClick(row: AbnormalOrder) {
  router.push(`/order/detail/${row.id}`)
}

onMounted(fetchList)
</script>

<style scoped lang="scss">
.mr-6 {
  margin-right: 6px;
}

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
