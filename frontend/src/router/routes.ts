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
  { key: 'shipment', title: '发货履约', icon: 'Van' },
  { key: 'product', title: '商品与库存', icon: 'Goods' },
  { key: 'finance', title: '财务对账', icon: 'Money' },
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
    meta: { title: '经营总览', icon: 'Odometer', group: 'dashboard', perm: 'dashboard:overview' },
  },
  {
    path: '/dashboard/channel',
    name: 'DashboardChannel',
    component: () => import('@/views/dashboard/channel.vue'),
    meta: { title: '渠道与店铺', icon: 'Share', group: 'dashboard', perm: 'dashboard:channel' },
  },
  {
    path: '/dashboard/product',
    name: 'DashboardProduct',
    component: () => import('@/views/dashboard/product.vue'),
    meta: { title: '商品销售', icon: 'Goods', group: 'dashboard', perm: 'dashboard:product' },
  },
  {
    path: '/dashboard/fulfillment',
    name: 'DashboardFulfillment',
    component: () => import('@/views/dashboard/fulfillment.vue'),
    meta: { title: '订单与履约', icon: 'Van', group: 'dashboard', perm: 'dashboard:fulfillment' },
  },
  {
    path: '/dashboard/after-sale',
    name: 'DashboardAfterSale',
    component: () => import('@/views/dashboard/after-sale.vue'),
    meta: { title: '售后分析', icon: 'RefreshLeft', group: 'dashboard', perm: 'dashboard:after_sale' },
  },
  {
    path: '/dashboard/inventory',
    name: 'DashboardInventory',
    component: () => import('@/views/dashboard/inventory.vue'),
    meta: { title: '库存分析', icon: 'Box', group: 'dashboard', perm: 'dashboard:inventory' },
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
  // 订单处理与售后（M3 + M7）
  {
    path: '/order/abnormal',
    name: 'OrderAbnormal',
    component: () => import('@/views/order/abnormal.vue'),
    meta: { title: '异常订单池', icon: 'Warning', group: 'order', perm: 'order:abnormal' },
  },
  {
    path: '/after-sale/list',
    name: 'AfterSaleList',
    component: () => import('@/views/after-sale/list.vue'),
    meta: { title: '售后管理', icon: 'RefreshLeft', group: 'order', perm: 'order:after_sale' },
  },
  // 发货履约（M6）
  {
    path: '/shipment/pending',
    name: 'ShipmentPending',
    component: () => import('@/views/shipment/pending.vue'),
    meta: { title: '待发货', icon: 'Box', group: 'shipment', perm: 'shipment:pending' },
  },
  {
    path: '/shipment/ship',
    name: 'ShipmentShip',
    component: () => import('@/views/shipment/ship.vue'),
    meta: { title: '打单发货', icon: 'Printer', group: 'shipment', perm: 'shipment:ship' },
  },
  {
    path: '/shipment/list',
    name: 'ShipmentList',
    component: () => import('@/views/shipment/list.vue'),
    meta: { title: '发货记录', icon: 'List', group: 'shipment', perm: 'shipment:list' },
  },
  {
    path: '/shipment/alert',
    name: 'ShipmentAlert',
    component: () => import('@/views/shipment/alert.vue'),
    meta: { title: '物流异常', icon: 'Van', group: 'shipment', perm: 'shipment:alert' },
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
  // 财务对账（M8）
  {
    path: '/finance/bill',
    name: 'FinanceBill',
    component: () => import('@/views/finance/bill.vue'),
    meta: { title: '账单管理', icon: 'Tickets', group: 'finance', perm: 'finance:bill' },
  },
  {
    path: '/finance/difference',
    name: 'FinanceDifference',
    component: () => import('@/views/finance/difference.vue'),
    meta: { title: '对账差异', icon: 'Warning', group: 'finance', perm: 'finance:difference' },
  },
  {
    path: '/finance/settlement',
    name: 'FinanceSettlement',
    component: () => import('@/views/finance/settlement.vue'),
    meta: { title: '结算汇总', icon: 'Money', group: 'finance', perm: 'finance:settlement' },
  },
  {
    path: '/finance/profit',
    name: 'FinanceProfit',
    component: () => import('@/views/finance/profit.vue'),
    meta: { title: '毛利核算', icon: 'TrendCharts', group: 'finance', perm: 'finance:profit' },
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
