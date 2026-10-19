<template>
  <div class="page wide">
    <h1 class="page-title">关系图谱</h1>
    <p class="page-sub">力导向动态布局 · 悬停查看节点 · 点击节点逐层展开 · 点击关系链查看关联详情</p>

    <div class="toolbar tyt-card">
      <el-select v-model="selectedCompanyId" filterable remote :remote-method="searchCompanies"
                 :loading="searching" placeholder="搜索企业名称，选择后加载图谱" style="width: 320px" clearable
                 @change="onSelectCompany">
        <el-option v-for="c in companyOptions" :key="c.id" :label="c.name" :value="c.id" />
      </el-select>

      <el-divider direction="vertical" />

      <span class="tool-label">路径查询：</span>
      <el-input-number v-model="fromId" :min="1" :controls="false" placeholder="起点ID" style="width: 110px" />
      <span class="arrow">→</span>
      <el-input-number v-model="toId" :min="1" :controls="false" placeholder="终点ID" style="width: 110px" />
      <el-button @click="findPath">查路径</el-button>

      <el-divider direction="vertical" />
      <el-button @click="resetGraph">清空画布</el-button>
      <span class="tool-tip text-dim">💡 拖拽节点可拉伸布局 · 单击节点展开一层 · 点击连线看关系</span>
    </div>
    <SampleChips :samples="['腾讯', '贵州茅台', '比亚迪', '三六零']" @pick="pickGraphCompany" />

    <div class="graph-wrap tyt-card">
      <div ref="container" class="graph-container"></div>
      <div class="legend">
        <span><i class="dot company"></i>企业</span>
        <span><i class="dot person"></i>自然人</span>
      </div>

      <!-- 关系链详情卡：点击边时显示 -->
      <div v-if="edgeCard.show" class="edge-card" :style="{ left: edgeCard.x + 'px', top: edgeCard.y + 'px' }">
        <button class="edge-close" @click="hideEdgeCard">✕</button>
        <div class="edge-title">🔗 关联关系</div>
        <div class="edge-parties">
          <div class="edge-node">
            <span class="edge-role">起点</span>
            <b>{{ edgeCard.sourceName }}</b>
          </div>
          <div class="edge-arrow">—{{ edgeCard.label }}→</div>
          <div class="edge-node">
            <span class="edge-role">终点</span>
            <b>{{ edgeCard.targetName }}</b>
          </div>
        </div>
        <div class="edge-meta">
          <span class="k">关系类型</span><b>{{ relText(edgeCard.rel) }}</b>
        </div>
        <div class="edge-meta">
          <span class="k">方向</span><b>{{ edgeCard.sourceName }} → {{ edgeCard.targetName }}</b>
        </div>
      </div>

      <el-empty v-if="empty" description="搜索并选择一家企业开始探索" class="graph-empty" />
    </div>

    <div class="bottom-panels">
      <div class="tyt-card panel">
        <h3>疑似实际控制人</h3>
        <template v-if="controllerCompanyId">
          <el-empty v-if="!controllers.length" description="未推导出自然人控股链路" :image-size="50" />
          <div v-for="(c, i) in controllers" :key="i" class="ctrl-item">
            <div class="ctrl-head">
              <span class="ctrl-name">{{ c.person }}</span>
              <el-tag type="warning" size="small" effect="dark">综合持股 {{ (c.effective * 100).toFixed(2) }}%</el-tag>
            </div>
            <div class="chain">
              <template v-for="(link, k) in c.chain" :key="k">
                <span class="link-node">{{ link.src }}</span>
                <span class="link-rel">—{{ link.rel === 'SHAREHOLDER_OF' ? `持股${link.ratio ?? ''}%` : link.rel }}→</span>
              </template>
              <span class="link-node">目标企业</span>
            </div>
          </div>
        </template>
        <p v-else class="text-dim panel-tip">加载任意企业图谱后自动推导</p>
      </div>

      <div class="tyt-card panel">
        <h3>路径结果</h3>
        <template v-if="pathResult">
          <el-empty v-if="!pathResult.found" description="4 跳内未找到关联路径" :image-size="50" />
          <template v-else>
            <el-tag type="success" effect="dark" style="margin-bottom: 10px">
              找到路径 · {{ pathResult.hops }} 跳
            </el-tag>
            <div class="path-chain">
              <template v-for="(n, i) in pathResult.nodes" :key="i">
                <span class="link-node" :class="n.type">{{ n.name }}</span>
                <span v-if="i < pathResult.nodes.length - 1" class="link-rel">
                  —{{ pathResult.edges[i]?.label || '关联' }}→
                </span>
              </template>
            </div>
          </template>
        </template>
        <p v-else class="text-dim panel-tip">输入两个节点 ID 查询最短关联路径</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import G6 from '@antv/g6'
import { ElMessage } from 'element-plus'
import SampleChips from '@/components/SampleChips.vue'
import { bizApi, graphApi } from '@/api/modules'

const container = ref<HTMLElement>()
const empty = ref(true)

const companyOptions = ref<any[]>([])
const searching = ref(false)
const selectedCompanyId = ref<number>()
const controllerCompanyId = ref<number>()
const controllers = ref<any[]>([])

const fromId = ref<number>()
const toId = ref<number>()
const pathResult = ref<any>(null)

let graph: any = null
let activeEdge: any = null

/* 数据驱动：G6 模型数组 + 名称索引，changeData 后力导向布局自动演化 */
const graphData = reactive<{ nodes: any[]; edges: any[] }>({ nodes: [], edges: [] })
const nodeMap = new Map<string, { id: string; name: string; nodeType: string }>()

const REL_NAMES: Record<string, string> = {
  HAS_LEGAL_REP: '法定代表人', EXECUTIVE_OF: '任职', SHAREHOLDER_OF: '持股',
  INVESTS_IN: '投资', SUPPLIES_TO: '供应', CO_INVESTOR_WITH: '共同投资',
}

function relText(rel: string) {
  return REL_NAMES[rel] || rel || '关联'
}

function esc(s: any) {
  return String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c] as string))
}

function degree(id: string) {
  return graphData.edges.filter((e) => e.source === id || e.target === id).length
}

/* 悬停节点信息卡（G6 Tooltip 插件） */
const tooltip = new G6.Tooltip({
  offsetX: 14,
  offsetY: 16,
  fixToNode: [1, 0.5],
  itemTypes: ['node'],
  getContent(e: any) {
    const m = e.item.getModel()
    const typeText = m.nodeType === 'person' ? '自然人' : '企业'
    const rel = degree(m.id)
    return `<div class="g6-tip">
      <div class="g6-tip-title">${esc(m.label)}</div>
      <div class="g6-tip-row"><span>类型</span><b>${typeText}</b></div>
      <div class="g6-tip-row"><span>关联关系</span><b>${rel} 条</b></div>
      <div class="g6-tip-row"><span>节点 ID</span><b>${esc(m.id)}</b></div>
      <div class="g6-tip-hint">🖱 单击展开下一层 · 拖拽拉伸布局</div>
    </div>`
  },
})

/* 关系链详情卡状态 */
const edgeCard = reactive({ show: false, x: 0, y: 0, sourceName: '', targetName: '', label: '', rel: '' })

function hideEdgeCard() {
  edgeCard.show = false
  if (activeEdge && !activeEdge.destroyed) graph?.setItemState(activeEdge, 'active', false)
  activeEdge = null
}

async function searchCompanies(q: string) {
  if (!q || q.trim().length < 1) return
  searching.value = true
  try {
    const data = await bizApi.searchCompanies({ keyword: q.trim(), page_size: 10 })
    companyOptions.value = data.items || []
  } finally {
    searching.value = false
  }
}

async function onSelectCompany(id?: number) {
  if (!id) return
  resetGraphData()
  const data = await graphApi.companyGraph(id)
  seedGraph(data, id)
  controllerCompanyId.value = id
  const ctrl = await graphApi.controller(id)
  controllers.value = ctrl.controllers || []
}

async function pickGraphCompany(q: string) {
  await searchCompanies(q)
  const first = companyOptions.value[0]
  if (!first) return ElMessage.warning(`未找到企业：${q}`)
  selectedCompanyId.value = first.id
  onSelectCompany(first.id)
}

function resetGraphData() {
  hideEdgeCard()
  graphData.nodes = []
  graphData.edges = []
  nodeMap.clear()
  controllers.value = []
  pathResult.value = null
  controllerCompanyId.value = undefined
  if (graph) {
    graph.clear()
    graph.render()
  }
}

function nodeStyle(n: any): any {
  const isPerson = n.type === 'person'
  return {
    id: String(n.id),
    label: n.name,
    nodeType: n.type,
    labelCfg: { style: { fill: '#475569', fontSize: 11 } },
    style: { fill: isPerson ? '#059669' : '#4f46e5', stroke: isPerson ? '#34d399' : '#818cf8' },
  }
}

function edgeStyle(e: any) {
  return {
    source: String(e.source),
    target: String(e.target),
    label: e.label || relText(e.rel),
    rel: e.rel,
    style: { stroke: '#94a3b8', lineWidth: 2, endArrow: { path: G6.Arrow.triangle(8, 8, 12), fill: '#94a3b8' } },
    labelCfg: { style: { fill: '#475569', fontSize: 10, background: { fill: '#ffffffd9', padding: [2, 4, 2, 4] } } },
  }
}

function seedGraph(data: any, centerId: number) {
  if (!graph) return
  const nodes = (data.nodes || []).map((n: any) => {
    const s: any = nodeStyle(n)
    if (n.id === centerId) {
      s.size = 46
      s.style = { fill: '#4f46e5', stroke: '#6366f1', lineWidth: 2 }
      s.labelCfg = { style: { fill: '#ffffff', fontSize: 13, fontWeight: 600 } }
    }
    return s
  })
  const edges = (data.edges || []).map(edgeStyle)
  nodes.forEach((n: any) => nodeMap.set(n.id, { id: n.id, name: n.label, nodeType: n.nodeType }))
  graphData.nodes = nodes
  graphData.edges = edges
  graph.changeData({ nodes: JSON.parse(JSON.stringify(nodes)), edges: JSON.parse(JSON.stringify(edges)) })
  empty.value = false
}

async function onNodeClick(evt: any) {
  const id = Number(evt.item.getID())
  try {
    const data = await graphApi.expand(id)
    if (!data.nodes?.length) {
      ElMessage.info('该节点暂无可展开的关系')
      return
    }
    let added = 0
    ;(data.nodes || []).forEach((n: any) => {
      const sid = String(n.id)
      if (nodeMap.has(sid)) return
      const s: any = nodeStyle(n)
      nodeMap.set(sid, { id: sid, name: n.name, nodeType: n.type })
      graphData.nodes.push(s)
      added++
    })
    ;(data.edges || []).forEach((e: any) => {
      const key = `${e.source}|${e.target}|${e.label || e.rel}`
      if (graphData.edges.some((x) => `${x.source}|${x.target}|${x.label}` === key)) return
      graphData.edges.push(edgeStyle(e))
    })
    // changeData 触发力导向重算：旧节点以当前位置为初值，新节点被弹开排布
    graph.changeData({ nodes: JSON.parse(JSON.stringify(graphData.nodes)), edges: JSON.parse(JSON.stringify(graphData.edges)) })
    if (added) ElMessage.success(`展开 ${added} 个关联节点，布局已自动调整`)
    else ElMessage.info('该节点的关联节点已在画布中')
  } catch {
    /* 429 等已提示 */
  }
}

async function findPath() {
  if (!fromId.value || !toId.value) return ElMessage.warning('请输入起点与终点节点 ID')
  const data = await graphApi.path(fromId.value, toId.value)
  pathResult.value = data
  if (data.found && graph) {
    resetGraphData()
    const nodes = (data.nodes || []).map((n: any) => nodeStyle(n))
    const edges = (data.edges || []).map(edgeStyle)
    nodes.forEach((n: any) => nodeMap.set(n.id, { id: n.id, name: n.label, nodeType: n.nodeType }))
    graphData.nodes = nodes
    graphData.edges = edges
    graph.changeData({ nodes: JSON.parse(JSON.stringify(nodes)), edges: JSON.parse(JSON.stringify(edges)) })
    empty.value = false
  }
}

function resetGraph() {
  resetGraphData()
  empty.value = true
  selectedCompanyId.value = undefined
}

function initGraph() {
  if (!container.value) return
  graph = new G6.Graph({
    container: container.value,
    width: container.value.clientWidth,
    height: 560,
    plugins: [tooltip],
    modes: {
      default: ['drag-canvas', 'zoom-canvas', 'drag-node', 'activate-relations'],
    },
    layout: {
      type: 'force',
      preventOverlap: true,
      nodeSize: 44,
      nodeStrength: -70,
      edgeStrength: 0.6,
      collide: 70,
      linkDistance: 140,
      alpha: 0.9,
      alphaDecay: 0.028,
      alphaMin: 0.001,
    },
    defaultNode: {
      type: 'circle',
      size: 36,
      style: { fill: '#6366f1', stroke: '#818cf8', lineWidth: 1.5 },
      stateStyles: { inactive: { opacity: 0.25 } },
    },
    defaultEdge: {
      type: 'quadratic',
      style: { stroke: '#94a3b8', lineWidth: 2 },
      stateStyles: {
        hover: { stroke: '#818cf8', lineWidth: 4 },
        active: { stroke: '#6366f1', lineWidth: 3.5 },
        inactive: { opacity: 0.15 },
      },
    },
  })

  graph.on('node:click', onNodeClick)

  // 点击关系链：弹出两端节点的关系详情卡
  graph.on('edge:click', (evt: any) => {
    const m = evt.item.getModel()
    const src = nodeMap.get(m.source)
    const dst = nodeMap.get(m.target)
    if (activeEdge && !activeEdge.destroyed) graph.setItemState(activeEdge, 'active', false)
    activeEdge = evt.item
    graph.setItemState(evt.item, 'active', true)
    const wrap = container.value!.getBoundingClientRect()
    const x = Math.min(Math.max(12, evt.canvasX + 16), wrap.width - 268)
    const y = Math.min(Math.max(12, evt.canvasY - 10), wrap.height - 190)
    edgeCard.show = true
    edgeCard.x = x
    edgeCard.y = y
    edgeCard.sourceName = src?.name || m.source
    edgeCard.targetName = dst?.name || m.target
    edgeCard.label = m.label || relText(m.rel)
    edgeCard.rel = m.rel
  })

  graph.on('canvas:click', hideEdgeCard)
  graph.on('node:click', hideEdgeCard)

  // 悬停关系链：变粗高亮 + 手型光标，提示可点击
  graph.on('edge:mouseenter', (evt: any) => {
    graph.setItemState(evt.item, 'hover', true)
    graph.get('canvas').setCursor('pointer')
  })
  graph.on('edge:mouseleave', (evt: any) => {
    graph.setItemState(evt.item, 'hover', false)
    graph.get('canvas').setCursor('default')
  })

  // 拖拽节点松手后重新触发布局：连线弹力带动周边节点重新排布，实现"可拉伸"
  graph.on('node:dragend', () => {
    graph.layout()
  })

  window.addEventListener('resize', resize)
}

function resize() {
  if (graph && container.value) graph.changeSize(container.value.clientWidth, 560)
}

onMounted(initGraph)
onBeforeUnmount(() => {
  window.removeEventListener('resize', resize)
  if (graph) graph.destroy()
})
</script>

<style scoped>
.wide { max-width: 1400px; }
.toolbar { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 14px; }
.tool-label { color: var(--tyt-text-dim); font-size: 13px; }
.arrow { color: var(--tyt-text-dim); }
.tool-tip { font-size: 12px; margin-left: auto; }
.graph-wrap { position: relative; padding: 0; overflow: hidden; }
.graph-container { width: 100%; height: 560px; }
.graph-empty { position: absolute; top: 200px; left: 50%; transform: translateX(-50%); }
.legend { position: absolute; top: 14px; right: 16px; display: flex; gap: 16px; font-size: 12px; color: var(--tyt-text-dim); }
.dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 5px; }
.dot.company { background: #6366f1; }
.dot.person { background: #059669; }

/* 关系链详情卡 */
.edge-card {
  position: absolute; z-index: 20; width: 252px;
  background: #fff; border: 1px solid var(--tyt-border); border-radius: 12px;
  box-shadow: 0 12px 32px -8px rgba(15, 23, 42, .22); padding: 14px 16px;
}
.edge-close {
  position: absolute; top: 8px; right: 8px; width: 22px; height: 22px;
  border: none; border-radius: 6px; background: var(--tyt-bg-soft);
  color: var(--tyt-text-dim); cursor: pointer; font-size: 11px; line-height: 1;
}
.edge-close:hover { color: var(--tyt-primary); background: var(--tyt-primary-soft); }
.edge-title { font-size: 13.5px; font-weight: 700; margin-bottom: 10px; color: var(--tyt-text); }
.edge-parties { display: flex; flex-direction: column; gap: 8px; margin-bottom: 10px; }
.edge-node {
  background: var(--tyt-bg-soft); border-radius: 8px; padding: 6px 10px;
  display: flex; flex-direction: column; gap: 1px;
}
.edge-role { font-size: 10.5px; color: var(--tyt-text-tertiary); }
.edge-node b { font-size: 13px; color: var(--tyt-text); word-break: break-all; }
.edge-arrow {
  align-self: center; font-size: 12px; font-weight: 700;
  color: var(--tyt-primary-dark); background: var(--tyt-primary-soft);
  border-radius: 999px; padding: 2px 12px;
}
.edge-meta { display: flex; align-items: baseline; gap: 10px; font-size: 12px; padding: 3px 0; }
.edge-meta .k { color: var(--tyt-text-dim); flex-shrink: 0; }
.edge-meta b { color: var(--tyt-text); word-break: break-all; }

.bottom-panels { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 16px; }
.panel h3 { margin: 0 0 12px; font-size: 15px; }
.panel-tip { font-size: 12.5px; margin: 8px 0 0; }
.ctrl-item { border: 1px solid var(--tyt-border); border-radius: 10px; padding: 10px 12px; margin-bottom: 10px; }
.ctrl-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.ctrl-name { font-weight: 700; font-size: 14px; }
.chain, .path-chain { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; font-size: 12.5px; line-height: 2; }
.link-node { background: var(--tyt-card-2); border: 1px solid var(--tyt-border); border-radius: 6px; padding: 2px 8px; }
.link-node.person { border-color: #059669; color: #34d399; }
.link-rel { color: var(--tyt-text-dim); font-size: 12px; }
</style>

<style>
/* G6 Tooltip 全局样式（插件挂载在 body 下，scoped 不生效） */
.g6-component-tooltip {
  border: none !important; border-radius: 10px !important;
  box-shadow: 0 12px 32px -8px rgba(15, 23, 42, .25) !important;
  background: #fff !important; padding: 0 !important; overflow: hidden;
}
.g6-tip { min-width: 168px; padding: 10px 14px; }
.g6-tip-title {
  font-size: 13.5px; font-weight: 700; color: #1e293b; margin-bottom: 7px;
  padding-left: 8px; border-left: 3px solid #6366f1; line-height: 1.35;
}
.g6-tip-row { display: flex; justify-content: space-between; gap: 16px; font-size: 12px; padding: 2.5px 0; }
.g6-tip-row span { color: #94a3b8; }
.g6-tip-row b { color: #334155; font-weight: 600; }
.g6-tip-hint {
  margin-top: 7px; padding-top: 6px; border-top: 1px dashed #e2e8f0;
  font-size: 10.5px; color: #94a3b8;
}
</style>
