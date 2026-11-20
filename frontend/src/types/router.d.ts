import 'vue-router'

declare module 'vue-router' {
  interface RouteMeta {
    /** 菜单标题 */
    title?: string
    /** 菜单图标（Element Plus 图标组件名） */
    icon?: string
    /** 所属一级菜单分组 key */
    group?: string
    /** 访问所需功能权限码，缺省表示登录即可访问 */
    perm?: string
    /** 是否在菜单中隐藏 */
    hidden?: boolean
  }
}

export {}
