<template>
  <div class="sample-bar">
    <span class="sample-label">{{ label }}</span>
    <button v-for="s in samples" :key="String(s)" type="button" class="sample-chip"
            @click="$emit('pick', typeof s === 'string' ? s : s.value)">
      {{ typeof s === 'string' ? s : s.label }}
    </button>
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  label?: string
  samples: (string | { label: string; value: string })[]
}>(), { label: '试试：' })

defineEmits<{ pick: [value: string] }>()
</script>

<style scoped>
.sample-bar { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin: -10px 0 18px; }
.sample-label { font-size: 12px; color: var(--tyt-text-dim); flex-shrink: 0; }
.sample-chip {
  font-size: 12px; color: var(--tyt-text-dim); background: var(--tyt-card);
  border: 1px solid var(--tyt-border); border-radius: 999px; padding: 4px 13px;
  cursor: pointer; transition: all .18s ease; white-space: nowrap;
}
.sample-chip:hover {
  color: #fff; background: var(--tyt-gradient-brand); border-color: transparent;
  box-shadow: 0 2px 8px -2px rgba(99, 102, 241, .5); transform: translateY(-1px);
}
</style>
