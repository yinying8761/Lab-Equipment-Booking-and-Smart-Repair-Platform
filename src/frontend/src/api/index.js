import http from './http'

export const authApi = {
  login: (data) => http.post('/auth/login', data),
  me: () => http.get('/auth/me'),
  logout: () => http.post('/auth/logout')
}

export const equipmentApi = {
  list: (params) => http.get('/equipments', { params }),
  detail: (id) => http.get(`/equipments/${id}`),
  options: (keyword) => http.get('/equipments/options', { params: { keyword } }),
  create: (data) => http.post('/admin/equipments', data),
  update: (id, data) => http.put(`/admin/equipments/${id}`, data),
  changeStatus: (id, status) => http.patch(`/admin/equipments/${id}/status`, { status })
}

export const reservationApi = {
  create: (data) => http.post('/reservations', data),
  mine: (params) => http.get('/reservations/mine', { params }),
  detail: (id) => http.get(`/reservations/${id}`),
  cancel: (id) => http.post(`/reservations/${id}/cancel`),
  adminList: (params) => http.get('/admin/reservations', { params }),
  review: (id, data) => http.post(`/admin/reservations/${id}/review`, data),
  complete: (id) => http.post(`/admin/reservations/${id}/complete`)
}

export const repairApi = {
  create: (data) => http.post('/repairs', data),
  mine: (params) => http.get('/repairs/mine', { params }),
  detail: (id) => http.get(`/repairs/${id}`),
  adminList: (params) => http.get('/admin/repairs', { params }),
  accept: (id) => http.post(`/admin/repairs/${id}/accept`),
  progress: (id, resolution) => http.post(`/admin/repairs/${id}/progress`, { resolution }),
  complete: (id, resolution) => http.post(`/admin/repairs/${id}/complete`, { resolution }),
  close: (id, reason) => http.post(`/admin/repairs/${id}/close`, { reason })
}

export const knowledgeApi = {
  list: () => http.get('/admin/knowledge'),
  upload: (formData) =>
    http.post('/admin/knowledge/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),
  remove: (id) => http.delete(`/admin/knowledge/${id}`),
  reindex: () => http.post('/admin/knowledge/reindex')
}

export const aiApi = {
  chat: (data) => http.post('/ai/chat', data),
  agentChat: (data) => http.post('/ai/agent/chat', data),
  confirm: (data) => http.post('/ai/agent/confirm', data),
  sessions: (mode) => http.get('/ai/sessions', { params: { mode } }),
  sessionDetail: (id) => http.get(`/ai/sessions/${id}`),
  trace: (id) => http.get(`/ai/sessions/${id}/trace`),
  health: () => http.get('/ai/health')
}

export const statsApi = {
  overview: () => http.get('/stats/overview')
}
