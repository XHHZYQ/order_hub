// 应用全局状态：侧边栏折叠、主题、布局配置
import { defineStore } from 'pinia'

interface AppState {
  sidebarCollapsed: boolean
  /** 主题标识（当前仅科技蓝玻璃风） */
  theme: string
}

const COLLAPSE_KEY = 'order_hub_sidebar_collapsed'

export const useAppStore = defineStore('app', {
  state: (): AppState => ({
    sidebarCollapsed: localStorage.getItem(COLLAPSE_KEY) === '1',
    theme: 'tech-blue',
  }),

  actions: {
    toggleSidebar() {
      this.sidebarCollapsed = !this.sidebarCollapsed
      localStorage.setItem(COLLAPSE_KEY, this.sidebarCollapsed ? '1' : '0')
    },
  },
})
