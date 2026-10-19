<template>
  <div class="page">
    <h1 class="page-title">企业查询</h1>
    <p class="page-sub">工商信息 · 股东高管 · 对外投资 · 司法与经营风险</p>

    <div class="tyt-card search-bar">
      <el-input v-model="keyword" placeholder="企业名称 / 经营范围 / 行业关键词" size="large" clearable @keyup.enter="doSearch">
        <template #append>
          <el-button :loading="loading" @click="doSearch">查 询</el-button>
        </template>
      </el-input>
    </div>
    <SampleChips :samples="['贵州茅台', '宁德时代', '比亚迪', '腾讯', '华为']"
                 @pick="v => { keyword = v; doSearch() }" />

    <template v-if="searched">
      <p class="result-count text-dim" v-if="total">共 {{ total }} 家匹配企业</p>
      <el-empty v-if="!loading && !items.length" description="未找到匹配企业" />
      <div class="c-list">
        <div v-for="c in pagedItems" :key="c.id" class="tyt-card c-card" @click="goDetail(c.id)">
          <div class="c-head">
            <span class="c-name">{{ c.name }}</span>
            <el-tag size="small" effect="dark" :type="c.reg_status === '存续' ? 'success' : 'danger'">{{ c.reg_status }}</el-tag>
          </div>
          <div class="c-meta">
            <span v-if="c.legal_person">法代：{{ c.legal_person }}</span>
            <span v-if="c.reg_capital_wan">注册资本：{{ c.reg_capital_wan }} 万</span>
            <span v-if="c.founded_date">成立：{{ c.founded_date }}</span>
          </div>
          <div class="c-meta2">
            <span v-if="c.industry">行业：{{ c.industry }}</span>
            <span>{{ c.province }}{{ c.city ? ' · ' + c.city : '' }}</span>
            <span v-if="c.listed_code" class="mono">证券：{{ c.listed_code }}</span>
          </div>
        </div>
      </div>
      <div class="pager" v-if="items.length > 10">
        <el-pagination background layout="prev, pager, next" :total="items.length" :page-size="10"
                       :current-page="itemsPage" @current-change="(p: number) => itemsPage = p" />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import SampleChips from '@/components/SampleChips.vue'
import { bizApi } from '@/api/modules'
import { usePager } from '@/composables/usePager'

const router = useRouter()
const keyword = ref('')
const loading = ref(false)
const searched = ref(false)
const items = ref<any[]>([])
const total = ref(0)
const { page: itemsPage, paged: pagedItems } = usePager(items)

async function doSearch() {
  if (!keyword.value.trim()) return ElMessage.warning('请输入关键词')
  loading.value = true
  try {
    const data = await bizApi.searchCompanies({ keyword: keyword.value.trim(), page_size: 20 })
    items.value = data.items || []
    total.value = data.total || 0
    searched.value = true
  } finally {
    loading.value = false
  }
}

function goDetail(id: number) {
  router.push(`/biz/companies/${id}`)
}
</script>

<style scoped>
.search-bar { margin-bottom: 16px; }
.result-count { font-size: 13px; margin: 0 0 12px; }
.c-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(420px, 1fr)); gap: 14px; }
.pager { display: flex; justify-content: center; margin-top: 16px; }
.c-card { cursor: pointer; transition: border-color .2s; }
.c-card:hover { border-color: rgba(99,102,241,.45); }
.c-head { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; flex-wrap: wrap; }
.c-name { font-size: 15.5px; font-weight: 700; }
.c-meta, .c-meta2 { display: flex; gap: 14px; flex-wrap: wrap; color: var(--tyt-text-dim); font-size: 12.5px; margin-bottom: 5px; }
</style>
