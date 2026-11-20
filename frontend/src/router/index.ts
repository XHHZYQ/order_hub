// 路由实例与全局守卫（登录校验 + 功能权限校验）
import { createRouter, createWebHistory } from 'vue-router'
import { ElMessage } from 'element-plus'
import routes from './routes'
import { getToken } from '@/utils/auth'
import { useUserStore } from '@/store/user'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

const WHITE_LIST = ['/login']

router.beforeEach(async (to) => {
  const token = getToken()

  // 已登录访问登录页 -> 跳首页
  if (to.path === '/login') {
    return token ? { path: '/dashboard/overview' } : true
  }

  // 未登录 -> 跳登录页
  if (!token) {
    if (WHITE_LIST.includes(to.path)) return true
    return { path: '/login', query: { redirect: to.fullPath } }
  }

  const userStore = useUserStore()
  // 已登录但未加载用户信息 -> 拉取
  if (!userStore.loaded) {
    try {
      await userStore.fetchUserInfo()
    } catch {
      userStore.reset()
      return { path: '/login', query: { redirect: to.fullPath } }
    }
  }

  // 功能权限校验
  if (to.meta.perm && !userStore.hasPermission(to.meta.perm)) {
    ElMessage.warning('无访问权限')
    if (to.path !== '/dashboard/overview') {
      return { path: '/dashboard/overview' }
    }
    return false
  }

  return true
})

router.afterEach((to) => {
  const title = (to.meta.title as string) || ''
  document.title = title ? `${title} - 订单汇聚管理系统` : '订单汇聚管理系统'
})

export default router
