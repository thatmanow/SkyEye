<template>
  <div class="page stock-page">
    <h1 class="page-title">多智能体股票分析</h1>
    <p class="page-sub">六位智能体协同作业：量化计算 + 本地大模型研判 —— 演示宇宙 · 演示数据，不构成投资建议</p>

    <!-- 搜索栏 -->
    <div class="stock-search-bar">
      <div class="stock-search">
        <el-select v-model="selected" filterable remote :remote-method="doSearch" :loading="searching"
                   placeholder="输入股票代码或名称，如：600519 或 贵州茅台" size="large" class="stock-select"
                   @change="onSelect">
          <el-option v-for="s in searchResults" :key="s.code" :value="s.code"
                     :label="`${s.name}（${s.code}）`">
            <span class="opt-name">{{ s.name }}</span>
            <span class="opt-meta">{{ s.code }} · {{ s.industry }}</span>
          </el-option>
        </el-select>
        <el-button type="primary" size="large" class="analyze-btn" :loading="running" :disabled="!selected" @click="analyze">
          {{ running ? '智能体作业中…' : '开始多智能体分析' }}
        </el-button>
      </div>
      <span class="quota-chip" v-if="auth.isLogged">今日剩余分析：{{ quotaText }}</span>
    </div>
    <SampleChips :samples="[{ label: '贵州茅台 600519', value: '600519' },
                            { label: '宁德时代 300750', value: '300750' },
                            { label: '工商银行 601398', value: '601398' },
                            { label: '平安银行 000001', value: '000001' }]"
                 @pick="pickStock" />

    <!-- 大盘指数 -->
    <div class="indices-grid">
      <div v-for="i in indices" :key="i.code" class="index-item">
        <div class="index-name">{{ i.name }}</div>
        <div class="index-price" :class="i.direction">{{ fmt(i.price) }}</div>
        <div class="index-chg" :class="i.direction">{{ i.pct_chg > 0 ? '+' : '' }}{{ i.pct_chg }}%</div>
      </div>
    </div>

    <div class="stock-layout">
      <!-- 左：K 线 + 资讯 -->
      <div class="stock-left">
        <div class="tyt-card chart-card">
          <div class="card-head">
            <div class="card-title">
              股票走势
              <span v-if="quote" class="quote-chip">
                {{ quote.name }}（{{ quote.code }}）
                <b :class="quote.pct_chg >= 0 ? 'up' : 'down'">{{ quote.price }}</b>
                <span :class="quote.pct_chg >= 0 ? 'up' : 'down'">{{ quote.pct_chg > 0 ? '+' : '' }}{{ quote.pct_chg }}%</span>
              </span>
            </div>
            <div class="chart-tabs">
              <button v-for="t in tabs" :key="t.key" class="chart-tab"
                      :class="{ active: tab === t.key }" @click="switchTab(t.key)">{{ t.label }}</button>
            </div>
          </div>
          <div v-show="quote" ref="klineEl" class="kline-box"></div>
          <div v-if="!quote" class="chart-empty">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <line x1="12" y1="1" x2="12" y2="23"></line>
              <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
            </svg>
            <div>选择证券后开始 AI 智能分析</div>
          </div>
        </div>

        <div class="tyt-card news-card" v-if="news.length">
          <div class="card-head"><div class="card-title">近期公开资讯（演示）</div></div>
          <ul class="news-list">
            <li v-for="(n, i) in news" :key="i">📰 {{ n }}</li>
          </ul>
        </div>
      </div>

      <!-- 右：智能体流水线 -->
      <div class="stock-right">
        <div class="tyt-card agents-card">
          <div class="card-head">
            <div class="card-title">智能体流水线</div>
            <span class="pipeline-status" :class="phaseClass">{{ phaseText }}</span>
          </div>
          <div class="agents-list">
            <div v-for="a in agents" :key="a.key" class="agent-item" :class="state(a.key)">
              <div class="agent-head" @click="toggle(a.key)">
                <span class="agent-icon">{{ a.icon }}</span>
                <span class="agent-name">{{ a.name }}</span>
                <span class="agent-state">
                  <template v-if="st(a.key) === 'running'"><span class="mini-spinner"></span>分析中</template>
                  <template v-else-if="st(a.key) === 'done'">✓ 完成</template>
                  <template v-else>待命</template>
                </span>
                <svg class="agent-arrow" :class="{ open: expanded[a.key] }" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg>
              </div>
              <div v-if="expanded[a.key]" class="agent-body">
                <template v-if="content[a.key]">
                  <p v-for="(line, i) in content[a.key].split('\n')" :key="i" :class="{ 'md-h': line.startsWith('#'), 'md-li': line.startsWith('- ') }">
                    {{ line.replace(/^#+\s*/, '').replace(/^- /, '· ').replace(/\*\*/g, '') }}
                  </p>
                </template>
                <span v-else class="agent-waiting">等待上游智能体输出…</span>
                <span v-if="st(a.key) === 'running' && a.key === 'chief' && !content.chief" class="cursor">▍</span>
              </div>
            </div>
          </div>
          <p class="disclaimer">⚠️ 免责声明：以上内容由本地大模型基于演示数据生成，仅供技术演示与研究学习，不构成任何投资建议。</p>
        </div>

        <!-- 综合分析报告：全部智能体完成后输出 -->
        <div class="tyt-card report-card" v-if="report">
          <div class="card-head">
            <div class="card-title">📋 综合分析报告</div>
            <span class="report-meta" v-if="reportMeta">{{ reportMeta }}</span>
          </div>
          <div class="report-body">
            <p v-for="(l, i) in reportLines" :key="i" :class="l.cls">{{ l.text }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import SampleChips from '@/components/SampleChips.vue'
import { stockApi } from '@/api/modules'
import { ssePost } from '@/api/sse'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const selected = ref('')
const searching = ref(false)
const searchResults = ref<any[]>([])
const indices = ref<any[]>([])
const quote = ref<any>(null)
const news = ref<string[]>([])
const running = ref(false)
const tab = ref('daily')
const tabs = [
  { key: 'daily', label: '日K' },
  { key: 'weekly', label: '周K' },
  { key: 'monthly', label: '月K' },
]

const agents = ref<any[]>([])
const states = ref<Record<string, string>>({})
const content = ref<Record<string, string>>({})
const expanded = ref<Record<string, boolean>>({})
const report = ref('')
const reportMeta = ref('')

const klineEl = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

const quotaText = computed(() => {
  const q = (auth.quotas as any)?.stock_analysis
  if (!q) return '—'
  if (q.limit < 0) return '不限'
  return `${Math.max(0, q.remaining ?? (q.limit - q.used))} / ${q.limit}`
})

const phaseClass = computed(() => running.value ? 'running' : 'idle')
const phaseText = computed(() => {
  if (running.value) {
    const active = Object.keys(states.value).filter((k) => states.value[k] === 'running')
    return active.length ? `${agentName(active[0])} 作业中` : '流水线运行中'
  }
  return Object.keys(states.value).length ? '已完成' : '待启动'
})

function agentName(key: string) {
  return agents.value.find((a) => a.key === key)?.name || key
}
function st(key: string) { return states.value[key] || 'idle' }
function state(key: string) { return { [st(key)]: true } }
function toggle(key: string) { expanded.value[key] = !expanded.value[key] }

/* 报告按行渲染：标题/列表/引用/正文 */
const reportLines = computed(() => {
  if (!report.value) return []
  return report.value.split('\n').filter((l) => l.trim()).map((line) => {
    if (/^#{1,4}\s/.test(line)) return { text: line.replace(/^#+\s*/, '').replace(/\*\*/g, ''), cls: 'rpt-h' }
    if (/^[-*·]\s/.test(line)) return { text: line.replace(/^[-*·]\s*/, '· ').replace(/\*\*/g, ''), cls: 'rpt-li' }
    if (/^>\s?/.test(line)) return { text: line.replace(/^>\s?/, ''), cls: 'rpt-quote' }
    return { text: line.replace(/\*\*/g, ''), cls: 'rpt-p' }
  })
})

function fmt(n: number) { return n.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }

async function doSearch(kw: string) {
  searching.value = true
  try {
    searchResults.value = await stockApi.search({ keyword: kw })
  } finally {
    searching.value = false
  }
}

async function onSelect(code: string) {
  if (!code) return
  try {
    quote.value = await stockApi.quote(code)
    await nextTick()
    renderKline()
  } catch {
    quote.value = null
  }
}

function pickStock(code: string) {
  selected.value = code
  onSelect(code)
}

function switchTab(key: string) {
  tab.value = key
  if (quote.value) renderKline()
}

/* ---- K 线渲染 ---- */
function aggregate(kline: any[], factor: number) {
  if (factor <= 1) return kline
  const out: any[] = []
  for (let i = 0; i < kline.length; i += factor) {
    const slice = kline.slice(i, i + factor)
    if (!slice.length) break
    out.push({
      date: slice[slice.length - 1].date,
      open: slice[0].open,
      close: slice[slice.length - 1].close,
      high: Math.max(...slice.map((k) => k.high)),
      low: Math.min(...slice.map((k) => k.low)),
      volume: slice.reduce((s, k) => s + k.volume, 0),
    })
  }
  return out
}

function maLine(closes: number[], n: number) {
  return closes.map((_, i) => (i < n - 1 ? null : +(closes.slice(i - n + 1, i + 1).reduce((a, b) => a + b, 0) / n).toFixed(2)))
}

function renderKline() {
  if (!klineEl.value || !quote.value) return
  if (!chart) chart = echarts.init(klineEl.value)
  const factor = tab.value === 'weekly' ? 5 : tab.value === 'monthly' ? 22 : 1
  const kline = aggregate(quote.value.kline, factor)
  const closes = kline.map((k: any) => k.close)

  chart.setOption({
    animation: true,
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
    axisPointer: { link: [{ xAxisIndex: 'all' }] },
    grid: [
      { left: 56, right: 16, top: 24, height: '58%' },
      { left: 56, right: 16, top: '76%', height: '16%' },
    ],
    xAxis: [
      { type: 'category', data: kline.map((k: any) => k.date.slice(5)), gridIndex: 0,
        axisLine: { lineStyle: { color: '#cbd5e1' } }, axisLabel: { color: '#94a3b8', fontSize: 10 } },
      { type: 'category', data: kline.map((k: any) => k.date.slice(5)), gridIndex: 1,
        axisLabel: { show: false }, axisLine: { show: false }, axisTick: { show: false } },
    ],
    yAxis: [
      { scale: true, gridIndex: 0, splitLine: { lineStyle: { color: '#f1f5f9' } },
        axisLabel: { color: '#94a3b8', fontSize: 10 } },
      { gridIndex: 1, show: false, scale: true },
    ],
    dataZoom: [{ type: 'inside', xAxisIndex: [0, 1], start: 55, end: 100 }],
    series: [
      {
        name: 'K线', type: 'candlestick', xAxisIndex: 0, yAxisIndex: 0,
        data: kline.map((k: any) => [k.open, k.close, k.low, k.high]),
        itemStyle: { color: '#ef4444', color0: '#10b981', borderColor: '#ef4444', borderColor0: '#10b981' },
      },
      { name: 'MA5', type: 'line', data: maLine(closes, 5), smooth: true, showSymbol: false, lineStyle: { width: 1.3, color: '#6366f1' } },
      { name: 'MA10', type: 'line', data: maLine(closes, 10), smooth: true, showSymbol: false, lineStyle: { width: 1.3, color: '#f59e0b' } },
      { name: 'MA20', type: 'line', data: maLine(closes, 20), smooth: true, showSymbol: false, lineStyle: { width: 1.3, color: '#a78bfa' } },
      {
        name: '成交量', type: 'bar', xAxisIndex: 1, yAxisIndex: 1,
        data: kline.map((k: any) => ({ value: k.volume,
          itemStyle: { color: k.close >= k.open ? 'rgba(239,68,68,.65)' : 'rgba(16,185,129,.65)' } })),
        barWidth: '62%',
      },
    ],
  }, true)
  chart.resize()
}

function resizeHandler() { chart?.resize() }

/* ---- 多智能体流水线（SSE）：工作中的智能体展开工作信息，完成后收缩 ---- */
async function analyze() {
  if (!selected.value || running.value) return
  running.value = true
  states.value = {}
  content.value = {}
  expanded.value = {}
  report.value = ''
  reportMeta.value = ''
  try {
    await ssePost('/biz/stock/analyze', { code: selected.value }, (ev) => {
      if (ev.type === 'agent_start') {
        states.value[ev.agent] = 'running'
        // 只展示正在工作的智能体：收起所有已完成的
        Object.keys(states.value).forEach((k) => {
          if (states.value[k] !== 'running') expanded.value[k] = false
        })
        expanded.value[ev.agent] = true
      } else if (ev.type === 'agent_done') {
        states.value[ev.agent] = 'done'
        content.value[ev.agent] = ev.content || ''
        // 完成即收缩工作信息
        expanded.value[ev.agent] = false
      } else if (ev.type === 'chief_chunk') {
        content.value.chief = (content.value.chief || '') + ev.content
      } else if (ev.type === 'done') {
        states.value.chief = 'done'
        // 流水线结束：全部收缩，输出综合报告
        expanded.value = {}
        report.value = content.value.chief || ''
        reportMeta.value = quote.value
          ? `${quote.value.name}（${quote.value.code}）· ${new Date().toLocaleString('zh-CN', { hour12: false })}`
          : new Date().toLocaleString('zh-CN', { hour12: false })
        news.value = ev.news || []
        quote.value = { ...quote.value, kline: ev.kline || quote.value?.kline }
        nextTick(renderKline)
        auth.fetchMe().catch(() => {})
      } else if (ev.type === 'error') {
        ElMessage.error(ev.message || '分析失败')
      }
    })
  } catch (e: any) {
    ElMessage.error(e.message || String(e))
  } finally {
    running.value = false
    Object.keys(states.value).forEach((k) => { if (states.value[k] === 'running') states.value[k] = 'done' })
  }
}

onMounted(async () => {
  window.addEventListener('resize', resizeHandler)
  try { agents.value = await stockApi.agents() } catch { /* ignore */ }
  try { indices.value = await stockApi.indices() } catch { /* ignore */ }
  doSearch('')
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeHandler)
  chart?.dispose()
  chart = null
})
</script>

<style scoped>
.stock-search-bar { display: flex; align-items: center; gap: 14px; margin-bottom: 16px; flex-wrap: wrap; }
.stock-search { display: flex; gap: 10px; flex: 1; min-width: 360px; }
.stock-select { flex: 1; }
.opt-name { font-weight: 600; }
.opt-meta { float: right; color: var(--tyt-text-tertiary); font-size: 12px; }
.analyze-btn {
  background: var(--tyt-gradient-brand); border: none; font-weight: 600;
  box-shadow: 0 4px 16px -4px rgba(99, 102, 241, .45);
}
.quota-chip {
  font-size: 12px; padding: 6px 12px; border-radius: 999px;
  background: var(--tyt-primary-soft); color: var(--tyt-primary-dark); font-weight: 500;
}

.indices-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 18px; }
.index-item {
  background: var(--tyt-card); border: 1px solid var(--tyt-border); border-radius: 12px;
  padding: 13px 16px;
}
.index-name { font-size: 12.5px; color: var(--tyt-text-dim); margin-bottom: 5px; }
.index-price { font-size: 17px; font-weight: 800; letter-spacing: -0.01em; }
.index-chg { font-size: 12px; font-weight: 600; margin-top: 2px; }
.up { color: var(--tyt-red); }
.down { color: var(--tyt-green); }

.stock-layout { display: grid; grid-template-columns: 1.35fr 1fr; gap: 18px; align-items: stretch; }
.stock-left, .stock-right { display: flex; flex-direction: column; }
.card-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; gap: 10px; flex-wrap: wrap; }
.card-title { font-size: 15px; font-weight: 700; display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.quote-chip {
  font-size: 12.5px; font-weight: 500; color: var(--tyt-text-dim);
  background: var(--tyt-bg-soft); border-radius: 999px; padding: 3px 12px;
}
.quote-chip b { font-weight: 700; }
.chart-tabs { display: flex; background: var(--tyt-bg-soft); border-radius: 8px; padding: 2px; }
.chart-tab {
  border: none; background: transparent; font-size: 12px; color: var(--tyt-text-dim);
  padding: 5px 13px; border-radius: 7px; cursor: pointer;
}
.chart-tab.active { background: var(--tyt-card); color: var(--tyt-text); box-shadow: var(--tyt-shadow-sm); font-weight: 600; }

.kline-box { width: 100%; height: 380px; }
.chart-empty {
  height: 380px; display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 12px; color: var(--tyt-text-tertiary); font-size: 13.5px; background: var(--tyt-card-2);
  border-radius: 10px;
}
.chart-empty svg { width: 38px; height: 38px; opacity: .4; }

.news-card { margin-top: 16px; flex: 1; }
.news-list { margin: 0; padding-left: 18px; font-size: 13px; line-height: 2.1; color: var(--tyt-text-dim); }

/* 智能体流水线 */
.pipeline-status {
  font-size: 12px; font-weight: 600; border-radius: 999px; padding: 4px 12px;
}
.pipeline-status.idle { background: var(--tyt-bg-soft); color: var(--tyt-text-tertiary); }
.pipeline-status.running { background: var(--tyt-primary-soft); color: var(--tyt-primary-dark); animation: pulse 1.6s infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: .55; } }

.agents-list { display: flex; flex-direction: column; gap: 9px; }
.agent-item {
  border: 1px solid var(--tyt-border); border-radius: 11px; overflow: hidden;
  transition: border-color .2s;
}
.agent-item.running { border-color: rgba(99, 102, 241, .5); }
.agent-item.done { border-color: var(--tyt-border); }
.agent-head {
  display: flex; align-items: center; gap: 9px; padding: 10px 13px; cursor: pointer;
  background: var(--tyt-card-2); transition: background .15s;
}
.agent-head:hover { background: var(--tyt-primary-soft); }
.agent-icon { font-size: 17px; }
.agent-name { font-size: 13.5px; font-weight: 700; flex: 1; }
.agent-state { font-size: 11.5px; display: flex; align-items: center; gap: 5px; }
.agent-item.idle .agent-state { color: var(--tyt-text-tertiary); }
.agent-item.running .agent-state { color: var(--tyt-primary-dark); }
.agent-item.done .agent-state { color: var(--tyt-green); }
.agent-arrow { color: var(--tyt-text-tertiary); transition: transform .2s; }
.agent-arrow.open { transform: rotate(180deg); }
.mini-spinner {
  width: 11px; height: 11px; border-radius: 50%;
  border: 2px solid var(--tyt-primary-soft); border-top-color: var(--tyt-primary);
  animation: spin .8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.agent-body {
  padding: 10px 14px 12px; max-height: 260px; overflow-y: auto;
  border-top: 1px dashed var(--tyt-border-light); background: var(--tyt-card);
}
.agent-body p { margin: 0 0 6px; font-size: 12.5px; line-height: 1.85; color: var(--tyt-text); white-space: pre-wrap; }
.agent-body .md-h { font-weight: 700; color: var(--tyt-primary-dark); margin-top: 4px; }
.agent-body .md-li { color: var(--tyt-text-dim); }
.agent-waiting { font-size: 12.5px; color: var(--tyt-text-tertiary); }
.cursor { animation: blink 1s infinite; color: var(--tyt-primary); }
@keyframes blink { 0%, 100% { opacity: 0; } 50% { opacity: 1; } }

.disclaimer {
  margin: 14px 0 0; font-size: 11.5px; color: var(--tyt-text-tertiary);
  background: rgba(245, 158, 11, .08); border: 1px solid rgba(245, 158, 11, .25);
  border-radius: 8px; padding: 8px 12px; line-height: 1.7;
}

/* 综合分析报告 */
.report-card {
  margin-top: 16px;
  flex: 1;
  display: flex;
  flex-direction: column;
  border: 1px solid rgba(99, 102, 241, .35);
  animation: rpt-in .45s ease;
}
@keyframes rpt-in {
  from { opacity: 0; transform: translateY(14px); }
  to { opacity: 1; transform: translateY(0); }
}
.report-meta {
  font-size: 12px; color: var(--tyt-text-dim);
  background: var(--tyt-bg-soft); border-radius: 999px; padding: 4px 12px;
}
.report-body { flex: 1; min-height: 0; overflow-y: auto; padding-right: 4px; }
.report-body p {
  margin: 0 0 7px; font-size: 13px; line-height: 1.9;
  color: var(--tyt-text); white-space: pre-wrap;
}
.report-body .rpt-h {
  font-weight: 800; font-size: 14px; color: var(--tyt-primary-dark);
  margin-top: 13px; padding-left: 9px; border-left: 3px solid var(--tyt-primary);
}
.report-body .rpt-h:first-child { margin-top: 2px; }
.report-body .rpt-li { color: var(--tyt-text-dim); padding-left: 6px; }
.report-body .rpt-quote { color: var(--tyt-text-tertiary); font-size: 12px; }

@media (max-width: 1080px) {
  .stock-layout { grid-template-columns: 1fr; }
  .indices-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
