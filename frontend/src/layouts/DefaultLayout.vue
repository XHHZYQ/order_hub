<template>
  <el-container class="default-layout">
    <el-aside :width="sidebarWidth" class="default-layout__aside">
      <SideMenu :collapsed="collapsed" />
    </el-aside>
    <el-container class="default-layout__main">
      <el-header class="default-layout__header" height="60px">
        <HeaderBar />
      </el-header>
      <el-main class="default-layout__content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
// 主布局：左侧玻璃深色菜单 + 顶栏 + 内容区
import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import SideMenu from './components/SideMenu.vue'
import HeaderBar from './components/HeaderBar.vue'
import { useAppStore } from '@/store/app'

const appStore = useAppStore()
const { sidebarCollapsed: collapsed } = storeToRefs(appStore)

const sidebarWidth = computed(() => (collapsed.value ? '64px' : '220px'))
</script>

<style scoped lang="scss">
.default-layout {
  height: 100vh;
  overflow: hidden;

  &__aside {
    background: var(--layout-sider-bg);
    backdrop-filter: blur(var(--glass-blur));
    -webkit-backdrop-filter: blur(var(--glass-blur));
    transition: width 0.25s ease;
    overflow: hidden;
    box-shadow: 2px 0 16px rgba(15, 23, 42, 0.12);
    z-index: 10;
  }

  &__main {
    overflow: hidden;
  }

  &__header {
    display: flex;
    align-items: center;
    background: var(--glass-bg-hover);
    backdrop-filter: blur(var(--glass-blur));
    -webkit-backdrop-filter: blur(var(--glass-blur));
    border-bottom: 1px solid var(--glass-border);
    padding: 0 var(--padding-base);
  }

  &__content {
    padding: var(--padding-base);
    overflow-y: auto;
    background: transparent;
  }
}
</style>
