// 金额 / 数字格式化工具

/**
 * 金额格式化：千分位 + 两位小数 + ¥ 前缀
 * @param value 金额
 * @param symbol 是否显示 ¥ 前缀，默认 true
 */
export function formatAmount(value?: number | string | null, symbol = true): string {
  if (value === undefined || value === null || value === '') return symbol ? '¥0.00' : '0.00'
  const num = typeof value === 'string' ? Number(value) : value
  if (Number.isNaN(num)) return symbol ? '¥0.00' : '0.00'
  const text = num.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
  return symbol ? `¥${text}` : text
}

/** 数字格式化：千分位 */
export function formatNumber(value?: number | string | null, fractionDigits = 0): string {
  if (value === undefined || value === null || value === '') return '0'
  const num = typeof value === 'string' ? Number(value) : value
  if (Number.isNaN(num)) return '0'
  return num.toLocaleString('zh-CN', {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  })
}

/** 百分比格式化：保留位数 + % */
export function formatPercent(value?: number | string | null, fractionDigits = 2): string {
  if (value === undefined || value === null || value === '') return '0%'
  const num = typeof value === 'string' ? Number(value) : value
  if (Number.isNaN(num)) return '0%'
  return `${num.toFixed(fractionDigits)}%`
}
