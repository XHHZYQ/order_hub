// 时间格式化工具（基于 dayjs）
import dayjs from 'dayjs'

/** 统一时间展示格式：YYYY-MM-DD HH:mm:ss（24 小时制） */
export const DATETIME_FORMAT = 'YYYY-MM-DD HH:mm:ss'

/** 格式化日期时间，空值返回 '-' */
export function formatDateTime(value?: string | number | Date | null): string {
  if (value === undefined || value === null || value === '') return '-'
  const d = dayjs(value)
  return d.isValid() ? d.format(DATETIME_FORMAT) : '-'
}

/** 格式化日期（不含时间）：YYYY-MM-DD */
export function formatDate(value?: string | number | Date | null): string {
  if (value === undefined || value === null || value === '') return '-'
  const d = dayjs(value)
  return d.isValid() ? d.format('YYYY-MM-DD') : '-'
}

export default dayjs
