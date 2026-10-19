import { defineStore } from 'pinia'
import { authApi } from '@/api/modules'

export interface QuotaInfo { used: number; limit: number; remaining?: number }

// 角色/状态短轮询：后台管理员改角色、Celery 到期降级等场景，
// 让前端菜单/标签/路由守卫在无需重新登录的情况下及时同步（与后端实时角色保持一致）。
let roleTimer: ReturnType<typeof setInterval> | null = null
const ROLE_SYNC_MS = 30_000

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('tyt_access_token') || '',
    user: null as any,
    quotas: {} as Record<string, QuotaInfo>,
    loaded: false,
  }),
  getters: {
    isLogged: (s) => !!s.token,
    role: (s) => s.user?.role || 'guest',
    isPremium: (s) => s.user?.role === 'premium',
    isAdmin: (s) => ['platform_admin'].includes(s.user?.role || ''),
    canAdmin: (s) => ['platform_admin', 'enterprise_admin'].includes(s.user?.role || ''),
  },
  actions: {
    async login(account: string, password: string) {
      const data = await authApi.login({ account, password })
      this.token = data.access_token
      localStorage.setItem('tyt_access_token', data.access_token)
      localStorage.setItem('tyt_refresh_token', data.refresh_token)
      await this.fetchMe()
      this.ensureRoleSync()
    },
    async fetchMe() {
      if (!this.token) return
      const data = await authApi.me()
      this.user = data.user
      this.quotas = data.quotas || {}
      this.loaded = true
      this.ensureRoleSync()
    },
    async init() {
      // 应用启动时的会话恢复：优先用 refresh token 主动续期，拿到新的 access token 后再拉取用户信息。
      // 这样即使本地存储的 access token 已过期，也能在发起任何受保护请求「之前」完成续期，
      // 避免「每次重新打开网站都要重新登录」（原逻辑只在 401 后才尝试刷新，存在竞态/失败窗口）。
      // 只要 refresh token 仍有效（默认 7 天），重开即可保持登录。
      const rt = localStorage.getItem('tyt_refresh_token')
      const at = localStorage.getItem('tyt_access_token')
      if (!rt && !at) {
        this.loaded = true
        return
      }
      if (rt) {
        try {
          const d: any = await authApi.refresh(rt)
          if (d?.access_token) {
            this.token = d.access_token
            localStorage.setItem('tyt_access_token', d.access_token)
            if (d.refresh_token) localStorage.setItem('tyt_refresh_token', d.refresh_token)
            await this.fetchMe()
            return
          }
        } catch {
          // refresh 失败：尝试用旧 access token 兜底
        }
      }
      if (at) {
        try {
          await this.fetchMe()
          return
        } catch {
          // 旧 access token 也失效
        }
      }
      // 续期与兜底都失败：清理本地登录态（下次访问受保护路由会跳转登录页）
      this.token = ''
      this.user = null
      this.quotas = {}
      localStorage.removeItem('tyt_access_token')
      localStorage.removeItem('tyt_refresh_token')
      this.loaded = true
    },
    ensureRoleSync() {
      if (roleTimer || typeof window === 'undefined') return
      roleTimer = setInterval(() => {
        if (this.token) this.fetchMe().catch(() => { /* 网络/401 忽略，下一个周期重试 */ })
      }, ROLE_SYNC_MS)
    },
    stopRoleSync() {
      if (roleTimer) {
        clearInterval(roleTimer)
        roleTimer = null
      }
    },
    async logout() {
      try { await authApi.logout() } catch { /* 忽略 */ }
      this.stopRoleSync()
      this.token = ''
      this.user = null
      this.quotas = {}
      localStorage.removeItem('tyt_access_token')
      localStorage.removeItem('tyt_refresh_token')
    },
  },
})
