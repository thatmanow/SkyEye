<template>
  <div class="page">
    <h1 class="page-title">商业尽调中心</h1>
    <p class="page-sub">合作、投资、投标前的标准动作 —— 数据来自公开工商与司法渠道</p>

    <div class="entries">
      <router-link to="/biz/companies" class="entry">
        <div class="e-ic">🏢</div>
        <div class="e-title">企业查询</div>
        <div class="e-desc">工商 · 股东 · 投资 · 风险</div>
      </router-link>
      <router-link to="/biz/graph" class="entry">
        <div class="e-ic">🕸️</div>
        <div class="e-title">关系图谱</div>
        <div class="e-desc">股权穿透 · 实控人推导</div>
      </router-link>
      <router-link to="/biz/monitor" class="entry">
        <div class="e-ic">📡</div>
        <div class="e-title">商业监控</div>
        <div class="e-desc">动态追踪 · 日报周报</div>
      </router-link>
      <router-link to="/biz/reports" class="entry">
        <div class="e-ic">📄</div>
        <div class="e-title">尽调报告</div>
        <div class="e-desc">一键生成 PDF / Excel</div>
      </router-link>
      <router-link to="/biz/leads" class="entry">
        <div class="e-ic">💡</div>
        <div class="e-title">商机线索</div>
        <div class="e-desc">风险企业衍生商机</div>
      </router-link>
      <router-link to="/biz/stock" class="entry" v-if="auth.isLogged">
        <div class="e-ic">📈</div>
        <div class="e-title">股票分析</div>
        <div class="e-desc">六智能体协同 · 多维研判</div>
      </router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
const auth = useAuthStore()
</script>

<style scoped>
.entries { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; }
.entry { display: block; background: var(--tyt-card); border: 1px solid var(--tyt-border);
  border-radius: 14px; padding: 24px 20px; transition: all .2s; }
.entry:hover { transform: translateY(-3px); border-color: rgba(99,102,241,.45); }
.e-ic { font-size: 26px; margin-bottom: 10px; }
.e-title { font-size: 16px; font-weight: 700; margin-bottom: 6px; }
.e-desc { color: var(--tyt-text-dim); font-size: 12.5px; }
</style>
