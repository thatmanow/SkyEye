<template>
  <div class="page">
    <h1 class="page-title">尽调报告</h1>
    <p class="page-sub">一键生成 · Celery 异步 · PDF / Excel 双格式</p>

    <div class="tyt-card create-bar">
      <el-alert
        v-if="!isPremium"
        class="expiry-tip"
        type="info"
        :closable="false"
        show-icon
        title="会员已过期"
        description="历史生成的报告仍可查看与下载；升级高级会员后可生成新报告。"
      />
      <el-select v-model="companyId" filterable remote :remote-method="searchCompanies"
                 :loading="searching" placeholder="选择企业" style="width: 340px">
        <el-option v-for="c in companyOptions" :key="c.id" :label="c.name" :value="c.id" />
      </el-select>
      <el-select v-model="template" style="width: 160px">
        <el-option label="标准版" value="standard" />
        <el-option label="深度版" value="deep" />
      </el-select>
      <el-tooltip v-if="!isPremium" content="升级高级会员后可生成新报告" placement="top">
        <el-button type="primary" disabled
                   style="background:linear-gradient(135deg,#6366f1,#8b5cf6);border:none">
          生成报告
        </el-button>
      </el-tooltip>
      <el-button v-else type="primary" :loading="creating" @click="create"
                 style="background:linear-gradient(135deg,#6366f1,#8b5cf6);border:none">
        生成报告
      </el-button>
    </div>

    <div class="tyt-card">
      <h3 style="margin: 0 0 12px; font-size: 15px">我的报告（{{ reports.length }}）</h3>
      <el-empty v-if="!reports.length" description="还没有生成过报告" :image-size="70" />
      <el-table :data="pagedReports" size="small">
        <el-table-column prop="id" label="任务号" width="80" />
        <el-table-column prop="company_name" label="企业" min-width="220" />
        <el-table-column label="模板" width="90">
          <template #default="{ row }">{{ row.template === 'deep' ? '深度版' : '标准版' }}</template>
        </el-table-column>
        <el-table-column label="状态" width="150">
          <template #default="{ row }">
            <RiskTag :map="row.status" />
            <el-progress v-if="row.status === 'running'" :percentage="row.progress" :stroke-width="6"
                         style="width: 90px; margin-left: 6px" />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170" />
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <template v-if="row.status === 'done'">
              <el-button size="small" type="primary" link @click="download(row.id, 'pdf')">PDF</el-button>
              <el-button size="small" type="success" link @click="download(row.id, 'xlsx')">Excel</el-button>
            </template>
            <span v-else-if="row.status === 'failed'" class="text-dim">{{ row.error }}</span>
            <span v-else class="text-dim">生成中…</span>
          </template>
        </el-table-column>
      </el-table>
      <div class="pager" v-if="reports.length > 10">
        <el-pagination small background layout="prev, pager, next" :total="reports.length" :page-size="10"
                       :current-page="rpPage" @current-change="(p: number) => rpPage = p" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { bizApi, reportApi, reportDownloadUrl } from '@/api/modules'
import RiskTag from '@/components/RiskTag.vue'
import { usePager } from '@/composables/usePager'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const isPremium = computed(() => auth.isPremium)

const companyOptions = ref<any[]>([])
const searching = ref(false)
const companyId = ref<number>()
const template = ref('standard')
const creating = ref(false)
const reports = ref<any[]>([])
const { page: rpPage, paged: pagedReports } = usePager(reports)
let timer: any = null

async function searchCompanies(q: string) {
  if (!q) return
  searching.value = true
  try {
    const data = await bizApi.searchCompanies({ keyword: q.trim(), page_size: 10 })
    companyOptions.value = data.items || []
  } finally {
    searching.value = false
  }
}

async function create() {
  if (!companyId.value) return ElMessage.warning('请先选择企业')
  creating.value = true
  try {
    await reportApi.create({ company_id: companyId.value, template: template.value })
    ElMessage.success('报告任务已提交')
    await load()
  } finally {
    creating.value = false
  }
}

async function load() {
  const data = await reportApi.list()
  reports.value = data.items || []
  const running = reports.value.some((r) => ['queued', 'running'].includes(r.status))
  if (running && !timer) {
    timer = setInterval(load, 2500)
  } else if (!running && timer) {
    clearInterval(timer)
    timer = null
  }
}

function download(id: number, format: 'pdf' | 'xlsx') {
  const token = localStorage.getItem('tyt_access_token') || ''
  fetch(reportDownloadUrl(id, format), { headers: { Authorization: `Bearer ${token}` } })
    .then(async (resp) => {
      if (!resp.ok) {
        const body = await resp.json().catch(() => ({}))
        throw new Error(body.message || '下载失败')
      }
      const blob = await resp.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `尽调报告_${id}.${format}`
      a.click()
      URL.revokeObjectURL(url)
    })
    .catch((e) => ElMessage.error(e.message))
}

onMounted(load)
onBeforeUnmount(() => timer && clearInterval(timer))
</script>

<style scoped>
.create-bar { display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 16px; align-items: center; }
.expiry-tip { width: 100%; margin-bottom: 4px; }
.pager { display: flex; justify-content: center; margin-top: 14px; }
</style>
