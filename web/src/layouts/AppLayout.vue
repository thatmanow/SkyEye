<template>
  <div class="app-wrapper" :class="{ 'sidebar-open': sidebarOpen }">
    <div class="sidebar-mask" @click="sidebarOpen = false"></div>

    <aside class="sidebar">
      <div class="sidebar-header">
        <router-link to="/" class="brand">
          <img src="/skyeye-logo.jpg" alt="天眼通" class="sidebar-logo">
          <span class="sidebar-brand">天眼通</span>
        </router-link>
      </div>

      <nav class="sidebar-nav">
        <div class="nav-group">
          <div class="nav-group-title">工作台</div>
          <router-link to="/life" class="nav-item" :class="{ active: isActive('/life', true) }">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="3" width="7" height="7"></rect>
              <rect x="14" y="3" width="7" height="7"></rect>
              <rect x="14" y="14" width="7" height="7"></rect>
              <rect x="3" y="14" width="7" height="7"></rect>
            </svg>
            <span>仪表盘</span>
          </router-link>
        </div>

        <div class="nav-group">
          <div class="nav-group-title">生活避坑</div>
          <router-link to="/life/merchants" class="nav-item" :class="{ active: isActive('/life/merchants') }">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"></path>
              <line x1="3" y1="6" x2="21" y2="6"></line>
              <path d="M16 10a4 4 0 0 1-8 0"></path>
            </svg>
            <span>商家查询</span>
          </router-link>
          <router-link to="/life/housing" class="nav-item" :class="{ active: isActive('/life/housing') }">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
              <polyline points="9 22 9 12 15 12 15 22"></polyline>
            </svg>
            <span>房源查询</span>
          </router-link>
          <router-link to="/life/jobs" class="nav-item" :class="{ active: isActive('/life/jobs') }">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect>
              <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path>
            </svg>
            <span>求职避坑</span>
          </router-link>
          <router-link to="/life/person" class="nav-item" :class="{ active: isActive('/life/person') }">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
              <circle cx="12" cy="7" r="4"></circle>
            </svg>
            <span>个人查询</span>
          </router-link>
          <router-link v-if="auth.isLogged && auth.role !== 'guest'" to="/life/vision" class="nav-item" :class="{ active: isActive('/life/vision') }">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
              <circle cx="12" cy="13" r="4"></circle>
            </svg>
            <span>AI 识图</span>
          </router-link>
          <router-link to="/life/weather" class="nav-item" :class="{ active: isActive('/life/weather') }">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="5"></circle>
              <line x1="12" y1="1" x2="12" y2="3"></line>
              <line x1="12" y1="21" x2="12" y2="23"></line>
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
              <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
              <line x1="1" y1="12" x2="3" y2="12"></line>
              <line x1="21" y1="12" x2="23" y2="12"></line>
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
            </svg>
            <span>定位天气</span>
          </router-link>
          <router-link to="/community" class="nav-item" :class="{ active: isActive('/community') }">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
              <circle cx="9" cy="7" r="4"></circle>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
            </svg>
            <span>生活圈</span>
          </router-link>
        </div>

        <div class="nav-group">
          <div class="nav-group-title">商业尽调</div>
          <router-link to="/biz/companies" class="nav-item" :class="{ active: isActive('/biz/companies') }">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M3 21h18"></path>
              <path d="M5 21V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16"></path>
              <line x1="9" y1="7" x2="9.01" y2="7"></line>
              <line x1="15" y1="7" x2="15.01" y2="7"></line>
              <line x1="9" y1="11" x2="9.01" y2="11"></line>
              <line x1="15" y1="11" x2="15.01" y2="11"></line>
              <line x1="9" y1="15" x2="9.01" y2="15"></line>
              <line x1="15" y1="15" x2="15.01" y2="15"></line>
              <path d="M11 21v-4h2v4"></path>
            </svg>
            <span>企业查询</span>
          </router-link>
          <router-link to="/biz/graph" class="nav-item" :class="{ active: isActive('/biz/graph') }">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="18" cy="5" r="3"></circle>
              <circle cx="6" cy="12" r="3"></circle>
              <circle cx="18" cy="19" r="3"></circle>
              <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line>
              <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line>
            </svg>
            <span>关系图谱</span>
          </router-link>
          <router-link to="/biz/monitor" class="nav-item" :class="{ active: isActive('/biz/monitor') }">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
            </svg>
            <span>商业监控</span>
          </router-link>
          <router-link to="/biz/reports" class="nav-item" :class="{ active: isActive('/biz/reports') }">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
              <line x1="16" y1="13" x2="8" y2="13"></line>
              <line x1="16" y1="17" x2="8" y2="17"></line>
            </svg>
            <span>尽调报告</span>
          </router-link>
          <router-link to="/biz/leads" class="nav-item" :class="{ active: isActive('/biz/leads') }">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"></circle>
              <circle cx="12" cy="12" r="6"></circle>
              <circle cx="12" cy="12" r="2"></circle>
            </svg>
            <span>商机线索</span>
          </router-link>
          <router-link v-if="auth.isLogged && auth.role !== 'guest'" to="/biz/stock" class="nav-item" :class="{ active: isActive('/biz/stock') }">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="22 7 13.5 15.5 8.5 10.5 2 17"></polyline>
              <polyline points="16 7 22 7 22 13"></polyline>
            </svg>
            <span>股票分析</span>
          </router-link>
        </div>

        <div class="nav-group">
          <div class="nav-group-title">智能与管理</div>
          <router-link v-if="auth.isLogged" to="/ai" class="nav-item" :class="{ active: isActive('/ai') }">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
            <span>AI 问答</span>
          </router-link>
          <router-link v-if="auth.isAdmin" to="/admin" class="nav-item" :class="{ active: isActive('/admin') }">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
              <line x1="3" y1="9" x2="21" y2="9"></line>
              <line x1="9" y1="21" x2="9" y2="9"></line>
            </svg>
            <span>平台管理</span>
          </router-link>
          <router-link to="/me" class="nav-item" :class="{ active: isActive('/me', true) }">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
              <circle cx="12" cy="7" r="4"></circle>
            </svg>
            <span>个人中心</span>
          </router-link>
        </div>
      </nav>

      <div class="sidebar-footer">
        <template v-if="auth.isLogged">
          <div class="sidebar-user" @click="router.push('/me')">
            <div class="sidebar-user-avatar" :class="{ 'has-img': !!auth.user?.avatar }"
                 :style="auth.user?.avatar ? { backgroundImage: `url(${auth.user.avatar})` } : undefined">
              <span v-if="!auth.user?.avatar">{{ avatarChar }}</span>
            </div>
            <div class="sidebar-user-info">
              <div class="sidebar-user-name">{{ auth.user?.nickname || '用户' }}</div>
              <div class="sidebar-user-role">{{ roleName }}</div>
            </div>
            <button class="sidebar-logout" title="退出登录" @click.stop="onLogout">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                <polyline points="16 17 21 12 16 7"></polyline>
                <line x1="21" y1="12" x2="9" y2="12"></line>
              </svg>
            </button>
          </div>
        </template>
        <template v-else>
          <div class="sidebar-guest">
            <router-link to="/login" class="ghost-btn">登录</router-link>
            <router-link to="/register" class="solid-btn">免费注册</router-link>
          </div>
        </template>
      </div>
    </aside>

    <div class="main-container">
      <header class="topbar">
        <div class="topbar-left">
          <button class="topbar-toggle" title="菜单" @click="sidebarOpen = !sidebarOpen">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="3" y1="12" x2="21" y2="12"></line>
              <line x1="3" y1="6" x2="21" y2="6"></line>
              <line x1="3" y1="18" x2="21" y2="18"></line>
            </svg>
          </button>
          <h1 class="topbar-title">{{ pageTitle }}</h1>
        </div>
        <div class="topbar-right">
          <template v-if="auth.isLogged">
            <!-- 消息中心：铃铛 + 未读徽标（virtual-ref 模式保证徽标实时刷新） -->
            <el-popover :visible="noticeOpen" :virtual-ref="bellRef" virtual-triggering
                        placement="bottom-end" :width="330" :show-arrow="false" :offset="10"
                        popper-class="notice-popper">
              <div class="notice-panel" @click.stop>
                <div class="notice-head">
                  <span class="notice-title">消息中心</span>
                  <el-button v-if="unreadCount > 0" link type="primary" size="small" @click="markAllRead">
                    全部已读
                  </el-button>
                </div>
                <el-empty v-if="!notices.length" description="暂无消息" :image-size="56" />
                <div v-else class="notice-list">
                  <div v-for="n in notices" :key="n.id" class="notice-item"
                       :class="{ unread: !n.is_read }" @click="openNotice(n)">
                    <span class="notice-dot" v-if="!n.is_read"></span>
                    <span class="notice-icon" :class="`ntype-${n.type}`">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <template v-if="n.type === 'social'">
                          <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
                        </template>
                        <template v-else-if="n.type === 'membership'">
                          <path d="m2 4 3 12h14l3-12-6 7-4-7-4 7-6-7zm3 16h14"></path>
                        </template>
                        <template v-else-if="n.type === 'monitor'">
                          <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
                          <circle cx="12" cy="13" r="4"></circle>
                        </template>
                        <template v-else>
                          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                          <polyline points="22 4 12 14.01 9 11.01"></polyline>
                        </template>
                      </svg>
                    </span>
                    <div class="notice-body">
                      <div class="notice-name">{{ n.title }}</div>
                      <div class="notice-desc">{{ n.content }}</div>
                      <div class="notice-time">{{ n.created_at }}</div>
                    </div>
                  </div>
                </div>
              </div>
            </el-popover>
            <button class="bell-zone" ref="bellRef" title="消息中心" @click="toggleNotice">
              <el-badge :value="unreadCount" :hidden="unreadCount === 0" :max="99">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
                  <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
                </svg>
              </el-badge>
            </button>
            <!-- 点击头像/昵称弹出用户菜单：升级权益入口（普通用户）/ 会员中心（高级会员）
                 头像仍渲染在 popover 虚拟引用容器内直接绑定 store，保证头像更新后实时刷新 -->
            <div class="user-zone" ref="userZoneRef" @click="toggleUserMenu">
              <span class="user-avatar" :class="{ 'has-img': !!auth.user?.avatar }"
                    :style="auth.user?.avatar ? { backgroundImage: `url(${auth.user.avatar})` } : undefined">{{ avatarChar }}</span>
              <span class="user-chip">
                <span class="user-name">{{ auth.user?.nickname || '用户' }}</span>
                <el-tag size="small" :type="roleTagType" class="role-tag">{{ roleName }}</el-tag>
              </span>
            </div>
            <el-popover :visible="menuOpen" :virtual-ref="userZoneRef" virtual-triggering
                        placement="bottom-end" :width="256" :show-arrow="false" :offset="10"
                        popper-class="user-menu-popper">
              <div class="user-menu" @click.stop>
                <button v-if="auth.role === 'user'" class="upgrade-entry" @click="goMembership">
                  <span class="upgrade-crown">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="m2 4 3 12h14l3-12-6 7-4-7-4 7-6-7zm3 16h14"></path>
                    </svg>
                  </span>
                  <span class="upgrade-info">
                    <span class="upgrade-title">升级权益</span>
                    <span class="upgrade-sub">解锁尽调报告 / 商业监控 / AI 不限次</span>
                  </span>
                  <svg class="upgrade-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="9 18 15 12 9 6"></polyline>
                  </svg>
                </button>
                <button v-else-if="auth.role === 'premium'" class="menu-item member-entry" @click="goMembership">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="m2 4 3 12h14l3-12-6 7-4-7-4 7-6-7zm3 16h14"></path>
                  </svg>
                  会员中心
                </button>
                <button class="menu-item" @click="goMe">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                    <circle cx="12" cy="7" r="4"></circle>
                  </svg>
                  个人中心
                </button>
                <div class="menu-divider"></div>
                <button class="menu-item danger" @click="doLogout">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                    <polyline points="16 17 21 12 16 7"></polyline>
                    <line x1="21" y1="12" x2="9" y2="12"></line>
                  </svg>
                  退出登录
                </button>
              </div>
            </el-popover>
          </template>
          <template v-else>
            <router-link to="/login" class="ghost-btn">登录</router-link>
            <router-link to="/register" class="solid-btn">免费注册</router-link>
          </template>
        </div>
      </header>

      <main class="main-content">
        <router-view />
      </main>

      <footer class="app-footer">
        天眼通 TianYanTong · 生活避坑 / 商业尽调 · 所有数据来源公开、合法、可溯源 · 演示数据仅用于功能验证
      </footer>
    </div>

    <!-- 会员权益弹窗（升级权益 / 会员中心入口） -->
    <MembershipDialog v-model="memberDialog" />
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { notificationApi } from '@/api/modules'
import MembershipDialog from '@/components/MembershipDialog.vue'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const sidebarOpen = ref(false)
watch(() => route.fullPath, () => { sidebarOpen.value = false })

function isActive(path: string, exact = false) {
  return exact ? route.path === path : route.path.startsWith(path)
}

const pageTitle = computed(() => {
  if (route.path === '/life') return '仪表盘'
  return (route.meta.title as string) || '天眼通'
})

const avatarChar = computed(() => (auth.user?.nickname || '用')[0])
const roleNames: Record<string, string> = {
  user: '普通用户', premium: '高级会员', enterprise_admin: '企业管理员',
  platform_admin: '平台管理员', guest: '游客',
}
const roleName = computed(() => roleNames[auth.role] || auth.role)
const roleTagType = computed(() => ({
  premium: 'success', enterprise_admin: 'warning', platform_admin: 'danger',
} as Record<string, string>)[auth.role] || 'info')

/* ===== 用户菜单（点击头像/昵称弹出；el-popover 虚拟引用 + 手动控制显隐） ===== */
const userZoneRef = ref<HTMLElement | null>(null)
const menuOpen = ref(false)
const memberDialog = ref(false)   // 会员权益弹窗（升级权益 / 会员中心）

function toggleUserMenu() {
  menuOpen.value = !menuOpen.value
  if (menuOpen.value) noticeOpen.value = false   // 与消息中心互斥
}

function onDocClick(e: MouseEvent) {
  const t = e.target as HTMLElement
  // 用户菜单外点关闭
  if (menuOpen.value) {
    if (userZoneRef.value?.contains(t)) return          // 点击头像/昵称区域：由 toggle 处理
    if (t.closest('.user-menu-popper')) return           // 点击弹层内部：由菜单项自行关闭
    menuOpen.value = false
  }
  // 消息中心外点关闭
  if (noticeOpen.value) {
    if (bellRef.value?.contains(t)) return               // 点击铃铛：由 toggle 处理
    if (t.closest('.notice-popper')) return               // 点击弹层内部：由面板项自行处理
    noticeOpen.value = false
  }
}

onMounted(() => document.addEventListener('click', onDocClick))
onBeforeUnmount(() => document.removeEventListener('click', onDocClick))

function goMembership() {
  menuOpen.value = false
  memberDialog.value = true
}

function goMe() {
  menuOpen.value = false
  router.push('/me')
}

/* ===== 消息中心（铃铛）：站内消息 + 帖子点赞/评论提醒 ===== */
const bellRef = ref<HTMLElement | null>(null)
const noticeOpen = ref(false)
const unreadCount = ref(0)
const notices = ref<any[]>([])
let pollTimer: number | undefined

async function refreshUnread() {
  if (!auth.isLogged) { unreadCount.value = 0; return }
  try {
    const r = await notificationApi.unreadCount()
    unreadCount.value = r?.count ?? 0
  } catch { /* 静默失败，下个周期重试 */ }
}

async function toggleNotice() {
  noticeOpen.value = !noticeOpen.value
  if (noticeOpen.value) {
    menuOpen.value = false                       // 与用户菜单互斥
    const r = await notificationApi.list({ page_size: 10 })
    notices.value = r?.items || []
    refreshUnread()
  }
}

async function markAllRead() {
  await notificationApi.markAllRead()
  notices.value = notices.value.map((n) => ({ ...n, is_read: true }))
  unreadCount.value = 0
  ElMessage.success('已全部标记为已读')
}

async function openNotice(n: any) {
  if (!n.is_read) {
    await notificationApi.markRead(n.id)
    n.is_read = true
    unreadCount.value = Math.max(0, unreadCount.value - 1)
    if (n.ref_url) {
      noticeOpen.value = false
      router.push(n.ref_url)
    }
    return
  }
  // 已读消息再次点击：从消息中心移除（消失）
  try {
    await notificationApi.remove(n.id)
    notices.value = notices.value.filter((it) => it.id !== n.id)
  } catch { /* 移除失败：保留该条 */ }
}

onMounted(() => {
  refreshUnread()
  pollTimer = window.setInterval(refreshUnread, 30000)   // 30s 轮询未读数
})
onBeforeUnmount(() => { if (pollTimer) window.clearInterval(pollTimer) })
watch(() => route.fullPath, () => refreshUnread())       // 路由切换时同步未读数

async function doLogout() {
  menuOpen.value = false
  await onLogout()
}

async function onLogout() {
  await auth.logout()
  router.push('/')
}
</script>

<style scoped>
.app-wrapper { min-height: 100vh; }

.sidebar-mask { position: fixed; inset: 0; background: rgba(15, 23, 42, 0.42); z-index: 110; display: none; }

.sidebar {
  position: fixed; top: 0; left: 0; bottom: 0; z-index: 120;
  width: 260px; background: var(--tyt-card);
  border-right: 1px solid var(--tyt-border);
  display: flex; flex-direction: column;
  transition: transform 0.3s ease;
}

.sidebar-header {
  padding: 18px 22px; border-bottom: 1px solid var(--tyt-border-light);
  display: flex; align-items: center; flex-shrink: 0;
}
.brand { display: flex; align-items: center; gap: 12px; }
.sidebar-logo {
  width: 36px; height: 36px; border-radius: 10px; object-fit: cover; flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.12);
}
.sidebar-brand {
  font-size: 19px; font-weight: 800; letter-spacing: -0.02em; white-space: nowrap;
  background: var(--tyt-gradient-brand);
  -webkit-background-clip: text; background-clip: text; color: transparent;
}

.sidebar-nav { flex: 1; padding: 16px 12px; overflow-y: auto; overflow-x: hidden; }
.sidebar-nav::-webkit-scrollbar { width: 4px; }
.sidebar-nav::-webkit-scrollbar-thumb { background: var(--tyt-border); border-radius: 2px; }

.nav-group { margin-bottom: 22px; }
.nav-group-title {
  font-size: 11px; font-weight: 600; color: var(--tyt-text-tertiary);
  text-transform: uppercase; letter-spacing: 0.05em;
  padding: 0 12px 8px; white-space: nowrap;
}
.nav-item {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 12px; border-radius: 8px; margin-bottom: 2px;
  color: var(--tyt-text-dim); font-size: 14px; font-weight: 500;
  white-space: nowrap; transition: all 0.2s ease;
}
.nav-item svg { width: 19px; height: 19px; flex-shrink: 0; }
.nav-item:hover { background: rgba(99, 102, 241, 0.08); color: var(--tyt-text); }
.nav-item.active { background: rgba(99, 102, 241, 0.12); color: var(--tyt-primary); font-weight: 600; }

.sidebar-footer { padding: 14px 16px; border-top: 1px solid var(--tyt-border-light); flex-shrink: 0; }
.sidebar-user {
  display: flex; align-items: center; gap: 12px; padding: 10px;
  border-radius: 10px; cursor: pointer; transition: background 0.2s ease;
}
.sidebar-user:hover { background: var(--tyt-bg-soft); }
.sidebar-user-avatar {
  width: 40px; height: 40px; border-radius: 50%; flex-shrink: 0;
  background: var(--tyt-gradient-brand); color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-weight: 600; font-size: 14px;
}
.sidebar-user-avatar.has-img {
  background-size: cover; background-position: center; background-repeat: no-repeat;
}
.sidebar-user-info { flex: 1; min-width: 0; }
.sidebar-user-name {
  font-size: 14px; font-weight: 600; color: var(--tyt-text);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.sidebar-user-role { font-size: 12px; color: var(--tyt-text-tertiary); white-space: nowrap; }
.sidebar-logout {
  padding: 8px; border-radius: 8px; border: none; background: transparent;
  color: var(--tyt-text-tertiary); cursor: pointer; flex-shrink: 0;
  display: flex; align-items: center; transition: all 0.2s ease;
}
.sidebar-logout svg { width: 18px; height: 18px; }
.sidebar-logout:hover { background: rgba(239, 68, 68, 0.1); color: var(--tyt-red); }

.sidebar-guest { display: flex; gap: 8px; }
.sidebar-guest .ghost-btn { flex: 1; text-align: center; }

.main-container {
  margin-left: 260px; min-height: 100vh;
  display: flex; flex-direction: column;
  transition: margin-left 0.3s ease;
}

.topbar {
  position: sticky; top: 0; z-index: 100; height: 64px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(12px) saturate(1.6);
  -webkit-backdrop-filter: blur(12px) saturate(1.6);
  border-bottom: 1px solid var(--tyt-border-light);
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 28px; flex-shrink: 0;
}
.topbar-left { display: flex; align-items: center; gap: 14px; }
.topbar-toggle {
  display: none; width: 36px; height: 36px; border-radius: 8px;
  align-items: center; justify-content: center; cursor: pointer;
  color: var(--tyt-text-dim); border: none; background: transparent;
  transition: all 0.2s ease;
}
.topbar-toggle svg { width: 20px; height: 20px; }
.topbar-toggle:hover { background: var(--tyt-bg-soft); color: var(--tyt-text); }
.topbar-title { font-size: 18px; font-weight: 600; color: var(--tyt-text); margin: 0; }

.topbar-right { display: flex; align-items: center; gap: 12px; }
/* 消息中心铃铛 */
.bell-zone {
  display: inline-flex; align-items: center; justify-content: center;
  width: 34px; height: 34px; padding: 0; border: none; background: none;
  border-radius: 8px; cursor: pointer; color: var(--tyt-text-dim);
  transition: background 0.15s ease, color 0.15s ease;
}
.bell-zone:hover { background: var(--tyt-bg-soft); color: var(--tyt-text); }
.bell-zone svg { width: 19px; height: 19px; }
/* 消息面板 */
.notice-panel { margin: -4px -2px; }
.notice-head {
  display: flex; justify-content: space-between; align-items: center;
  padding: 4px 6px 10px; border-bottom: 1px solid var(--tyt-border-light);
}
.notice-title { font-size: 14px; font-weight: 700; color: var(--tyt-text); }
.notice-list { max-height: 380px; overflow-y: auto; padding: 6px 2px; }
.notice-item {
  position: relative; display: flex; gap: 10px; padding: 9px 8px;
  border-radius: 8px; cursor: pointer; transition: background 0.15s ease;
}
.notice-item:hover { background: var(--tyt-bg-soft); }
.notice-item.unread { background: rgba(99, 102, 241, 0.05); }
.notice-dot {
  position: absolute; top: 14px; left: 2px; width: 6px; height: 6px;
  border-radius: 50%; background: var(--tyt-primary);
}
.notice-icon {
  display: grid; place-items: center; width: 30px; height: 30px; flex-shrink: 0;
  border-radius: 8px; background: var(--tyt-primary-soft); color: var(--tyt-primary);
}
.notice-icon svg { width: 15px; height: 15px; }
.notice-icon.ntype-social { background: rgba(239, 68, 68, 0.1); color: var(--tyt-red); }
.notice-icon.ntype-membership { background: rgba(245, 158, 11, 0.12); color: var(--tyt-amber); }
.notice-icon.ntype-monitor { background: var(--tyt-primary-soft); color: var(--tyt-primary); }
.notice-icon.ntype-audit { background: rgba(16, 185, 129, 0.1); color: var(--tyt-green); }
.notice-body { flex: 1; min-width: 0; }
.notice-name { font-size: 13px; font-weight: 600; color: var(--tyt-text); }
.notice-desc {
  font-size: 12px; color: var(--tyt-text-dim); margin-top: 2px;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.notice-time { font-size: 11px; color: var(--tyt-text-tertiary); margin-top: 3px; }
.user-zone { display: flex; align-items: center; gap: 8px; cursor: pointer; padding: 4px 6px; margin-right: -6px; border-radius: 8px; transition: background 0.15s ease; }
.user-zone:hover { background: var(--tyt-bg-soft); }
.user-chip { display: flex; align-items: center; gap: 8px; cursor: pointer; }

/* ===== 用户菜单弹层内容 ===== */
.user-menu { display: flex; flex-direction: column; gap: 2px; }
.user-menu .upgrade-entry {
  display: flex; align-items: center; gap: 10px; width: 100%;
  border: none; border-radius: 10px; padding: 10px 12px; margin: 0 0 6px;
  background: linear-gradient(135deg, #0b0e27 0%, #312e81 100%);
  color: #fff; cursor: pointer; text-align: left;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.user-menu .upgrade-entry:hover { transform: translateY(-1px); box-shadow: 0 6px 16px rgba(49, 46, 129, 0.35); }
.upgrade-crown {
  width: 30px; height: 30px; border-radius: 8px; flex-shrink: 0;
  background: rgba(245, 158, 11, 0.18); color: #fbbf24;
  display: flex; align-items: center; justify-content: center;
}
.upgrade-crown svg { width: 16px; height: 16px; }
.upgrade-info { flex: 1; display: flex; flex-direction: column; gap: 2px; }
.upgrade-title { font-size: 14px; font-weight: 700; letter-spacing: -0.01em; }
.upgrade-sub { font-size: 11px; color: rgba(255, 255, 255, 0.72); }
.upgrade-arrow { width: 14px; height: 14px; color: rgba(255, 255, 255, 0.55); }
.user-menu .menu-item {
  display: flex; align-items: center; gap: 10px; width: 100%;
  border: none; background: none; padding: 9px 10px; border-radius: 8px;
  font-size: 13.5px; color: var(--tyt-text-dim); cursor: pointer; text-align: left;
  transition: background 0.15s ease, color 0.15s ease;
}
.user-menu .menu-item:hover { background: var(--tyt-bg-soft); color: var(--tyt-text); }
.user-menu .menu-item svg { width: 15px; height: 15px; }
.user-menu .menu-item.member-entry { color: var(--tyt-primary); font-weight: 600; }
.user-menu .menu-item.member-entry:hover { background: var(--tyt-primary-soft); color: var(--tyt-primary-dark); }
.user-menu .menu-item.danger:hover { background: rgba(239, 68, 68, 0.08); color: var(--tyt-red); }
.menu-divider { height: 1px; background: var(--tyt-border-light); margin: 4px 0; }
.user-avatar {
  width: 26px; height: 26px; border-radius: 50%; flex-shrink: 0;
  background: var(--tyt-gradient-brand); color: #fff; font-size: 13px; font-weight: 600;
  display: flex; align-items: center; justify-content: center;
}
.user-avatar.has-img {
  background-size: cover; background-position: center; background-repeat: no-repeat;
  font-size: 0;
}
.user-name { font-size: 14px; color: var(--tyt-text); }

.ghost-btn { color: var(--tyt-text-dim); font-size: 14px; }
.ghost-btn:hover { color: var(--tyt-text); }
.solid-btn {
  background: var(--tyt-gradient-brand); color: #fff;
  padding: 8px 18px; border-radius: 8px; font-size: 14px; font-weight: 600;
  box-shadow: 0 4px 16px -4px rgba(99, 102, 241, 0.45);
  transition: transform 0.25s cubic-bezier(0.22, 1, 0.36, 1), box-shadow 0.25s ease;
}
.solid-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 28px -6px rgba(99, 102, 241, 0.55);
}

.main-content { flex: 1; }
.app-footer {
  text-align: center; color: var(--tyt-text-tertiary); font-size: 12px;
  padding: 18px 12px 26px; border-top: 1px solid var(--tyt-border);
  background: var(--tyt-card);
}

@media (max-width: 960px) {
  .sidebar { transform: translateX(-100%); }
  .app-wrapper.sidebar-open .sidebar {
    transform: translateX(0);
    box-shadow: 0 0 48px rgba(15, 23, 42, 0.22);
  }
  .app-wrapper.sidebar-open .sidebar-mask { display: block; }
  .main-container { margin-left: 0; }
  .topbar-toggle { display: inline-flex; }
  .topbar { padding: 0 16px; }
  .user-name, .role-tag { display: none; }
}
</style>
