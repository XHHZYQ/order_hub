<template>
  <div class="side-menu">
    <div class="side-menu__logo">
      <el-icon class="side-menu__logo-icon"><ShoppingCart /></el-icon>
      <span v-show="!collapsed" class="side-menu__logo-text">订单汇聚</span>
    </div>

    <el-scrollbar class="side-menu__scroll">
      <el-menu
        :default-active="activePath"
        :collapse="collapsed"
        :collapse-transition="false"
        background-color="transparent"
        text-color="var(--layout-sider-text)"
        active-text-color="#ffffff"
        router
      >
        <template v-for="group in visibleGroups" :key="group.key">
          <el-sub-menu :index="group.key">
            <template #title>
              <el-icon><component :is="group.icon" /></el-icon>
              <span>{{ group.title }}</span>
            </template>
            <el-menu-item
              v-for="item in group.items"
              :key="item.path"
              :index="item.path"
            >
              <el-icon v-if="item.icon"><component :is="item.icon" /></el-icon>
              <template #title>{{ item.title }}</template>
            </el-menu-item>
          </el-sub-menu>
        </template>
      </el-menu>
    </el-scrollbar>
  </div>
</template>

<script setup lang="ts">
// 侧边菜单：由路由表按当前用户功能权限码过滤动态生成
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { ShoppingCart } from '@element-plus/icons-vue'
import { MENU_GROUPS, layoutChildren } from '@/router/routes'
import { useUserStore } from '@/store/user'

defineProps<{ collapsed: boolean }>()

const route = useRoute()
const userStore = useUserStore()

const activePath = computed(() => route.path)

interface MenuItem {
  path: string
  title: string
  icon?: string
}

interface VisibleGroup {
  key: string
  title: string
  icon: string
  items: MenuItem[]
}

const visibleGroups = computed<VisibleGroup[]>(() => {
  return MENU_GROUPS.map((group) => {
    const items = layoutChildren
      .filter((r) => r.meta?.group === group.key && !r.meta?.hidden)
      .filter((r) => userStore.hasPermission(r.meta?.perm as string | undefined))
      .map((r) => ({
        path: r.path,
        title: (r.meta?.title as string) ?? '',
        icon: r.meta?.icon as string | undefined,
      }))
    return { key: group.key, title: group.title, icon: group.icon, items }
  }).filter((group) => group.items.length > 0)
})
</script>

<style scoped lang="scss">
.side-menu {
  height: 100%;
  display: flex;
  flex-direction: column;

  &__logo {
    height: 60px;
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 0 20px;
    color: #fff;
    font-size: 17px;
    font-weight: 700;
    letter-spacing: 1px;
    border-bottom: 1px solid rgba(148, 163, 184, 0.15);
    white-space: nowrap;
    overflow: hidden;
  }

  &__logo-icon {
    font-size: 22px;
    color: var(--color-primary-hover);
    flex-shrink: 0;
  }

  &__scroll {
    flex: 1;
  }

  :deep(.el-menu) {
    border-right: none;
    padding: 8px;
  }

  :deep(.el-sub-menu__title),
  :deep(.el-menu-item) {
    border-radius: var(--radius-sm);
    margin-bottom: 4px;
  }

  :deep(.el-menu-item.is-active) {
    background: var(--layout-sider-active-bg);
    font-weight: 600;
  }

  :deep(.el-menu-item:hover),
  :deep(.el-sub-menu__title:hover) {
    background: rgba(148, 163, 184, 0.12);
  }
}
</style>
