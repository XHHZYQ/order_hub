<template>
  <div class="page-container">
    <!-- 页头 -->
    <div class="glass-card detail-header">
      <div class="detail-header__left">
        <el-button :icon="ArrowLeft" @click="goBack">返回</el-button>
        <span class="detail-header__no">{{ detail?.order_no || '-' }}</span>
        <StatusTag v-if="detail" :value="detail.status" scene="order" />
        <el-tag v-if="detail && detail.is_abnormal === 1" type="danger" effect="light" round>异常</el-tag>
      </div>
      <div class="detail-header__right">
        <span class="text-secondary">来源：{{ detail?.source || '-' }}</span>
        <span class="text-secondary">下单时间：{{ formatDateTime(detail?.order_time) }}</span>
      </div>
    </div>

    <div class="glass-card detail-body" v-loading="loading">
      <el-tabs v-model="activeTab">
        <!-- 订单信息 -->
        <el-tab-pane label="订单信息" name="info">
          <el-descriptions :column="3" border>
            <el-descriptions-item label="订单号">{{ detail?.order_no || '-' }}</el-descriptions-item>
            <el-descriptions-item label="平台订单号">{{ detail?.platform_order_no || '-' }}</el-descriptions-item>
            <el-descriptions-item label="所属平台">{{ detail?.platform_name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="店铺">{{ detail?.shop_name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="买家账号">{{ detail?.buyer_account || '-' }}</el-descriptions-item>
            <el-descriptions-item label="来源">{{ detail?.source || '-' }}</el-descriptions-item>
            <el-descriptions-item label="订单状态">
              <StatusTag v-if="detail" :value="detail.status" scene="order" />
            </el-descriptions-item>
            <el-descriptions-item label="平台状态">{{ detail?.platform_status || '-' }}</el-descriptions-item>
            <el-descriptions-item label="下单时间">{{ formatDateTime(detail?.order_time) }}</el-descriptions-item>
            <el-descriptions-item label="付款时间">{{ formatDateTime(detail?.paid_at) }}</el-descriptions-item>
            <el-descriptions-item label="发货时间">{{ formatDateTime(detail?.shipped_at) }}</el-descriptions-item>
            <el-descriptions-item label="最近同步">{{ formatDateTime(detail?.sync_time) }}</el-descriptions-item>
            <el-descriptions-item label="商家备注" :span="3">{{ detail?.merchant_remark || '-' }}</el-descriptions-item>
            <el-descriptions-item label="买家备注" :span="3">{{ detail?.buyer_remark || '-' }}</el-descriptions-item>
            <el-descriptions-item label="标签" :span="3">{{ detail?.tags || '-' }}</el-descriptions-item>
          </el-descriptions>

          <div class="section-title">金额信息</div>
          <el-descriptions :column="4" border>
            <el-descriptions-item label="商品金额">
              <AmountText :value="detail?.goods_amount" />
            </el-descriptions-item>
            <el-descriptions-item label="优惠金额">
              <AmountText :value="detail?.discount_amount" />
            </el-descriptions-item>
            <el-descriptions-item label="运费">
              <AmountText :value="detail?.freight_amount" />
            </el-descriptions-item>
            <el-descriptions-item label="实付金额">
              <AmountText :value="detail?.pay_amount" />
            </el-descriptions-item>
          </el-descriptions>
        </el-tab-pane>

        <!-- 商品明细 -->
        <el-tab-pane label="商品明细" name="items">
          <el-table :data="items" stripe border>
            <el-table-column type="index" label="#" width="60" align="center" />
            <el-table-column prop="product_name" label="商品名称" min-width="180" show-overflow-tooltip />
            <el-table-column prop="platform_sku_name" label="平台SKU名称" min-width="180" show-overflow-tooltip />
            <el-table-column prop="outer_sku_code" label="商家编码" min-width="130" show-overflow-tooltip />
            <el-table-column prop="sku_code" label="本地SKU编码" min-width="130" show-overflow-tooltip />
            <el-table-column prop="spec_desc" label="规格" min-width="140" show-overflow-tooltip />
            <el-table-column label="单价" width="110" align="right">
              <template #default="{ row }"><AmountText :value="row.price" /></template>
            </el-table-column>
            <el-table-column prop="quantity" label="数量" width="80" align="center" />
            <el-table-column label="小计" width="120" align="right">
              <template #default="{ row }"><AmountText :value="row.total_amount" /></template>
            </el-table-column>
            <el-table-column label="明细实付" width="120" align="right">
              <template #default="{ row }"><AmountText :value="row.pay_amount" /></template>
            </el-table-column>
            <el-table-column prop="shipped_quantity" label="已发货" width="90" align="center" />
            <el-table-column prop="refund_quantity" label="已退款" width="90" align="center" />
            <el-table-column label="匹配状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="row.is_matched === 1 ? 'success' : 'warning'" effect="light" round>
                  {{ row.is_matched === 1 ? '已匹配' : '未匹配' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 收货信息 -->
        <el-tab-pane label="收货信息" name="receiver">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="收件人">{{ detail?.receiver_name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="联系电话">{{ detail?.receiver_phone || '-' }}</el-descriptions-item>
            <el-descriptions-item label="省市区" :span="2">{{ regionText }}</el-descriptions-item>
            <el-descriptions-item label="详细地址" :span="2">{{ detail?.receiver_address || '-' }}</el-descriptions-item>
          </el-descriptions>
        </el-tab-pane>

        <!-- 平台扩展信息 -->
        <el-tab-pane label="平台扩展信息" name="ext">
          <el-table :data="ext" stripe border>
            <el-table-column prop="ext_name" label="字段名称" min-width="180" show-overflow-tooltip />
            <el-table-column prop="ext_key" label="字段标识" min-width="180" show-overflow-tooltip />
            <el-table-column prop="ext_value" label="字段值" min-width="240" show-overflow-tooltip />
          </el-table>
        </el-tab-pane>

        <!-- 操作日志与变更记录 -->
        <el-tab-pane label="操作日志与变更记录" name="logs">
          <div class="section-title">操作日志</div>
          <el-table :data="logs.logs" stripe border>
            <el-table-column prop="action" label="动作" width="120" />
            <el-table-column label="状态变更" width="180">
              <template #default="{ row }">
                {{ row.from_status || '-' }} → {{ row.to_status || '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="content" label="操作内容" min-width="220" show-overflow-tooltip />
            <el-table-column prop="operator" label="操作人" width="120" />
            <el-table-column prop="source" label="来源" width="90" />
            <el-table-column label="操作时间" min-width="170">
              <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
            </el-table-column>
          </el-table>

          <div class="section-title">变更记录</div>
          <el-table :data="logs.changes" stripe border>
            <el-table-column prop="field_label" label="变更字段" width="140" />
            <el-table-column prop="old_value" label="变更前" min-width="180" show-overflow-tooltip />
            <el-table-column prop="new_value" label="变更后" min-width="180" show-overflow-tooltip />
            <el-table-column prop="operator" label="操作人" width="120" />
            <el-table-column prop="source" label="来源" width="90" />
            <el-table-column label="变更时间" min-width="170">
              <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
// 订单详情：主信息 + 商品明细 + 收货信息 + 平台扩展 + 操作日志与变更记录
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import StatusTag from '@/components/StatusTag.vue'
import AmountText from '@/components/AmountText.vue'
import { getOrderDetail, getOrderItems, getOrderExt, getOrderLogs } from '@/api/order'
import { formatDateTime } from '@/utils/datetime'
import type { Order, OrderItem, OrderExt, OrderLogResult } from '@/types/order'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const activeTab = ref('info')

const detail = ref<Order | null>(null)
const items = ref<OrderItem[]>([])
const ext = ref<OrderExt[]>([])
const logs = ref<OrderLogResult>({ logs: [], changes: [] })

const regionText = computed(() => {
  const d = detail.value
  if (!d) return '-'
  const text = `${d.receiver_province ?? ''}${d.receiver_city ?? ''}${d.receiver_district ?? ''}`
  return text || '-'
})

async function fetchData() {
  const id = Number(route.params.id)
  if (!id) return
  loading.value = true
  try {
    const [detailRes, itemsRes, extRes, logsRes] = await Promise.all([
      getOrderDetail(id),
      getOrderItems(id),
      getOrderExt(id),
      getOrderLogs(id),
    ])
    detail.value = detailRes ?? null
    items.value = itemsRes ?? []
    ext.value = extRes ?? []
    logs.value = {
      logs: logsRes?.logs ?? [],
      changes: logsRes?.changes ?? [],
    }
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.push('/order/list')
}

onMounted(fetchData)
</script>

<style scoped lang="scss">
.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: var(--padding-base);
  flex-wrap: wrap;

  &__left {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  &__no {
    font-size: 18px;
    font-weight: 600;
    color: var(--color-text-base);
  }

  &__right {
    display: flex;
    align-items: center;
    gap: 20px;
  }
}

.detail-body {
  min-height: 320px;
}

.section-title {
  margin: 20px 0 12px;
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-base);
}
</style>
