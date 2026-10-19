import { computed, ref, watch, type Ref } from 'vue'

/** 客户端分页：每页最多 pageSize 条，超过一页才显示分页器 */
export function usePager(source: Ref<any[]>, pageSize = 10) {
  const page = ref(1)
  const total = computed(() => (source.value || []).length)
  const pages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))
  const paged = computed(() => {
    const arr = source.value || []
    if (total.value <= pageSize) return arr
    return arr.slice((page.value - 1) * pageSize, page.value * pageSize)
  })
  // 数据源整体替换（新搜索结果）时回到第一页
  watch(source, () => { page.value = 1 })
  watch(total, (t) => {
    if (page.value > Math.max(1, Math.ceil(t / pageSize))) page.value = 1
  })
  return { page, total, pages, paged, pageSize }
}
