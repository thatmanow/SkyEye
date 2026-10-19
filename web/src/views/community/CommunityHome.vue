<template>
  <div class="page">
    <div class="head-row">
      <div>
        <h1 class="page-title">生活圈</h1>
        <p class="page-sub" style="margin-bottom: 0">匿名分享避坑与推荐经验 · 全部先审后发</p>
      </div>
      <el-button type="primary" @click="dialog = true"
                 style="background:linear-gradient(135deg,#6366f1,#8b5cf6);border:none">
        ✏ 发布帖子
      </el-button>
    </div>

    <div class="filter-row">
      <div class="filter-main">
        <el-radio-group v-model="category" @change="load(1)">
          <el-radio-button value="">全部</el-radio-button>
          <el-radio-button value="avoid_pit">避雷</el-radio-button>
          <el-radio-button value="recommend">推荐</el-radio-button>
        </el-radio-group>
        <el-select v-model="topic" style="width: 150px" @change="load(1)">
          <el-option label="全部分类" value="" />
          <el-option v-for="t in topics" :key="t" :label="t" :value="t" />
        </el-select>
        <el-input v-model="keyword" placeholder="搜索标题 / 内容关键词" style="width: 240px" clearable
                  @keyup.enter="load(1)" @clear="load(1)" />
        <el-button type="primary" @click="load(1)"
                   style="background:linear-gradient(135deg,#6366f1,#8b5cf6);border:none">搜索</el-button>
      </div>
      <span class="topic-hint text-dim">分类由系统按帖子内容自动识别</span>
    </div>

    <el-empty v-if="!loading && !items.length" description="暂无匹配帖子，换个筛选条件试试" />
    <div class="p-list">
      <div v-for="p in items" :key="p.id" class="tyt-card p-card" @click="goDetail(p.id)">
        <div class="p-top">
          <el-tag :type="p.category === 'avoid_pit' ? 'danger' : 'success'" size="small" effect="dark">
            {{ p.category === 'avoid_pit' ? '避雷' : '推荐' }}
          </el-tag>
          <el-tag v-if="p.topic" size="small" effect="plain" class="p-topic">{{ p.topic }}</el-tag>
          <span class="p-author">{{ p.author_nickname }}</span>
          <span class="p-date">{{ p.created_at }}</span>
        </div>
        <h3 class="p-title">{{ p.title }}</h3>
        <p class="p-content">{{ p.content }}</p>
        <div v-if="p.images?.length" class="p-imgs" @click.stop>
          <el-image v-for="(img, i) in p.images.slice(0, 3)" :key="img" class="p-img"
                    :src="img" fit="cover" :alt="`帖子配图${i + 1}`" :preview-src-list="p.images"
                    :initial-index="i" :preview-teleported="true" loading="lazy" />
          <span v-if="p.images.length > 3" class="p-img-more">共 {{ p.images.length }} 张</span>
        </div>
        <div class="p-foot">
          <span>👍 {{ p.like_count }}</span>
          <span>💬 {{ p.comment_count }}</span>
        </div>
      </div>
    </div>

    <div class="pager" v-if="total > pageSize">
      <el-pagination background layout="prev, pager, next" :total="total" :page-size="pageSize"
                     :current-page="page" @current-change="load" />
    </div>

    <el-dialog v-model="dialog" title="发布帖子" width="560px">
      <el-alert type="info" :closable="false" style="margin-bottom: 14px">
        帖子提交后进入<strong>先审后发</strong>队列，审核通过后对外可见。禁止造谣诽谤与隐私猎取。
      </el-alert>
      <el-form label-position="top">
        <el-form-item label="类型">
          <el-radio-group v-model="form.category">
            <el-radio value="avoid_pit">避雷分享</el-radio>
            <el-radio value="recommend">好物推荐</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="标题">
          <el-input v-model="form.title" maxlength="100" show-word-limit placeholder="一句话说清主题" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="form.content" type="textarea" :rows="5" maxlength="3000" show-word-limit
                    placeholder="分享你的经历与建议（10 字以上）" />
        </el-form-item>
        <el-form-item label="配图（最多 6 张，可选）">
          <div class="upload-area">
            <div v-for="(img, i) in formImages" :key="img.url" class="up-item">
              <img :src="img.url" alt="帖子配图预览" />
              <span v-if="img.uploading" class="up-mask">上传中…</span>
              <button type="button" class="up-del" title="移除" @click="removeImage(i)">×</button>
            </div>
            <button v-if="formImages.length < 6" type="button" class="up-add" :disabled="uploadingCount > 0"
                    title="添加图片" @click="pickImages">＋</button>
            <input ref="fileInput" type="file" accept="image/jpeg,image/png,image/webp,image/gif"
                   multiple class="sr-file-input" @change="onFilesChosen" />
          </div>
          <div class="upload-tip">支持 jpg / png / webp / gif，单张不超过 8MB</div>
        </el-form-item>
        <div class="detect-hint" v-if="form.title.trim() || form.content.trim()">
          🏷 系统将自动识别分类：<b>{{ detectedTopic }}</b>
        </div>
        <el-form-item label="匿名发布">
          <el-switch v-model="form.is_anonymous" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submit"
                   style="background:linear-gradient(135deg,#6366f1,#8b5cf6);border:none">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { communityApi } from '@/api/modules'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

const items = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 10
const loading = ref(false)
const category = ref('')
const topic = ref('')
const keyword = ref('')
const topics = ref<string[]>([])

const dialog = ref(false)
const submitting = ref(false)
const form = reactive({ category: 'avoid_pit', title: '', content: '', is_anonymous: true })
const topicRules = ref<Record<string, string[]>>({})

/* ---- 帖子配图：本地预览 + 上传 ---- */
const formImages = ref<{ url: string; uploading: boolean }[]>([])
const fileInput = ref<HTMLInputElement | null>(null)
const uploadingCount = computed(() => formImages.value.filter((i) => i.uploading).length)

function pickImages() {
  fileInput.value?.click()
}

async function onFilesChosen(e: Event) {
  const input = e.target as HTMLInputElement
  const files = Array.from(input.files || [])
  input.value = ''
  const room = 6 - formImages.value.length
  if (!room) return ElMessage.warning('最多上传 6 张图片')
  const picked = files.slice(0, room)
  if (files.length > room) ElMessage.warning(`最多 6 张，已忽略多余 ${files.length - room} 张`)
  if (!picked.length) return
  if (!auth.isLogged) return ElMessage.warning('请先登录后再上传图片')
  for (const f of picked) {
    if (f.size > 8 * 1024 * 1024) {
      ElMessage.warning(`「${f.name}」超过 8MB，已跳过`)
      continue
    }
    const localUrl = URL.createObjectURL(f)
    const item = { url: localUrl, uploading: true }
    formImages.value.push(item)
    communityApi.uploadImage(f)
      .then((d: any) => {
        item.url = d.url
        item.uploading = false
      })
      .catch(() => {
        formImages.value = formImages.value.filter((x) => x !== item)
        ElMessage.error(`「${f.name}」上传失败`)
      })
      .finally(() => URL.revokeObjectURL(localUrl))
  }
}

function removeImage(i: number) {
  const [removed] = formImages.value.splice(i, 1)
  if (removed?.url.startsWith('blob:')) URL.revokeObjectURL(removed.url)
}

// 发帖实时预览：用服务端下发的关键词规则本地计算（最终入库以服务端识别为准）
const detectedTopic = computed(() => {
  const text = `${form.title} ${form.content}`
  let best = '其他', bestHits = 0
  for (const [tp, words] of Object.entries(topicRules.value)) {
    const hits = words.filter((w) => w && text.includes(w)).length
    if (hits > bestHits) { best = tp; bestHits = hits }
  }
  return best
})

async function load(p = 1) {
  page.value = p
  loading.value = true
  try {
    const data = await communityApi.listPosts({
      page: p, page_size: pageSize,
      category: category.value || undefined,
      topic: topic.value || undefined,
      keyword: keyword.value.trim() || undefined,
    })
    items.value = data.items || []
    total.value = data.total || 0
    if (data.topics?.length) topics.value = data.topics
  } finally {
    loading.value = false
  }
}

function goDetail(id: number) {
  router.push(`/community/${id}`)
}

async function submit() {
  if (!auth.isLogged) return ElMessage.warning('请先登录')
  if (form.title.trim().length < 2) return ElMessage.warning('标题至少 2 个字')
  if (form.content.trim().length < 10) return ElMessage.warning('内容至少 10 个字')
  if (uploadingCount.value > 0) return ElMessage.warning('图片还在上传中，请稍候')
  const images = formImages.value.map((i) => i.url)
  submitting.value = true
  try {
    await communityApi.createPost({
      category: form.category, title: form.title.trim(),
      content: form.content.trim(), is_anonymous: form.is_anonymous, images,
    })
    ElMessage.success('已提交，审核通过后对外可见')
    dialog.value = false
    form.title = ''
    form.content = ''
    formImages.value = []
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  load()
  try {
    const t = await communityApi.getTopics()
    topicRules.value = t.rules || {}
  } catch { /* 预览降级为"其他" */ }
})
</script>

<style scoped>
.head-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; }
.filter-row { margin-bottom: 16px; display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
.filter-main { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.topic-hint { font-size: 12px; }
.p-topic { background: rgba(99, 102, 241, .1); border-color: rgba(99, 102, 241, .3); color: var(--tyt-primary-dark); }
.detect-hint {
  margin: -4px 0 12px; padding: 8px 12px; border-radius: 8px; font-size: 12.5px;
  background: rgba(99, 102, 241, .08); border: 1px dashed rgba(99, 102, 241, .35); color: var(--tyt-primary-dark);
}
.p-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); gap: 14px; }
.p-card { cursor: pointer; transition: border-color .2s; }
.p-card:hover { border-color: rgba(99,102,241,.45); }
.p-top { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; font-size: 12.5px; color: var(--tyt-text-dim); }
.p-title { margin: 0 0 6px; font-size: 15.5px; }
.p-content { margin: 0 0 10px; color: var(--tyt-text-dim); font-size: 13px; line-height: 1.8;
  display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.p-foot { display: flex; gap: 16px; font-size: 12.5px; color: var(--tyt-text-dim); }
.p-imgs { display: flex; align-items: center; gap: 6px; margin: 0 0 10px; }
.p-img { width: 78px; height: 78px; border-radius: 8px; overflow: hidden; cursor: zoom-in;
  border: 1px solid var(--tyt-border); background: var(--tyt-bg, #f5f7fa); }
.p-img-more { font-size: 12px; color: var(--tyt-text-dim); padding-left: 2px; }
.upload-area { display: flex; flex-wrap: wrap; gap: 8px; }
.up-item { position: relative; width: 76px; height: 76px; border-radius: 8px; overflow: hidden;
  border: 1px solid var(--tyt-border); }
.up-item img { width: 100%; height: 100%; object-fit: cover; display: block; }
.up-mask { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
  background: rgba(15, 23, 42, .5); color: #fff; font-size: 12px; }
.up-del { position: absolute; top: 2px; right: 2px; width: 18px; height: 18px; border-radius: 50%;
  border: none; background: rgba(15, 23, 42, .65); color: #fff; font-size: 13px; line-height: 18px;
  padding: 0; cursor: pointer; }
.up-del:hover { background: #ef4444; }
.up-add { width: 76px; height: 76px; border-radius: 8px; border: 1px dashed var(--tyt-border);
  background: transparent; color: var(--tyt-text-dim); font-size: 22px; cursor: pointer; }
.up-add:hover:not(:disabled) { border-color: var(--tyt-primary); color: var(--tyt-primary); }
.up-add:disabled { opacity: .5; cursor: not-allowed; }
.upload-tip { width: 100%; font-size: 12px; color: var(--tyt-text-dim); margin-top: 6px; }
/* 视觉隐藏但保留在可访问性树中（屏幕阅读器/自动化可定位） */
.sr-file-input { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px;
  overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0; }
.pager { display: flex; justify-content: center; margin-top: 20px; }
</style>
