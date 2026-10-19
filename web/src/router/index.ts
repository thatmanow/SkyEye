import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'landing', component: () => import('@/views/LandingView.vue') },
    { path: '/login', name: 'login', component: () => import('@/views/LoginView.vue') },
    { path: '/register', name: 'register', component: () => import('@/views/RegisterView.vue') },

    {
      path: '/',
      component: () => import('@/layouts/AppLayout.vue'),
      children: [
        { path: 'life', name: 'life-home', component: () => import('@/views/life/LifeHome.vue'),
          meta: { title: '仪表盘' } },
        { path: 'life/merchants', name: 'merchants', component: () => import('@/views/life/MerchantSearch.vue'),
          meta: { title: '商家查询' } },
        { path: 'life/housing', name: 'housing', component: () => import('@/views/life/HousingSearch.vue'),
          meta: { title: '房源查询' } },
        { path: 'life/jobs', name: 'jobs', component: () => import('@/views/life/JobCompany.vue'),
          meta: { title: '求职避坑' } },
        { path: 'life/person', name: 'person', component: () => import('@/views/life/PersonSearch.vue'),
          meta: { title: '个人查询' } },
        { path: 'life/vision', name: 'vision', component: () => import('@/views/life/AiVision.vue'),
          meta: { title: 'AI 识图', roles: ['user', 'premium', 'enterprise_admin', 'platform_admin'] } },
        { path: 'life/weather', name: 'weather', component: () => import('@/views/life/WeatherMap.vue'),
          meta: { title: '定位天气' } },

        { path: 'community', name: 'community', component: () => import('@/views/community/CommunityHome.vue'),
          meta: { title: '生活圈' } },
        { path: 'community/:id', name: 'post-detail', component: () => import('@/views/community/PostDetail.vue'),
          meta: { title: '帖子详情' } },

        { path: 'biz', name: 'biz-home', component: () => import('@/views/biz/BizHome.vue'),
          meta: { title: '商业尽调' } },
        { path: 'biz/companies', name: 'companies', component: () => import('@/views/biz/CompanySearch.vue'),
          meta: { title: '企业查询' } },
        { path: 'biz/companies/:id', name: 'company-detail', component: () => import('@/views/biz/CompanyDetail.vue'),
          meta: { title: '企业详情' } },
        { path: 'biz/graph', name: 'graph', component: () => import('@/views/biz/GraphExplorer.vue'),
          meta: { title: '关系图谱', roles: ['user', 'premium', 'enterprise_admin', 'platform_admin'] } },
        { path: 'biz/monitor', name: 'monitor', component: () => import('@/views/biz/MonitorCenter.vue'),
          meta: { title: '商业监控' } },
        { path: 'biz/reports', name: 'reports', component: () => import('@/views/biz/ReportCenter.vue'),
          meta: { title: '尽调报告' } },
        { path: 'biz/leads', name: 'leads', component: () => import('@/views/biz/LeadCenter.vue'),
          meta: { title: '商机线索' } },
        { path: 'biz/stock', name: 'stock', component: () => import('@/views/biz/StockAgents.vue'),
          meta: { title: '股票分析', roles: ['user', 'premium', 'enterprise_admin', 'platform_admin'] } },

        { path: 'ai', name: 'ai', component: () => import('@/views/ai/AiChat.vue'),
          meta: { title: 'AI 问答', roles: ['user', 'premium', 'enterprise_admin', 'platform_admin'] } },

        { path: 'admin', name: 'admin', component: () => import('@/views/admin/AdminConsole.vue'),
          meta: { title: '平台管理', roles: ['platform_admin'] } },

        { path: 'me', name: 'me', component: () => import('@/views/me/ProfileView.vue'),
          meta: { title: '个人中心' } },
      ],
    },
    { path: '/:pathMatch(.*)*', name: 'not-found', component: () => import('@/views/NotFoundView.vue') },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (!auth.loaded) {
    // 启动会话恢复：主动用 refresh token 续期（详见 auth.init），保证重开网站保持登录
    try { await auth.init() } catch { /* 失败则保持游客态，由下方逻辑决定跳转 */ }
  }
  const roles = to.meta.roles as string[] | undefined
  if (roles && roles.length) {
    if (!auth.isLogged) return { path: '/login', query: { redirect: to.fullPath } }
    if (!roles.includes(auth.role)) {
      return { path: '/' }
    }
  }
  document.title = to.meta.title ? `${to.meta.title} · 天眼通` : '天眼通'
})

export default router
