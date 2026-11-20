<template>
  <div class="page-table">
    <!-- 查询区 -->
    <div v-if="$slots.query" class="page-table__query glass-card">
      <slot name="query" />
    </div>

    <!-- 表格主体区 -->
    <div class="page-table__body glass-card">
      <div v-if="$slots.toolbar || title" class="page-table__toolbar">
        <div class="page-table__title">{{ title }}</div>
        <div class="page-table__actions">
          <slot name="toolbar" />
        </div>
      </div>

      <div v-if="$slots.tips" class="page-table__tips">
        <slot name="tips" />
      </div>

      <slot />

      <!-- 分页 -->
      <div v-if="showPagination" class="page-table__pager">
        <el-pagination
          :current-page="page"
          :page-size="pageSize"
          :total="total"
          :page-sizes="pageSizes"
          :layout="layout"
          background
          @current-change="handleCurrentChange"
          @size-change="handleSizeChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// 列表页通用容器：查询区 + 表格 + 分页 + 操作区
interface Props {
  total?: number
  page?: number
  pageSize?: number
  title?: string
  pageSizes?: number[]
  layout?: string
  showPagination?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  total: 0,
  page: 1,
  pageSize: 10,
  title: '',
  pageSizes: () => [10, 20, 50, 100],
  layout: 'total, sizes, prev, pager, next, jumper',
  showPagination: true,
})

const emit = defineEmits<{
  (e: 'update:page', value: number): void
  (e: 'update:pageSize', value: number): void
  (e: 'change', payload: { page: number; pageSize: number }): void
}>()

function handleCurrentChange(page: number) {
  emit('update:page', page)
  emit('change', { page, pageSize: props.pageSize })
}

function handleSizeChange(pageSize: number) {
  emit('update:pageSize', pageSize)
  emit('update:page', 1)
  emit('change', { page: 1, pageSize })
}
</script>

<style scoped lang="scss">
.page-table {
  display: flex;
  flex-direction: column;
  gap: var(--padding-base);

  &__query {
    padding-bottom: 0;
  }

  &__body {
    :deep(.el-table) {
      background-color: transparent;
    }
  }

  &__toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 12px;
  }

  &__title {
    font-size: 16px;
    font-weight: 600;
    color: var(--color-text-base);
  }

  &__actions {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }

  &__tips {
    margin-bottom: 12px;
  }

  &__pager {
    display: flex;
    justify-content: flex-end;
    margin-top: 16px;
  }
}
</style>
