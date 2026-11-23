// 路由表（与菜单对应）
// 只声明本批次（批次 1：M10 系统管理 + M1 平台与店铺）已实现的页面
import type { RouteRecordRaw } from 'vue-router'

/** 一级菜单分组（用于侧边栏分组渲染，顺序即菜单顺序） */
export interface MenuGroup {
  key: string
  title: string
  icon: string
}

export const MENU_GROUPS: MenuGroup[] = [
  { key: 'dashboard', title: '数据看板', icon: 'DataLine' },
  { key: 'order', title: '订单中心', icon: 'Tickets' },
  { key: 'product', title: '商品与库存', icon: 'Goods' },
  { key: 'platform', title: '平台与店铺', icon: 'Shop' },
  { key: 'system', title: '系统管理', icon: 'Setting' },
]

/** 无需登录的路由 */
export const constantRoutes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/index.vue'),
    meta: { title: '登录', hidden: true },
  },
]

/** 需要登录、参与菜单渲染的路由（作为 DefaultLayout 的子路由） */
export const layoutChildren: RouteRecordRaw[] = [
  {
    path: '/dashboard/overview',
    name: 'DashboardOverview',
    component: () => import('@/views/dashboard/overview.vue'),
    meta: { title: '经营总览', icon: 'Odometer', group: 'dashboard' },
  },
  // 订单中心（M2）
  {
    path: '/order/list',
    name: 'OrderList',
    component: () => import('@/views/order/list.vue'),
    meta: { title: '订单列表', icon: 'Tickets', group: 'order', perm: 'order:list' },
  },
  {
    path: '/order/detail/:id',
    name: 'OrderDetail',
    component: () => import('@/views/order/detail.vue'),
    meta: { title: '订单详情', icon: 'Document', group: 'order', perm: 'order:detail', hidden: true },
  },
  // 商品与库存（M4 商品与 SKU 映射 + M5 库存同步与防超卖）
  {
    path: '/product/list',
    name: 'ProductList',
    component: () => import('@/views/product/list.vue'),
    meta: { title: '本地商品', icon: 'Goods', group: 'product', perm: 'product:list' },
  },
  {
    path: '/product/platform',
    name: 'ProductPlatform',
    component: () => import('@/views/product/platform.vue'),
    meta: { title: '平台商品', icon: 'ShoppingBag', group: 'product', perm: 'product:platform' },
  },
  {
    path: '/product/mapping',
    name: 'ProductMapping',
    component: () => import('@/views/product/mapping.vue'),
    meta: { title: 'SKU 映射', icon: 'Connection', group: 'product', perm: 'product:mapping' },
  },
  {
    path: '/inventory/list',
    name: 'InventoryList',
    component: () => import('@/views/inventory/list.vue'),
    meta: { title: '库存管理', icon: 'Box', group: 'product', perm: 'inventory:list' },
  },
  {
    path: '/inventory/flow',
    name: 'InventoryFlow',
    component: () => import('@/views/inventory/flow.vue'),
    meta: { title: '库存流水', icon: 'List', group: 'product', perm: 'inventory:flow' },
  },
  {
    path: '/inventory/share',
    name: 'InventoryShare',
    component: () => import('@/views/inventory/share.vue'),
    meta: { title: '库存共享', icon: 'Share', group: 'product', perm: 'inventory:share' },
  },
  {
    path: '/inventory/alert',
    name: 'InventoryAlert',
    component: () => import('@/views/inventory/alert.vue'),
    meta: { title: '库存预警', icon: 'Warning', group: 'product', perm: 'inventory:alert' },
  },
  {
    path: '/inventory/stocktake',
    name: 'InventoryStocktake',
    component: () => import('@/views/inventory/stocktake.vue'),
    meta: { title: '库存盘点', icon: 'Memo', group: 'product', perm: 'inventory:stocktake' },
  },
  // 平台与店铺（M1）
  {
    path: '/platform/list',
    name: 'PlatformList',
    component: () => import('@/views/platform/list.vue'),
    meta: { title: '平台管理', icon: 'Grid', group: 'platform', perm: 'platform:list' },
  },
  {
    path: '/platform/shop',
    name: 'PlatformShop',
    component: () => import('@/views/platform/shop.vue'),
    meta: { title: '店铺管理', icon: 'Shop', group: 'platform', perm: 'shop:list' },
  },
  {
    path: '/platform/sync-task',
    name: 'PlatformSyncTask',
    component: () => import('@/views/platform/sync-task.vue'),
    meta: { title: '同步任务', icon: 'Refresh', group: 'platform', perm: 'sync:task_list' },
  },
  {
    path: '/platform/sync-log',
    name: 'PlatformSyncLog',
    component: () => import('@/views/platform/sync-log.vue'),
    meta: { title: '同步日志', icon: 'Document', group: 'platform', perm: 'sync:log_list' },
  },
  // 系统管理（M10）
  {
    path: '/system/user',
    name: 'SystemUser',
    component: () => import('@/views/system/user.vue'),
    meta: { title: '用户管理', icon: 'User', group: 'system', perm: 'user:list' },
  },
  {
    path: '/system/role',
    name: 'SystemRole',
    component: () => import('@/views/system/role.vue'),
    meta: { title: '角色管理', icon: 'UserFilled', group: 'system', perm: 'role:list' },
  },
  {
    path: '/system/log',
    name: 'SystemLog',
    component: () => import('@/views/system/log.vue'),
    meta: { title: '操作日志', icon: 'Tickets', group: 'system', perm: 'log:list' },
  },
]

/** 需要通过 DefaultLayout 访问的主路由 */
export const layoutRoute: RouteRecordRaw = {
  path: '/',
  name: 'Layout',
  component: () => import('@/layouts/DefaultLayout.vue'),
  redirect: '/dashboard/overview',
  children: layoutChildren,
}

/** 通配路由：未匹配时回到首页 */
export const notFoundRoute: RouteRecordRaw = {
  path: '/:pathMatch(.*)*',
  redirect: '/dashboard/overview',
  meta: { hidden: true },
}

export const routes: RouteRecordRaw[] = [...constantRoutes, layoutRoute, notFoundRoute]
export default routes
