import type { ClassValue } from 'clsx'
import { clsx } from 'clsx'
import { format } from 'sql-formatter'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export const formatSQL = (sql: string) => {
  return format(sql, { language: 'postgresql' })
}
