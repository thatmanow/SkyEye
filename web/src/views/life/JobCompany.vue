<template>
  <div class="page">
    <h1 class="page-title">求职避坑</h1>
    <p class="page-sub">入职前查一查：经营状态 · 欠薪 / 劳动仲裁公开记录</p>

    <div class="tyt-card search-bar">
      <el-input v-model="name" placeholder="公司名称（至少 2 个字）" size="large" clearable @keyup.enter="doSearch">
        <template #append>
          <el-button :loading="loading" @click="doSearch">查 询</el-button>
        </template>
      </el-input>
    </div>
    <SampleChips :samples="[{ label: '星辰贸易 · 有欠薪记录', value: '星辰贸易' }, '华为技术', '字节跳动']"
                 @pick="v => { name = v; doSearch() }" />

    <template v-if="searched">
      <el-empty v-if="!loading && !items.length" description="未找到匹配公司" />
      <div class="j-list">
        <div v-for="(c, i) in pagedItems" :key="i" class="tyt-card j-card">
          <div class="j-head">
            <span class="j-name">{{ c.name }}</span>
            <el-tag size="small" effect="dark" :type="c.reg_status === '存续' ? 'success' : 'danger'">
              {{ c.reg_status }}
            </el-tag>
          </div>
          <div class="j-meta" v-if="c.legal_person">法定代表人：{{ c.legal_person }}</div>

          <div class="j-risk">
            <span class="j-label">欠薪 / 劳动风险：</span>
            <template v-if="c.risk_records?.length">
              <el-tag type="danger" size="small" effect="dark" style="margin-right: 6px">
                {{ c.risk_records.length }} 条记录
              </el-tag>
              <div v-for="(r, k) in c.risk_records" :key="k" class="j-risk-item">⚠ {{ r.title }}</div>
            </template>
            <span v-else class="j-ok">✓ 未发现公开欠薪 / 劳动仲裁记录</span>
          </div>

          <div class="j-src text-dim">来源：{{ c.source || '公开渠道' }}</div>
        </div>
      </div>
      <div class="pager" v-if="itemsTotal > 10">
        <el-pagination background layout="prev, pager, next" :total="itemsTotal" :page-size="10"
                       :current-page="itemsPage" @current-change="(p: number) => itemsPage = p" />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import SampleChips from '@/components/SampleChips.vue'
import { lifeApi } from '@/api/modules'
import { usePager } from '@/composables/usePager'

const name = ref('')
const loading = ref(false)
const searched = ref(false)
const items = ref<any[]>([])
const { page: itemsPage, total: itemsTotal, paged: pagedItems } = usePager(items)

async function doSearch() {
  if (name.value.trim().length < 2) return ElMessage.warning('公司名称至少 2 个字')
  loading.value = true
  try {
    const data = await lifeApi.jobCompanies({ name: name.value.trim() })
    items.value = data.items || []
    searched.value = true
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.search-bar { margin-bottom: 18px; }
.j-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(420px, 1fr)); gap: 14px; }
.pager { display: flex; justify-content: center; margin-top: 16px; }
.j-head { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
.j-name { font-size: 16px; font-weight: 700; }
.j-meta { color: var(--tyt-text-dim); font-size: 13px; margin-bottom: 10px; }
.j-risk { font-size: 13px; margin-bottom: 8px; }
.j-label { color: var(--tyt-text-dim); }
.j-risk-item { color: var(--tyt-red); font-size: 12.5px; margin-top: 4px; line-height: 1.7; }
.j-ok { color: var(--tyt-green); }
.j-src { font-size: 12px; }
</style>
