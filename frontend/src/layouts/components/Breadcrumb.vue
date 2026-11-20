<template>
  <el-breadcrumb class="breadcrumb" separator="/">
    <el-breadcrumb-item
      v-for="(item, index) in breadcrumbs"
      :key="index"
    >
      {{ item }}
    </el-breadcrumb-item>
  </el-breadcrumb>
</template>

<script setup lang="ts">
// 面包屑：根据当前路由匹配链生成
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { MENU_GROUPS } from '@/router/routes'

const route = useRoute()

const breadcrumbs = computed<string[]>(() => {
  const list: string[] = []
  const groupKey = route.meta.group as string | undefined
  if (groupKey) {
    const group = MENU_GROUPS.find((g) => g.key === groupKey)
    if (group) list.push(group.title)
  }
  if (route.meta.title) list.push(route.meta.title as string)
  return list.length ? list : ['首页']
})
</script>

<style scoped lang="scss">
.breadcrumb {
  font-size: 14px;
}
</style>
