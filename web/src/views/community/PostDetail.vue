<template>
  <div class="page narrow">
    <el-button text @click="$router.back()" class="back">← 返回</el-button>

    <template v-if="post">
      <div class="tyt-card">
        <div class="d-top">
          <el-tag :type="post.category === 'avoid_pit' ? 'danger' : 'success'" effect="dark">
            {{ post.category === 'avoid_pit' ? '避雷' : '推荐' }}
          </el-tag>
          <el-tag v-if="post.topic" size="small" effect="plain" class="d-topic">{{ post.topic }}</el-tag>
          <span class="d-author">{{ post.author_nickname }}</span>
          <span class="d-date">{{ post.created_at }}</span>
        </div>
        <h1 class="d-title">{{ post.title }}</h1>
        <p class="d-content">{{ post.content }}</p>
        <div v-if="post.images?.length" class="d-imgs">
          <el-image v-for="(img, i) in post.images" :key="img" class="d-img"
                    :src="img" fit="cover" :alt="`帖子配图${i + 1}`" :preview-src-list="post.images"
                    :initial-index="i" :preview-teleported="true" />
        </div>
        <div class="d-actions">
          <el-button :type="post.liked ? 'primary' : ''" round @click="toggleLike">
            👍 {{ post.like_count }}
          </el-button>
          <el-button round @click="reportVisible = true">🚩 举报</el-button>
        </div>
      </div>

      <div class="tyt-card" style="margin-top: 16px">
        <h3 style="margin: 0 0 14px; font-size: 15px">评论（{{ comments.length }}）</h3>
        <el-empty v-if="!comments.length" description="暂无评论" :image-size="60" />
        <div v-for="c in pagedComments" :key="c.id" class="c-item">
          <div class="c-head">
            <span class="c-author">{{ c.author_nickname }}</span>
            <span class="c-date">{{ c.created_at }}</span>
          </div>
          <p class="c-text">{{ c.content }}</p>
        </div>
        <div class="pager" v-if="commentsTotal > 10">
          <el-pagination background layout="prev, pager, next" :total="commentsTotal" :page-size="10"
                         :current-page="commentsPage" @current-change="(p: number) => commentsPage = p" />
        </div>

        <el-divider />
        <div class="c-form">
          <el-input v-model="commentText" type="textarea" :rows="2" maxlength="500" placeholder="友善评论（先审后发）" />
          <el-button type="primary" :loading="commenting" @click="submitComment"
                     style="background:linear-gradient(135deg,#6366f1,#8b5cf6);border:none">评论</el-button>
        </div>
      </div>
    </template>

    <el-dialog v-model="reportVisible" title="举报内容" width="440px">
      <el-form label-position="top">
        <el-form-item label="举报理由">
          <el-select v-model="reportReason" style="width: 100%">
            <el-option v-for="r in reasons" :key="r" :label="r" :value="r" />
          </el-select>
        </el-form-item>
        <el-form-item label="补充说明（可选）">
          <el-input v-model="reportDesc" type="textarea" :rows="2" maxlength="500" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reportVisible = false">取消</el-button>
        <el-button type="danger" @click="submitReport">提交举报</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { communityApi } from '@/api/modules'
import { useAuthStore } from '@/stores/auth'
import { usePager } from '@/composables/usePager'

const route = useRoute()
const auth = useAuthStore()
const postId = Number(route.params.id)

const post = ref<any>(null)
const comments = ref<any[]>([])
const { page: commentsPage, total: commentsTotal, paged: pagedComments } = usePager(comments)
const commentText = ref('')
const commenting = ref(false)
const reportVisible = ref(false)
const reportReason = ref('虚假信息')
const reportDesc = ref('')
const reasons = ['虚假信息', '侵犯隐私', '造谣诽谤', '辱骂攻击', '广告 spam', '其他']

async function load() {
  try {
    post.value = await communityApi.getPost(postId)
    comments.value = post.value.comments || []
  } catch {
    post.value = null
    ElMessage.error('帖子不存在或未过审')
  }
}

async function toggleLike() {
  if (!auth.isLogged) return ElMessage.warning('请先登录')
  const data = await communityApi.likePost(postId)
  post.value.liked = data.liked
  post.value.like_count = data.like_count
}

async function submitComment() {
  if (!auth.isLogged) return ElMessage.warning('请先登录')
  if (commentText.value.trim().length < 2) return ElMessage.warning('评论至少 2 个字')
  commenting.value = true
  try {
    await communityApi.commentPost(postId, { content: commentText.value.trim(), is_anonymous: true })
    ElMessage.success('评论已提交，先审后发')
    commentText.value = ''
  } finally {
    commenting.value = false
  }
}

async function submitReport() {
  await communityApi.report({
    target_type: 'post', target_id: postId, reason: reportReason.value,
    description: reportDesc.value,
  })
  ElMessage.success('举报已提交，平台将尽快核实')
  reportVisible.value = false
}

onMounted(load)
</script>

<style scoped>
.narrow { max-width: 860px; }
.back { margin-bottom: 12px; color: var(--tyt-text-dim); }
.d-top { display: flex; align-items: center; gap: 10px; font-size: 12.5px; color: var(--tyt-text-dim); margin-bottom: 10px; }
.d-topic { background: rgba(99, 102, 241, .1); border-color: rgba(99, 102, 241, .3); color: var(--tyt-primary-dark); }
.d-title { margin: 0 0 12px; font-size: 21px; }
.d-content { color: var(--tyt-text); font-size: 14.5px; line-height: 2; white-space: pre-wrap; margin: 0 0 16px; }
.d-imgs { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 10px; margin-bottom: 16px; }
.d-img { width: 100%; aspect-ratio: 4 / 3; border-radius: 10px; overflow: hidden; cursor: zoom-in;
  border: 1px solid var(--tyt-border); background: var(--tyt-bg, #f5f7fa); }
.d-actions { display: flex; gap: 10px; }
.c-item { border-bottom: 1px dashed var(--tyt-border); padding: 10px 0; }
.pager { display: flex; justify-content: center; margin-top: 14px; }
.c-head { display: flex; gap: 10px; font-size: 12.5px; color: var(--tyt-text-dim); margin-bottom: 4px; }
.c-text { margin: 0; font-size: 13.5px; line-height: 1.8; }
.c-form { display: flex; gap: 10px; align-items: flex-start; }
.c-form .el-textarea { flex: 1; }
</style>
