<template>
  <div class="header-bar">
    <div class="header-bar__left">
      <el-icon class="header-bar__collapse" @click="appStore.toggleSidebar()">
        <Expand v-if="collapsed" />
        <Fold v-else />
      </el-icon>
      <Breadcrumb />
    </div>

    <div class="header-bar__right">
      <el-tooltip content="刷新" placement="bottom">
        <el-icon class="header-bar__action" @click="handleRefresh"><Refresh /></el-icon>
      </el-tooltip>

      <el-dropdown trigger="click" @command="handleCommand">
        <div class="header-bar__user">
          <el-avatar :size="30" class="header-bar__avatar">
            {{ avatarText }}
          </el-avatar>
          <span class="header-bar__name">{{ userStore.realName || userStore.username }}</span>
          <el-icon><CaretBottom /></el-icon>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="profile" disabled>
              <el-icon><User /></el-icon> 个人信息
            </el-dropdown-item>
            <el-dropdown-item divided command="logout">
              <el-icon><SwitchButton /></el-icon> 退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup lang="ts">
// 顶栏：折叠按钮 + 面包屑 + 用户菜单 + 退出登录
import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Expand,
  Fold,
  Refresh,
  CaretBottom,
  User,
  SwitchButton,
} from '@element-plus/icons-vue'
import Breadcrumb from './Breadcrumb.vue'
import { useAppStore } from '@/store/app'
import { useUserStore } from '@/store/user'

const appStore = useAppStore()
const userStore = useUserStore()
const router = useRouter()
const { sidebarCollapsed: collapsed } = storeToRefs(appStore)

const avatarText = computed(() => {
  const name = userStore.realName || userStore.username || 'U'
  return name.charAt(0).toUpperCase()
})

function handleRefresh() {
  window.location.reload()
}

async function handleCommand(command: string) {
  if (command === 'logout') {
    try {
      await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      })
    } catch {
      return
    }
    await userStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  }
}
</script>

<style scoped lang="scss">
.header-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;

  &__left {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  &__collapse {
    font-size: 20px;
    cursor: pointer;
    color: var(--color-text-secondary);

    &:hover {
      color: var(--color-primary);
    }
  }

  &__right {
    display: flex;
    align-items: center;
    gap: 20px;
  }

  &__action {
    font-size: 18px;
    cursor: pointer;
    color: var(--color-text-secondary);

    &:hover {
      color: var(--color-primary);
    }
  }

  &__user {
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    padding: 4px 8px;
    border-radius: var(--radius-sm);
    transition: background 0.2s;

    &:hover {
      background: rgba(148, 163, 184, 0.12);
    }
  }

  &__avatar {
    background: var(--color-primary);
    color: #fff;
    font-weight: 600;
  }

  &__name {
    color: var(--color-text-base);
    font-size: 14px;
  }
}
</style>
