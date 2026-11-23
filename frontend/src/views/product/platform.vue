<template>
  <div class="page-container">
    <PageTable :total="total" :page="query.page" :page-size="query.page_size" @change="handlePageChange">
      <template #query>
        <QueryForm :loading="loading" @search="handleSearch" @reset="handleReset">
          <el-form-item label="店铺">
            <DictSelect v-model="query.shop_id" type="shop" width="180px" />
          </el-form-item>
          <el-form-item label="平台">
            <DictSelect v-model="query.platform_code" type="platform" width="160px" />
          </el-form-item>
          <el-form-item label="关键字">
            <el-input
              v-model="query.keyword"
              placeholder="平台商品 ID / 标题"
              clearable
              style="width: 200px"
              @keyup.enter="handleSearch"
            />
          </el-form-item>
          <el-form-item label="匹配状态">
            <DictSelect v-model="query.is_matched" type="matchStatus" width="140px" />
          </el-form-item>
        </QueryForm>
      </template>

      <el-table
        v-loading="loading"
        class="clickable-table"
        :data="list"
        stripe
        border
        @row-click="openDetail"
      >
        <el-table-column type="index" label="#" width="60" align="center" />
        <el-table-column prop="platform_product_id" label="平台商品 ID" min-width="160" show-overflow-tooltip />
        <el-table-column prop="product_title" label="商品标题" min-width="220" show-overflow-tooltip />
        <el-table-column prop="shop_name" label="店铺" min-width="150" show-overflow-tooltip />
        <el-table-column prop="platform_name" label="平台" min-width="110" />
        <el-table-column prop="category_name" label="平台类目" min-width="120" show-overflow-tooltip />
        <el-table-column label="规格数" width="90" align="center">
          <template #default="{ row }">{{ row.sku_count ?? '-' }}</template>
        </el-table-column>
        <el-table-column label="已映射" width="90" align="center">
          <template #default="{ row }">
            <span :class="{ 'text-warning': row.matched_count !== row.sku_count }">
              {{ row.matched_count ?? 0 }} / {{ row.sku_count ?? 0 }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="同步时间" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.sync_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="90" align="right" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click.stop="openDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </PageTable>

    <!-- 平台商品详情 -->
    <el-drawer v-model="detailVisible" title="平台商品详情" size="62%">
      <div v-loading="detailLoading">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="平台商品 ID">{{ detail?.platform_product_id || '-' }}</el-descriptions-item>
          <el-descriptions-item label="商品标题">{{ detail?.product_title || '-' }}</el-descriptions-item>
          <el-descriptions-item label="店铺">{{ detail?.shop_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="平台">{{ detail?.platform_name || detail?.platform_code || '-' }}</el-descriptions-item>
          <el-descriptions-item label="平台类目">{{ detail?.category_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="平台状态">{{ detail?.status || '-' }}</el-descriptions-item>
          <el-descriptions-item label="同步时间">{{ formatDateTime(detail?.sync_time) }}</el-descriptions-item>
        </el-descriptions>

        <div class="section-title">平台规格（平台 SKU）</div>
        <el-table :data="detailSkus" stripe border>
          <el-table-column type="index" label="#" width="60" align="center" />
          <el-table-column prop="platform_sku_id" label="平台规格 ID" min-width="150" show-overflow-tooltip />
          <el-table-column prop="sku_name" label="规格名称" min-width="180" show-overflow-tooltip />
          <el-table-column prop="spec_desc" label="规格描述" min-width="140" show-overflow-tooltip />
          <el-table-column prop="outer_sku_code" label="商家编码" min-width="130" show-overflow-tooltip />
          <el-table-column label="平台售价" width="120" align="right">
            <template #default="{ row }"><AmountText :value="row.price" /></template>
          </el-table-column>
          <el-table-column prop="platform_stock" label="平台库存" width="100" align="center" />
          <el-table-column label="是否已映射" width="110" align="center">
            <template #default="{ row }">
              <StatusTag :value="row.is_matched" scene="match" />
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
// 平台商品：按店铺/平台筛选，查看平台商品与其平台规格（含是否已映射）
import { computed, onMounted, reactive, ref } from 'vue'
import PageTable from '@/components/PageTable.vue'
import QueryForm from '@/components/QueryForm.vue'
import DictSelect from '@/components/DictSelect.vue'
import StatusTag from '@/components/StatusTag.vue'
import AmountText from '@/components/AmountText.vue'
import { getPlatformProductList, getPlatformProductDetail } from '@/api/product'
import { formatDateTime } from '@/utils/datetime'
import type { PlatformProduct } from '@/types/product'

const loading = ref(false)
const list = ref<PlatformProduct[]>([])
const total = ref(0)

const query = reactive({
  page: 1,
  page_size: 10,
  shop_id: undefined as number | undefined,
  platform_code: undefined as string | undefined,
  keyword: '',
  is_matched: undefined as number | undefined,
})

async function fetchList() {
  loading.value = true
  try {
    const res = await getPlatformProductList({
      page: query.page,
      page_size: query.page_size,
      shop_id: query.shop_id,
      platform_code: query.platform_code,
      keyword: query.keyword || undefined,
      is_matched: query.is_matched,
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
  query.is_matched = undefined
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
const detail = ref<PlatformProduct | null>(null)
const detailSkus = computed(() => detail.value?.skus ?? [])

async function openDetail(row: PlatformProduct) {
  detailVisible.value = true
  detailLoading.value = true
  detail.value = null
  try {
    const res = await getPlatformProductDetail(row.id)
    detail.value = res ?? null
  } finally {
    detailLoading.value = false
  }
}

onMounted(fetchList)
</script>

<style scoped lang="scss">
.section-title {
  margin: 20px 0 12px;
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-base);
}

/* 可点击行：鼠标悬浮手型 + 高亮，提示该行可查看详情 */
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
