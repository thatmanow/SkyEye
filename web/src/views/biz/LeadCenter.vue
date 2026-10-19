<template>
  <div class="page">
    <h1 class="page-title">商机线索</h1>
    <p class="page-sub">基于公开工商与风险变化推导 —— 风险缓解=潜在客户，经营扩张=合作机会</p>

    <div class="tyt-card filter-bar">
      <el-select v-model="filters.industry" placeholder="行业" clearable style="width: 150px" @change="load(1)">
        <el-option v-for="i in options.industries" :key="i" :label="i" :value="i" />
      </el-select>
      <el-select v-model="filters.province" placeholder="地域" clearable style="width: 130px" @change="load(1)">
        <el-option v-for="p in options.provinces" :key="p" :label="p" :value="p" />
      </el-select>
      <el-select v-model="filters.scale" placeholder="规模" clearable style="width: 130px" @change="load(1)">
        <el-option v-for="s in options.scales" :key="s" :label="s" :value="s" />
      </el-select>
      <el-select v-model="filters.risk_delta" placeholder="风险变化" clearable style="width: 130px" @change="load(1)">
        <el-option label="改善" value="improved" />
        <el-option label="恶化" value="worsened" />
      </el-select>
      <span class="text-dim total">共 {{ total }} 条线索</span>
    </div>

    <el-empty v-if="!loading && !items.length" description="没有匹配的线索" />
    <div class="l-list">
      <div v-for="l in items" :key="l.id" class="tyt-card l-card">
        <div class="l-head">
          <router-link :to="`/biz/companies/${l.company_id}`" class="l-name">{{ l.company_name }}</router-link>
          <el-tag size="small" effect="dark" :type="l.risk_delta < 0 ? 'success' : l.risk_delta > 0 ? 'danger' : 'info'">
            风险{{ l.risk_delta < 0 ? '改善' : l.risk_delta > 0 ? '恶化' : '持平' }}
          </el-tag>
          <el-tag size="small" effect="plain" type="warning">价值分 {{ l.score }}</el-tag>
          <el-button size="small" :type="l.favorited ? 'warning' : 'default'" plain style="margin-left: auto"
                     @click="toggleFav(l)">
            {{ l.favorited ? '★' : '☆' }}
          </el-button>
        </div>
        <div class="l-meta">
          <span v-if="l.industry">{{ l.industry }}</span>
          <span v-if="l.province">{{ l.province }}</span>
          <span v-if="l.employee_scale">{{ l.employee_scale }}</span>
          <span v-if="l.discovered_at">发现于 {{ l.discovered_at }}</span>
        </div>
        <div class="l-signal">
          <el-tag size="small" effect="dark" type="success">{{ l.signal_type }}</el-tag>
          <span class="l-signal-desc">{{ l.signal_desc }}</span>
        </div>
        <div class="l-foot">
          <template v-if="l.follow">
            <el-tag size="small" effect="plain">{{ followName(l.follow.status) }}</el-tag>
            <span class="l-note text-dim" v-if="l.follow.note">{{ l.follow.note }}</span>
          </template>
          <el-button size="small" text type="primary" @click="openFollow(l)" style="margin-left: auto">
            {{ l.follow ? '更新跟进' : '开始跟进' }}
          </el-button>
        </div>
      </div>
    </div>

    <div class="pager" v-if="total > pageSize">
      <el-pagination background layout="prev, pager, next" :total="total" :page-size="pageSize"
                     :current-page="page" @current-change="load" />
    </div>

    <el-dialog v-model="followDlg" title="线索跟进" width="480px">
      <el-form label-position="top">
        <el-form-item label="跟进状态">
          <el-radio-group v-model="followForm.status">
            <el-radio value="new">新线索</el-radio>
            <el-radio value="following">跟进中</el-radio>
            <el-radio value="won">已成交</el-radio>
            <el-radio value="lost">已放弃</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="跟进备注">
          <el-input v-model="followForm.note" type="textarea" :rows="2" maxlength="1000" />
        </el-form-item>
        <el-form-item label="下一步动作">
          <el-input v-model="followForm.next_action" maxlength="256" placeholder="如：下周电话联系" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="followDlg = false">取消</el-button>
        <el-button type="primary" @click="saveFollow"
                   style="background:linear-gradient(135deg,#6366f1,#8b5cf6);border:none">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { leadApi } from '@/api/modules'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const options = ref<any>({ industries: [], provinces: [], scales: [] })
const items = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 10
const loading = ref(false)
const filters = reactive({ industry: '', province: '', scale: '', risk_delta: '' })

const followDlg = ref(false)
const followForm = reactive({ status: 'following', note: '', next_action: '' })
let followTarget: any = null

function followName(s: string) {
  return ({ new: '新线索', following: '跟进中', won: '已成交', lost: '已放弃' } as any)[s] || s
}

async function load(p = 1) {
  page.value = p
  loading.value = true
  try {
    const params: any = { page: p, page_size: pageSize }
    for (const [k, v] of Object.entries(filters)) if (v) params[k] = v
    const data = await leadApi.list(params)
    items.value = data.items || []
    total.value = data.total || 0
  } finally {
    loading.value = false
  }
}

async function toggleFav(l: any) {
  if (!auth.isLogged) return ElMessage.warning('请先登录')
  await leadApi.favorite(l.id)
  l.favorited = !l.favorited
}

function openFollow(l: any) {
  if (!auth.isLogged) return ElMessage.warning('请先登录')
  followTarget = l
  followForm.status = l.follow?.status || 'following'
  followForm.note = l.follow?.note || ''
  followForm.next_action = l.follow?.next_action || ''
  followDlg.value = true
}

async function saveFollow() {
  if (!followTarget) return
  await leadApi.follow(followTarget.id, { ...followForm })
  ElMessage.success('跟进信息已保存')
  followDlg.value = false
  await load(page.value)
}

onMounted(async () => {
  options.value = await leadApi.options()
  await load()
})
</script>

<style scoped>
.filter-bar { display: flex; gap: 10px; align-items: center; margin-bottom: 16px; flex-wrap: wrap; }
.total { margin-left: auto; font-size: 13px; }
.l-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(460px, 1fr)); gap: 14px; }
.l-head { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; flex-wrap: wrap; }
.l-name { font-size: 15px; font-weight: 700; }
.l-meta { display: flex; gap: 12px; color: var(--tyt-text-dim); font-size: 12.5px; margin-bottom: 8px; flex-wrap: wrap; }
.l-signal { display: flex; gap: 8px; align-items: baseline; margin-bottom: 10px; }
.l-signal-desc { font-size: 13px; color: var(--tyt-text); line-height: 1.7; }
.l-foot { display: flex; align-items: center; gap: 8px; border-top: 1px dashed var(--tyt-border); padding-top: 10px; }
.l-note { font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 240px; }
.pager { display: flex; justify-content: center; margin-top: 20px; }
</style>
