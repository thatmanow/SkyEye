<template>
  <div class="page">
    <h1 class="page-title">房源查询</h1>
    <p class="page-sub">小区物业投诉 · 房东押金纠纷 · 中介套路 —— 签约前先查一查</p>

    <el-tabs v-model="tab" class="tyt-card">
      <el-tab-pane label="查小区" name="estate">
        <div class="search-panel">
          <div class="search-row">
            <el-input v-model="estateKw" size="large" placeholder="小区名称，如：翠湖天地" clearable
                      @keyup.enter="searchEstate" />
            <el-button size="large" type="primary" :loading="loading" @click="searchEstate" class="g-btn">查询</el-button>
          </div>
          <SampleChips :samples="['翠湖天地', '阳光花园', '锦绣江南']"
                       @pick="v => { estateKw = v; searchEstate() }" />
        </div>

        <!-- 未搜索：三步指引 + 投诉类型速览，填充空态 -->
        <template v-if="!estate">
          <div class="steps-card">
            <div class="steps-title">🧭 租房避坑三步走</div>
            <div class="steps">
              <div class="step">
                <div class="step-no">1</div>
                <div class="step-body">
                  <div class="step-name">查小区</div>
                  <div class="step-desc">物业纠纷、邻里投诉、过审记录</div>
                </div>
              </div>
              <div class="step-arrow">→</div>
              <div class="step">
                <div class="step-no">2</div>
                <div class="step-body">
                  <div class="step-name">查房东</div>
                  <div class="step-desc">押金纠纷、提前解约、维修责任</div>
                </div>
              </div>
              <div class="step-arrow">→</div>
              <div class="step">
                <div class="step-no">3</div>
                <div class="step-body">
                  <div class="step-name">查中介</div>
                  <div class="step-desc">虚假房源、违规收费记录</div>
                </div>
              </div>
            </div>
          </div>

          <div class="cat-grid">
            <div v-for="c in categories.slice(0, 6)" :key="c.name" class="cat-item">
              <span class="cat-ic">{{ c.icon }}</span>
              <div class="cat-body">
                <div class="cat-name">{{ c.name }}</div>
                <div class="cat-desc">{{ c.desc }}</div>
              </div>
            </div>
          </div>

          <div class="hint-bar">
            ℹ️ 所有投诉均由用户提交、平台<strong>先审后发</strong>，仅展示过审记录；查询行为写入审计日志。
          </div>
        </template>

        <template v-else>
          <div class="estate-card">
            <div class="estate-head">
              <span class="estate-name">{{ estate.name }}</span>
              <span class="estate-region">{{ estate.city }} · {{ estate.district }}</span>
            </div>
            <div class="desc-grid">
              <div class="desc-item"><span class="k">开发商</span><span class="v">{{ estate.developer || '--' }}</span></div>
              <div class="desc-item"><span class="k">物业公司</span><span class="v">{{ estate.property_company || '--' }}</span></div>
              <div class="desc-item"><span class="k">建成年份</span><span class="v">{{ estate.build_year || '--' }}</span></div>
              <div class="desc-item"><span class="k">过审投诉</span>
                <span class="v" :class="estate.complaint_count > 0 ? 'warn' : 'ok'">{{ estate.complaint_count }} 条</span>
              </div>
            </div>
          </div>

          <h4>过审投诉记录</h4>
          <el-empty v-if="!records.complaints?.length" description="该小区暂无过审投诉" :image-size="60" />
          <div v-for="(c, i) in pagedComplaints" :key="i" class="row-item">
            <el-tag size="small" type="warning" effect="plain">{{ c.category }}</el-tag>
            <span>{{ c.content }}</span>
          </div>
          <div class="pager" v-if="complaintsTotal > 10">
            <el-pagination background layout="prev, pager, next" :total="complaintsTotal" :page-size="10"
                           :current-page="complaintsPage" @current-change="(p: number) => complaintsPage = p" />
          </div>
        </template>
      </el-tab-pane>

      <el-tab-pane label="查房东 / 中介" name="landlord">
        <div class="search-panel">
          <div class="search-row">
            <el-select v-model="subjectType" size="large" class="type-select">
              <el-option label="房东" value="landlord" />
              <el-option label="中介" value="agency" />
            </el-select>
            <el-input v-model="subjectKw" size="large" placeholder="脱敏名（如 陈*）或中介公司名" clearable
                      @keyup.enter="searchSubject" />
            <el-button size="large" type="primary" :loading="loading2" @click="searchSubject" class="g-btn">查询</el-button>
          </div>
          <SampleChips :samples="[{ label: '房东 陈*', value: 'landlord|陈*' },
                                  { label: '房东 周*', value: 'landlord|周*' },
                                  { label: '中介 众诚房地产', value: 'agency|众诚房地产经纪有限公司' }]"
                       @pick="pickSubject" />
        </div>

        <template v-if="subjectSearched">
          <h4>过审投诉（{{ subjectComplaints.length }}）</h4>
          <el-empty v-if="!subjectComplaints.length" description="未找到该主体的过审投诉" :image-size="60" />
          <div v-for="(c, i) in pagedSubjectComplaints" :key="i" class="row-item">
            <el-tag size="small" type="warning" effect="plain">{{ c.category }}</el-tag>
            <span>{{ c.content }}</span>
          </div>
          <div class="pager" v-if="subjectComplaintsTotal > 10">
            <el-pagination background layout="prev, pager, next" :total="subjectComplaintsTotal" :page-size="10"
                           :current-page="subjectComplaintsPage" @current-change="(p: number) => subjectComplaintsPage = p" />
          </div>
        </template>
        <div v-else class="hint-bar" style="margin-top: 0">
          ℹ️ 房东查询仅支持<strong>脱敏名</strong>（如「陈*」），不提供任何身份信息检索；中介支持公司全名或简称。
        </div>
      </el-tab-pane>

      <el-tab-pane label="提交投诉" name="complaint">
        <el-form label-position="top" style="max-width: 560px" class="complaint-form">
          <el-form-item label="投诉对象">
            <el-select v-model="complaintForm.subject_type">
              <el-option label="小区" value="estate" />
              <el-option label="房东（填脱敏名）" value="landlord" />
              <el-option label="中介公司" value="agency" />
            </el-select>
          </el-form-item>
          <el-form-item label="对象名称">
            <el-input v-model="complaintForm.subject_label" placeholder="小区名 / 房东脱敏名 / 中介公司名" />
          </el-form-item>
          <el-form-item label="投诉类型">
            <el-select v-model="complaintForm.category">
              <el-option v-for="c in categories" :key="c.name" :label="c.name" :value="c.name" />
            </el-select>
          </el-form-item>
          <el-form-item label="投诉内容（10 字以上；请勿包含他人隐私信息，先审后发）">
            <el-input v-model="complaintForm.content" type="textarea" :rows="4" maxlength="1000" show-word-limit />
          </el-form-item>
          <el-button type="primary" :loading="submitting" @click="submitComplaint" class="g-btn">提交投诉</el-button>
        </el-form>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import SampleChips from '@/components/SampleChips.vue'
import { lifeApi } from '@/api/modules'
import { useAuthStore } from '@/stores/auth'
import { usePager } from '@/composables/usePager'

const auth = useAuthStore()
const tab = ref('estate')

const estateKw = ref('')
const loading = ref(false)
const estate = ref<any>(null)
const records = ref<any>({})

const subjectType = ref('landlord')
const subjectKw = ref('')
const loading2 = ref(false)
const subjectSearched = ref(false)
const subjectComplaints = ref<any[]>([])

const estateComplaints = computed<any[]>(() => records.value?.complaints || [])
const { page: complaintsPage, total: complaintsTotal, paged: pagedComplaints } = usePager(estateComplaints)
const { page: subjectComplaintsPage, total: subjectComplaintsTotal, paged: pagedSubjectComplaints } = usePager(subjectComplaints)

const categories = [
  { name: '物业纠纷', icon: '🔧', desc: '物业服务差、公共设施失修' },
  { name: '押金纠纷', icon: '💰', desc: '退租扣押金、乱扣费用' },
  { name: '维修责任', icon: '🛠️', desc: '屋内设施损坏无人修' },
  { name: '虚假房源', icon: '🏷️', desc: '图文不符、挂假房钓鱼' },
  { name: '违规收费', icon: '📋', desc: '中介乱收服务费/看房费' },
  { name: '提前解约', icon: '📄', desc: '未到期被赶、单方毁约' },
]
const complaintForm = reactive({ subject_type: 'estate', subject_label: '', category: '物业纠纷', content: '' })
const submitting = ref(false)

async function searchEstate() {
  if (!estateKw.value.trim()) return ElMessage.warning('请输入小区名称')
  loading.value = true
  try {
    const data = await lifeApi.housingRecords({ subject_type: 'estate', keyword: estateKw.value.trim() })
    estate.value = data.estate
    records.value = data
  } finally {
    loading.value = false
  }
}

async function searchSubject() {
  if (!subjectKw.value.trim()) return ElMessage.warning('请输入关键词')
  loading2.value = true
  try {
    const data = await lifeApi.housingRecords({ subject_type: subjectType.value, keyword: subjectKw.value.trim() })
    subjectComplaints.value = data.complaints || []
    subjectSearched.value = true
  } finally {
    loading2.value = false
  }
}

function pickSubject(v: string) {
  const [type, kw] = v.split('|')
  subjectType.value = type
  subjectKw.value = kw
  searchSubject()
}

async function submitComplaint() {
  if (!auth.isLogged) return ElMessage.warning('请先登录')
  if (complaintForm.subject_label.trim().length < 2) return ElMessage.warning('请填写投诉对象名称')
  if (complaintForm.content.trim().length < 10) return ElMessage.warning('投诉内容至少 10 个字')
  submitting.value = true
  try {
    await lifeApi.createComplaint({
      subject_type: complaintForm.subject_type,
      subject_id: 0,
      subject_label: complaintForm.subject_label.trim(),
      content: complaintForm.content.trim(),
      category: complaintForm.category,
    })
    ElMessage.success('投诉已提交，审核通过后对外可见')
    complaintForm.content = ''
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
/* ===== 搜索面板：容器感 + 样例条同源对齐 ===== */
.search-panel {
  background: var(--tyt-bg-soft); border: 1px solid var(--tyt-border);
  border-radius: 12px; padding: 16px 16px 2px; margin-bottom: 22px;
}
.search-panel :deep(.sample-bar) { margin-top: 10px; }
.search-row { display: flex; gap: 10px; }
.search-row .el-input { flex: 1; }
.type-select { width: 118px; flex-shrink: 0; }
.g-btn { background: var(--tyt-gradient-brand); border: none; padding: 0 28px; font-weight: 600; }
.g-btn:hover, .g-btn:focus { background: linear-gradient(135deg, #4f46e5, #7c3aed); }

/* ===== 未搜索空态：三步走 + 类型速览 ===== */
.steps-card {
  border: 1px solid var(--tyt-border-light); border-radius: 12px;
  background: var(--tyt-card-2); padding: 18px 20px; margin-bottom: 18px;
}
.steps-title { font-size: 14.5px; font-weight: 700; margin-bottom: 14px; }
.steps { display: flex; align-items: stretch; gap: 12px; flex-wrap: wrap; }
.step {
  flex: 1; min-width: 180px; display: flex; align-items: center; gap: 12px;
  background: var(--tyt-card); border: 1px solid var(--tyt-border-light);
  border-radius: 10px; padding: 12px 14px;
}
.step-no {
  width: 26px; height: 26px; border-radius: 50%; flex-shrink: 0;
  display: inline-flex; align-items: center; justify-content: center;
  color: #fff; font-size: 13px; font-weight: 700;
  background: var(--tyt-gradient-brand);
}
.step-name { font-size: 13.5px; font-weight: 700; }
.step-desc { font-size: 12px; color: var(--tyt-text-dim); margin-top: 2px; }
.step-arrow { align-self: center; color: var(--tyt-text-tertiary); font-size: 16px; }

.cat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; margin-bottom: 18px; }
.cat-item {
  display: flex; align-items: center; gap: 12px;
  background: var(--tyt-card); border: 1px solid var(--tyt-border-light);
  border-radius: 10px; padding: 12px 14px; transition: all .18s;
}
.cat-item:hover { border-color: rgba(99, 102, 241, .4); transform: translateY(-2px); }
.cat-ic { font-size: 22px; }
.cat-name { font-size: 13.5px; font-weight: 700; }
.cat-desc { font-size: 12px; color: var(--tyt-text-dim); margin-top: 2px; }

.hint-bar {
  font-size: 12.5px; color: var(--tyt-text-dim); line-height: 1.8;
  background: var(--tyt-primary-soft); border-radius: 10px; padding: 10px 16px;
}
.hint-bar strong { color: var(--tyt-primary-dark); }

/* ===== 小区结果卡 ===== */
.estate-card {
  border: 1px solid var(--tyt-border-light); border-radius: 12px;
  background: var(--tyt-card-2); padding: 16px 20px; margin-bottom: 14px;
}
.estate-head { display: flex; align-items: baseline; gap: 12px; flex-wrap: wrap; margin-bottom: 12px; }
.estate-name { font-size: 17px; font-weight: 700; }
.estate-region {
  font-size: 12px; color: var(--tyt-primary-dark);
  background: var(--tyt-primary-soft); border-radius: 999px; padding: 2px 10px;
}
.desc-item .v.warn { color: var(--tyt-amber); font-weight: 700; }
.desc-item .v.ok { color: var(--tyt-green); font-weight: 700; }

.complaint-form { margin-top: 8px; }
h4 { margin: 18px 0 10px; font-size: 14px; }
.row-item { display: flex; align-items: baseline; gap: 8px; margin-bottom: 10px; font-size: 13px; line-height: 1.7; }
.pager { display: flex; justify-content: center; margin-top: 14px; }
</style>
