import axios from 'axios'
import { ElMessage } from 'element-plus'

export interface ApiResp<T = any> {
  code: number
  message: string
  data: T
}

export const http = axios.create({ baseURL: '/api/v1', timeout: 120000 })

http.interceptors.request.use((cfg) => {
  const token = localStorage.getItem('tyt_access_token')
  if (token) cfg.headers.Authorization = `Bearer ${token}`
  return cfg
})

http.interceptors.response.use(
  (resp) => {
    const body = resp.data
    if (body && typeof body.code === 'number' && body.code !== 0) {
      const msg = body.message || '请求失败'
      if (body.code === 429 || body.code === 403) ElMessage.warning(msg)
      else ElMessage.error(msg)
      return Promise.reject(new Error(msg))
    }
    return body?.data !== undefined ? body.data : body
  },
  async (err) => {
    const status = err.response?.status
    const detail = err.response?.data
    if (status === 401) {
      const refreshed = await tryRefresh()
      if (refreshed) return http(err.config)
      localStorage.removeItem('tyt_access_token')
      localStorage.removeItem('tyt_refresh_token')
      if (location.pathname !== '/login') {
        ElMessage.error('登录已过期，请重新登录')
        location.href = '/login'
      }
      return Promise.reject(err)
    }
    const msg = detail?.message || detail?.detail || err.message || '网络错误'
    if (status !== 404 || !String(err.config?.url).includes('/api/')) ElMessage.error(String(msg))
    return Promise.reject(err)
  },
)

let refreshing: Promise<boolean> | null = null
async function tryRefresh(): Promise<boolean> {
  if (!refreshing) {
    refreshing = (async () => {
      const rt = localStorage.getItem('tyt_refresh_token')
      if (!rt) return false
      try {
        const resp = await axios.post('/api/v1/auth/refresh', { refresh_token: rt })
        const d = resp.data?.data
        if (d?.access_token) {
          localStorage.setItem('tyt_access_token', d.access_token)
          if (d.refresh_token) localStorage.setItem('tyt_refresh_token', d.refresh_token)
          return true
        }
        return false
      } catch {
        return false
      } finally {
        setTimeout(() => (refreshing = null), 100)
      }
    })()
  }
  return refreshing
}
