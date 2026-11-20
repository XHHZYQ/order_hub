<template>
  <div class="overview">
    <div class="overview__banner glass-card">
      <div class="overview__greeting">
        <h2 class="overview__hello">你好，{{ userStore.realName || userStore.username }} 👋</h2>
        <p class="overview__desc">欢迎使用订单汇聚管理系统，祝你工作顺利！</p>
      </div>
      <el-tag type="primary" effect="light" round>当前版本：批次 1（基础底座）</el-tag>
    </div>

    <div class="overview__cards">
      <div v-for="card in cards" :key="card.title" class="overview__card glass-card">
        <div class="overview__card-icon" :style="{ background: card.bg, color: card.color }">
          <el-icon :size="22"><component :is="card.icon" /></el-icon>
        </div>
        <div class="overview__card-body">
          <div class="overview__card-title">{{ card.title }}</div>
          <div class="overview__card-text">{{ card.text }}</div>
        </div>
      </div>
    </div>

    <div class="overview__placeholder glass-card">
      <el-empty description="经营总览看板建设中，将在批次 5 上线核心指标与趋势分析" />
    </div>
  </div>
</template>

<script setup lang="ts">
// 首页：批次 1 占位页（M9 看板在批次 5 实现）
import { useUserStore } from '@/store/user'

const userStore = useUserStore()

const cards = [
  {
    title: '平台与店铺',
    text: '登记平台、绑定店铺并配置同步任务',
    icon: 'Shop',
    color: '#6366f1',
    bg: 'rgba(99,102,241,0.12)',
  },
  {
    title: '系统管理',
    text: '维护用户、角色、功能与数据权限',
    icon: 'Setting',
    color: '#10b981',
    bg: 'rgba(16,185,129,0.12)',
  },
  {
    title: '同步日志',
    text: '查看同步结果与失败原因并重试',
    icon: 'Document',
    color: '#f59e0b',
    bg: 'rgba(245,158,11,0.12)',
  },
]
</script>

<style scoped lang="scss">
.overview {
  display: flex;
  flex-direction: column;
  gap: var(--padding-base);

  &__banner {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  &__hello {
    margin: 0 0 6px;
    font-size: 20px;
    font-weight: 700;
    color: var(--color-text-base);
  }

  &__desc {
    margin: 0;
    color: var(--color-text-secondary);
  }

  &__cards {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: var(--padding-base);
  }

  &__card {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  &__card-icon {
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: var(--radius-sm);
    flex-shrink: 0;
  }

  &__card-title {
    font-size: 15px;
    font-weight: 600;
    color: var(--color-text-base);
    margin-bottom: 4px;
  }

  &__card-text {
    font-size: 13px;
    color: var(--color-text-secondary);
  }
}
</style>
