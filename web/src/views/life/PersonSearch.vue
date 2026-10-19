<template>
  <div class="page">
    <h1 class="page-title">个人查询（严格受限）</h1>
    <p class="page-sub">仅支持公开合法的失信 / 涉诉 / 行政处罚记录检索，结果强制脱敏</p>

    <el-alert type="warning" :closable="false" class="comp-alert">
      <p><b>合规声明：</b>本功能不提供身份证号、手机号、住址等任何非公开信息检索；姓名仅作检索条件，返回结果全部脱敏；
      不建立"姓名 → 个人档案"聚合页；查询行为全量写入审计日志。请勿将本工具用于任何违法用途。</p>
    </el-alert>

    <div class="tyt-card search-bar">
      <el-input v-model="name" placeholder="姓名（2 个汉字以上）" size="large" clearable @keyup.enter="doSearch">
        <template #append>
          <el-button :loading="loading" @click="doSearch">查 询</el-button>
        </template>
      </el-input>
    </div>
    <SampleChips :samples="['张小三', '李亚四', '王小五']" @pick="v => { name = v; doSearch() }" />

    <template v-if="result">
      <div class="tyt-card">
        <div class="r-head">
          <span class="r-name mono">{{ result.masked_name }}</span>
          <el-tag :type="result.total ? 'danger' : 'success'" effect="dark">
            {{ result.total ? `发现 ${result.total} 条公开风险记录` : '未发现公开风险记录' }}
          </el-tag>
        </div>

        <template v-if="result.records?.length">
          <div v-for="r in pagedRecords" :key="r.id" class="r-item">
            <div class="r-title">
              <RiskTag :map="r.risk_type" />
              <RiskTag :map="r.risk_level" />
              <span class="r-subtype">{{ r.risk_subtype }}</span>
            </div>
            <div class="r-body">
              <p class="r-digest">{{ r.title }}</p>
              <div class="r-meta">
                <span v-if="r.court">{{ r.court }}</span>
                <span v-if="r.case_no" class="mono">{{ r.case_no }}</span>
                <span v-if="r.occur_date">{{ r.occur_date }}</span>
                <span class="text-dim">来源：{{ r.source }}</span>
              </div>
            </div>
          </div>
          <div class="pager" v-if="recordsTotal > 10">
            <el-pagination background layout="prev, pager, next" :total="recordsTotal" :page-size="10"
                           :current-page="recordsPage" @current-change="(p: number) => recordsPage = p" />
          </div>
        </template>

        <p class="r-note">{{ result.compliance_note }}</p>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import SampleChips from '@/components/SampleChips.vue'
import { lifeApi } from '@/api/modules'
import RiskTag from '@/components/RiskTag.vue'
import { useAuthStore } from '@/stores/auth'
import { usePager } from '@/composables/usePager'

const auth = useAuthStore()
const name = ref('')
const loading = ref(false)
const result = ref<any>(null)

const riskRecords = computed<any[]>(() => result.value?.records || [])
const { page: recordsPage, total: recordsTotal, paged: pagedRecords } = usePager(riskRecords)

async function doSearch() {
  if (!auth.isLogged) return ElMessage.warning('请先登录后使用个人查询')
  if (name.value.trim().length < 2) return ElMessage.warning('姓名至少 2 个字')
  loading.value = true
  try {
    result.value = await lifeApi.personSearch({ name: name.value.trim() })
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.comp-alert { margin-bottom: 16px; }
.comp-alert p { margin: 0; font-size: 13px; line-height: 1.8; }
.search-bar { margin-bottom: 16px; }
.r-head { display: flex; align-items: center; gap: 14px; margin-bottom: 14px; }
.r-name { font-size: 18px; font-weight: 700; }
.r-item { border: 1px solid var(--tyt-border); border-radius: 10px; padding: 12px 14px; margin-bottom: 10px; }
.pager { display: flex; justify-content: center; margin-top: 14px; }
.r-title { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.r-subtype { color: var(--tyt-text-dim); font-size: 12.5px; }
.r-digest { margin: 0 0 6px; font-size: 13.5px; line-height: 1.7; }
.r-meta { display: flex; gap: 14px; flex-wrap: wrap; color: var(--tyt-text-dim); font-size: 12px; }
.r-note { color: #94a3b8; font-size: 12px; margin: 14px 0 0; line-height: 1.8; }
</style>
