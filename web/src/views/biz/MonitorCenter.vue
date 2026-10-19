<template>
  <div class="page">
    <h1 class="page-title">商业监控</h1>
    <p class="page-sub">关注企业动态 · 风险事件流 · 日报周报推送</p>

    <div class="grid">
      <div class="tyt-card watch-card" ref="watchCardRef">
        <h3>监控列表（{{ watches.length }}）</h3>
        <el-alert
          v-if="!isPremium"
          class="expiry-tip"
          type="info"
          :closable="false"
          show-icon
          title="会员已过期"
          description="仍可查看曾关注的企业、历史事件与通知；升级高级会员后可新增 / 取消监控、调整订阅。"
        />
        <el-empty v-if="!watches.length" description="暂未监控任何企业" :image-size="60" />
        <div v-for="w in pagedWatches" :key="w.watch_id" class="w-item">
          <div class="w-info">
            <router-link :to="`/biz/companies/${w.company_id}`" class="w-name" :title="w.company_name">{{ w.company_name }}</router-link>
            <span class="w-date text-dim">关注于 {{ w.created_at }}</span>
          </div>
          <div class="w-latest" v-if="w.latest_event">
            <RiskTag :map="w.latest_event.event_type" />
            <span class="w-latest-title">{{ w.latest_event.title }}</span>
          </div>
          <el-tooltip v-if="!isPremium" content="升级高级会员后可取消监控" placement="top">
            <el-button size="small" type="danger" plain disabled>取消</el-button>
          </el-tooltip>
          <el-button v-else size="small" type="danger" plain @click="remove(w.watch_id)">取消</el-button>
        </div>
        <div class="pager" v-if="watchTotal > 6">
          <el-pagination small background layout="prev, pager, next" :total="watchTotal" :page-size="6"
                         :current-page="watchPage" @current-change="(p: number) => watchPage = p" />
        </div>
      </div>

      <div class="tyt-card event-card" ref="eventCardRef">
        <h3>风险事件流</h3>
        <div class="e-scroll">
          <el-empty v-if="!events.length" description="暂无事件，事件由周期扫描生成" :image-size="60" />
          <div v-for="e in events" :key="e.id" class="e-item">
            <div class="e-top">
              <RiskTag :map="e.event_type" />
              <RiskTag v-if="e.risk_level" :map="e.risk_level" />
              <span class="e-company">{{ e.company_name }}</span>
              <span class="e-date text-dim">{{ e.occurred_at }}</span>
            </div>
            <p class="e-title">{{ e.title }}</p>
            <p class="e-digest" v-if="e.digest">{{ e.digest }}</p>
          </div>
        </div>
      </div>
    </div>

    <div class="grid2">
      <div class="tyt-card sub-card">
        <h3>订阅设置</h3>
        <el-form label-position="left" label-width="90px" style="max-width: 380px">
          <el-form-item label="启用推送">
            <el-switch v-model="schedule.enabled" :disabled="!isPremium" @change="saveSchedule" />
          </el-form-item>
          <el-form-item label="频率">
            <el-radio-group v-model="schedule.freq" :disabled="!isPremium || !schedule.enabled" @change="saveSchedule">
              <el-radio value="daily">日报</el-radio>
              <el-radio value="weekly">周报</el-radio>
            </el-radio-group>
          </el-form-item>
        </el-form>
        <div class="sub-doc">
          <p class="doc-h">订阅后您将收到</p>
          <ul class="doc-list">
            <li><b>风险事件</b>：司法、经营、行政处罚等新增风险，按「高 / 中 / 低」级别生成事件提醒</li>
            <li><b>工商变更</b>：注册资本、经营范围、高管等工商信息变更，附「变更前 → 变更后」对比</li>
            <li><b>站内通知</b>：事件生成的同时实时推送站内消息，点击直达该企业详情页</li>
            <li><b>日报 / 周报</b>：开启推送后按频率定期汇总关注企业全部动态，以站内消息送达</li>
          </ul>
          <p class="doc-quote">提示：「启用推送」仅控制日报 / 周报的定期汇总投递；风险事件与站内通知始终实时生成。</p>
        </div>
      </div>

      <div class="tyt-card">
        <h3>站内通知（{{ unreadCount }} 未读）</h3>
        <el-empty v-if="!notifications.length" description="暂无通知" :image-size="60" />
        <div v-for="n in pagedNotifications" :key="n.id" class="n-item" :class="{ unread: !n.is_read }" @click="markRead(n)">
          <div class="n-top">
            <el-tag size="small" :type="n.type === 'report' ? 'success' : n.type === 'audit' ? 'info' : 'warning'">
              {{ { report: '报告', audit: '审核', monitor: '监控' }[n.type as string] || n.type }}
            </el-tag>
            <span class="n-title">{{ n.title }}</span>
          </div>
          <p class="n-content">{{ n.content }}</p>
        </div>
        <div class="pager" v-if="notifTotal > 6">
          <el-pagination small background layout="prev, pager, next" :total="notifTotal" :page-size="6"
                         :current-page="notifPage" @current-change="(p: number) => notifPage = p" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { monitorApi } from '@/api/modules'
import RiskTag from '@/components/RiskTag.vue'
import { usePager } from '@/composables/usePager'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const isPremium = computed(() => auth.isPremium)

const watches = ref<any[]>([])
const events = ref<any[]>([])
const notifications = ref<any[]>([])
const schedule = reactive({ enabled: true, freq: 'daily' })

const { page: watchPage, total: watchTotal, paged: pagedWatches } = usePager(watches, 6)
const { page: notifPage, total: notifTotal, paged: pagedNotifications } = usePager(notifications, 6)
// 风险事件流改为滑动浏览，不再分页

const unreadCount = computed(() => notifications.value.filter((n) => !n.is_read).length)

/* 事件流卡片高度与监控列表卡片保持一致：监控列表固定每页 6 条，
   右侧事件流整卡等高、内部滚动滑动浏览 */
const watchCardRef = ref<HTMLElement | null>(null)
const eventCardRef = ref<HTMLElement | null>(null)

async function syncEventCard() {
  await nextTick()
  if (!watchCardRef.value || !eventCardRef.value) return
  // 用小数像素精确同步，保证两卡视觉高度完全一致
  eventCardRef.value.style.height = `${watchCardRef.value.getBoundingClientRect().height}px`
}
watch(watchPage, () => syncEventCard())   // 翻页后保持等高

async function load() {
  const [w, e, n, s] = await Promise.all([
    monitorApi.watches(),
    monitorApi.events({ page_size: 50 }),
    monitorApi.notifications(),
    monitorApi.schedule(),
  ])
  watches.value = w.items || w || []
  events.value = e.items || []
  notifications.value = n.items || n || []
  schedule.enabled = !!s.enabled
  schedule.freq = s.freq || 'daily'
}

async function remove(id: number) {
  if (!isPremium.value) return
  await monitorApi.removeWatch(id)
  ElMessage.success('已取消监控')
  await load()
  syncEventCard()
}

async function saveSchedule() {
  if (!isPremium.value) return
  await monitorApi.updateSchedule({ enabled: schedule.enabled, freq: schedule.freq })
  ElMessage.success('订阅设置已保存')
}

async function markRead(n: any) {
  if (n.is_read || !isPremium.value) return
  await monitorApi.markRead(n.id)
  n.is_read = true
}

onMounted(async () => {
  await load()
  syncEventCard()
})
</script>

<style scoped>
.grid { display: grid; grid-template-columns: 1fr 1.4fr; gap: 16px; margin-bottom: 16px; align-items: start; }
.expiry-tip { margin-bottom: 12px; }
/* align-items:start：左卡保持自然高度（每页 6 条），不被右卡初始高度撑大，
   右卡高度由 JS 同步为左卡实际高度 */
.grid2 { display: grid; grid-template-columns: 1fr 1.4fr; gap: 16px; }
h3 { margin: 0 0 12px; font-size: 15px; }
.w-item { display: flex; align-items: center; gap: 12px; border-bottom: 1px dashed var(--tyt-border); padding: 10px 0; }
.w-item :deep(.el-button) { flex-shrink: 0; }
.pager { display: flex; justify-content: center; margin-top: 14px; }
.w-info { flex: 1 1 auto; min-width: 0; display: flex; flex-direction: column; gap: 3px; }
.w-name {
  font-weight: 600; font-size: 14px; display: block;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;   /* 名称始终横向单行，超长省略号，hover 显示全称 */
}
.w-date { font-size: 12px; }
.w-latest { display: flex; align-items: center; gap: 6px; font-size: 12px; max-width: 260px; flex: 0 1 auto; min-width: 0; }
.w-latest-title { color: var(--tyt-text-dim); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
/* 风险事件流：与监控列表卡片等高（JS 同步），内部滑动浏览；
   两卡最小高度 440px（滚动区约 370px），保证事件流最小窗口可完整展示 4 条事件 */
.event-card { box-sizing: border-box; display: flex; flex-direction: column; overflow: hidden; max-height: 760px; min-height: 440px; }
.watch-card { box-sizing: border-box; min-height: 440px; }   /* 同为 border-box，两卡下限渲染高度一致（含 padding/border） */
.e-scroll { flex: 1; min-height: 0; overflow-y: auto; padding-right: 4px; }
.e-item { border: 1px solid var(--tyt-border); border-radius: 10px; padding: 10px 12px; margin-bottom: 10px; }
.e-top { display: flex; align-items: center; gap: 8px; margin-bottom: 5px; flex-wrap: wrap; }
.e-company { font-size: 13px; font-weight: 600; }
.e-date { margin-left: auto; font-size: 12px; }
@media (max-width: 960px) {
  .grid, .grid2 { grid-template-columns: 1fr; }   /* 窄屏单列，保证公司名称横向完整显示 */
}
.e-title { margin: 0; font-size: 13.5px; }
.e-digest { margin: 4px 0 0; color: var(--tyt-text-dim); font-size: 12.5px; }
.n-item { border-bottom: 1px dashed var(--tyt-border); padding: 10px 4px; cursor: pointer; }
.n-item.unread .n-title { color: var(--tyt-primary); font-weight: 600; }
.n-top { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.n-title { font-size: 13.5px; }
.n-content { margin: 0; color: var(--tyt-text-dim); font-size: 12.5px; line-height: 1.7; }
/* 订阅讲解：markdown 风格排版（### 标题、- 列表、> 引用）。
   订阅卡为纵向 flex，讲解区 flex:1 并纵向均布内容，
   无论右侧站内通知卡多高都能填满卡片，保持两卡等高且留白不多 */
.sub-card { display: flex; flex-direction: column; }
.sub-doc { flex: 1; display: flex; flex-direction: column; margin-top: 12px; padding-top: 12px; border-top: 1px dashed var(--tyt-border); }
.doc-h { margin: 0 0 8px; font-size: 13px; font-weight: 700; color: var(--tyt-text); }
.doc-h::before { content: '###'; margin-right: 6px; color: var(--tyt-primary); font-size: 12px; }
.doc-list { flex: 1; margin: 0; padding: 0; list-style: none; display: flex; flex-direction: column; justify-content: space-evenly; gap: 7px; }
.doc-list li { position: relative; padding-left: 16px; font-size: 12.5px; line-height: 1.65; color: var(--tyt-text-dim); }
.doc-list li::before { content: '-'; position: absolute; left: 4px; top: 0; color: var(--tyt-primary); font-weight: 700; }
.doc-list b { color: var(--tyt-text); }
.doc-quote { margin: 10px 0 0; padding: 8px 10px; border-left: 3px solid var(--tyt-primary); background: rgba(99, 102, 241, .07); border-radius: 0 8px 8px 0; font-size: 12px; line-height: 1.6; color: var(--tyt-text-dim); }
.doc-quote::before { content: '> '; color: var(--tyt-primary); font-weight: 700; }
</style>
