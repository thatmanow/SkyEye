<template>
  <div class="page">
    <h1 class="page-title">生活避坑中心</h1>
    <p class="page-sub">消费、租房、求职前的三分钟核查 —— 数据来自公开渠道与平台过审 UGC</p>

    <div class="group-label">🧭 生活类 · 快捷入口</div>
    <div class="entries">
      <router-link to="/life/merchants" class="entry">
        <div class="e-ic">🍜</div>
        <div class="e-title">商家查询</div>
        <div class="e-desc">工商状态 · 评价聚合 · 投诉记录</div>
      </router-link>
      <router-link to="/life/housing" class="entry">
        <div class="e-ic">🏘️</div>
        <div class="e-title">房源查询</div>
        <div class="e-desc">小区投诉 · 房东纠纷 · 中介套路</div>
      </router-link>
      <router-link to="/life/jobs" class="entry">
        <div class="e-ic">💼</div>
        <div class="e-title">求职避坑</div>
        <div class="e-desc">经营状态 · 欠薪记录 · 劳动仲裁</div>
      </router-link>
      <router-link to="/life/person" class="entry">
        <div class="e-ic">🛡️</div>
        <div class="e-title">个人查询</div>
        <div class="e-desc">仅公开失信/涉诉记录，姓名强制脱敏</div>
      </router-link>
      <router-link to="/life/vision" class="entry" v-if="auth.isLogged">
        <div class="e-ic">📷</div>
        <div class="e-title">AI 识图</div>
        <div class="e-desc">智能识图引擎 · 多轮追问</div>
      </router-link>
      <router-link to="/life/weather" class="entry">
        <div class="e-ic">🌤️</div>
        <div class="e-title">定位天气</div>
        <div class="e-desc">实时天气 · 高德地图 · 生活指数</div>
      </router-link>
    </div>

    <!-- 商业尽调中心 -->
    <h1 class="page-title biz-title-gap">商业尽调中心</h1>
    <p class="page-sub">企业查询 · 股权穿透 · 风险监控 · 多智能体研判 —— 商业决策前的尽调入口</p>

    <div class="group-label">💼 商业类 · 快捷入口</div>
    <div class="entries">
      <router-link to="/biz/companies" class="entry">
        <div class="e-ic">🏢</div>
        <div class="e-title">企业查询</div>
        <div class="e-desc">工商 · 股东 · 投资 · 风险</div>
      </router-link>
      <router-link to="/biz/graph" class="entry" v-if="auth.isLogged">
        <div class="e-ic">🕸️</div>
        <div class="e-title">关系图谱</div>
        <div class="e-desc">股权穿透 · 实控人推导</div>
      </router-link>
      <router-link to="/biz/monitor" class="entry">
        <div class="e-ic">📡</div>
        <div class="e-title">商业监控</div>
        <div class="e-desc">动态追踪 · 日报周报</div>
      </router-link>
      <router-link to="/biz/reports" class="entry">
        <div class="e-ic">📄</div>
        <div class="e-title">尽调报告</div>
        <div class="e-desc">一键生成 PDF / Excel</div>
      </router-link>
      <router-link to="/biz/leads" class="entry">
        <div class="e-ic">💡</div>
        <div class="e-title">商机线索</div>
        <div class="e-desc">风险企业衍生商机</div>
      </router-link>
      <router-link to="/biz/stock" class="entry" v-if="auth.isLogged">
        <div class="e-ic">📈</div>
        <div class="e-title">股票分析</div>
        <div class="e-desc">六智能体协同 · 多维研判</div>
      </router-link>
    </div>

    <!-- 爬虫实时流（第一版双源爬虫：人民网资讯 + baostock 证券） -->
    <div class="tyt-card crawler-card">
      <div class="crawler-head">
        <div class="crawler-title">
          <span class="news-stream-dot"></span> 爬虫实时流
          <span class="crawler-sub">人民网资讯 · baostock 证券 双数据源</span>
        </div>
        <div class="crawler-actions">
          <div class="crawler-filters">
            <button v-for="f in sourceFilters" :key="f.key" class="crawler-chip"
                    :class="{ active: filter === f.key }" @click="switchFilter(f.key)">{{ f.label }}</button>
          </div>
          <button class="crawler-toggle" :title="paused ? '继续滚动' : '暂停滚动'" @click="paused = !paused">
            <svg v-if="!paused" width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16" rx="1"></rect><rect x="14" y="4" width="4" height="16" rx="1"></rect></svg>
            <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
          </button>
          <button class="crawler-toggle" title="重新加载" @click="reloadStream">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"></polyline><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path></svg>
          </button>
        </div>
      </div>

      <div class="news-stream-body" ref="streamBody"
           :class="{ paused }"
           @mouseenter="hovering = true" @mouseleave="hovering = false">
        <div v-if="!items.length && !done" class="news-stream-placeholder">正在获取爬虫数据…</div>
        <div v-else-if="!items.length" class="news-stream-placeholder">暂无爬虫数据</div>
        <div v-for="(it, i) in items" :key="streamId + '-' + i" class="news-stream-item clickable"
             :style="{ animationDelay: '0s', borderLeftColor: it.badge_color }"
             :title="'点击在 AI 问答中解读（Top5 相似检索）'" @click="askInAi(it)">
          <span class="news-stream-item__channel" :style="{ background: it.badge_color }">{{ it.badge }}</span>
          <div class="news-stream-item__content">
            <div class="news-stream-item__title">
              <span class="src-mark" :class="it.source">{{ it.source === 'people' ? '人民网' : 'baostock' }}</span>
              {{ it.title }}
            </div>
            <div class="news-stream-item__meta">
              <span>{{ it.meta }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="crawler-stats" v-if="stats">
        <span class="stat-pill people">📰 人民网 {{ stats.people_total }} 篇</span>
        <span class="stat-pill baostock">📈 baostock {{ stats.baostock_securities }} 证券 / {{ stats.baostock_kline }} K线</span>
        <span class="stat-time">{{ done ? `流式完成 · ${items.length} 条` : (loading ? '接收中…' : '待加载') }} · {{ stats.generated_at }}</span>
      </div>
    </div>

    <div class="tyt-card" style="margin-top: 22px">
      <h3 style="margin: 0 0 10px; font-size: 15px">🛡️ 使用须知</h3>
      <ul class="notes">
        <li>个人查询仅返回<strong>脱敏姓名</strong>与公开风险记录，不提供身份证号 / 手机号 / 住址等任何非公开信息检索。</li>
        <li>商家评价、小区投诉、生活圈帖子均为用户提交，<strong>先审后发</strong>，审核通过后对外可见。</li>
        <li>所有查询行为写入审计日志；普通用户每日查询次数有限额，升级高级会员可解锁更多额度。</li>
        <li>爬虫实时流数据来自第一版两个采集器（人民网 Sitemap 增量抓取 / baostock 官方 SDK 查询），仅供演示与研究。</li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

function askInAi(it: any) {
  if (!['premium', 'enterprise_admin', 'platform_admin'].includes(auth.role)) {
    return ElMessage.warning('AI 问答为高级会员功能，可用 premium@tyt.demo 演示账号体验')
  }
  const q = it.source === 'people' ? it.title : `${it.title} 的最新行情如何解读？`
  router.push({ path: '/ai', query: { q } })
}

/* ===== 爬虫实时流（SSE） ===== */
const sourceFilters = [
  { key: 'all', label: '全部' },
  { key: 'people', label: '人民网' },
  { key: 'baostock', label: 'baostock' },
]
const filter = ref('all')
const items = ref<any[]>([])
const stats = ref<any>(null)
const loading = ref(false)
const done = ref(false)
const paused = ref(false)
const hovering = ref(false)
const streamBody = ref<HTMLElement>()
const streamId = ref(0)

let streamSeq = 0
let stream: EventSource | null = null

function disconnect() {
  streamSeq++
  stream?.close()
  stream = null
}

function connect() {
  const seq = ++streamSeq
  stream?.close()
  items.value = []
  done.value = false
  loading.value = true
  stats.value = null
  const es = new EventSource(`/api/v1/dashboard/crawler-stream?limit=500&source=${filter.value}`)
  stream = es
  es.onmessage = (ev) => {
    if (seq !== streamSeq) return
    let msg: any
    try { msg = JSON.parse(ev.data) } catch { return }
    if (msg.type === 'start') {
      streamId.value++
      stats.value = msg.stats || {}
      stats.value.generated_at = msg.generated_at
    } else if (msg.type === 'item') {
      items.value.push(msg.data)
      if (!paused.value && !hovering.value) scrollBottom()
    } else if (msg.type === 'done') {
      done.value = true
      loading.value = false
      es.close()
    }
  }
  es.onerror = () => {
    // 连接中断（服务重启/网络波动）：直接关闭，避免 EventSource 自动重连导致数据重复
    es.close()
    if (seq === streamSeq) {
      done.value = true
      loading.value = false
    }
  }
}

function switchFilter(key: string) {
  if (filter.value === key) return
  filter.value = key
  connect()
}

function reloadStream() { connect() }

function scrollBottom() {
  nextTick(() => {
    if (streamBody.value) streamBody.value.scrollTop = streamBody.value.scrollHeight
  })
}

onMounted(connect)
onBeforeUnmount(disconnect)
</script>

<style scoped>
.group-label {
  display: flex; align-items: center; gap: 10px;
  margin: 24px 0 14px; font-size: 14.5px; font-weight: 700; color: var(--tyt-text);
}
.group-label::before {
  content: ""; width: 4px; height: 16px; border-radius: 2px; flex-shrink: 0;
  background: var(--tyt-gradient-brand);
}
.group-label::after {
  content: ""; flex: 1; height: 1px; background: var(--tyt-border-light);
}

/* 商业尽调中心标题（与生活类大标题样式一致，仅增加顶部间距） */
.biz-title-gap { margin-top: 34px; }
.entries { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 16px; }
.entry {
  display: block; background: var(--tyt-card); border: 1px solid var(--tyt-border);
  border-radius: 14px; padding: 26px 22px; transition: all .2s;
}
.entry:hover { transform: translateY(-3px); border-color: rgba(99,102,241,.45); }
.e-ic { font-size: 28px; margin-bottom: 10px; }
.e-title { font-size: 17px; font-weight: 700; margin-bottom: 6px; color: var(--tyt-text); }
.e-desc { color: var(--tyt-text-dim); font-size: 13px; }
.notes { margin: 0; padding-left: 18px; color: var(--tyt-text-dim); font-size: 13px; line-height: 2; }
.notes strong { color: var(--tyt-primary); }

/* ===== 爬虫实时流（复刻第一版 news-stream-card） ===== */
.crawler-card { margin-top: 22px; display: flex; flex-direction: column; }
.crawler-head {
  display: flex; align-items: center; justify-content: space-between;
  gap: 12px; flex-wrap: wrap; margin-bottom: 12px;
}
.crawler-title { display: flex; align-items: center; gap: 8px; font-size: 15px; font-weight: 700; }
.crawler-sub {
  font-size: 12px; font-weight: 500; color: var(--tyt-text-dim);
  background: var(--tyt-bg-soft); border: 1px solid var(--tyt-border-light);
  border-radius: 999px; padding: 3px 10px;
}
.crawler-actions { display: flex; align-items: center; gap: 10px; }
.crawler-filters { display: flex; gap: 4px; background: var(--tyt-bg-soft); border-radius: 999px; padding: 3px; }
.crawler-chip {
  border: none; background: transparent; font-size: 12px; color: var(--tyt-text-dim);
  padding: 5px 13px; border-radius: 999px; cursor: pointer; transition: all .2s; white-space: nowrap;
}
.crawler-chip:hover { color: var(--tyt-text); }
.crawler-chip.active {
  background: var(--tyt-gradient-brand); color: #fff; font-weight: 600;
  box-shadow: 0 2px 8px -2px rgba(99,102,241,.5);
}
.crawler-toggle {
  width: 30px; height: 30px; border-radius: 8px; border: 1px solid var(--tyt-border);
  background: var(--tyt-card); color: var(--tyt-text-dim); cursor: pointer;
  display: inline-flex; align-items: center; justify-content: center; transition: all .2s;
}
.crawler-toggle:hover { color: var(--tyt-primary); border-color: var(--tyt-primary); background: var(--tyt-primary-soft); }

.news-stream-dot {
  width: 8px; height: 8px; border-radius: 50%; background: #22c55e; flex-shrink: 0;
  animation: streamPulse 1.5s ease-in-out infinite;
}
@keyframes streamPulse {
  0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.5); }
  50% { opacity: 0.6; box-shadow: 0 0 0 6px rgba(34, 197, 94, 0); }
}

.news-stream-body {
  overflow-y: auto; padding: 12px 14px; min-height: 180px; max-height: 300px;
  display: flex; flex-direction: column; gap: 6px;
  background: var(--tyt-card-2); border: 1px solid var(--tyt-border-light); border-radius: 10px;
  scrollbar-width: thin;
}
.news-stream-body.paused { scrollbar-color: rgba(99,102,241,.45) transparent; }
.news-stream-placeholder {
  color: var(--tyt-text-tertiary); font-size: 13px; text-align: center; padding: 40px 0;
}
.news-stream-item {
  display: flex; align-items: flex-start; gap: 8px; padding: 8px 10px;
  border-radius: 8px; background: var(--tyt-card);
  border: 1px solid var(--tyt-border-light); border-left: 3px solid var(--tyt-primary);
  animation: streamSlideIn 0.55s ease backwards;
  box-shadow: 0 1px 3px rgba(15, 23, 42, .04);
}
.news-stream-item.clickable { cursor: pointer; transition: border-color .18s, background .18s, transform .18s; }
.news-stream-item.clickable:hover {
  border-color: rgba(99, 102, 241, .5); background: var(--tyt-primary-soft);
  transform: translateX(2px);
}
@keyframes streamSlideIn {
  from { opacity: 0; transform: translateX(-12px); }
  to { opacity: 1; transform: translateX(0); }
}
.news-stream-item__channel {
  flex-shrink: 0; font-size: 11px; font-weight: 600; color: #fff;
  padding: 2px 7px; border-radius: 4px; margin-top: 2px; white-space: nowrap;
}
.news-stream-item__content { flex: 1; min-width: 0; }
.news-stream-item__title {
  font-size: 13px; font-weight: 500; color: var(--tyt-text); line-height: 1.5;
  overflow: hidden; text-overflow: ellipsis; display: -webkit-box;
  -webkit-line-clamp: 2; -webkit-box-orient: vertical;
}
.src-mark {
  display: inline-block; font-size: 10.5px; font-weight: 700; border-radius: 4px;
  padding: 1px 6px; margin-right: 6px; vertical-align: 1px;
}
.src-mark.people { background: var(--tyt-primary-soft); color: var(--tyt-primary-dark); }
.src-mark.baostock { background: rgba(8, 145, 178, .12); color: #0891b2; }
.news-stream-item__meta {
  font-size: 11px; color: var(--tyt-text-tertiary); margin-top: 3px;
  display: flex; gap: 10px; flex-wrap: wrap;
}

.crawler-stats {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-top: 12px;
}
.stat-pill {
  font-size: 12px; font-weight: 600; border-radius: 999px; padding: 4px 12px;
}
.stat-pill.people { background: var(--tyt-primary-soft); color: var(--tyt-primary-dark); }
.stat-pill.baostock { background: rgba(8, 145, 178, .1); color: #0891b2; }
.stat-time { font-size: 11.5px; color: var(--tyt-text-tertiary); margin-left: auto; }

@media (max-width: 720px) {
  .crawler-head { flex-direction: column; align-items: flex-start; }
  .stat-time { margin-left: 0; }
}
</style>
