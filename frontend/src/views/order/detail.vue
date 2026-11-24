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

    <!-- 订单处理操作栏 -->
    <div class="glass-card detail-actions">
      <el-button v-permission="'order:audit'" type="primary" :icon="Select" @click="openAudit('PASS')">
        审核通过
      </el-button>
      <el-button v-permission="'order:audit'" type="danger" plain :icon="CloseBold" @click="openAudit('REJECT')">
        审核驳回
      </el-button>
      <el-button v-permission="'order:price'" :icon="Money" @click="openPrice">改价</el-button>
      <el-button v-permission="'order:address'" :icon="Location" @click="openAddress">改址</el-button>
      <el-button :icon="PriceTag" @click="openRemark">备注打标</el-button>
      <el-button :icon="Operation" @click="openStatus">状态流转</el-button>
      <el-button :icon="Connection" @click="openMerge">合并</el-button>
      <el-button v-permission="'order:list'" :icon="Scissor" @click="openSplit">拆分</el-button>
      <el-button :icon="RefreshRight" @click="fetchData">刷新</el-button>
    </div>

    <div v-loading="loading" class="glass-card detail-body">
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
            <el-descriptions-item label="标签" :span="3">
              <el-tag
                v-for="t in tagList"
                :key="t"
                type="primary"
                effect="light"
                size="small"
                class="mr-6"
              >
                {{ t }}
              </el-tag>
              <span v-if="!tagList.length">-</span>
            </el-descriptions-item>
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

        <!-- 关联售后 -->
        <el-tab-pane name="after-sale">
          <template #label>关联售后（{{ afterSales.length }}）</template>
          <el-table :data="afterSales" stripe border>
            <el-table-column prop="after_sale_no" label="售后单号" min-width="180" show-overflow-tooltip />
            <el-table-column label="类型" width="110" align="center">
              <template #default="{ row }">
                <StatusTag :value="row.type" scene="afterSaleType" />
              </template>
            </el-table-column>
            <el-table-column prop="reason" label="原因" min-width="150" show-overflow-tooltip />
            <el-table-column label="退款金额" width="120" align="right">
              <template #default="{ row }"><AmountText :value="row.refund_amount" /></template>
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
          </el-table>
          <el-empty v-if="!afterSales.length" description="暂无关联售后单" :image-size="80" />
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
            <el-table-column prop="change_type" label="变更类型" width="110" />
            <el-table-column label="变更字段" width="140">
              <template #default="{ row }">{{ FIELD_LABELS[row.field_name] || row.field_name }}</template>
            </el-table-column>
            <el-table-column prop="before_value" label="变更前" min-width="160" show-overflow-tooltip />
            <el-table-column prop="after_value" label="变更后" min-width="160" show-overflow-tooltip />
            <el-table-column prop="reason" label="变更原因" min-width="150" show-overflow-tooltip />
            <el-table-column prop="operator" label="操作人" width="120" />
            <el-table-column label="变更时间" min-width="170">
              <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 审核 -->
    <el-dialog v-model="auditVisible" :title="auditForm.action === 'PASS' ? '审核通过' : '审核驳回'" width="480px">
      <el-form label-width="90px">
        <el-form-item label="订单号"><span>{{ detail?.order_no }}</span></el-form-item>
        <el-form-item label="审核说明">
          <el-input v-model="auditForm.reason" type="textarea" :rows="3" placeholder="请输入审核说明" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="auditVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitAudit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 改价 -->
    <el-dialog v-model="priceVisible" title="订单改价" width="520px">
      <el-form label-width="100px">
        <el-form-item label="商品金额">
          <el-input-number v-model="priceForm.goods_amount" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="优惠金额">
          <el-input-number v-model="priceForm.discount_amount" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="运费">
          <el-input-number v-model="priceForm.freight_amount" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="实付金额">
          <el-input-number v-model="priceForm.pay_amount" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="改价原因">
          <el-input v-model="priceForm.reason" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="priceVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitPrice">确定</el-button>
      </template>
    </el-dialog>

    <!-- 改址 -->
    <el-dialog v-model="addressVisible" title="修改收货地址" width="520px">
      <el-form label-width="100px">
        <el-form-item label="收件人">
          <el-input v-model="addressForm.receiver_name" />
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input v-model="addressForm.receiver_phone" />
        </el-form-item>
        <el-form-item label="省份">
          <el-input v-model="addressForm.receiver_province" />
        </el-form-item>
        <el-form-item label="城市">
          <el-input v-model="addressForm.receiver_city" />
        </el-form-item>
        <el-form-item label="区县">
          <el-input v-model="addressForm.receiver_district" />
        </el-form-item>
        <el-form-item label="详细地址">
          <el-input v-model="addressForm.receiver_address" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="修改原因">
          <el-input v-model="addressForm.reason" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addressVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitAddress">确定</el-button>
      </template>
    </el-dialog>

    <!-- 备注打标 -->
    <el-dialog v-model="remarkVisible" title="备注与打标" width="520px">
      <el-form label-width="100px">
        <el-form-item label="商家备注">
          <el-input v-model="remarkForm.merchant_remark" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="追加备注">
          <el-switch v-model="remarkForm.append" />
          <span class="ml-8 text-secondary">开启后在原备注后追加</span>
        </el-form-item>
        <el-form-item label="买家备注">
          <el-input v-model="remarkForm.buyer_remark" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="标签">
          <el-select
            v-model="remarkForm.tags"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="输入后回车新增标签"
            style="width: 100%"
          >
            <el-option v-for="t in tagList" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="remarkVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitRemark">确定</el-button>
      </template>
    </el-dialog>

    <!-- 状态流转 -->
    <el-dialog v-model="statusVisible" title="订单状态流转" width="480px">
      <el-form label-width="100px">
        <el-form-item label="当前状态">
          <StatusTag v-if="detail" :value="detail.status" scene="order" />
        </el-form-item>
        <el-form-item label="目标状态">
          <el-select v-model="statusForm.to_status" placeholder="请选择目标状态" style="width: 100%">
            <el-option
              v-for="o in statusOptions"
              :key="o.status"
              :label="o.status_name"
              :value="o.status"
            />
          </el-select>
          <div v-if="!statusOptions.length" class="text-secondary mt-8">
            当前状态无允许流转的下一状态（可能已处于终态）
          </div>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="statusForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="statusVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="submitting"
          :disabled="!statusForm.to_status"
          @click="submitStatus"
        >
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 合并 -->
    <el-dialog v-model="mergeVisible" title="订单合并" width="520px">
      <el-alert
        class="mb-16"
        type="info"
        :closable="false"
        title="将当前订单与其他订单合并为一个合并组（需买家/收件人一致），请输入需合并的订单 ID（英文逗号分隔）"
        show-icon
      />
      <el-form label-width="100px">
        <el-form-item label="当前订单">
          <span>{{ detail?.order_no }}（ID: {{ detail?.id }}）</span>
        </el-form-item>
        <el-form-item label="合并订单ID">
          <el-input v-model="mergeIds" placeholder="如：12,13,14" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="mergeRemark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="mergeVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitMerge">确定合并</el-button>
      </template>
    </el-dialog>

    <!-- 拆分 -->
    <el-dialog v-model="splitVisible" title="订单拆分" width="720px">
      <el-alert
        class="mb-16"
        type="info"
        :closable="false"
        title="将订单商品按数量拆分为多个子单；各子单数量之和不得超过商品数量"
        show-icon
      />
      <el-table :data="items" stripe border size="small" class="mb-16">
        <el-table-column prop="product_name" label="商品" min-width="160" show-overflow-tooltip />
        <el-table-column prop="spec_desc" label="规格" min-width="120" show-overflow-tooltip />
        <el-table-column prop="quantity" label="可拆数量" width="100" align="center" />
      </el-table>

      <div v-for="(part, pi) in splitParts" :key="pi" class="split-part">
        <div class="split-part__head">
          <span>子单 {{ pi + 1 }}</span>
          <el-button
            v-if="splitParts.length > 2"
            link
            type="danger"
            :icon="Delete"
            @click="splitParts.splice(pi, 1)"
          >
            删除
          </el-button>
        </div>
        <div v-for="(line, li) in part.items" :key="li" class="split-line">
          <el-select v-model="line.item_id" placeholder="选择商品" style="flex: 1">
            <el-option
              v-for="it in items"
              :key="it.id"
              :label="`${it.product_name}（剩余可拆 ${it.quantity}）`"
              :value="it.id as number"
            />
          </el-select>
          <el-input-number v-model="line.quantity" :min="1" :max="maxQty(line.item_id)" style="width: 130px" />
          <el-button link type="danger" :icon="Delete" @click="part.items.splice(li, 1)" />
        </div>
        <el-button link type="primary" :icon="Plus" @click="part.items.push({ item_id: 0, quantity: 1 })">
          添加明细
        </el-button>
      </div>
      <el-button class="mt-8" :icon="Plus" @click="splitParts.push({ items: [{ item_id: 0, quantity: 1 }] })">
        添加子单
      </el-button>

      <el-form label-width="80px" class="mt-16">
        <el-form-item label="备注">
          <el-input v-model="splitRemark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="splitVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitSplit">确定拆分</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
// 订单详情：主信息 + 商品明细 + 收货信息 + 关联售后 + 平台扩展 + 操作日志与变更记录
// 并支持 M3 订单处理：审核 / 改价 / 改址 / 备注打标 / 状态流转 / 合并 / 拆分
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft,
  Select,
  CloseBold,
  Money,
  Location,
  PriceTag,
  Operation,
  Connection,
  Scissor,
  RefreshRight,
  Delete,
  Plus,
} from '@element-plus/icons-vue'
import StatusTag from '@/components/StatusTag.vue'
import AmountText from '@/components/AmountText.vue'
import {
  getOrderDetail,
  getOrderItems,
  getOrderExt,
  getOrderLogs,
  getOrderAfterSales,
  auditOrder,
  changeOrderPrice,
  changeOrderAddress,
  addOrderRemark,
  changeOrderStatus,
  getOrderStatusOptions,
  mergeOrders,
  splitOrder,
} from '@/api/order'
import { formatDateTime } from '@/utils/datetime'
import type {
  Order,
  OrderItem,
  OrderExt,
  OrderLogResult,
  StatusOption,
  OrderAuditForm,
  OrderSplitPart,
} from '@/types/order'
import type { AfterSale } from '@/types/afterSale'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const submitting = ref(false)
const activeTab = ref('info')
const orderId = computed(() => Number(route.params.id))

const detail = ref<Order | null>(null)
const items = ref<OrderItem[]>([])
const ext = ref<OrderExt[]>([])
const logs = ref<OrderLogResult>({ logs: [], changes: [] })
const afterSales = ref<AfterSale[]>([])

// 变更字段中文名（仅前端展示映射，数据库字段名保持与《数据库设计》一致）
const FIELD_LABELS: Record<string, string> = {
  status: '订单状态',
  platform_status: '平台原始状态',
  goods_amount: '商品金额',
  discount_amount: '优惠金额',
  freight_amount: '运费',
  pay_amount: '实付金额',
  receiver_name: '收件人',
  receiver_phone: '收件人电话',
  receiver_province: '省份',
  receiver_city: '城市',
  receiver_district: '区县',
  receiver_address: '详细地址',
  buyer_account: '买家账号',
  buyer_nick: '买家昵称',
  merchant_remark: '商家备注',
  buyer_remark: '买家备注',
  tags: '订单标签',
}

const regionText = computed(() => {
  const d = detail.value
  if (!d) return '-'
  const text = `${d.receiver_province ?? ''}${d.receiver_city ?? ''}${d.receiver_district ?? ''}`
  return text || '-'
})

const tagList = computed(() =>
  (detail.value?.tags ?? '')
    .split(',')
    .map((t) => t.trim())
    .filter(Boolean),
)

async function fetchData() {
  if (!orderId.value) return
  loading.value = true
  try {
    const [detailRes, itemsRes, extRes, logsRes, asRes] = await Promise.all([
      getOrderDetail(orderId.value),
      getOrderItems(orderId.value),
      getOrderExt(orderId.value),
      getOrderLogs(orderId.value),
      getOrderAfterSales(orderId.value),
    ])
    detail.value = detailRes ?? null
    items.value = itemsRes ?? []
    ext.value = extRes ?? []
    logs.value = { logs: logsRes?.logs ?? [], changes: logsRes?.changes ?? [] }
    afterSales.value = asRes ?? []
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.push('/order/list')
}

// ---------- 审核 ----------
const auditVisible = ref(false)
const auditForm = reactive<OrderAuditForm>({ action: 'PASS', reason: '' })

function openAudit(action: 'PASS' | 'REJECT') {
  auditForm.action = action
  auditForm.reason = ''
  auditVisible.value = true
}

async function submitAudit() {
  submitting.value = true
  try {
    await auditOrder(orderId.value, { action: auditForm.action, reason: auditForm.reason || null })
    ElMessage.success('审核完成')
    auditVisible.value = false
    fetchData()
  } finally {
    submitting.value = false
  }
}

// ---------- 改价 ----------
const priceVisible = ref(false)
const priceForm = reactive({
  goods_amount: 0,
  discount_amount: 0,
  freight_amount: 0,
  pay_amount: 0,
  reason: '',
})

function openPrice() {
  priceForm.goods_amount = detail.value?.goods_amount ?? 0
  priceForm.discount_amount = detail.value?.discount_amount ?? 0
  priceForm.freight_amount = detail.value?.freight_amount ?? 0
  priceForm.pay_amount = detail.value?.pay_amount ?? 0
  priceForm.reason = ''
  priceVisible.value = true
}

async function submitPrice() {
  submitting.value = true
  try {
    await changeOrderPrice(orderId.value, { ...priceForm, reason: priceForm.reason || null })
    ElMessage.success('改价成功')
    priceVisible.value = false
    fetchData()
  } finally {
    submitting.value = false
  }
}

// ---------- 改址 ----------
const addressVisible = ref(false)
const addressForm = reactive({
  receiver_name: '',
  receiver_phone: '',
  receiver_province: '',
  receiver_city: '',
  receiver_district: '',
  receiver_address: '',
  reason: '',
})

function openAddress() {
  const d = detail.value
  addressForm.receiver_name = d?.receiver_name ?? ''
  addressForm.receiver_phone = d?.receiver_phone ?? ''
  addressForm.receiver_province = d?.receiver_province ?? ''
  addressForm.receiver_city = d?.receiver_city ?? ''
  addressForm.receiver_district = d?.receiver_district ?? ''
  addressForm.receiver_address = d?.receiver_address ?? ''
  addressForm.reason = ''
  addressVisible.value = true
}

async function submitAddress() {
  submitting.value = true
  try {
    await changeOrderAddress(orderId.value, { ...addressForm, reason: addressForm.reason || null })
    ElMessage.success('改址成功')
    addressVisible.value = false
    fetchData()
  } finally {
    submitting.value = false
  }
}

// ---------- 备注打标 ----------
const remarkVisible = ref(false)
const remarkForm = reactive({
  merchant_remark: '',
  buyer_remark: '',
  tags: [] as string[],
  append: false,
})

function openRemark() {
  remarkForm.merchant_remark = detail.value?.merchant_remark ?? ''
  remarkForm.buyer_remark = detail.value?.buyer_remark ?? ''
  remarkForm.tags = [...tagList.value]
  remarkForm.append = false
  remarkVisible.value = true
}

async function submitRemark() {
  submitting.value = true
  try {
    await addOrderRemark(orderId.value, {
      merchant_remark: remarkForm.merchant_remark || null,
      buyer_remark: remarkForm.buyer_remark || null,
      tags: remarkForm.tags,
      append: remarkForm.append,
    })
    ElMessage.success('保存成功')
    remarkVisible.value = false
    fetchData()
  } finally {
    submitting.value = false
  }
}

// ---------- 状态流转 ----------
const statusVisible = ref(false)
const statusOptions = ref<StatusOption[]>([])
const statusForm = reactive({ to_status: '', remark: '' })

async function openStatus() {
  statusForm.to_status = ''
  statusForm.remark = ''
  statusVisible.value = true
  statusOptions.value = []
  const res = await getOrderStatusOptions(orderId.value)
  statusOptions.value = res.options ?? []
}

async function submitStatus() {
  submitting.value = true
  try {
    await changeOrderStatus(orderId.value, {
      to_status: statusForm.to_status,
      remark: statusForm.remark || null,
    })
    ElMessage.success('状态流转成功')
    statusVisible.value = false
    fetchData()
  } finally {
    submitting.value = false
  }
}

// ---------- 合并 ----------
const mergeVisible = ref(false)
const mergeIds = ref('')
const mergeRemark = ref('')

function openMerge() {
  mergeIds.value = ''
  mergeRemark.value = ''
  mergeVisible.value = true
}

async function submitMerge() {
  const ids = mergeIds.value
    .split(',')
    .map((s) => Number(s.trim()))
    .filter((n) => Number.isFinite(n) && n > 0)
  if (!ids.length) {
    ElMessage.warning('请输入至少一个需合并的订单 ID')
    return
  }
  submitting.value = true
  try {
    const res = await mergeOrders({
      order_ids: [orderId.value, ...ids],
      remark: mergeRemark.value || null,
    })
    ElMessageBox.alert(
      `合并组：${res.merge_group_no}，共 ${res.order_count} 笔订单（${res.order_nos.join('、')}）`,
      '合并成功',
    )
    mergeVisible.value = false
    fetchData()
  } finally {
    submitting.value = false
  }
}

// ---------- 拆分 ----------
const splitVisible = ref(false)
const splitRemark = ref('')
const splitParts = ref<OrderSplitPart[]>([
  { items: [{ item_id: 0, quantity: 1 }] },
  { items: [{ item_id: 0, quantity: 1 }] },
])

function maxQty(itemId: number) {
  return items.value.find((it) => it.id === itemId)?.quantity ?? 1
}

function openSplit() {
  splitParts.value = [
    { items: [{ item_id: 0, quantity: 1 }] },
    { items: [{ item_id: 0, quantity: 1 }] },
  ]
  splitRemark.value = ''
  splitVisible.value = true
}

async function submitSplit() {
  const parts = splitParts.value.filter((p) => p.items.some((it) => it.item_id > 0))
  if (parts.length < 2) {
    ElMessage.warning('至少需要 2 个子单，且每个子单需选择商品')
    return
  }
  submitting.value = true
  try {
    const res = await splitOrder(orderId.value, {
      parts: parts.map((p) => ({ items: p.items.filter((it) => it.item_id > 0) })),
      remark: splitRemark.value || null,
    })
    ElMessage.success(`拆分成功，生成 ${res.child_count} 个子单`)
    splitVisible.value = false
    fetchData()
  } finally {
    submitting.value = false
  }
}

onMounted(fetchData)
</script>

<style scoped lang="scss">
.mb-16 {
  margin-bottom: 16px;
}

.mt-8 {
  margin-top: 8px;
}

.mt-16 {
  margin-top: 16px;
}

.ml-8 {
  margin-left: 8px;
}

.mr-6 {
  margin-right: 6px;
}

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

.detail-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: var(--padding-base);
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

.split-part {
  border: 1px solid var(--color-border);
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 12px;

  &__head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8px;
    font-weight: 600;
    color: var(--color-text-base);
  }
}

.split-line {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
</style>
