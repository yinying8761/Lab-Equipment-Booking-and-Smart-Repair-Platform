export const reservationStatusType = {
  PENDING: 'warning',
  APPROVED: 'success',
  REJECTED: 'danger',
  CANCELLED: 'info',
  COMPLETED: 'success'
}

export const repairStatusType = {
  PENDING: 'warning',
  PROCESSING: 'primary',
  COMPLETED: 'success',
  CLOSED: 'info'
}

export const equipmentStatusType = {
  AVAILABLE: 'success',
  MAINTENANCE: 'warning',
  DISABLED: 'info'
}

export const equipmentStatusLabel = {
  AVAILABLE: '可用',
  MAINTENANCE: '维修中',
  DISABLED: '停用'
}

export function formatDateTime(value) {
  if (!value) return '-'
  return String(value).replace('T', ' ').slice(0, 16)
}

export function shortCode(code, length = 12) {
  if (!code) return '-'
  return code.length > length ? code.slice(0, length) + '…' : code
}
