<template>
  <el-form class="query-form" :model="model" inline @submit.prevent>
    <slot />
    <el-form-item class="query-form__actions">
      <el-button type="primary" :loading="loading" :icon="Search" @click="handleSearch">
        查询
      </el-button>
      <el-button :icon="RefreshLeft" @click="handleReset">重置</el-button>
      <slot name="extra" />
    </el-form-item>
  </el-form>
</template>

<script setup lang="ts">
// 通用查询表单：提供查询/重置按钮，查询区项目由默认插槽传入
import { Search, RefreshLeft } from '@element-plus/icons-vue'

interface Props {
  model?: Record<string, unknown>
  loading?: boolean
}

withDefaults(defineProps<Props>(), {
  model: () => ({}),
  loading: false,
})

const emit = defineEmits<{
  (e: 'search'): void
  (e: 'reset'): void
}>()

function handleSearch() {
  emit('search')
}

function handleReset() {
  emit('reset')
}
</script>

<style scoped lang="scss">
.query-form {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  row-gap: 4px;

  :deep(.el-form-item) {
    margin-bottom: 16px;
    margin-right: 16px;
  }

  &__actions {
    :deep(.el-form-item__content) {
      gap: 8px;
    }
  }
}
</style>
