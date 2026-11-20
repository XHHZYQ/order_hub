<template>
  <div class="page-container">
    <PageTable :total="total" :page="query.page" :page-size="query.page_size" @change="handlePageChange">
      <template #query>
        <QueryForm :loading="loading" @search="handleSearch" @reset="handleReset">
          <el-form-item label="店铺">
            <DictSelect v-model="query.shop_id" type="shop" width="180px" />
          </el-form-item>
          <el-form-item label="同步类型">
            <DictSelect v-model="query.sync_type" type="syncType" width="130px" />
          </el-form-item>
          <el-form-item label="同步状态">
            <DictSelect v-model="query.status" type="syncStatus" width="130px" />
          </el-form-item>
          <el-form-item label="同步时间">
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
        </QueryForm>
      </template>

      <el-table v-loading="loading" :data="list" stripe border>
        <el-table-column type="index" label="#" width="60" align="center" />
        <el-table-column prop="shop_name" label="店铺" min-width="150" show-overflow-tooltip />
        <el-table-column label="同步类型" width="100" align="center">
          <template #default="{ row }">
            <StatusTag :value="row.sync_type" scene="syncType" />
          </template>
        </el-table-column>
        <el-table-column label="触发方式" width="100" align="center">
          <template #default="{ row }">
            <StatusTag :value="row.trigger_type" scene="trigger" />
          </template>
        </el-table-column>
        <el-table-column label="同步状态" width="110" align="center">
          <template #default="{ row }">
            <StatusTag :value="row.status" scene="syncStatus" />
          </template>
        </el-table-column>
        <el-table-column prop="success_count" label="成功数" width="90" align="center" />
        <el-table-column label="失败数" width="90" align="center">
          <template #default="{ row }">
            <span :class="{ 'text-danger': row.fail_count > 0 }">{{ row.fail_count }}</span>
          </template>
        </el-table-column>
        <el-table-column label="耗时" width="100" align="center">
          <template #default="{ row }">{{ row.cost_ms }} ms</template>
        </el-table-column>
        <el-table-column label="开始时间" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.start_time) }}</template>
        </el-table-column>
        <el-table-column label="结束时间" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.end_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="150" align="right" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)">详情</el-button>
            <el-button
              v-if="row.status === '失败' || row.status === '部分失败'"
              v-permission="'sync:retry'"
              link
              type="warning"
              @click="handleRetry(row)"
            >
              重试
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </PageTable>

    <el-dialog v-model="detailVisible" title="同步日志详情" width="600px" destroy-on-close>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="店铺">{{ detail?.shop_name }}</el-descriptions-item>
        <el-descriptions-item label="同步类型">{{ syncTypeLabel }}</el-descriptions-item>
        <el-descriptions-item label="触发方式">{{ detail?.trigger_type }}</el-descriptions-item>
        <el-descriptions-item label="同步状态">{{ detail?.status }}</el-descriptions-item>
        <el-descriptions-item label="成功数">{{ detail?.success_count }}</el-descriptions-item>
        <el-descriptions-item label="失败数">{{ detail?.fail_count }}</el-descriptions-item>
        <el-descriptions-item label="耗时">{{ detail?.cost_ms }} ms</el-descriptions-item>
        <el-descriptions-item label="开始时间">{{ formatDateTime(detail?.start_time) }}</el-descriptions-item>
        <el-descriptions-item label="结束时间">{{ formatDateTime(detail?.end_time) }}</el-descriptions-item>
        <el-descriptions-item label="记录时间">{{ formatDateTime(detail?.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="失败原因" :span="2">
          <pre class="fail-reason">{{ detail?.fail_reason || '-' }}</pre>
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button
          v-if="detail && (detail.status === '失败' || detail.status === '部分失败')"
          v-permission="'sync:retry'"
          type="warning"
          @click="handleRetry(detail)"
        >
          重试
        </el-button>
        <el-button type="primary" @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
// 同步日志：列表 + 详情 + 按失败日志重试
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageTable from '@/components/PageTable.vue'
import QueryForm from '@/components/QueryForm.vue'
import StatusTag from '@/components/StatusTag.vue'
import DictSelect from '@/components/DictSelect.vue'
import { getSyncLogList, getSyncLogDetail, retrySyncLog } from '@/api/sync'
import { SYNC_TYPE_DICT } from '@/store/dict'
import { formatDateTime } from '@/utils/datetime'
import type { SyncLog } from '@/types/platform'

const loading = ref(false)
const list = ref<SyncLog[]>([])
const total = ref(0)
const timeRange = ref<[string, string] | null>(null)

const query = reactive({
  page: 1,
  page_size: 10,
  shop_id: undefined as number | undefined,
  sync_type: undefined as string | undefined,
  status: undefined as string | undefined,
})

async function fetchList() {
  loading.value = true
  try {
    const res = await getSyncLogList({
      page: query.page,
      page_size: query.page_size,
      shop_id: query.shop_id,
      sync_type: query.sync_type,
      status: query.status,
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
  query.sync_type = undefined
  query.status = undefined
  timeRange.value = null
  query.page = 1
  fetchList()
}

function handlePageChange(payload: { page: number; pageSize: number }) {
  query.page = payload.page
  query.page_size = payload.pageSize
  fetchList()
}

const detailVisible = ref(false)
const detail = ref<SyncLog | null>(null)

const syncTypeLabel = computed(
  () => SYNC_TYPE_DICT.find((d) => d.value === detail.value?.sync_type)?.label ?? detail.value?.sync_type ?? '-',
)

async function openDetail(row: SyncLog) {
  detail.value = row
  detailVisible.value = true
  const full = await getSyncLogDetail(row.id)
  if (full) detail.value = full
}

async function handleRetry(row: SyncLog) {
  try {
    await ElMessageBox.confirm('确定要按该失败日志重新触发一次同步吗？', '提示', { type: 'warning' })
  } catch {
    return
  }
  await retrySyncLog(row.id)
  ElMessage.success('已重新触发，请稍后查看结果')
  detailVisible.value = false
  fetchList()
}

onMounted(fetchList)
</script>

<style scoped lang="scss">
.fail-reason {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
  font-family: inherit;
  color: var(--color-danger);
}
</style>
