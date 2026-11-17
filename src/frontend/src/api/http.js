import axios from 'axios'
import { ElMessage } from 'element-plus'

const http = axios.create({
  baseURL: '/api',
  timeout: 120000
})

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('labcare_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (response) => {
    const body = response.data
    if (body && typeof body.code === 'number' && body.code !== 0) {
      ElMessage.error(body.message || '请求失败')
      return Promise.reject(new Error(body.message || '请求失败'))
    }
    return body
  },
  (error) => {
    const status = error.response?.status
    const body = error.response?.data
    const message = body?.message || error.message || '网络异常'

    if (status === 401) {
      localStorage.removeItem('labcare_token')
      localStorage.removeItem('labcare_user')
      if (!location.hash.startsWith('#/login')) {
        ElMessage.warning('登录状态已失效，请重新登录')
        location.hash = '#/login'
      }
    } else if (status === 403) {
      ElMessage.error('无权访问该操作')
    } else if (status === 503) {
      ElMessage.error(message || 'AI 服务暂不可用')
    } else {
      ElMessage.error(message)
    }
    return Promise.reject(error)
  }
)

export default http
