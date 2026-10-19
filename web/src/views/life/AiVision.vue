<template>
  <div class="page vision-page">
    <h1 class="page-title">AI 识图</h1>
    <p class="page-sub">{{ visionSubText }}</p>

    <div class="vision-layout">
      <!-- 左侧：上传 + 历史 -->
      <div class="vision-left">
        <div class="tyt-card upload-card">
          <div class="card-head">
            <div class="card-title">图片识别</div>
            <span class="quota-badge">今日剩余 {{ quotaText }}</span>
          </div>
          <div class="upload-area" :class="{ dragging }" @click="pickFile"
               @dragover.prevent="dragging = true" @dragleave.prevent="dragging = false"
               @drop.prevent="onDrop">
            <template v-if="!previewUrl">
              <div class="upload-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                  <polyline points="17 8 12 3 7 8"></polyline>
                  <line x1="12" y1="3" x2="12" y2="15"></line>
                </svg>
              </div>
              <div class="upload-title">拖拽图片到此处</div>
              <div class="upload-desc">或点击选择图片，支持 JPG / PNG 格式</div>
            </template>
            <img v-else :src="previewUrl" class="upload-preview" alt="预览" />
            <div class="vision-model-tag">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="14" x2="23" y2="14"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="14" x2="4" y2="14"/></svg>
              <span>识别引擎：{{ usingBailianVision ? '百炼云端' : '本地 Ollama' }} ·
                <b>{{ visionModelName }}</b>（{{ usingBailianVision ? '图片上传至百炼处理' : '数据不出设备' }}）</span>
            </div>
            <div class="upload-actions">
              <el-button type="primary" class="upload-btn" :loading="analyzing" :disabled="!previewUrl" @click="recognize">
                {{ analyzing ? '正在识别…' : (result ? '重新识别' : '开始识别') }}
              </el-button>
            </div>
          </div>
          <input ref="fileInput" type="file" accept="image/*" style="display: none" @change="onFileChange" />
        </div>

        <div class="tyt-card history-card">
          <div class="card-head">
            <div class="card-title">识别历史</div>
            <span class="text-dim history-count" v-if="records.length">{{ records.length }} 条</span>
          </div>
          <div class="history-list">
            <el-empty v-if="!records.length" description="暂无识别记录" :image-size="64" />
            <div v-for="r in pagedRecords" :key="r.id" class="history-item"
                 :class="{ active: result?.id === r.id }" @click="loadRecord(r)">
              <div class="history-thumb" :style="{ background: thumbGradient(r.id) }">{{ (r.name || '图')[0] }}</div>
              <div class="history-info">
                <div class="history-name">{{ r.name || '识别完成' }}</div>
                <div class="history-time">{{ r.created_at }}</div>
              </div>
              <button class="history-del" title="删除" @click.stop="removeRecord(r.id)">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="3 6 5 6 21 6"></polyline>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
              </button>
            </div>
            <div class="pager" v-if="recordsTotal > 10">
              <el-pagination small background layout="prev, pager, next" :total="recordsTotal" :page-size="10"
                             :current-page="recordsPage" @current-change="(p: number) => recordsPage = p" />
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：识别结果 + 追问 -->
      <div class="tyt-card vision-right">
        <div class="card-head">
          <div class="card-title">识别结果</div>
          <el-button v-if="result" size="small" plain @click="resetAll">再识一张</el-button>
        </div>

        <div class="result-body">
          <!-- 识别中 -->
          <div v-if="analyzing" class="analyzing-box">
            <div class="spinner"></div>
            <div class="analyzing-step">{{ stepText }}</div>
            <img v-if="previewUrl" :src="previewUrl" class="analyzing-thumb" alt="识别中" />
          </div>

          <!-- 空状态 -->
          <template v-else-if="!result">
            <div class="result-img-empty">
              <svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="opacity:.35">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                <circle cx="8.5" cy="8.5" r="1.5"/>
                <polyline points="21 15 16 10 5 21"/>
              </svg>
              <div class="empty-text">等待识别</div>
              <div class="empty-desc">上传一张图片，AI 将为你智能识别并提供详细信息</div>
            </div>
          </template>

          <!-- 结果 -->
          <template v-else>
            <img :src="result.image_url" class="result-img" alt="识别图片" />
            <div class="result-name-row">
              <div class="result-name-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M9 11l3 3L22 4"></path>
                  <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path>
                </svg>
              </div>
              <div class="result-name">{{ result.name }}</div>
              <span v-if="result.category" class="result-category">{{ result.category }}</span>
            </div>

            <div class="confidence-section">
              <div class="confidence-label">
                <span>置信度</span>
                <span class="confidence-badge" :class="confLevel">{{ confText }}</span>
              </div>
              <div class="confidence-bar">
                <div class="confidence-fill" :style="{ width: confWidth }"></div>
              </div>
            </div>

            <div class="result-tags" v-if="result.tags?.length">
              <span v-for="t in result.tags" :key="t" class="tag-chip">{{ t }}</span>
            </div>

            <div class="key-elements" v-if="result.key_elements?.length">
              <div class="key-elements-title">关键元素</div>
              <ul class="key-elements-list">
                <li v-for="(e, i) in result.key_elements" :key="i">{{ e }}</li>
              </ul>
            </div>

            <div class="result-desc" v-if="result.description">{{ result.description }}</div>

            <!-- 追问对话 -->
            <div class="chat-section">
              <div class="chat-title">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2z"></path>
                  <path d="M8 12h.01M12 12h.01M16 12h.01"></path>
                </svg>
                AI 追问
              </div>
              <div class="chat-log" ref="chatLog">
                <el-empty v-if="!chat.length" description="对这张图片有什么想问的？例如：这是什么品种？" :image-size="56" />
                <div v-for="(m, i) in chat" :key="i" class="chat-msg" :class="m.role">
                  <div class="chat-bubble">{{ m.content }}</div>
                </div>
                <div v-if="asking" class="chat-msg assistant">
                  <div class="chat-bubble thinking">{{ answerBuf || '思考中…' }}<span class="cursor">▍</span></div>
                </div>
              </div>
              <div class="chat-input">
                <input v-model="question" type="text" placeholder="输入你的问题，按 Enter 发送…"
                       :disabled="asking" @keyup.enter="ask" />
                <button class="send-btn" :disabled="asking || !question.trim()" @click="ask">发送</button>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { visionApi, aiApi } from '@/api/modules'
import { ssePost } from '@/api/sse'
import { useAuthStore } from '@/stores/auth'
import { usePager } from '@/composables/usePager'

const auth = useAuthStore()

// 识图模型状态：跟随管理员「模型管理-百炼识图」开关与用户角色动态展示
const aiStatus = ref<any>({})
const usingBailianVision = computed(() => !!aiStatus.value.use_bailian_vision)
const visionModelName = computed(() => {
  const m = String(aiStatus.value.vision_model || 'minicpm-v4.6:latest')
  return m.startsWith('bailian:') ? m.slice('bailian:'.length) : m
})
const visionSubText = computed(() => usingBailianVision.value
  ? `百炼云端 · ${visionModelName.value} 识图，图片上传至百炼处理 —— 识别 + 多轮追问`
  : '本地 Ollama · MiniCPM-V 推理，图片不离开设备 —— 识别 + 多轮追问')

async function refreshStatus() {
  try {
    aiStatus.value = await aiApi.status()
  } catch { /* 权限不足时保持默认文案 */ }
}

const fileInput = ref<HTMLInputElement>()
const previewUrl = ref('')
const imageBase64 = ref('')
const analyzing = ref(false)
const dragging = ref(false)
const stepText = ref('正在识别图片…')
const result = ref<any>(null)
const records = ref<any[]>([])
const { page: recordsPage, total: recordsTotal, paged: pagedRecords } = usePager(records)
const chat = ref<any[]>([])
const question = ref('')
const asking = ref(false)
const answerBuf = ref('')
const chatLog = ref<HTMLElement>()

const quotaText = computed(() => {
  if (!auth.isLogged) return '—'
  const q = (auth.quotas as any)?.vision
  if (!q) return '—'
  if (q.limit < 0) return '不限'
  return `${Math.max(0, (q.remaining ?? (q.limit - q.used)))} / ${q.limit}`
})

const confText = computed(() => result.value ? `${Math.round(result.value.confidence * 100)}%` : '--')
const confWidth = computed(() => result.value ? `${Math.round(result.value.confidence * 100)}%` : '0%')
const confLevel = computed(() => {
  const c = result.value?.confidence ?? 0
  if (c >= 0.75) return 'high'
  if (c >= 0.5) return 'mid'
  return 'low'
})

function pickFile() {
  if (!analyzing.value) fileInput.value?.click()
}

function onFileChange(e: Event) {
  const f = (e.target as HTMLInputElement).files?.[0]
  if (f) readImage(f)
  ;(e.target as HTMLInputElement).value = ''
}

function onDrop(e: DragEvent) {
  dragging.value = false
  const f = e.dataTransfer?.files?.[0]
  if (f && f.type.startsWith('image/')) readImage(f)
}

function readImage(file: File) {
  if (file.size > 8 * 1024 * 1024) {
    ElMessage.warning('图片不能超过 8MB')
    return
  }
  const reader = new FileReader()
  reader.onload = () => {
    previewUrl.value = String(reader.result)
    imageBase64.value = String(reader.result)
    result.value = null
    chat.value = []
  }
  reader.readAsDataURL(file)
}

async function recognize() {
  if (!imageBase64.value || analyzing.value) return
  analyzing.value = true
  stepText.value = '正在识别图片…'
  const timer = setTimeout(() => { stepText.value = 'AI 正在分析图片内容，请稍候…' }, 4000)
  try {
    const data = await visionApi.recognize({ image_base64: imageBase64.value })
    // 识别接口返回 record_id，历史/详情接口返回 id；统一补上 id 供追问与历史高亮使用
    result.value = { ...data, id: data.record_id }
    chat.value = []
    await loadRecords()
    auth.fetchMe().catch(() => {})
    refreshStatus()
  } finally {
    clearTimeout(timer)
    analyzing.value = false
  }
}

function resetAll() {
  result.value = null
  previewUrl.value = ''
  imageBase64.value = ''
  chat.value = []
}

async function loadRecords() {
  try {
    records.value = await visionApi.records()
  } catch { /* 未登录等 */ }
}

async function loadRecord(r: any) {
  try {
    const detail = await visionApi.recordDetail(r.id)
    result.value = { ...detail, image_url: `data:image/jpeg;base64,${detail.image_b64}` }
    previewUrl.value = result.value.image_url
    imageBase64.value = ''
    chat.value = []
  } catch { /* ignore */ }
}

async function removeRecord(id: number) {
  await ElMessageBox.confirm('确定删除这条识别记录吗？', '删除确认', { type: 'warning' })
  await visionApi.deleteRecord(id)
  if (result.value?.id === id) resetAll()
  await loadRecords()
}

async function ask() {
  const text = question.value.trim()
  if (!text || asking.value || !result.value) return
  question.value = ''
  chat.value.push({ role: 'user', content: text })
  asking.value = true
  answerBuf.value = ''
  scrollChat()
  try {
    await ssePost('/vision/followup', { record_id: result.value.id, question: text }, (ev) => {
      if (ev.content) {
        answerBuf.value += ev.content
        scrollChat()
      }
    })
    chat.value.push({ role: 'assistant', content: answerBuf.value })
  } catch (e: any) {
    chat.value.push({ role: 'assistant', content: answerBuf.value || `生成失败：${e.message || e}` })
  } finally {
    asking.value = false
    answerBuf.value = ''
    scrollChat()
  }
}

function scrollChat() {
  nextTick(() => {
    if (chatLog.value) chatLog.value.scrollTop = chatLog.value.scrollHeight
  })
}

const gradients = [
  'linear-gradient(135deg, #6366f1, #8b5cf6)',
  'linear-gradient(135deg, #22d3ee, #0891b2)',
  'linear-gradient(135deg, #f59e0b, #f97316)',
  'linear-gradient(135deg, #10b981, #34d399)',
  'linear-gradient(135deg, #ef4444, #f97316)',
]
function thumbGradient(id: number) {
  return gradients[id % gradients.length]
}

onMounted(() => {
  loadRecords()
  refreshStatus()
})
</script>

<style scoped>
.vision-layout { display: grid; grid-template-columns: 360px 1fr; gap: 18px; align-items: start; }

.card-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.card-title { font-size: 15px; font-weight: 700; }
.quota-badge {
  font-size: 12px; padding: 4px 10px; border-radius: 999px; font-weight: 500;
  background: var(--tyt-primary-soft); color: var(--tyt-primary-dark);
}

/* 上传区 */
.upload-area {
  border: 2px dashed var(--tyt-border); border-radius: 12px;
  padding: 26px 18px; text-align: center; cursor: pointer;
  transition: all .2s; background: var(--tyt-card-2);
}
.upload-area:hover, .upload-area.dragging {
  border-color: var(--tyt-primary); background: var(--tyt-primary-soft);
}
.upload-icon { color: var(--tyt-primary); opacity: .8; margin-bottom: 10px; }
.upload-icon svg { width: 34px; height: 34px; }
.upload-title { font-size: 14.5px; font-weight: 600; margin-bottom: 4px; }
.upload-desc { font-size: 12.5px; color: var(--tyt-text-tertiary); }
.upload-preview { max-width: 100%; max-height: 220px; border-radius: 10px; object-fit: contain; margin-bottom: 12px; }
.vision-model-tag {
  display: inline-flex; align-items: center; gap: 6px;
  font-size: 11.5px; color: var(--tyt-text-dim);
  background: var(--tyt-bg-soft); border: 1px solid var(--tyt-border);
  border-radius: 999px; padding: 5px 12px; margin-bottom: 14px;
}
.upload-actions { display: flex; justify-content: center; }
.upload-btn {
  background: var(--tyt-gradient-brand); border: none; color: #fff; font-weight: 600;
  box-shadow: 0 4px 16px -4px rgba(99, 102, 241, .45);
}

/* 历史 */
.history-card { margin-top: 16px; }
.history-count { font-size: 12px; }
.history-list { max-height: 320px; overflow-y: auto; display: flex; flex-direction: column; gap: 6px; }
.pager { display: flex; justify-content: center; margin-top: 8px; }
.history-item {
  display: flex; align-items: center; gap: 12px; padding: 9px 10px;
  border-radius: 10px; cursor: pointer; transition: background .15s;
  border: 1px solid transparent;
}
.history-item:hover { background: var(--tyt-bg-soft); }
.history-item.active { background: var(--tyt-primary-soft); border-color: rgba(99, 102, 241, .35); }
.history-thumb {
  width: 40px; height: 40px; border-radius: 9px; flex-shrink: 0;
  color: #fff; font-size: 16px; font-weight: 600;
  display: flex; align-items: center; justify-content: center;
}
.history-info { flex: 1; min-width: 0; }
.history-name { font-size: 13.5px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.history-time { font-size: 11.5px; color: var(--tyt-text-tertiary); }
.history-del {
  border: none; background: transparent; color: var(--tyt-text-tertiary);
  padding: 6px; border-radius: 7px; cursor: pointer; display: flex; transition: all .15s;
}
.history-del:hover { background: rgba(239, 68, 68, .1); color: var(--tyt-red); }

/* 右侧结果 */
.vision-right { min-height: 560px; }
.result-body { display: flex; flex-direction: column; gap: 16px; }

.analyzing-box { display: flex; flex-direction: column; align-items: center; padding: 48px 0; gap: 14px; }
.spinner {
  width: 40px; height: 40px; border-radius: 50%;
  border: 3px solid var(--tyt-primary-soft); border-top-color: var(--tyt-primary);
  animation: spin 0.9s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.analyzing-step { font-size: 14.5px; font-weight: 500; }
.analyzing-thumb { max-width: 100%; max-height: 240px; border-radius: 10px; object-fit: contain; }

.result-img-empty { text-align: center; padding: 64px 0 48px; color: var(--tyt-text-dim); }
.empty-text { font-size: 15px; font-weight: 600; margin-top: 12px; }
.empty-desc { font-size: 12.5px; color: var(--tyt-text-tertiary); margin-top: 4px; }

.result-img { width: 100%; max-height: 320px; object-fit: contain; border-radius: 10px; background: var(--tyt-bg-soft); }

.result-name-row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.result-name-icon {
  width: 30px; height: 30px; border-radius: 9px; flex-shrink: 0;
  background: var(--tyt-gradient-brand); color: #fff;
  display: flex; align-items: center; justify-content: center;
}
.result-name { font-size: 19px; font-weight: 700; letter-spacing: -0.01em; }
.result-category {
  font-size: 12px; padding: 3px 10px; border-radius: 999px;
  background: var(--tyt-primary-soft); color: var(--tyt-primary-dark); font-weight: 500;
}

.confidence-label { display: flex; justify-content: space-between; align-items: center; font-size: 13px; margin-bottom: 7px; color: var(--tyt-text-dim); }
.confidence-badge { font-weight: 700; font-size: 14px; }
.confidence-badge.high { color: var(--tyt-green); }
.confidence-badge.mid { color: var(--tyt-amber); }
.confidence-badge.low { color: var(--tyt-red); }
.confidence-bar { height: 8px; border-radius: 999px; background: var(--tyt-bg-soft); overflow: hidden; }
.confidence-fill { height: 100%; border-radius: 999px; background: var(--tyt-gradient-brand); transition: width .6s var(--tyt-ease); }

.result-tags { display: flex; flex-wrap: wrap; gap: 8px; }
.tag-chip {
  font-size: 12px; padding: 4px 12px; border-radius: 999px;
  background: var(--tyt-primary-soft); color: var(--tyt-primary-dark);
  border: 1px solid rgba(99, 102, 241, .25);
}

.key-elements-title { font-size: 13px; font-weight: 600; margin-bottom: 8px; color: var(--tyt-text-dim); }
.key-elements-list { margin: 0; padding-left: 18px; font-size: 13px; line-height: 2; color: var(--tyt-text); }

.result-desc {
  font-size: 13.5px; line-height: 1.9; color: var(--tyt-text-dim);
  background: var(--tyt-card-2); border: 1px solid var(--tyt-border-light);
  border-radius: 10px; padding: 12px 14px;
}

/* 追问 */
.chat-section { border-top: 1px solid var(--tyt-border-light); padding-top: 14px; }
.chat-title {
  display: flex; align-items: center; gap: 6px;
  font-size: 13.5px; font-weight: 600; margin-bottom: 10px; color: var(--tyt-primary-dark);
}
.chat-log { height: 220px; overflow-y: auto; padding: 4px 2px; display: flex; flex-direction: column; gap: 10px; }
.chat-msg { display: flex; }
.chat-msg.user { justify-content: flex-end; }
.chat-bubble {
  max-width: 80%; border-radius: 12px; padding: 9px 13px;
  font-size: 13px; line-height: 1.8; white-space: pre-wrap; word-break: break-word;
}
.chat-msg.user .chat-bubble { background: var(--tyt-gradient-brand); color: #fff; }
.chat-msg.assistant .chat-bubble { background: var(--tyt-card-2); border: 1px solid var(--tyt-border); }
.chat-bubble.thinking { color: var(--tyt-text-dim); }
.cursor { animation: blink 1s infinite; }
@keyframes blink { 0%, 100% { opacity: 0; } 50% { opacity: 1; } }

.chat-input { display: flex; gap: 8px; margin-top: 12px; }
.chat-input input {
  flex: 1; border: 1px solid var(--tyt-border); border-radius: 9px;
  padding: 9px 13px; font-size: 13px; outline: none; background: var(--tyt-card);
  transition: border-color .2s, box-shadow .2s;
}
.chat-input input:focus { border-color: var(--tyt-primary); box-shadow: 0 0 0 3px var(--tyt-primary-soft); }
.send-btn {
  border: none; border-radius: 9px; padding: 0 18px; font-size: 13px; font-weight: 600;
  background: var(--tyt-gradient-brand); color: #fff; cursor: pointer;
  transition: opacity .2s;
}
.send-btn:disabled { opacity: .5; cursor: not-allowed; }
.send-btn:not(:disabled):hover { opacity: .92; }

@media (max-width: 960px) {
  .vision-layout { grid-template-columns: 1fr; }
}
</style>
