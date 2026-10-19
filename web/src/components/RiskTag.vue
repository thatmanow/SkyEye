<template>
  <el-tag :type="typeMap[map] || 'info'" size="small" effect="dark" round>{{ label }}</el-tag>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ map: string; value?: string }>()

const typeMap: Record<string, string> = {
  judicial: 'danger', business: 'warning', finance: 'warning',
  public_opinion: 'info', admin_penalty: 'danger',
  high: 'danger', medium: 'warning', low: 'success',
  approved: 'success', pending: 'warning', rejected: 'danger', offline: 'info',
  done: 'success', queued: 'info', running: 'warning', failed: 'danger',
  存续: 'success', 注销: 'danger', 吊销: 'danger', 迁出: 'info',
}

const labelMap: Record<string, string> = {
  judicial: '司法风险', business: '经营风险', finance: '财务风险',
  public_opinion: '舆情风险', admin_penalty: '行政处罚',
  high: '高', medium: '中', low: '低',
  approved: '已过审', pending: '待审核', rejected: '未通过', offline: '已下线',
  done: '已完成', queued: '排队中', running: '生成中', failed: '失败',
}

const label = computed(() => props.value ?? labelMap[props.map] ?? props.map)
</script>
