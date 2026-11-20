// v-permission 按钮级权限指令
import type { App, Directive, DirectiveBinding } from 'vue'
import { useUserStore } from '@/store/user'

type PermValue = string | string[]

/**
 * 用法：
 *   v-permission="'order:audit'"
 *   v-permission="['order:audit', 'order:edit']"  // 满足任意一个即可
 * 无权限时移除元素。
 */
const permission: Directive = {
  mounted(el: HTMLElement, binding: DirectiveBinding<PermValue>) {
    const value = binding.value
    if (!value) return
    const userStore = useUserStore()
    const perms = Array.isArray(value) ? value : [value]
    const allowed = perms.some((perm) => userStore.hasPermission(perm))
    if (!allowed) {
      el.parentNode?.removeChild(el)
    }
  },
}

export function setupPermissionDirective(app: App) {
  app.directive('permission', permission)
}

export default permission
