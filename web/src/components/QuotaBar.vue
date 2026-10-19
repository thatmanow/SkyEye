<template>
  <div class="quota-bar" v-if="label">
    <span class="q-label">{{ label }}</span>
    <el-progress :percentage="percent" :stroke-width="8" :color="barColor"
                 :show-text="false" class="q-progress" />
    <span class="q-text mono">{{ used }} / {{ limit === -1 ? '∞' : limit }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ label: string; used?: number; limit?: number }>()

const percent = computed(() => {
  if (!props.limit || props.limit < 0 || !props.used) return 0
  return Math.min(100, Math.round((props.used / props.limit) * 100))
})
const barColor = computed(() =>
  percent.value >= 100 ? '#ef4444' : percent.value >= 70 ? '#f59e0b' : '#6366f1')
</script>

<style scoped>
.quota-bar { display: flex; align-items: center; gap: 10px; font-size: 12px; }
.q-label { color: var(--tyt-text-dim); white-space: nowrap; }
.q-progress { width: 90px; }
.q-text { color: var(--tyt-text-dim); white-space: nowrap; }
</style>
