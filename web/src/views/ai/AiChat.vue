<template>
  <div class="page ai-page">
    <div class="ai-layout">
      <!-- 左侧：历史问答（当前用户专属） -->
      <aside class="tyt-card history-panel">
        <div class="history-head">
          <span class="history-title">🕘 历史问答</span>
          <el-button v-if="history.length" size="small" text type="danger" @click="confirmClear">清空</el-button>
        </div>
        <p class="history-owner text-dim">{{ auth.user?.nickname || '当前用户' }} 的问答记录</p>
        <el-scrollbar class="history-scroll">
          <el-empty v-if="!history.length" description="暂无历史记录" :image-size="60" />
          <div v-for="h in pagedHistory" :key="h.id" class="history-item" :class="{ active: activeId === h.id }"
               @click="showHistory(h)">
            <div class="h-q">{{ h.question }}</div>
            <div class="h-meta">
              <span class="text-dim">{{ h.created_at }}</span>
              <span class="h-del" title="删除该条" @click.stop="removeOne(h)">🗑</span>
            </div>
          </div>
          <div class="pager" v-if="historyTotal > 10">
            <el-pagination small background layout="prev, pager, next" :total="historyTotal" :page-size="10"
                           :current-page="historyPage" @current-change="(p: number) => historyPage = p" />
          </div>
        </el-scrollbar>
      </aside>

      <!-- 右侧：聊天区 -->
      <div class="tyt-card chat-panel">
        <div class="chat-head">
          <h1 class="page-title" style="font-size: 18px">AI 问答助手</h1>
          <div class="ai-status">
            <el-tag :type="status.ollama ? 'success' : 'danger'" size="small" effect="dark">
              {{ status.ollama ? '模型在线' : '模型离线' }}
            </el-tag>
            <span class="text-dim mono">{{ status.chat_model }}</span>
            <el-tag v-if="status.rerank" type="success" size="small" effect="plain">Rerank</el-tag>
            <el-button v-if="messages.length" size="small" text @click="newChat">✚ 新对话</el-button>
          </div>
        </div>

        <div class="chat-body" ref="chatBody">
          <el-empty v-if="!messages.length" description="问点什么吧，例如：什么是股权穿透？">
            <div class="examples">
              <el-button v-for="q in examples" :key="q" size="small" plain @click="ask(q)">{{ q }}</el-button>
            </div>
          </el-empty>
          <div v-for="(m, i) in messages" :key="i" class="msg" :class="m.role">
            <div class="bubble">
              <template v-if="m.role === 'user'">{{ m.content }}</template>
              <template v-else>
                <div class="answer md-body" v-html="renderMd(m.content)"></div>
                <div v-if="m.references?.length" class="refs">
                  <span class="refs-title">参考来源（{{ refsTitle(m) }}）：</span>
                  <template v-for="(r, k) in m.references" :key="k">
                    <a v-if="r && r.url" :href="r.url" target="_blank" rel="noopener noreferrer"
                       class="ref-chip ref-link" :title="`${r.source} · ${r.url}`">🔗 {{ r.title }}<span v-if="r.similarity != null" class="ref-score">{{ r.similarity.toFixed(2) }}</span></a>
                    <span v-else class="ref-chip">{{ typeof r === 'object' ? r.title : r }}<span v-if="typeof r === 'object' && r.similarity != null" class="ref-score">{{ r.similarity.toFixed(2) }}</span></span>
                  </template>
                </div>
                <div class="msg-meta text-dim">{{ m.model }} · {{ m.answered_at }}</div>
              </template>
            </div>
          </div>
          <div v-if="thinking" class="msg assistant">
            <div class="bubble thinking">思考中<span class="dots"><i></i><i></i><i></i></span></div>
          </div>
        </div>

        <div class="chat-input">
          <el-input v-model="question" placeholder="输入问题（2-500 字）" size="large" :disabled="thinking"
                    @keyup.enter="ask()" />
          <el-button type="primary" size="large" :loading="thinking" @click="ask()"
                     style="background:linear-gradient(135deg,#6366f1,#8b5cf6);border:none">发送</el-button>
        </div>
        <p class="quota text-dim" v-if="quota">今日剩余 AI 问答次数：{{ quotaText }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { aiApi } from '@/api/modules'
import { useAuthStore } from '@/stores/auth'
import { usePager } from '@/composables/usePager'

marked.setOptions({ gfm: true, breaks: true })

// 助手回答按 Markdown 渲染（DOMPurify 消毒防 XSS）
function renderMd(text: string): string {
  if (!text) return ''
  return DOMPurify.sanitize(marked.parse(text) as string)
}

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const status = ref<any>({})
const messages = ref<any[]>([])
const question = ref('')
const thinking = ref(false)
const chatBody = ref<HTMLElement>()
const quota = computed(() => auth.quotas?.ai_chat)

const history = ref<any[]>([])
const activeId = ref<number | null>(null)
const { page: historyPage, total: historyTotal, paged: pagedHistory } = usePager(history)

const examples = [
  '什么是企业尽职调查？',
  '股权穿透是什么意思？',
  '如何识别预付卡消费风险？',
  '失信被执行人和被执行人的区别？',
]

const quotaText = computed(() => {
  if (!quota.value) return '--'
  if (quota.value.limit < 0) return '不限'
  return `${quota.value.remaining ?? Math.max(0, quota.value.limit - quota.value.used)} / ${quota.value.limit}`
})

async function loadHistory() {
  try {
    const data = await aiApi.history()
    history.value = data.items || []
  } catch { /* 权限不足时忽略 */ }
}

function newChat() {
  messages.value = []
  activeId.value = null
}

// 旧历史记录无阈值字段时保持原文案
function refsTitle(m: any): string {
  const n = m.references?.length || 0
  return m.similarity_threshold != null
    ? `相似度 ≥ ${m.similarity_threshold} · ${n} 条`
    : `Top${n} 相似检索`
}

function showHistory(h: any) {
  activeId.value = h.id
  messages.value = [
    { role: 'user', content: h.question },
    {
      role: 'assistant', content: h.answer, references: h.references,
      model: h.model, answered_at: h.created_at,
    },
  ]
  scrollBottom()
}

async function removeOne(h: any) {
  await aiApi.removeHistory(h.id)
  history.value = history.value.filter((x) => x.id !== h.id)
  if (activeId.value === h.id) newChat()
  ElMessage.success('已删除该条记录')
}

function confirmClear() {
  ElMessageBox.confirm('将清空当前账号的全部历史问答记录，且不可恢复。', '清空历史', {
    confirmButtonText: '清空',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(async () => {
    await aiApi.clearHistory()
    history.value = []
    newChat()
    ElMessage.success('历史记录已清空')
  }).catch(() => {})
}

async function ask(q?: string) {
  const text = (q || question.value).trim()
  if (text.length < 2) return ElMessage.warning('问题至少 2 个字')
  if (thinking.value) return
  activeId.value = null
  messages.value.push({ role: 'user', content: text })
  question.value = ''
  thinking.value = true
  scrollBottom()
  try {
    // 异步问答：提交即返回 task_id，回答在后台生成，前端轮询获取
    const { task_id } = await aiApi.chat(text)
    await pollTask(task_id)
  } catch {
    /* 提交失败已由拦截器提示 */
  } finally {
    thinking.value = false
    scrollBottom()
  }
}

let pollTimer: number | undefined

function pollTask(taskId: number): Promise<void> {
  return new Promise((resolve, reject) => {
    const poll = async () => {
      try {
        const data = await aiApi.task(taskId)
        if (data.status === 'done') {
          messages.value.push({
            role: 'assistant', content: data.answer, references: data.references,
            model: data.model, answered_at: data.answered_at,
            similarity_threshold: data.similarity_threshold,
          })
          auth.fetchMe().catch(() => {})
          loadHistory()
          refreshStatus()
          resolve()
        } else if (data.status === 'failed') {
          messages.value.push({
            role: 'assistant', content: `回答生成失败：${data.error || '服务暂时不可用，请稍后重试'}`,
          })
          resolve()
        } else {
          pollTimer = window.setTimeout(poll, 1500)
        }
      } catch (e) {
        reject(e)
      }
    }
    poll()
  })
}

function scrollBottom() {
  nextTick(() => {
    if (chatBody.value) chatBody.value.scrollTop = chatBody.value.scrollHeight
  })
}

// 刷新模型状态徽标：管理员切换百炼开关后，模型名称随之更新
async function refreshStatus() {
  try {
    status.value = await aiApi.status()
  } catch { /* 权限不足时忽略 */ }
}

onMounted(async () => {
  loadHistory()
  await refreshStatus()
  // 来自爬虫实时流的跳转：自动带入问题并发起提问
  const q = typeof route.query.q === 'string' ? route.query.q.trim() : ''
  if (q.length >= 2) {
    router.replace({ query: {} })
    ask(q)
  }
})

// 离开页面停止轮询（后台任务继续执行，完成后答案会进入历史记录，回来不丢）
onUnmounted(() => {
  if (pollTimer) {
    clearTimeout(pollTimer)
    pollTimer = undefined
  }
})
</script>

<style scoped>
.ai-page { max-width: 1240px; }
.ai-layout { display: grid; grid-template-columns: 280px 1fr; gap: 16px; align-items: start; }
@media (max-width: 900px) { .ai-layout { grid-template-columns: 1fr; } }

/* 左侧历史栏 */
.history-panel { padding: 16px; position: sticky; top: 76px; }
.history-head { display: flex; align-items: center; justify-content: space-between; }
.history-title { font-weight: 700; font-size: 15px; }
.history-owner { font-size: 11.5px; margin: 6px 0 10px; padding-bottom: 8px;
  border-bottom: 1px dashed var(--tyt-border); }
.history-scroll { height: 520px; }
.pager { display: flex; justify-content: center; margin-top: 8px; }
.history-item {
  border: 1px solid var(--tyt-border); border-radius: 10px; padding: 9px 11px;
  margin-bottom: 8px; cursor: pointer; transition: all .18s;
  background: var(--tyt-card-2);
}
.history-item:hover { border-color: var(--tyt-primary); transform: translateX(2px); }
.history-item.active {
  border-color: var(--tyt-primary); background: var(--tyt-primary-soft);
  box-shadow: 0 2px 10px -4px rgba(99, 102, 241, .45);
}
.h-q {
  font-size: 12.5px; line-height: 1.5; color: var(--tyt-text);
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  overflow: hidden; font-weight: 600;
}
.h-meta { display: flex; justify-content: space-between; align-items: center; margin-top: 6px; font-size: 11px; }
.h-del { opacity: 0; transition: opacity .15s; cursor: pointer; padding: 2px 4px; border-radius: 4px; }
.history-item:hover .h-del { opacity: .75; }
.h-del:hover { opacity: 1; background: rgba(239, 68, 68, .12); }

/* 右侧聊天区 */
.chat-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; flex-wrap: wrap; gap: 8px; }
.ai-status { display: flex; align-items: center; gap: 8px; font-size: 12px; }
.chat-body { height: 480px; overflow-y: auto; padding: 6px 4px; }
.examples { display: flex; flex-direction: column; gap: 8px; margin-top: 8px; }
.msg { display: flex; margin-bottom: 14px; }
.msg.user { justify-content: flex-end; }
.bubble { max-width: 78%; border-radius: 12px; padding: 10px 14px; font-size: 13.5px; line-height: 1.9; }
.msg.user .bubble { background: linear-gradient(135deg,#6366f1,#8b5cf6); color: #fff; }
.msg.assistant .bubble { background: var(--tyt-card-2); border: 1px solid var(--tyt-border); }
.answer { margin: 0; }
/* Markdown 渲染样式（v-html 内容需用 :deep 穿透 scoped） */
.answer.md-body { font-size: 13.5px; }
.answer.md-body :deep(h1), .answer.md-body :deep(h2), .answer.md-body :deep(h3), .answer.md-body :deep(h4) {
  margin: 10px 0 6px; font-weight: 700; line-height: 1.5;
}
.answer.md-body :deep(h1) { font-size: 15px; }
.answer.md-body :deep(h2) { font-size: 14px; }
.answer.md-body :deep(h3) { font-size: 13.5px; }
.answer.md-body :deep(p) { margin: 0 0 6px; }
.answer.md-body :deep(p:last-child) { margin-bottom: 0; }
.answer.md-body :deep(ul), .answer.md-body :deep(ol) { margin: 4px 0 8px; padding-left: 20px; }
.answer.md-body :deep(li) { margin: 2px 0; }
.answer.md-body :deep(strong) { font-weight: 700; color: var(--tyt-primary-dark, #4f46e5); }
.answer.md-body :deep(code) {
  background: rgba(99, 102, 241, .12); border-radius: 4px; padding: 1px 5px;
  font-family: Consolas, monospace; font-size: 12px;
}
.answer.md-body :deep(pre) {
  background: rgba(15, 23, 42, .05); border: 1px solid var(--tyt-border);
  border-radius: 8px; padding: 10px 12px; overflow-x: auto; margin: 6px 0;
}
.answer.md-body :deep(pre code) { background: none; padding: 0; font-size: 12px; }
.answer.md-body :deep(blockquote) {
  border-left: 3px solid var(--tyt-primary); background: var(--tyt-primary-soft);
  border-radius: 0 8px 8px 0; margin: 6px 0; padding: 4px 12px; color: var(--tyt-text-dim);
}
.answer.md-body :deep(table) { border-collapse: collapse; margin: 6px 0; max-width: 100%; }
.answer.md-body :deep(th), .answer.md-body :deep(td) {
  border: 1px solid var(--tyt-border); padding: 4px 10px; font-size: 12.5px; line-height: 1.6;
}
.answer.md-body :deep(th) { background: var(--tyt-primary-soft); font-weight: 600; }
.answer.md-body :deep(a) { color: var(--tyt-primary); text-decoration: none; }
.answer.md-body :deep(a:hover) { text-decoration: underline; }
.answer.md-body :deep(hr) { border: none; border-top: 1px dashed var(--tyt-border); margin: 8px 0; }
.refs { margin-top: 8px; display: flex; gap: 6px; flex-wrap: wrap; align-items: center; }
.refs-title { font-size: 12px; color: var(--tyt-text-dim); }
.ref-chip { font-size: 11.5px; background: var(--tyt-primary-soft); border: 1px solid rgba(99,102,241,.3);
  color: var(--tyt-primary-dark); border-radius: 6px; padding: 1px 8px; }
.ref-link { text-decoration: none; cursor: pointer; transition: all .18s; max-width: 260px;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; display: inline-block; vertical-align: bottom; }
.ref-link:hover { background: var(--tyt-gradient-brand); color: #fff; border-color: transparent; }
.ref-score { font-size: 10px; font-weight: 600; font-style: normal; color: rgba(99,102,241,.95);
  background: rgba(99,102,241,.14); border-radius: 4px; padding: 0 4px; margin-left: 6px; }
.ref-link:hover .ref-score { color: #fff; background: rgba(255,255,255,.22); }
.msg-meta { font-size: 11px; margin-top: 6px; }
.thinking { color: var(--tyt-text-dim); }
.dots i { display: inline-block; width: 5px; height: 5px; border-radius: 50%; background: var(--tyt-text-dim);
  margin-left: 4px; animation: blink 1.2s infinite; }
.dots i:nth-child(2) { animation-delay: .2s; }
.dots i:nth-child(3) { animation-delay: .4s; }
@keyframes blink { 0%, 80%, 100% { opacity: .2; } 40% { opacity: 1; } }
.chat-input { display: flex; gap: 10px; margin-top: 12px; }
.quota { font-size: 12px; margin: 10px 0 0; text-align: right; }
</style>
