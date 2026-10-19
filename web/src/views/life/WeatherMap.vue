<template>
  <div class="page weather-page">
    <h1 class="page-title">定位天气</h1>
    <p class="page-sub">Open-Meteo 开放数据 · 高德地图渲染 —— 当前天气 / 逐时预报 / 7 日趋势 / 生活指数</p>

    <!-- 顶栏 -->
    <div class="wth-topbar">
      <div class="wth-loc">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
        <span class="wth-loc-text">{{ userCity || w.city }}</span>
        <span class="wth-loc-tag" :class="locTagClass"
              :title="locMethod === 'ip' ? 'IP 定位仅能到城市级；允许浏览器定位权限后点击重新定位，可精确到区县' : undefined">{{ locTagText }}</span>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="opacity:.5"><polyline points="6 9 12 15 18 9"></polyline></svg>
      </div>
      <div class="wth-topbar-actions">
        <!-- 网络定位辅助：WiFi / 基站 / 融合（第一版同款定位方式切换） -->
        <el-dropdown trigger="click" @command="onNetworkLocate">
          <button class="wth-icon-btn" :class="{ active: netLocating }" title="网络定位辅助（WiFi / 基站 / 融合）">
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12.55a11 11 0 0 1 14.08 0"></path><path d="M1.42 9a16 16 0 0 1 21.16 0"></path><path d="M8.53 16.11a6 6 0 0 1 6.95 0"></path><line x1="12" y1="20" x2="12.01" y2="20"></line></svg>
          </button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="auto">自动定位 · 融合（±50m）</el-dropdown-item>
              <el-dropdown-item command="wifi">WiFi 定位（±500m）</el-dropdown-item>
              <el-dropdown-item command="cellular">基站定位（±2km）</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <button class="wth-icon-btn" title="重新定位" @click="reload">
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="16"></line><line x1="8" y1="12" x2="16" y2="12"></line></svg>
        </button>
        <button class="wth-icon-btn" title="地图全屏" @click="openMapOverlay">
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"></polygon><line x1="8" y1="2" x2="8" y2="18"></line><line x1="16" y1="6" x2="16" y2="22"></line></svg>
        </button>
      </div>
    </div>

    <div v-if="loading" class="wth-loading">
      <div class="spinner"></div>
      <div>天气数据加载中…</div>
    </div>

    <div v-else class="wth-layout">
      <!-- 主栏 -->
      <div class="wth-col-main">
        <!-- 当前天气 -->
        <div class="wth-current-card">
          <div class="wth-current-time">{{ currentTime }}</div>
          <div class="wth-current-body">
            <div class="wth-current-icon">{{ w.icon }}</div>
            <div class="wth-current-temp">{{ w.temperature }}°</div>
            <div class="wth-current-desc">
              <div class="wth-current-cond">{{ w.condition }}</div>
              <div class="wth-current-feels">体感 {{ w.feels_like }}°</div>
            </div>
          </div>
          <div class="wth-current-summary">{{ w.summary }}</div>
          <div class="wth-card-updated">{{ w.source }} · 更新于 {{ w.updated_at }}</div>
          <div class="wth-metrics">
            <div class="wth-metric">
              <span class="wth-metric-dot" :style="{ background: aqiColor }"></span>
              <span class="wth-metric-label">空气质量</span>
              <span class="wth-metric-value">{{ w.aqi }}</span>
              <span class="wth-metric-unit">{{ w.aqi_level }}</span>
            </div>
            <div class="wth-metric"><span class="wth-metric-label">风速</span><span class="wth-metric-value">{{ w.wind_speed }} km/h</span></div>
            <div class="wth-metric"><span class="wth-metric-label">湿度</span><span class="wth-metric-value">{{ w.humidity }}%</span></div>
            <div class="wth-metric"><span class="wth-metric-label">能见度</span><span class="wth-metric-value">{{ w.visibility }} km</span></div>
            <div class="wth-metric"><span class="wth-metric-label">气压</span><span class="wth-metric-value">{{ w.pressure }} hPa</span></div>
            <div class="wth-metric"><span class="wth-metric-label">露点</span><span class="wth-metric-value">{{ w.dew }}°</span></div>
          </div>
        </div>

        <!-- 每小时预报 -->
        <div class="wth-forecast-section">
          <div class="wth-forecast-header">
            <div class="wth-forecast-tabs">
              <button v-for="t in fcTabs" :key="t.key" class="wth-fc-tab"
                      :class="{ active: fcTab === t.key }" @click="fcTab = t.key">{{ t.label }}</button>
            </div>
            <div class="wth-forecast-view">
              <button class="wth-view-btn" :class="{ active: fcView === 'chart' }" @click="fcView = 'chart'">图表</button>
              <button class="wth-view-btn" :class="{ active: fcView === 'list' }" @click="fcView = 'list'">列表</button>
            </div>
          </div>

          <div v-if="fcView === 'chart'" class="wth-hourly-chart">
            <div class="wth-hourly-header">
              <span class="wth-hourly-title">{{ fcMeta.title }}</span>
              <label class="wth-toggle">
                <input v-if="fcTab === 'overview'" v-model="showFeels" type="checkbox">
                <span class="wth-toggle-track"></span>
                <span v-if="fcTab === 'overview'" class="wth-toggle-label">体感温度</span>
              </label>
            </div>
            <div class="wth-hourly-body">
              <div class="wth-hourly-curve">
                <svg class="wth-hourly-svg" viewBox="0 0 800 200" preserveAspectRatio="none">
                  <defs>
                    <linearGradient id="wth-temp-grad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stop-color="#3b82f6" stop-opacity="0.3"></stop>
                      <stop offset="100%" stop-color="#3b82f6" stop-opacity="0"></stop>
                    </linearGradient>
                  </defs>
                  <path :d="fillPath" fill="url(#wth-temp-grad)"></path>
                  <path :d="linePath" fill="none" :stroke="fcMeta.color" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path>
                  <path v-if="fcTab === 'overview' && showFeels" :d="feelsPath" fill="none" stroke="#a78bfa" stroke-width="1.5" stroke-dasharray="4 3" stroke-linecap="round"></path>
                </svg>
                <div class="wth-hourly-items">
                  <div v-for="(h, i) in w.hourly" :key="i" class="wth-hourly-item">
                    <div class="wth-h-time">{{ h.time }}</div>
                    <div class="wth-h-icon">{{ h.icon }}</div>
                    <div class="wth-h-val">{{ fcVal(h) }}{{ fcMeta.unit }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-else class="wth-hourly-list">
            <div v-for="(h, i) in pagedHourly" :key="i" class="wth-h-row">
              <span class="wth-h-row-time">{{ h.time }}</span>
              <span class="wth-h-row-icon">{{ h.icon }}</span>
              <span class="wth-h-row-cond">{{ h.condition }}</span>
              <span class="wth-h-row-val">{{ fcVal(h) }}{{ fcMeta.unit }}<template v-if="fcTab === 'overview'"> · 体感 {{ h.feels }}°</template></span>
              <span class="wth-h-row-pop" v-if="h.pop">降水 {{ h.pop }}%</span>
            </div>
            <div class="pager" v-if="hourlyTotal > 10">
              <el-pagination small background layout="prev, pager, next" :total="hourlyTotal" :page-size="10"
                             :current-page="hourlyPage" @current-change="(p: number) => hourlyPage = p" />
            </div>
          </div>
        </div>

        <!-- 7 日预报 -->
        <div class="wth-daily-scroll">
          <div v-for="(d, i) in w.daily" :key="i" class="wth-daily-item" :class="{ today: i === 0 }">
            <div class="wth-daily-day">{{ d.day }}</div>
            <div class="wth-daily-date">{{ d.date }}</div>
            <div class="wth-daily-icon">{{ d.icon }}</div>
            <div class="wth-daily-cond">{{ d.condition }}</div>
            <div class="wth-daily-temps"><span class="hi">{{ d.high }}°</span> <span class="lo">{{ d.low }}°</span></div>
          </div>
        </div>
      </div>

      <!-- 侧栏 -->
      <div class="wth-col-side">
        <div class="wth-map-card">
          <div class="wth-map-tabs">
            <button v-for="t in mapTabs" :key="t.key" class="wth-map-tab"
                    :class="{ active: mapLayer === t.key }" @click="switchLayer(t.key)">{{ t.label }}</button>
          </div>
          <div class="wth-map-body">
            <div class="wmap-stage">
              <div id="wth-amap" class="amap-container"></div>
              <span class="wmap-coord">{{ w.latitude?.toFixed(4) }}, {{ w.longitude?.toFixed(4) }}</span>
            </div>
          </div>
          <div class="wth-map-footer">
            <span class="wth-map-info">{{ mapInfo }}</span>
            <button class="wth-map-open-link" @click="openMapOverlay">打开地图 ›</button>
          </div>
        </div>

        <!-- 周边地点（网络定位辅助结果） -->
        <div v-if="nearbyPlaces.length" class="wth-nearby-card">
          <div class="wth-nearby-head">
            <span class="wth-nearby-title">📍 周边地点</span>
            <span class="wth-nearby-sub">{{ netLocLabel }} · {{ nearbyPlaces.length }} 个地点</span>
          </div>
          <div class="wth-nearby-list">
            <div v-for="p in nearbyPlaces" :key="p.name" class="wth-nearby-item">
              <span class="wth-nearby-icon">{{ p.icon }}</span>
              <span class="wth-nearby-name">{{ p.name }}</span>
              <span class="wth-nearby-type">{{ p.type }}</span>
              <span class="wth-nearby-dist">{{ fmtDist(p.distance_m) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 生活指数：页面最底部，全宽横排 -->
    <div v-if="!loading" class="wth-life-section">
      <div class="wth-life-head">🌤️ 生活指数</div>
      <div class="wth-life-grid">
        <div v-for="l in w.life_index" :key="l.name" class="wth-life-item">
          <div class="wth-life-icon">{{ l.icon }}</div>
          <div class="wth-life-name">{{ l.name }}</div>
          <div class="wth-life-value">{{ l.value }}</div>
        </div>
      </div>
    </div>

    <!-- 地图全屏弹窗 -->
    <div class="amap-overlay" :class="{ show: mapOverlay }" @click.self="closeMapOverlay">
      <div class="amap-overlay-header">
        <span class="amap-overlay-title">{{ userCity || w.city }} · 地图全屏</span>
        <button class="amap-overlay-back" @click="closeMapOverlay">‹ 返回天气</button>
      </div>
      <div id="wth-amap-full" class="amap-overlay-body"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { weatherApi } from '@/api/modules'
import { usePager } from '@/composables/usePager'
import { nearestCity, wgs84ToGcj02 } from '@/utils/chinaGeo'

const loading = ref(true)
const w = ref<any>({})
const currentTime = ref('')
const showFeels = ref(false)
const fcTab = ref('overview')
const fcView = ref('chart')
const mapLayer = ref('rain')
const mapOverlay = ref(false)

const fcTabs = [
  { key: 'overview', label: '每小时预报' },
  { key: 'rain', label: '降水' },
  { key: 'wind', label: '风速' },
  { key: 'humidity', label: '湿度' },
]
const mapTabs = [
  { key: 'rain', label: '降水' },
  { key: 'temp', label: '温度' },
  { key: 'wind', label: '风速' },
]
const MAP_STYLES: Record<string, string> = {
  rain: 'amap://styles/normal',
  temp: 'amap://styles/fresh',
  wind: 'amap://styles/grey',
}

const hourlyList = computed<any[]>(() => w.value.hourly || [])
const { page: hourlyPage, total: hourlyTotal, paged: pagedHourly } = usePager(hourlyList)

const fcMeta = computed(() => ({
  overview: { title: '概览', color: '#3b82f6', unit: '°' },
  rain: { title: '降水概率', color: '#0ea5e9', unit: '%' },
  wind: { title: '风速', color: '#10b981', unit: ' km/h' },
  humidity: { title: '相对湿度', color: '#8b5cf6', unit: '%' },
} as any)[fcTab.value])

const aqiColor = computed(() => {
  const aqi = w.value.aqi ?? 50
  if (aqi <= 50) return '#22c55e'
  if (aqi <= 100) return '#f59e0b'
  return '#ef4444'
})

const mapInfo = computed(() => {
  if (mapLayer.value === 'rain') {
    const pop = Math.max(0, ...(w.value.hourly?.slice(0, 6).map((h: any) => h.pop ?? 0) || [0]))
    return pop > 30 ? `未来数小时降水概率 ${pop}%，建议携带雨具。` : '至少数小时内没有明显降水。'
  }
  if (mapLayer.value === 'temp') return `当前气温 ${w.value.temperature}°C，体感 ${w.value.feels_like}°C。`
  return `当前风速 ${w.value.wind_speed} km/h。`
})

function fcVal(h: any) {
  return ({ overview: h.temp, rain: h.pop, wind: h.wind, humidity: h.humidity } as any)[fcTab.value]
}

/* ---- SVG 平滑曲线 ---- */
function buildPath(vals: number[], width = 800, height = 200, pad = 20): { d: string } {
  if (!vals.length) return { d: '' }
  const min = Math.min(...vals), max = Math.max(...vals)
  const span = max - min || 1
  const step = (width - pad * 2) / (vals.length - 1 || 1)
  const pts = vals.map((v, i) => [pad + i * step, height - pad - ((v - min) / span) * (height - pad * 2)])
  let d = `M ${pts[0][0]},${pts[0][1]}`
  for (let i = 1; i < pts.length; i++) {
    const [x0, y0] = pts[i - 1], [x1, y1] = pts[i]
    const cx = (x0 + x1) / 2
    d += ` C ${cx},${y0} ${cx},${y1} ${x1},${y1}`
  }
  return { d }
}

const linePath = computed(() => {
  const vals = (w.value.hourly || []).map(fcVal).filter((v: any) => v !== undefined)
  return buildPath(vals).d
})
const fillPath = computed(() => {
  const vals = (w.value.hourly || []).map(fcVal).filter((v: any) => v !== undefined)
  const { d } = buildPath(vals)
  return d ? `${d} L 780,200 L 20,200 Z` : ''
})
const feelsPath = computed(() => {
  const vals = (w.value.hourly || []).map((h: any) => h.feels)
  return buildPath(vals).d
})

/* ---- 高德地图 + 用户位置标注 ---- */
let map: any = null
let mapFull: any = null
let amapKey = ''
let sideOverlay: { marker: any; circle: any } | null = null
let fullOverlay: { marker: any; circle: any } | null = null
const LOC_STYLE_ID = 'wth-loc-marker-style'

const locStatus = ref<'locating' | 'located' | 'default'>('locating')
const userCity = ref('')
const userDistrict = ref('')
const locAccuracy = ref(0)
const locMethod = ref<'none' | 'browser' | 'ip' | 'network'>('none')
/* 网络定位辅助（WiFi / 基站 / 融合，第一版同款） */
const netLocLabel = ref('')
const netLocating = ref(false)
const nearbyPlaces = ref<any[]>([])
const NETWORK_METHOD_LABELS: Record<string, string> = {
  auto: '融合定位', wifi: 'WiFi 定位', cellular: '基站定位',
}
const userPos = {
  wgs: null as { lat: number; lon: number; accuracy: number } | null,
  gcj: null as [number, number] | null,
}

/* 定位精度显示：±1800m / ±2.5km */
function fmtAcc(m: number): string {
  return m >= 1000 ? `±${(m / 1000).toFixed(m >= 10000 ? 0 : 1)}km` : `±${Math.round(m)}m`
}

/* 距离显示：1800m / 2.5km（周边地点用，无 ± 前缀） */
function fmtDist(m: number): string {
  return m >= 1000 ? `${(m / 1000).toFixed(m >= 10000 ? 0 : 1)}km` : `${Math.round(m)}m`
}

const locTagText = computed(() => {
  if (locStatus.value === 'locating') return '定位中…'
  if (locStatus.value === 'located') {
    if (locMethod.value === 'ip') return `IP 定位 · ${userCity.value}`
    if (locMethod.value === 'network') {
      const d = userDistrict.value ? ` · ${userDistrict.value}` : ''
      return `${netLocLabel.value}${d} ${fmtAcc(locAccuracy.value)}`
    }
    const d = userDistrict.value ? ` · ${userDistrict.value}` : ''
    const a = locAccuracy.value ? ` ${fmtAcc(locAccuracy.value)}` : ''
    return `已定位${d}${a}`
  }
  return '默认位置'
})
const locTagClass = computed(() =>
  ({ located: 'ok', default: 'dim' } as any)[locStatus.value] || '')

function defaultCenter(): [number, number] {
  return [w.value.longitude ?? 120.1551, w.value.latitude ?? 30.2741]
}

function loadAmapScript(key: string): Promise<void> {
  return new Promise((resolve, reject) => {
    if ((window as any).AMap) return resolve()
    const s = document.createElement('script')
    s.src = `https://webapi.amap.com/maps?v=2.0&key=${key}`
    s.onload = () => resolve()
    s.onerror = () => reject(new Error('高德地图脚本加载失败'))
    document.head.appendChild(s)
  })
}

/* 浏览器定位（WGS-84 坐标）；失败时返回 null 并记录原因（供降级提示） */
const locFailReason = ref<'' | 'unsupported' | 'denied' | 'unavailable' | 'timeout'>('')

function getUserPosition(timeoutMs = 9000): Promise<{ lat: number; lon: number; accuracy: number } | null> {
  return new Promise((resolve) => {
    if (!('geolocation' in navigator)) {
      locFailReason.value = 'unsupported'
      return resolve(null)
    }
    let settled = false
    const t = setTimeout(() => {
      if (!settled) { settled = true; locFailReason.value = 'timeout'; resolve(null) }
    }, timeoutMs)
    const done = (v: { lat: number; lon: number; accuracy: number } | null) => {
      if (!settled) { settled = true; clearTimeout(t); resolve(v) }
    }
    navigator.geolocation.getCurrentPosition(
      (p) => done({ lat: p.coords.latitude, lon: p.coords.longitude, accuracy: p.coords.accuracy || 0 }),
      (err) => {
        locFailReason.value = err?.code === 1 ? 'denied' : 'unavailable'
        done(null)
      },
      { enableHighAccuracy: true, timeout: timeoutMs, maximumAge: 300000 },
    )
  })
}

/* 位置标记样式：AMap 注入的 DOM 不受 scoped 样式作用，需全局注入一次 */
function ensureLocMarkerStyle() {
  if (document.getElementById(LOC_STYLE_ID)) return
  const st = document.createElement('style')
  st.id = LOC_STYLE_ID
  st.textContent = `
    .wth-loc-mk { position: relative; width: 18px; height: 18px; }
    .wth-loc-mk__label {
      position: absolute; bottom: calc(100% + 8px); left: 50%; transform: translateX(-50%);
      background: rgba(15, 23, 42, 0.88); color: #fff; font-size: 12px; font-weight: 600;
      padding: 4px 11px; border-radius: 999px; white-space: nowrap;
      border: 1px solid rgba(255, 255, 255, 0.22); letter-spacing: 0.02em;
      box-shadow: 0 4px 14px rgba(15, 23, 42, 0.3);
    }
    .wth-loc-mk__halo {
      position: absolute; inset: 0; border-radius: 50%;
      background: rgba(37, 99, 235, 0.4); animation: wth-loc-pulse 2s ease-out infinite;
    }
    .wth-loc-mk__core {
      position: absolute; inset: 0; border-radius: 50%; box-sizing: border-box;
      background: #2563eb; border: 3px solid #fff; box-shadow: 0 1px 6px rgba(37, 99, 235, 0.6);
    }
    @keyframes wth-loc-pulse {
      0% { transform: scale(0.5); opacity: 0.9; }
      100% { transform: scale(3); opacity: 0; }
    }`
  document.head.appendChild(st)
}

function userMarkerHtml(): string {
  const city = userCity.value || w.value.city || ''
  let label: string
  if (locMethod.value === 'ip') {
    label = `我的位置 · ${city}（IP 定位）`
  } else if (locMethod.value === 'network') {
    label = `我的位置 · ${userDistrict.value || city}（${netLocLabel.value}）`
  } else if (locMethod.value === 'browser') {
    label = `我的位置 · ${userDistrict.value || city}`
  } else {
    label = city || '默认位置'
  }
  return `<div class="wth-loc-mk"><div class="wth-loc-mk__label">${label}</div>` +
    `<span class="wth-loc-mk__halo"></span><span class="wth-loc-mk__core"></span></div>`
}

/* 在地图上标注用户所在位置：脉冲光点 + 城市/区县标签 + 定位精度圈 */
function applyLocationOverlay(target: any, AMap: any, existing: { marker: any; circle: any } | null, zoom: number) {
  const pos: [number, number] = userPos.gcj || defaultCenter()
  if (existing) {
    target.remove(existing.marker)
    if (existing.circle) target.remove(existing.circle)
  }
  ensureLocMarkerStyle()
  const marker = new AMap.Marker({
    position: pos, anchor: 'center',
    content: userMarkerHtml(),
  })
  target.add(marker)
  let circle: any = null
  const acc = locMethod.value === 'ip' ? 0 : (userPos.wgs?.accuracy ?? 0)
  if (acc > 20 && acc <= 20000) {
    circle = new AMap.Circle({
      center: pos, radius: acc,
      strokeColor: '#3b82f6', strokeOpacity: 0.35, strokeWeight: 1,
      fillColor: '#3b82f6', fillOpacity: 0.1,
    })
    target.add(circle)
  }
  target.setZoomAndCenter(zoom, pos)
  return { marker, circle }
}

async function initMaps() {
  if (!amapKey) return
  try {
    await loadAmapScript(amapKey)
    const AMap = (window as any).AMap
    // loading 切换（v-if/v-else）会重建地图容器，旧实例脱离文档后必须销毁重建
    if (map && !map.getContainer?.()?.isConnected) {
      map.destroy()
      map = null
      sideOverlay = null
    }
    if (!map) {
      map = new AMap.Map('wth-amap', {
        zoom: userPos.gcj ? 13 : 11, center: userPos.gcj || defaultCenter(),
        mapStyle: MAP_STYLES[mapLayer.value], viewMode: '2D',
      })
    }
    sideOverlay = applyLocationOverlay(map, AMap, sideOverlay, userPos.gcj ? 13 : 11)
  } catch { /* 地图加载失败不影响天气展示 */ }
}

/* 高德 IP 城市定位：无需用户授权，国内 IP 库城市级精度，返回 GCJ-02 城市中心 */
function amapIpLocate(): Promise<{ city: string; center: [number, number] } | null> {
  return new Promise((resolve) => {
    const AMap = (window as any).AMap
    if (!AMap) return resolve(null)
    let settled = false
    const finish = (v: { city: string; center: [number, number] } | null) => {
      if (!settled) { settled = true; clearTimeout(t); resolve(v) }
    }
    const t = setTimeout(() => finish(null), 7000)
    try {
      AMap.plugin('AMap.Geolocation', () => {
        new AMap.Geolocation({ noIpLocate: false, timeout: 6000 })
          .getCityInfo((status: string, r: any) => {
            /* 坐标字段为 position（[lng, lat] 数组），兼容 center 形式 */
            const c = r?.position || r?.center
            const center: [number, number] | null = c
              ? [Number(c.lng ?? c[0]), Number(c.lat ?? c[1])] : null
            if (status === 'complete' && r?.city && center) {
              finish({ city: String(r.city), center })
            } else finish(null)
          })
      })
    } catch { finish(null) }
  })
}

/* 后端逆地理编码：GCJ-02 坐标 -> 城市/区县（高德数据，按真实行政区划解析，比就近匹配城市中心准确） */
async function reverseGeocode(gcj: [number, number]): Promise<{ city: string; district: string } | null> {
  try {
    const data = await weatherApi.position(gcj[1], gcj[0])
    if (data?.city) return { city: String(data.city), district: String(data.district || '') }
    return null
  } catch { return null }
}

interface LocatedInfo {
  weatherLat: number
  weatherLon: number
  gcj: [number, number]
  city: string
  district: string
  method: 'browser' | 'ip' | 'network'
  accuracy: number
}

/* 应用定位结果：刷新天气 + 记录定位状态 + 地图标注 */
async function applyLocated(p: LocatedInfo) {
  locMethod.value = p.method
  locAccuracy.value = p.accuracy
  locStatus.value = 'located'
  userPos.wgs = { lat: p.weatherLat, lon: p.weatherLon, accuracy: p.accuracy }
  userPos.gcj = p.gcj
  if (p.city) userCity.value = p.city
  userDistrict.value = p.district
  try {
    const data = await weatherApi.now({ lat: p.weatherLat, lon: p.weatherLon })
    w.value = data
    amapKey = data.amap_key || amapKey
  } catch { /* 定位后天气刷新失败时保留默认城市数据 */ }
  await initMaps()
  if (mapFull && mapOverlay.value) {
    fullOverlay = applyLocationOverlay(mapFull, (window as any).AMap, fullOverlay, 12)
  }
}

/* 浏览器定位不可用时按失败原因提示（IP 定位只能到城市级，区县级需浏览器定位权限） */
function notifyIpFallback() {
  const denied = locFailReason.value === 'denied'
  const prefix = {
    denied: '浏览器定位权限被拒绝',
    timeout: '浏览器定位超时',
    unavailable: '浏览器定位不可用',
    unsupported: '当前浏览器不支持定位',
  } as any
  const tip = `${prefix[locFailReason.value] || '浏览器定位不可用'}，已按 IP 定位到城市级（如需精确到区县，请允许浏览器定位权限后点击"重新定位"）`
  denied ? ElMessage.warning(tip) : ElMessage.info(tip)
}

/* 定位策略：浏览器定位优先；失败或精度极差（>30km 的纯 IP 猜测，台式机常见）时改用高德 IP 城市定位 */
async function locateUser() {
  locFailReason.value = ''
  const pos = await getUserPosition()
  if (!pos || pos.accuracy > 30000) {
    const ipLoc = await amapIpLocate()
    if (ipLoc) {
      await applyLocated({
        weatherLat: ipLoc.center[1], weatherLon: ipLoc.center[0],
        gcj: ipLoc.center, city: ipLoc.city, district: '',
        method: 'ip', accuracy: 0,
      })
      if (!pos || locFailReason.value) notifyIpFallback()
      return
    }
  }
  if (pos) {
    const gcj = wgs84ToGcj02(pos.lon, pos.lat)
    const geo = await reverseGeocode(gcj)
    await applyLocated({
      weatherLat: pos.lat, weatherLon: pos.lon,
      gcj, city: geo?.city || nearestCity(gcj[0], gcj[1]) || '',
      district: geo?.district || '', method: 'browser', accuracy: pos.accuracy,
    })
    return
  }
  /* 浏览器与 IP 定位均失败：回落默认城市并提示 */
  locStatus.value = 'default'
  const prefix = { denied: '浏览器定位权限被拒绝', timeout: '浏览器定位超时', unavailable: '浏览器定位不可用', unsupported: '当前浏览器不支持定位' } as any
  ElMessage.warning(`${prefix[locFailReason.value] || '定位失败'}，已显示默认城市天气`)
}

/* 网络定位辅助（第一版同款）：手动选择 WiFi / 基站 / 融合定位方式；
   以当前已知位置（浏览器/IP 定位结果）为基准，返回城市 + 精度 + 周边地点 */
async function onNetworkLocate(method: string) {
  netLocating.value = true
  try {
    const base = userPos.gcj ? { lat: userPos.gcj[1], lon: userPos.gcj[0] } : {}
    const data = await weatherApi.locate({ method, ...base })
    nearbyPlaces.value = data?.nearby || []
    netLocLabel.value = NETWORK_METHOD_LABELS[data?.method_key] || NETWORK_METHOD_LABELS[method] || '网络定位'
    await applyLocated({
      weatherLat: data.latitude, weatherLon: data.longitude,
      gcj: [data.longitude, data.latitude],
      city: data.city || '', district: data.district || '',
      method: 'network', accuracy: data.accuracy_m || 0,
    })
  } catch { /* 错误提示由拦截器统一处理 */ } finally {
    netLocating.value = false
  }
}

function switchLayer(key: string) {
  mapLayer.value = key
  if (map) map.setMapStyle(MAP_STYLES[key])
  if (mapFull) mapFull.setMapStyle(MAP_STYLES[key])
}

async function openMapOverlay() {
  mapOverlay.value = true
  document.body.style.overflow = 'hidden'
  try {
    await loadAmapScript(amapKey)
    const AMap = (window as any).AMap
    await nextFrame()
    if (!mapFull) {
      mapFull = new AMap.Map('wth-amap-full', {
        zoom: userPos.gcj ? 12 : 10, center: userPos.gcj || defaultCenter(),
        mapStyle: MAP_STYLES[mapLayer.value], viewMode: '2D',
      })
    }
    fullOverlay = applyLocationOverlay(mapFull, AMap, fullOverlay, userPos.gcj ? 12 : 10)
  } catch { /* ignore */ }
}

function closeMapOverlay() {
  mapOverlay.value = false
  document.body.style.overflow = ''
}

function nextFrame() {
  return new Promise<void>((r) => requestAnimationFrame(() => r()))
}

function tick() {
  const n = new Date()
  currentTime.value = `${n.getMonth() + 1}月${n.getDate()}日 ${String(n.getHours()).padStart(2, '0')}:${String(n.getMinutes()).padStart(2, '0')}`
}

async function load() {
  loading.value = true
  locStatus.value = 'locating'
  try {
    const data = await weatherApi.now(userPos.wgs ? { lat: userPos.wgs.lat, lon: userPos.wgs.lon } : undefined)
    w.value = data
    amapKey = data.amap_key || ''
  } finally {
    loading.value = false
  }
  if (userPos.wgs) locStatus.value = 'located'
  // 等待 v-else 渲染出地图容器后再初始化，否则 AMap 拿不到挂载节点
  await nextFrame()
  await initMaps()
  // 首次进入：后台定位（浏览器优先，精度差/失败时高德 IP 兜底），成功后用真实坐标二次刷新天气并标注
  if (!userPos.wgs) await locateUser()
}

function reload() {
  // 重新定位：清除旧位置与周边地点，重走「默认渲染 -> 浏览器定位 / IP 定位 -> 标注」流程
  userPos.wgs = null
  userPos.gcj = null
  userCity.value = ''
  userDistrict.value = ''
  locMethod.value = 'none'
  locAccuracy.value = 0
  nearbyPlaces.value = []
  netLocLabel.value = ''
  load()
}

let timer: any = null
onMounted(() => {
  tick()
  timer = setInterval(tick, 30000)
  load()
})
onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
  map?.destroy?.()
  map = null
  mapFull?.destroy?.()
  mapFull = null
  sideOverlay = null
  fullOverlay = null
  document.getElementById(LOC_STYLE_ID)?.remove()
  document.body.style.overflow = ''
})
</script>

<style scoped>
.wth-loading { display: flex; flex-direction: column; align-items: center; gap: 14px; padding: 80px 0; color: var(--tyt-text-dim); }
.spinner {
  width: 38px; height: 38px; border-radius: 50%;
  border: 3px solid var(--tyt-primary-soft); border-top-color: var(--tyt-primary);
  animation: spin .9s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* 100% 窗口下放开宽度上限，全部功能平铺可见 */
.weather-page { max-width: 1680px; }

.wth-topbar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.wth-loc {
  display: inline-flex; align-items: center; gap: 8px; cursor: default;
  background: var(--tyt-card); border: 1px solid var(--tyt-border);
  border-radius: 999px; padding: 8px 16px; font-size: 13.5px; font-weight: 600;
  color: var(--tyt-text);
}
.wth-loc-tag {
  font-size: 11px; font-weight: 500; color: var(--tyt-primary-dark);
  background: var(--tyt-primary-soft); border-radius: 999px; padding: 2px 8px;
}
.wth-loc-tag.ok { color: #047857; background: #d1fae5; }
.wth-loc-tag.dim { color: #64748b; background: #f1f5f9; }
.wth-topbar-actions { display: flex; gap: 8px; }
.wth-icon-btn {
  width: 36px; height: 36px; border-radius: 10px; border: 1px solid var(--tyt-border);
  background: var(--tyt-card); color: var(--tyt-text-dim); cursor: pointer;
  display: inline-flex; align-items: center; justify-content: center; transition: all .2s;
}
.wth-icon-btn:hover { color: var(--tyt-primary); border-color: var(--tyt-primary); background: var(--tyt-primary-soft); }
.wth-icon-btn.active { color: var(--tyt-primary); border-color: var(--tyt-primary); background: var(--tyt-primary-soft); }

/* 周边地点（网络定位辅助结果） */
.wth-nearby-card {
  background: var(--tyt-card); border: 1px solid var(--tyt-border); border-radius: 14px;
  padding: 14px 16px; display: flex; flex-direction: column; min-height: 0;
}
.wth-nearby-head { display: flex; align-items: baseline; justify-content: space-between; gap: 8px; margin-bottom: 10px; }
.wth-nearby-title { font-size: 13.5px; font-weight: 700; }
.wth-nearby-sub { font-size: 11.5px; color: var(--tyt-text-tertiary); }
.wth-nearby-list { display: flex; flex-direction: column; overflow-y: auto; max-height: 260px; }
.wth-nearby-item {
  display: flex; align-items: center; gap: 9px; padding: 7px 2px; font-size: 12.5px;
  border-bottom: 1px solid var(--tyt-border-light);
}
.wth-nearby-item:last-child { border-bottom: none; }
.wth-nearby-icon { font-size: 15px; }
.wth-nearby-name { font-weight: 600; color: var(--tyt-text); flex: 1; min-width: 0; }
.wth-nearby-type {
  font-size: 10.5px; color: var(--tyt-text-dim); background: var(--tyt-bg-soft);
  border-radius: 999px; padding: 1px 8px; white-space: nowrap;
}
.wth-nearby-dist { font-size: 11.5px; color: var(--tyt-primary-dark); font-weight: 600; white-space: nowrap; }

/* 天气 : 地图 = 65 : 35；侧栏随主栏等高拉伸 */
.wth-layout { display: grid; grid-template-columns: 65fr 35fr; gap: 20px; align-items: stretch; }
.wth-col-main { min-width: 0; }
.wth-col-side { min-width: 0; display: flex; flex-direction: column; gap: 16px; }

/* 当前天气卡 */
.wth-current-card {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border-radius: 16px; padding: 22px 26px; color: #fff;
  box-shadow: 0 10px 30px -10px rgba(99, 102, 241, .5);
}
.wth-current-time { font-size: 13px; opacity: .85; margin-bottom: 10px; }
.wth-current-body { display: flex; align-items: center; gap: 16px; }
.wth-current-icon { font-size: 52px; line-height: 1; filter: drop-shadow(0 4px 8px rgba(0,0,0,.2)); }
.wth-current-temp { font-size: 56px; font-weight: 800; letter-spacing: -0.03em; }
.wth-current-cond { font-size: 17px; font-weight: 600; }
.wth-current-feels { font-size: 12.5px; opacity: .8; margin-top: 2px; }
.wth-current-summary { font-size: 13.5px; margin-top: 12px; opacity: .92; }
.wth-card-updated { font-size: 11.5px; opacity: .7; margin-top: 4px; }
.wth-metrics {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px 18px;
  margin-top: 18px; padding-top: 16px; border-top: 1px solid rgba(255, 255, 255, .25);
}
.wth-metric { display: flex; align-items: baseline; gap: 7px; font-size: 12.5px; flex-wrap: wrap; }
.wth-metric-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; align-self: center; }
.wth-metric-label { opacity: .78; }
.wth-metric-value { font-size: 14px; font-weight: 700; }
.wth-metric-unit { opacity: .7; font-size: 11.5px; }

/* 逐时预报 */
.wth-forecast-section {
  background: var(--tyt-card); border: 1px solid var(--tyt-border); border-radius: 14px;
  padding: 16px 18px; margin-top: 16px;
}
.wth-forecast-header { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 12px; flex-wrap: wrap; }
.wth-forecast-tabs { display: flex; gap: 4px; overflow-x: auto; }
.wth-fc-tab {
  border: none; background: transparent; color: var(--tyt-text-dim);
  font-size: 12.5px; padding: 6px 12px; border-radius: 999px; cursor: pointer;
  white-space: nowrap; transition: all .2s;
}
.wth-fc-tab:hover { color: var(--tyt-text); background: var(--tyt-bg-soft); }
.wth-fc-tab.active { background: var(--tyt-primary-soft); color: var(--tyt-primary-dark); font-weight: 600; }
.wth-forecast-view { display: flex; background: var(--tyt-bg-soft); border-radius: 8px; padding: 2px; }
.wth-view-btn {
  border: none; background: transparent; font-size: 12px; color: var(--tyt-text-dim);
  padding: 5px 12px; border-radius: 7px; cursor: pointer;
}
.wth-view-btn.active { background: var(--tyt-card); color: var(--tyt-text); box-shadow: var(--tyt-shadow-sm); }

.wth-hourly-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.wth-hourly-title { font-size: 13px; font-weight: 600; color: var(--tyt-text-dim); }
.wth-toggle { display: inline-flex; align-items: center; gap: 7px; cursor: pointer; }
.wth-toggle input { display: none; }
.wth-toggle-track {
  width: 32px; height: 18px; border-radius: 999px; background: var(--tyt-border);
  position: relative; transition: background .2s;
}
.wth-toggle-track::after {
  content: ''; position: absolute; top: 2px; left: 2px; width: 14px; height: 14px;
  border-radius: 50%; background: #fff; transition: transform .2s;
  box-shadow: 0 1px 3px rgba(0, 0, 0, .2);
}
.wth-toggle input:checked + .wth-toggle-track { background: var(--tyt-primary); }
.wth-toggle input:checked + .wth-toggle-track::after { transform: translateX(14px); }
.wth-toggle-label { font-size: 12px; color: var(--tyt-text-dim); }

.wth-hourly-curve { position: relative; }
.wth-hourly-svg { width: 100%; height: 120px; display: block; }
.wth-hourly-items {
  position: absolute; inset: 0; display: grid;
  grid-template-columns: repeat(12, 1fr);
}
.wth-hourly-item {
  display: flex; flex-direction: column; align-items: center; gap: 2px;
  padding-top: 4px; font-size: 11px; color: var(--tyt-text-dim);
}
.wth-h-time { font-weight: 600; }
.wth-h-icon { font-size: 14px; }
.wth-h-val { font-weight: 700; color: var(--tyt-text); }

.wth-hourly-list { max-height: 300px; overflow-y: auto; display: flex; flex-direction: column; }
.wth-h-row {
  display: grid; grid-template-columns: 56px 28px 90px 1fr auto; align-items: center;
  gap: 10px; padding: 9px 4px; font-size: 13px;
  border-bottom: 1px solid var(--tyt-border-light);
}
.wth-h-row:last-child { border-bottom: none; }
.wth-h-row-time { font-weight: 600; color: var(--tyt-text); }
.wth-h-row-icon { font-size: 15px; }
.wth-h-row-cond { color: var(--tyt-text-dim); }
.wth-h-row-val { font-weight: 600; }
.wth-h-row-pop { font-size: 11.5px; color: #0ea5e9; }
.pager { display: flex; justify-content: center; padding-top: 12px; }

/* 7 日 */
.wth-daily-scroll {
  display: flex; gap: 10px; overflow-x: auto; margin-top: 16px;
  padding-bottom: 6px;
}
.wth-daily-item {
  flex: 1 0 104px; background: var(--tyt-card); border: 1px solid var(--tyt-border);
  border-radius: 12px; padding: 14px 10px; text-align: center;
}
.wth-daily-item.today { border-color: rgba(99, 102, 241, .45); background: var(--tyt-primary-soft); }
.wth-daily-day { font-size: 12.5px; font-weight: 700; }
.wth-daily-date { font-size: 11px; color: var(--tyt-text-tertiary); margin-top: 2px; }
.wth-daily-icon { font-size: 26px; margin: 8px 0 6px; }
.wth-daily-cond { font-size: 12px; color: var(--tyt-text-dim); margin-bottom: 6px; }
.wth-daily-temps .hi { font-size: 15px; font-weight: 700; }
.wth-daily-temps .lo { font-size: 12.5px; color: var(--tyt-text-tertiary); }

/* 侧栏：地图卡片纵向拉伸填满主栏高度 */
.wth-map-card {
  background: var(--tyt-card); border: 1px solid var(--tyt-border); border-radius: 14px;
  overflow: hidden; flex: 1; display: flex; flex-direction: column; min-height: 0;
}
.wth-map-tabs { display: flex; border-bottom: 1px solid var(--tyt-border-light); }
.wth-map-tab {
  flex: 1; border: none; background: transparent; padding: 10px 0; font-size: 12.5px;
  color: var(--tyt-text-dim); cursor: pointer; transition: all .2s;
  border-bottom: 2px solid transparent;
}
.wth-map-tab.active { color: var(--tyt-primary-dark); font-weight: 600; border-bottom-color: var(--tyt-primary); background: var(--tyt-primary-soft); }
.wth-map-body { position: relative; flex: 1; display: flex; min-height: 0; }
.wmap-stage { position: relative; flex: 1; min-height: 260px; }
.amap-container { width: 100%; height: 100%; }
.wmap-coord {
  position: absolute; right: 10px; bottom: 10px; z-index: 5;
  font-size: 10.5px; font-family: var(--tyt-font-mono); color: var(--tyt-text-dim);
  background: rgba(255, 255, 255, .88); border-radius: 6px; padding: 2px 8px;
  border: 1px solid var(--tyt-border-light);
}
.wth-map-footer {
  display: flex; align-items: center; justify-content: space-between; gap: 8px;
  padding: 10px 14px; border-top: 1px solid var(--tyt-border-light);
}
.wth-map-info { font-size: 12px; color: var(--tyt-text-dim); }
.wth-map-open-link {
  border: none; background: transparent; color: var(--tyt-primary);
  font-size: 12.5px; cursor: pointer; font-weight: 600; white-space: nowrap;
}
.wth-map-open-link:hover { text-decoration: underline; }

/* 生活指数：页面底部全宽区块 */
.wth-life-section { margin-top: 20px; }
.wth-life-head {
  display: flex; align-items: center; gap: 10px;
  margin-bottom: 12px; font-size: 14.5px; font-weight: 700; color: var(--tyt-text);
}
.wth-life-head::before {
  content: ""; width: 4px; height: 16px; border-radius: 2px; flex-shrink: 0;
  background: var(--tyt-gradient-brand);
}
.wth-life-grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 12px; }
.wth-life-item {
  background: var(--tyt-card); border: 1px solid var(--tyt-border); border-radius: 12px;
  padding: 16px 10px; text-align: center; transition: all .18s;
}
.wth-life-item:hover { border-color: rgba(99, 102, 241, .4); transform: translateY(-2px); }
.wth-life-icon { font-size: 22px; }
.wth-life-name { font-size: 11.5px; color: var(--tyt-text-tertiary); margin-top: 6px; }
.wth-life-value { font-size: 12.5px; font-weight: 700; margin-top: 2px; color: var(--tyt-text); }

/* 全屏地图 */
.amap-overlay {
  position: fixed; inset: 0; z-index: 2000; background: var(--tyt-bg);
  display: flex; flex-direction: column;
  opacity: 0; visibility: hidden; transition: opacity .25s, visibility .25s;
}
.amap-overlay.show { opacity: 1; visibility: visible; }
.amap-overlay-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 20px; background: var(--tyt-card); border-bottom: 1px solid var(--tyt-border);
  flex-shrink: 0;
}
.amap-overlay-title { font-size: 15px; font-weight: 700; }
.amap-overlay-back {
  border: 1px solid var(--tyt-border); background: var(--tyt-card); color: var(--tyt-text-dim);
  border-radius: 8px; padding: 7px 14px; font-size: 13px; cursor: pointer; transition: all .2s;
}
.amap-overlay-back:hover { color: var(--tyt-primary); border-color: var(--tyt-primary); }
.amap-overlay-body { flex: 1; }

@media (max-width: 1080px) {
  .wth-layout { grid-template-columns: 1fr; }
  .wth-life-grid { grid-template-columns: repeat(3, 1fr); }
}
</style>
