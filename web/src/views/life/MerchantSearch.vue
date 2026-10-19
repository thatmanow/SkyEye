<template>
  <div class="page">
    <h1 class="page-title">商家查询</h1>
    <p class="page-sub">工商状态 · 评价聚合 · 过审投诉记录 —— 充值预付卡前先查一查</p>

    <div class="tyt-card search-bar">
      <el-input v-model="keyword" placeholder="商家名称 / 地址 / 经营范围" size="large" clearable
                @keyup.enter="doSearch" class="kw">
        <template #append>
          <el-button :loading="loading" @click="doSearch">查 询</el-button>
        </template>
      </el-input>
      <el-input v-model="city" placeholder="城市（可选）" style="width: 180px" clearable />
    </div>
    <SampleChips :samples="['江南小馆', '老王烧烤', '蓝天健身俱乐部', '优选生活超市', '启明教育培训中心']"
                 @pick="v => { keyword = v; doSearch() }" />

    <template v-if="searched">
      <el-empty v-if="!loading && !items.length" description="未找到匹配商家" />
      <div class="m-list">
        <div v-for="m in pagedItems" :key="m.id" class="tyt-card m-card" @click="openDetail(m.id)">
          <div class="m-head">
            <span class="m-name">{{ m.name }}</span>
            <el-tag size="small" effect="dark" type="success">{{ m.reg_status || '未知状态' }}</el-tag>
            <el-tag size="small" effect="plain" v-if="m.category">{{ m.category }}</el-tag>
          </div>
          <div class="m-meta">
            <span>📍 {{ m.address || '地址未公开' }}</span>
            <span class="mono">{{ m.credit_code || '--' }}</span>
          </div>
          <div class="m-foot">
            <el-rate :model-value="m.rating_avg" disabled size="small" />
            <span class="m-count">{{ m.rating_count }} 条评价</span>
            <span class="m-complaint" v-if="m.complaint_count">⚠ {{ m.complaint_count }} 条过审投诉</span>
          </div>
        </div>
      </div>
      <div class="pager" v-if="itemsTotal > 10">
        <el-pagination background layout="prev, pager, next" :total="itemsTotal" :page-size="10"
                       :current-page="itemsPage" @current-change="(p: number) => itemsPage = p" />
      </div>
    </template>

    <el-drawer v-model="drawer" size="560px" :title="detail?.name || '商家详情'">
      <template v-if="detail">
        <div class="desc-grid">
          <div class="desc-item"><span class="k">经营状态</span><span class="v">{{ detail.reg_status }}</span></div>
          <div class="desc-item"><span class="k">信用代码</span><span class="v mono">{{ detail.credit_code || '--' }}</span></div>
          <div class="desc-item"><span class="k">地址</span><span class="v">{{ detail.address }}</span></div>
          <div class="desc-item"><span class="k">经营范围</span><span class="v">{{ detail.business_scope }}</span></div>
        </div>

        <h4>过审投诉（{{ detail.complaints?.length || 0 }}）</h4>
        <el-empty v-if="!detail.complaints?.length" description="暂无过审投诉记录" :image-size="60" />
        <div v-for="(c, i) in pagedComplaints" :key="i" class="c-item">
          <el-tag size="small" type="warning" effect="plain">{{ c.category }}</el-tag>
          <span class="c-text">{{ c.content }}</span>
        </div>
        <div class="pager" v-if="complaintsTotal > 10">
          <el-pagination small background layout="prev, pager, next" :total="complaintsTotal" :page-size="10"
                         :current-page="complaintsPage" @current-change="(p: number) => complaintsPage = p" />
        </div>

        <h4>用户评价（{{ detail.reviews?.length || 0 }}）</h4>
        <el-empty v-if="!detail.reviews?.length" description="暂无过审评价" :image-size="60" />
        <div v-for="(r, i) in pagedReviews" :key="i" class="r-item">
          <el-rate :model-value="r.rating" disabled size="small" />
          <span class="r-text">{{ r.content }}</span>
          <span class="r-date">{{ r.created_at }}</span>
        </div>
        <div class="pager" v-if="reviewsTotal > 10">
          <el-pagination small background layout="prev, pager, next" :total="reviewsTotal" :page-size="10"
                         :current-page="reviewsPage" @current-change="(p: number) => reviewsPage = p" />
        </div>

        <el-divider />
        <h4>写评价</h4>
        <el-form label-position="top">
          <el-form-item label="评分">
            <el-rate v-model="reviewForm.rating" />
          </el-form-item>
          <el-form-item label="评价内容（10 字以上，先审后发）">
            <el-input v-model="reviewForm.content" type="textarea" :rows="3" maxlength="500" show-word-limit />
          </el-form-item>
          <el-button type="primary" @click="submitReview" :loading="submitting"
                     style="background:linear-gradient(135deg,#6366f1,#8b5cf6);border:none">
            提交评价
          </el-button>
        </el-form>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import SampleChips from '@/components/SampleChips.vue'
import { lifeApi } from '@/api/modules'
import { usePager } from '@/composables/usePager'

const keyword = ref('')
const city = ref('')
const loading = ref(false)
const searched = ref(false)
const items = ref<any[]>([])

const drawer = ref(false)
const detail = ref<any>(null)
const submitting = ref(false)
const reviewForm = reactive({ rating: 5, content: '' })

const { page: itemsPage, total: itemsTotal, paged: pagedItems } = usePager(items)
const detailComplaints = computed<any[]>(() => detail.value?.complaints || [])
const detailReviews = computed<any[]>(() => detail.value?.reviews || [])
const { page: complaintsPage, total: complaintsTotal, paged: pagedComplaints } = usePager(detailComplaints)
const { page: reviewsPage, total: reviewsTotal, paged: pagedReviews } = usePager(detailReviews)

async function doSearch() {
  if (!keyword.value.trim()) return ElMessage.warning('请输入关键词')
  loading.value = true
  try {
    const data = await lifeApi.searchMerchants({
      keyword: keyword.value.trim(), city: city.value.trim() || undefined, page_size: 20,
    })
    items.value = data.items || []
    searched.value = true
  } finally {
    loading.value = false
  }
}

async function openDetail(id: number) {
  detail.value = await lifeApi.merchantDetail(id)
  drawer.value = true
}

async function submitReview() {
  if (!detail.value) return
  if (reviewForm.content.trim().length < 10) return ElMessage.warning('评价内容至少 10 个字')
  submitting.value = true
  try {
    await lifeApi.createReview(detail.value.id, {
      rating: reviewForm.rating, content: reviewForm.content.trim(),
    })
    ElMessage.success('评价已提交，审核通过后展示')
    reviewForm.content = ''
    detail.value = await lifeApi.merchantDetail(detail.value.id)
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.search-bar { display: flex; gap: 12px; margin-bottom: 18px; }
.kw { flex: 1; }
.m-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(360px, 1fr)); gap: 14px; }
.pager { display: flex; justify-content: center; margin-top: 16px; grid-column: 1 / -1; }
.m-card { cursor: pointer; transition: border-color .2s; }
.m-card:hover { border-color: rgba(99,102,241,.45); }
.m-head { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; flex-wrap: wrap; }
.m-name { font-size: 16px; font-weight: 700; }
.m-meta { display: flex; flex-direction: column; gap: 4px; color: var(--tyt-text-dim); font-size: 12.5px; margin-bottom: 8px; }
.m-foot { display: flex; align-items: center; gap: 10px; font-size: 12px; color: var(--tyt-text-dim); }
.m-complaint { color: var(--tyt-amber); }
h4 { margin: 18px 0 10px; font-size: 14px; }
.c-item, .r-item { display: flex; align-items: baseline; gap: 8px; margin-bottom: 10px; font-size: 13px; }
.c-text, .r-text { color: var(--tyt-text); line-height: 1.7; }
.r-date { color: #94a3b8; font-size: 12px; }
</style>
