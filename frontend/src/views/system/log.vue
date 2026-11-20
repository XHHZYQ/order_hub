<template>
  <div class="page-container">
    <PageTable :total="total" :page="query.page" :page-size="query.page_size" @change="handlePageChange">
      <template #query>
        <QueryForm :loading="loading" @search="handleSearch" @reset="handleReset">
          <el-form-item label="操作人">
            <el-input
              v-model="query.username"
              placeholder="操作人账号"
              clearable
              style="width: 160px"
              @keyup.enter="handleSearch"
            />
          </el-form-item>
          <el-form-item label="模块">
            <el-input
              v-model="query.module"
              placeholder="所属模块"
              clearable
              style="width: 140px"
              @keyup.enter="handleSearch"
            />
          </el-form-item>
          <el-form-item label="操作时间">
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
        <el-table-column prop="username" label="操作人" min-width="120" />
        <el-table-column prop="module" label="模块" min-width="110" />
        <el-table-column prop="action" label="动作" min-width="110" />
        <el-table-column prop="target_type" label="对象类型" min-width="120" />
        <el-table-column prop="target_id" label="对象ID" min-width="110" show-overflow-tooltip />
        <el-table-column prop="content" label="操作内容" min-width="240" show-overflow-tooltip />
        <el-table-column prop="ip" label="IP" min-width="140" />
        <el-table-column label="操作时间" min-width="170">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="90" align="right" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </PageTable>

    <el-dialog v-model="detailVisible" title="操作日志详情" width="560px" destroy-on-close>
      <el-descriptions :column="1" border>
        <el-descriptions-item label="操作人">{{ detail?.username }}</el-descriptions-item>
        <el-descriptions-item label="模块">{{ detail?.module }}</el-descriptions-item>
        <el-descriptions-item label="动作">{{ detail?.action }}</el-descriptions-item>
        <el-descriptions-item label="对象类型">{{ detail?.target_type || '-' }}</el-descriptions-item>
        <el-descriptions-item label="对象ID">{{ detail?.target_id || '-' }}</el-descriptions-item>
        <el-descriptions-item label="操作内容">{{ detail?.content || '-' }}</el-descriptions-item>
        <el-descriptions-item label="IP">{{ detail?.ip || '-' }}</el-descriptions-item>
        <el-descriptions-item label="操作时间">{{ formatDateTime(detail?.created_at) }}</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button type="primary" @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
// 操作日志：列表 + 筛选 + 详情
import { onMounted, reactive, ref } from 'vue'
import PageTable from '@/components/PageTable.vue'
import QueryForm from '@/components/QueryForm.vue'
import { formatDateTime } from '@/utils/datetime'
import type { OperationLogItem } from '@/types/system'
import request from '@/api/request'
import type { PageResult } from '@/types'

const loading = ref(false)
const list = ref<OperationLogItem[]>([])
const total = ref(0)
const timeRange = ref<[string, string] | null>(null)

const query = reactive({
  page: 1,
  page_size: 10,
  username: '',
  module: '',
})

async function fetchList() {
  loading.value = true
  try {
    const res = await request.get<PageResult<OperationLogItem>>('/v1/operation-logs', {
      page: query.page,
      page_size: query.page_size,
      username: query.username || undefined,
      module: query.module || undefined,
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
  query.username = ''
  query.module = ''
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
const detail = ref<OperationLogItem | null>(null)

async function openDetail(row: OperationLogItem) {
  detail.value = row
  detailVisible.value = true
  const full = await request.get<OperationLogItem>(`/v1/operation-logs/${row.id}`)
  if (full) detail.value = full
}

onMounted(fetchList)
</script>
