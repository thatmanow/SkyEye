<template>
  <div class="page" v-if="company">
    <el-button text @click="$router.back()" class="back">← 返回</el-button>

    <div class="tyt-card head-card">
      <div class="h-top">
        <h1 class="h-name">{{ company.name }}</h1>
        <el-tag effect="dark" :type="company.reg_status === '存续' ? 'success' : 'danger'">{{ company.reg_status }}</el-tag>
        <el-tag v-if="company.listed_code" effect="plain" class="mono">{{ company.listed_code }}</el-tag>
      </div>
      <div class="h-actions">
        <el-button @click="watching ? unwatch() : watch()" :type="watching ? 'warning' : 'default'" round>
          {{ watching ? '★ 已监控' : '☆ 加入监控' }}
        </el-button>
        <el-button type="primary" round @click="genReport"
                   style="background:linear-gradient(135deg,#6366f1,#8b5cf6);border:none">
          📄 生成尽调报告
        </el-button>
      </div>

      <div class="desc-grid" style="margin-top: 14px">
        <div class="desc-item"><span class="k">法定代表人</span><span class="v">{{ company.legal_person || '--' }}</span></div>
        <div class="desc-item"><span class="k">注册资本</span><span class="v">{{ company.reg_capital_wan ? company.reg_capital_wan + ' 万元' : '--' }}</span></div>
        <div class="desc-item"><span class="k">实缴资本</span><span class="v">{{ company.paid_capital_wan ? company.paid_capital_wan + ' 万元' : '--' }}</span></div>
        <div class="desc-item"><span class="k">成立日期</span><span class="v">{{ company.founded_date || '--' }}</span></div>
        <div class="desc-item"><span class="k">企业类型</span><span class="v">{{ company.company_type || '--' }}</span></div>
        <div class="desc-item"><span class="k">所属行业</span><span class="v">{{ company.industry || '--' }}</span></div>
        <div class="desc-item"><span class="k">登记机关</span><span class="v">{{ company.reg_authority || '--' }}</span></div>
        <div class="desc-item"><span class="k">人员规模</span><span class="v">{{ company.employee_scale || '--' }}</span></div>
        <div class="desc-item"><span class="k">统一社会信用代码</span><span class="v mono">{{ company.credit_code || '--' }}</span></div>
        <div class="desc-item"><span class="k">注册地址</span><span class="v">{{ company.address || '--' }}</span></div>
      </div>
      <div class="scope-box">
        <span class="k">经营范围</span>
        <span class="v">{{ company.business_scope || '--' }}</span>
      </div>
      <p class="src text-dim">数据来源：{{ company.source || '公开渠道' }}
        <template v-if="company.source_url"> · <a :href="company.source_url" target="_blank" rel="noopener">来源链接</a></template>
        · 采集于 {{ company.collected_at || '--' }}
      </p>
    </div>

    <div class="tyt-card" style="margin-top: 16px">
      <el-tabs v-model="tab" @tab-change="onTab">
        <el-tab-pane label="股东信息" name="shareholders">
          <el-table :data="pagedShareholders" size="small">
            <el-table-column prop="holder_name" label="股东" min-width="200" />
            <el-table-column prop="holder_type" label="类型" width="110" />
            <el-table-column label="持股比例" width="110">
              <template #default="{ row }">{{ row.share_ratio != null ? row.share_ratio + '%' : '--' }}</template>
            </el-table-column>
            <el-table-column label="认缴出资（万元）" width="140">
              <template #default="{ row }">{{ row.subscribed_capital_wan ?? '--' }}</template>
            </el-table-column>
            <el-table-column prop="source" label="来源" width="120" />
          </el-table>
          <div class="pager" v-if="shareholders.length > 10">
            <el-pagination small background layout="prev, pager, next" :total="shareholders.length" :page-size="10"
                           :current-page="shPage" @current-change="(p: number) => shPage = p" />
          </div>
        </el-tab-pane>

        <el-tab-pane label="主要人员" name="personnel">
          <el-table :data="pagedPersonnel" size="small">
            <el-table-column prop="name" label="姓名" width="140" />
            <el-table-column prop="position" label="职位" width="160" />
            <el-table-column label="类型" width="120">
              <template #default="{ row }">
                <el-tag v-if="row.is_legal_person" type="danger" size="small" effect="plain">法定代表人</el-tag>
                <el-tag v-else type="info" size="small" effect="plain">高管</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="source" label="来源" width="120" />
          </el-table>
          <div class="pager" v-if="personnel.length > 10">
            <el-pagination small background layout="prev, pager, next" :total="personnel.length" :page-size="10"
                           :current-page="ppPage" @current-change="(p: number) => ppPage = p" />
          </div>
        </el-tab-pane>

        <el-tab-pane label="对外投资" name="investments">
          <el-table :data="pagedInvestments" size="small">
            <el-table-column prop="investee_name" label="被投企业" min-width="200" />
            <el-table-column label="持股比例" width="110">
              <template #default="{ row }">{{ row.share_ratio != null ? row.share_ratio + '%' : '--' }}</template>
            </el-table-column>
            <el-table-column label="投资额（万元）" width="130">
              <template #default="{ row }">{{ row.invested_amount_wan ?? '--' }}</template>
            </el-table-column>
            <el-table-column prop="investee_reg_status" label="状态" width="100" />
            <el-table-column prop="source" label="来源" width="120" />
          </el-table>
          <div class="pager" v-if="investments.length > 10">
            <el-pagination small background layout="prev, pager, next" :total="investments.length" :page-size="10"
                           :current-page="ivPage" @current-change="(p: number) => ivPage = p" />
          </div>
        </el-tab-pane>

        <el-tab-pane label="分支机构" name="branches">
          <el-table :data="pagedBranches" size="small">
            <el-table-column prop="branch_name" label="分支名称" min-width="220" />
            <el-table-column prop="branch_status" label="状态" width="100" />
            <el-table-column prop="branch_person" label="负责人" width="120" />
            <el-table-column label="地区" width="160">
              <template #default="{ row }">{{ [row.province, row.city].filter(Boolean).join(' · ') || '--' }}</template>
            </el-table-column>
          </el-table>
          <div class="pager" v-if="branches.length > 10">
            <el-pagination small background layout="prev, pager, next" :total="branches.length" :page-size="10"
                           :current-page="brPage" @current-change="(p: number) => brPage = p" />
          </div>
        </el-tab-pane>

        <el-tab-pane label="变更记录" name="changes">
          <el-table :data="pagedChanges" size="small">
            <el-table-column prop="change_date" label="日期" width="120" />
            <el-table-column prop="change_type" label="变更项目" width="160" />
            <el-table-column label="变更内容">
              <template #default="{ row }">{{ row.before_value }} → {{ row.after_value }}</template>
            </el-table-column>
            <el-table-column prop="source" label="来源" width="120" />
          </el-table>
          <div class="pager" v-if="changes.length > 10">
            <el-pagination small background layout="prev, pager, next" :total="changes.length" :page-size="10"
                           :current-page="chPage" @current-change="(p: number) => chPage = p" />
          </div>
        </el-tab-pane>

        <el-tab-pane :label="`风险信息（${risks.length}）`" name="risks">
          <div class="risk-filter">
            <el-radio-group v-model="riskType" size="small" @change="loadRisks">
              <el-radio-button value="">全部</el-radio-button>
              <el-radio-button value="judicial">司法</el-radio-button>
              <el-radio-button value="business">经营</el-radio-button>
              <el-radio-button value="finance">财务</el-radio-button>
              <el-radio-button value="admin_penalty">行政处罚</el-radio-button>
              <el-radio-button value="public_opinion">舆情</el-radio-button>
            </el-radio-group>
          </div>
          <el-empty v-if="!risks.length" description="未发现该类型风险记录" :image-size="70" />
          <div v-for="r in pagedRisks" :key="r.id" class="risk-item">
            <div class="r-top">
              <RiskTag :map="r.risk_type" />
              <RiskTag :map="r.risk_level" />
              <span class="r-sub">{{ r.risk_subtype }}</span>
              <span class="r-date">{{ r.occur_date || r.publish_date }}</span>
            </div>
            <p class="r-title">{{ r.title }}</p>
            <p class="r-digest" v-if="r.content_digest">{{ r.content_digest }}</p>
            <div class="r-meta">
              <span v-if="r.court">{{ r.court }}</span>
              <span v-if="r.case_no" class="mono">{{ r.case_no }}</span>
              <span v-if="r.amount_wan">涉案金额 {{ r.amount_wan }} 万元</span>
              <span class="text-dim">来源：{{ r.source }}</span>
            </div>
          </div>
          <div class="pager" v-if="rkTotal > 10">
            <el-pagination background layout="prev, pager, next" :total="rkTotal" :page-size="10"
                           :current-page="rkPage" @current-change="(p: number) => rkPage = p" />
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { bizApi, monitorApi, reportApi } from '@/api/modules'
import RiskTag from '@/components/RiskTag.vue'
import { useAuthStore } from '@/stores/auth'
import { usePager } from '@/composables/usePager'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const companyId = Number(route.params.id)

const company = ref<any>(null)
const tab = ref('shareholders')
const shareholders = ref<any[]>([])
const personnel = ref<any[]>([])
const investments = ref<any[]>([])
const branches = ref<any[]>([])
const changes = ref<any[]>([])
const risks = ref<any[]>([])

const { page: shPage, paged: pagedShareholders } = usePager(shareholders)
const { page: ppPage, paged: pagedPersonnel } = usePager(personnel)
const { page: ivPage, paged: pagedInvestments } = usePager(investments)
const { page: brPage, paged: pagedBranches } = usePager(branches)
const { page: chPage, paged: pagedChanges } = usePager(changes)
const { page: rkPage, total: rkTotal, paged: pagedRisks } = usePager(risks)
const riskType = ref('')
const watching = ref(false)

async function loadBase() {
  company.value = await bizApi.companyDetail(companyId)
  const ws = await monitorApi.watches().catch(() => ({ items: [] }))
  const list = ws.items || ws || []
  watching.value = list.some((w: any) => w.company_id === companyId)
  await loadRisks()
  await onTab('shareholders')
}

async function onTab(name: any) {
  // 后端返回 {items: [...]}，需解包后再交给表格
  const loaders: Record<string, () => Promise<void>> = {
    shareholders: async () => (shareholders.value = (await bizApi.shareholders(companyId))?.items ?? []),
    personnel: async () => (personnel.value = (await bizApi.personnel(companyId))?.items ?? []),
    investments: async () => (investments.value = (await bizApi.investments(companyId))?.items ?? []),
    branches: async () => (branches.value = (await bizApi.branches(companyId))?.items ?? []),
    changes: async () => (changes.value = (await bizApi.changes(companyId))?.items ?? []),
  }
  await loaders[String(name)]?.()
}

async function loadRisks() {
  const data = await bizApi.risks(companyId, riskType.value ? { risk_type: riskType.value } : undefined)
  risks.value = data.items || data || []
}

async function watch() {
  if (!auth.isLogged) return ElMessage.warning('请先登录')
  await monitorApi.addWatch({ company_id: companyId })
  watching.value = true
  ElMessage.success('已加入监控，可在「商业监控」中管理')
}

async function unwatch() {
  const ws = await monitorApi.watches()
  const list = ws.items || ws || []
  const target = list.find((w: any) => w.company_id === companyId)
  if (target) await monitorApi.removeWatch(target.watch_id)
  watching.value = false
  ElMessage.success('已取消监控')
}

async function genReport() {
  if (!auth.isLogged) return ElMessage.warning('请先登录')
  await ElMessageBox.confirm(
    '将基于当前公开数据生成尽调报告（PDF + Excel），继续？', '生成尽调报告', { type: 'info' })
  await reportApi.create({ company_id: companyId, template: 'standard' })
  ElMessage.success('报告任务已提交，请前往「尽调报告」页面查看进度')
  router.push('/biz/reports')
}

onMounted(loadBase)
</script>

<style scoped>
.back { margin-bottom: 10px; color: var(--tyt-text-dim); }
.h-top { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.h-name { margin: 0; font-size: 22px; }
.h-actions { margin-top: 12px; display: flex; gap: 10px; }
.scope-box { display: flex; gap: 14px; margin-top: 12px; font-size: 13px; line-height: 1.8; }
.scope-box .k { color: var(--tyt-text-dim); min-width: 88px; }
.src { font-size: 12px; margin: 14px 0 0; }
.risk-filter { margin-bottom: 14px; }
.pager { display: flex; justify-content: center; margin-top: 14px; }
.risk-item { border: 1px solid var(--tyt-border); border-radius: 10px; padding: 12px 14px; margin-bottom: 10px; }
.r-top { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; font-size: 12px; color: var(--tyt-text-dim); flex-wrap: wrap; }
.r-sub { font-size: 12.5px; }
.r-date { margin-left: auto; }
.r-title { margin: 0 0 4px; font-size: 14px; font-weight: 600; }
.r-digest { margin: 0 0 6px; color: var(--tyt-text-dim); font-size: 13px; line-height: 1.7; }
.r-meta { display: flex; gap: 14px; flex-wrap: wrap; font-size: 12px; color: var(--tyt-text-dim); }
</style>
