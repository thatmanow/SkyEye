<template>
  <el-dialog v-model="visible" width="min(880px, 94vw)" top="5vh"
             :close-on-click-modal="false" class="tyt-member-dialog">
    <template #header>
      <div class="dlg-head">
        <div class="dlg-title">
          <span class="dlg-crown">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="m2 4 3 12h14l3-12-6 7-4-7-4 7-6-7zm3 16h14"></path>
            </svg>
          </span>
          {{ isPremium ? '会员中心' : '升级权益' }}
        </div>
        <p class="dlg-sub">开通高级会员 · 解锁商业尽调与 AI 能力不限次使用（有效期 30 天）</p>
      </div>
    </template>

    <div class="dlg-body">
      <!-- 用户信息条（图片：头像 + 用户名 + 状态标签） -->
      <div class="who-bar">
        <span class="who-avatar" :class="{ 'has-img': !!auth.user?.avatar }"
              :style="auth.user?.avatar ? { backgroundImage: `url(${auth.user.avatar})` } : undefined">{{ avatarChar }}</span>
        <div class="who-meta">
          <span class="who-name">{{ auth.user?.nickname || '用户' }}</span>
          <el-tag size="small" :type="isPremium ? 'success' : 'info'">
            {{ isPremium ? '高级会员' : '免费' }}
          </el-tag>
        </div>
        <div v-if="isPremium" class="who-status">
          <!-- 连续包月自动续费中：不显示会员到期日期 -->
          <template v-if="membership.auto_renew">
            连续包月自动续费中 · 会员服务持续有效
          </template>
          <!-- 已取消自动续费：才显示会员到期日期 -->
          <template v-else-if="membership.vip_expire_at">
            会员有效期至 <b>{{ membership.vip_expire_at }}</b> · 到期后自动恢复为普通用户
          </template>
          <el-button v-if="membership.auto_renew" link type="danger" size="small" @click="cancelAutoRenew">
            取消自动续费
          </el-button>
        </div>
      </div>

      <!-- 企业管理员 / 平台管理员：无需购买 -->
      <div v-if="roleNoNeed" class="noneed">
        当前角色（{{ roleName }}）已具备全部能力，无需购买会员。
      </div>

      <template v-else>
        <!-- 计费周期切换（图片：连续包月 9折 / 单月购买） -->
        <div class="cycle-row">
          <button class="cycle-btn" :class="{ active: cycle === 'auto' }" @click="selectCycle('auto')">
            连续包月 <em>省钱推荐</em>
          </button>
          <button class="cycle-btn" :class="{ active: cycle === 'monthly' }" @click="selectCycle('monthly')">
            单月购买
          </button>
          <span class="cycle-note">
            {{ cycle === 'auto' ? '到期自动续费，可随时取消' : '有效期 30 天，到期不自动扣费' }}
          </span>
        </div>

        <!-- 高级会员卡片（单一会员类型，价格随周期切换） -->
        <div class="member-card">
          <div class="mc-head">
            <span v-if="isFirst" class="mc-badge">⭐ 首月优惠</span>
            <div class="mc-name">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="m2 4 3 12h14l3-12-6 7-4-7-4 7-6-7zm3 16h14"></path>
              </svg>
              高级会员
            </div>
            <div class="mc-price">
              <span class="cur">¥{{ displayPrice }}</span><span class="unit">/月</span>
              <del v-if="showOrigin" class="origin">¥{{ originPrice }}</del>
            </div>
            <p class="mc-note">{{ currentPlan?.note }}</p>
          </div>
          <div class="mc-benefits">
            <div v-for="b in benefits" :key="b.title" class="mc-benefit" :title="b.desc">
              <svg class="ck" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="20 6 9 17 4 12"></polyline>
              </svg>
              <span class="bt">{{ b.title }}</span>
              <span class="bd">{{ b.desc }}</span>
            </div>
          </div>
        </div>

        <!-- 支付区（图片底部：渠道 + 二维码 + 金额 + 价格说明 + 协议） -->
        <div class="pay-zone">
          <div class="pay-left">
            <div class="channel-row">
              <button v-for="ch in channels" :key="ch.key" class="channel-btn"
                      :class="{ active: channel === ch.key, [ch.key]: true }" @click="channel = ch.key">
                {{ ch.label }}
              </button>
            </div>
            <div class="qr-wrap" :class="{ ready: agreed, paying: !!pendingOrderId }">
              <canvas ref="qrCanvas" width="168" height="168"></canvas>
              <div v-if="!agreed" class="qr-lock">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                  <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                </svg>
                <span>同意协议后扫码支付</span>
              </div>
            </div>
            <p class="qr-tip">
              演示环境模拟支付{{ pendingOrderId ? '，点击右侧「模拟支付成功」完成开通' : '' }}
            </p>
          </div>
          <div class="pay-right">
            <div class="amount-row">
              <span class="amount-label">应付金额</span>
              <span class="amount">¥{{ currentAmount.toFixed(2) }}</span>
              <span v-if="isFirst" class="amount-first">首月优惠</span>
            </div>
            <p class="price-note">{{ fullTerms }}</p>
            <label class="agree-line">
              <input type="checkbox" v-model="agreed" />
              <span>同意
                <a @click.stop="openAgreement('user')">《用户协议》</a>
                <a @click.stop="openAgreement('privacy')">《隐私政策》</a>
                <a v-if="cycle === 'auto'" @click.stop="openAgreement('auto')">《连续包月自动续费服务协议》</a>
              </span>
            </label>
            <div class="pay-actions">
              <el-button type="primary" size="large" class="pay-btn"
                         :disabled="!agreed || paying" :loading="paying"
                         @click="pendingOrderId ? confirmPay() : createOrder()">
                {{ pendingOrderId ? '模拟支付成功'
                   : (isPremium ? '立即续费 · 扫码支付' : '立即升级 · 扫码支付') }}
              </el-button>
              <el-button v-if="pendingOrderId" link size="small" @click="cancelPending">取消支付</el-button>
            </div>
          </div>
        </div>

        <!-- 订阅记录（折叠区） -->
        <div v-if="orders.length" class="orders-sec">
          <el-collapse>
            <el-collapse-item :title="`订阅记录（${orders.length}）`">
              <el-table :data="orders" size="small">
                <el-table-column prop="id" label="订单号" width="76" />
                <el-table-column label="方案" width="96">
                  <template #default="{ row }">{{ row.plan_name }}</template>
                </el-table-column>
                <el-table-column label="金额" width="90">
                  <template #default="{ row }">¥{{ row.amount.toFixed(0) }}<el-tag v-if="row.is_first" size="small" style="margin-left:4px">首月</el-tag></template>
                </el-table-column>
                <el-table-column label="状态" width="86">
                  <template #default="{ row }">
                    <el-tag :type="row.status === 'paid' ? 'success' : row.status === 'pending' ? 'warning' : 'info'" size="small">
                      {{ statusNames[row.status] || row.status }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="period_end" label="会员到期" width="110" />
                <el-table-column prop="created_at" label="下单时间" min-width="140" />
              </el-table>
            </el-collapse-item>
          </el-collapse>
        </div>
      </template>
    </div>

    <!-- 协议内容弹窗 -->
    <el-dialog v-model="agreementDialog" :title="agreementTitles[agreementType]" width="560px" append-to-body>
      <div class="agreement-body">
        <template v-if="agreementType === 'auto'">
          <p>1. 连续包月会员为按月自动续费订阅服务，订阅成功后每个会员周期到期前自动扣费并延长 30 天会员有效期。</p>
          <p>2. 本演示环境为模拟扣款，不产生真实费用；正式环境下将通过您选择的支付渠道完成扣款。</p>
          <p>3. 您可随时在「会员权益」弹窗中取消自动续费，取消后当前周期内的会员权益保留至到期日。</p>
          <p>4. 若扣费失败或账户异常，平台将中断续费服务，会员到期后自动恢复为普通用户。</p>
        </template>
        <template v-else-if="agreementType === 'user'">
          <p>1. 本平台所有查询数据来源公开、合法、可溯源，查询结果仅供个人参考，不得用于非法用途。</p>
          <p>2. 会员服务为虚拟服务，开通后即享受对应功能额度提升；请合理使用，禁止批量爬取与转售。</p>
          <p>3. 账号安全由您自行保管，因账号密码泄露造成的损失由您自行承担。</p>
        </template>
        <template v-else>
          <p>1. 本平台严格保护您的个人隐私，敏感字段（手机号、邮箱等）采用 AES-GCM 加密存储。</p>
          <p>2. 查询与订阅记录仅用于提供服务与审计合规，不会向任何第三方出售您的个人信息。</p>
          <p>3. 您可随时在个人中心查看与管理自己的账号信息。</p>
        </template>
      </div>
    </el-dialog>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { billingApi } from '@/api/modules'
import { useAuthStore } from '@/stores/auth'

const props = defineProps<{ modelValue: boolean }>()
const emit = defineEmits<{ (e: 'update:modelValue', v: boolean): void }>()

const visible = computed({
  get: () => props.modelValue,
  set: (v: boolean) => emit('update:modelValue', v),
})

const auth = useAuthStore()

/* ===== 数据 ===== */
interface Plan { plan: string; name: string; price: number; first_price: number; auto_renew: boolean; badge: string; recommended: boolean; note: string }
interface Benefit { icon: string; title: string; desc: string }
interface Order { id: number; plan_name: string; amount: number; status: string; is_first: boolean; period_end: string | null; created_at: string | null }

const plans = ref<Plan[]>([])
const benefits = ref<Benefit[]>([])
const membership = ref<{ role: string; vip_expire_at: string | null; auto_renew: boolean; is_first: boolean }>({
  role: 'user', vip_expire_at: null, auto_renew: false, is_first: true,
})
const orders = ref<Order[]>([])
const cycle = ref<'auto' | 'monthly'>('auto')
const agreed = ref(false)
const paying = ref(false)
const channel = ref('alipay')
const pendingOrderId = ref(0)
const pendingAmount = ref(0)

const channels = [
  { key: 'alipay', label: '支付宝' },
  { key: 'wechat', label: '微信支付' },
]
const statusNames: Record<string, string> = { paid: '已支付', pending: '待支付', cancelled: '已取消' }

const avatarChar = computed(() => (auth.user?.nickname || '用')[0])
const isPremium = computed(() => auth.role === 'premium')
const isFirst = computed(() => membership.value.is_first)
const roleNoNeed = computed(() => ['enterprise_admin', 'platform_admin'].includes(auth.role))
const roleNames: Record<string, string> = {
  user: '普通用户', premium: '高级会员', enterprise_admin: '企业管理员', platform_admin: '平台管理员',
}
const roleName = computed(() => roleNames[auth.role] || auth.role)

const currentPlan = computed(() =>
  plans.value.find(p => p.plan === (cycle.value === 'auto' ? 'auto_monthly' : 'monthly')))
const displayPrice = computed(() => {
  const p = currentPlan.value
  if (!p) return 0
  return isFirst.value ? p.first_price : p.price
})
const originPrice = computed(() => plans.value.find(p => p.plan === 'monthly')?.price ?? 35)
const showOrigin = computed(() => cycle.value === 'auto' || isFirst.value)
const currentAmount = computed(() => (pendingOrderId.value ? pendingAmount.value : displayPrice.value))

function fmtDate(d: Date) {
  return `${d.getFullYear()}/${String(d.getMonth() + 1).padStart(2, '0')}/${String(d.getDate()).padStart(2, '0')}`
}
/* 下次续费时间：已有会员为当前到期日，新购为 30 天后 */
const nextRenewDate = computed(() => {
  if (membership.value.vip_expire_at) return membership.value.vip_expire_at.replace(/-/g, '/')
  return fmtDate(new Date(Date.now() + 30 * 86400000))
})

const fullTerms = computed(() => {
  const p = currentPlan.value
  if (!p) return ''
  if (cycle.value === 'auto') {
    return isFirst.value
      ? `首月 ¥${p.first_price} 优惠，之后 ¥${p.price}/月自动续费，下次续费时间 ${nextRenewDate.value}，可随时取消`
      : `¥${p.price}/月自动续费，下次续费时间 ${nextRenewDate.value}，可随时取消`
  }
  return isFirst.value
    ? `首月 ¥${p.first_price} 优惠，之后 ¥${p.price}/月，有效期 30 天，到期不自动扣费`
    : `¥${p.price}/月，有效期 30 天，到期不自动扣费`
})

/* ===== 加载方案 / 状态 / 订单 ===== */
async function loadAll() {
  const data = await billingApi.plans()
  plans.value = data.plans
  benefits.value = data.benefits
  membership.value = data.membership
  await loadOrders()
}

async function loadOrders() {
  const data = await billingApi.orders()
  orders.value = data.orders || []
}

/* 打开弹窗：重置交互态并加载数据 */
watch(() => props.modelValue, async (open) => {
  if (!open) return
  agreed.value = false
  pendingOrderId.value = 0
  channel.value = 'alipay'
  await loadAll()
  await nextTick()
  drawQr()
})

/* ===== 周期切换 / 下单 / 模拟支付 ===== */
function selectCycle(c: 'auto' | 'monthly') {
  cycle.value = c
  pendingOrderId.value = 0   // 切换周期后原待支付订单不再有效
}

async function createOrder() {
  paying.value = true
  try {
    const data = await billingApi.createOrder({
      plan: cycle.value === 'auto' ? 'auto_monthly' : 'monthly',
      pay_channel: channel.value,
    })
    pendingOrderId.value = data.order.id
    pendingAmount.value = data.order.amount
    ElMessage.success('订单已创建，请扫码完成支付')
  } catch { /* 拦截器已提示 */ } finally {
    paying.value = false
  }
}

function cancelPending() {
  pendingOrderId.value = 0
}

async function confirmPay() {
  paying.value = true
  try {
    const data = await billingApi.payOrder(pendingOrderId.value)
    pendingOrderId.value = 0
    agreed.value = false
    membership.value = data.membership
    ElMessage.success('支付成功，高级会员已开通！')
    await auth.fetchMe()     // 刷新角色：顶栏标签即时变绿
    await loadAll()         // 刷新首购资格与订阅记录
  } catch { /* 拦截器已提示 */ } finally {
    paying.value = false
  }
}

/* ===== 自动续费管理 ===== */
async function cancelAutoRenew() {
  await billingApi.cancelAutoRenew()
  membership.value.auto_renew = false
  ElMessage.success('已取消自动续费，会员权益保留至到期日')
}

/* ===== 模拟二维码（canvas 确定性伪随机图案，非真实支付码） ===== */
const qrCanvas = ref<HTMLCanvasElement | null>(null)

function drawQr() {
  const canvas = qrCanvas.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  const n = 25, cell = canvas.width / n
  // 以订单号做种子的简单 PRNG；无订单时用固定种子画静态展示码
  let seed = ((pendingOrderId.value || 7) * 2654435761) % 2147483647
  const rand = () => { seed = (seed * 48271) % 2147483647; return seed / 2147483647 }
  ctx.fillStyle = '#fff'
  ctx.fillRect(0, 0, canvas.width, canvas.height)
  ctx.fillStyle = '#0b0e27'
  for (let y = 0; y < n; y++) {
    for (let x = 0; x < n; x++) {
      const inFinder = (x < 7 && y < 7) || (x >= n - 7 && y < 7) || (x < 7 && y >= n - 7)
      if (inFinder) continue
      if (rand() > 0.52) ctx.fillRect(x * cell, y * cell, cell, cell)
    }
  }
  const finder = (fx: number, fy: number) => {
    ctx.fillRect(fx * cell, fy * cell, cell * 7, cell * 7)
    ctx.fillStyle = '#fff'
    ctx.fillRect((fx + 1) * cell, (fy + 1) * cell, cell * 5, cell * 5)
    ctx.fillStyle = '#0b0e27'
    ctx.fillRect((fx + 2) * cell, (fy + 2) * cell, cell * 3, cell * 3)
  }
  finder(0, 0); finder(n - 7, 0); finder(0, n - 7)
}

/* 下单成功 / 切换渠道后重绘订单码 */
watch([pendingOrderId, channel], () => nextTick(drawQr))

/* ===== 协议 ===== */
const agreementDialog = ref(false)
const agreementType = ref<'user' | 'privacy' | 'auto'>('user')
const agreementTitles: Record<string, string> = {
  user: '用户协议', privacy: '隐私政策', auto: '连续包月自动续费服务协议',
}
function openAgreement(type: 'user' | 'privacy' | 'auto') {
  agreementType.value = type
  agreementDialog.value = true
}
</script>

<style scoped>
/* ===== 弹窗骨架（对齐第一版靛紫主题） ===== */
.tyt-member-dialog :deep(.el-dialog) {
  border-radius: 16px;
  box-shadow: var(--tyt-shadow-xl);
}
.tyt-member-dialog :deep(.el-dialog__header) {
  padding: 22px 26px 12px;
  margin-right: 0;
}
.tyt-member-dialog :deep(.el-dialog__body) {
  padding: 4px 26px 24px;
}
.dlg-head { display: flex; flex-direction: column; gap: 4px; }
.dlg-title {
  display: flex; align-items: center; gap: 10px;
  font-size: 20px; font-weight: 800; letter-spacing: -0.02em; color: var(--tyt-text);
}
.dlg-crown {
  width: 32px; height: 32px; border-radius: 9px;
  background: rgba(245, 158, 11, 0.15); color: #f59e0b;
  display: flex; align-items: center; justify-content: center;
}
.dlg-crown svg { width: 17px; height: 17px; }
.dlg-sub { margin: 0; font-size: 12.5px; color: var(--tyt-text-tertiary); }

.dlg-body { display: flex; flex-direction: column; gap: 16px; }

/* ===== 用户信息条 ===== */
.who-bar {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 16px; border-radius: 12px;
  background: var(--tyt-bg-soft); border: 1px solid var(--tyt-border-light);
}
.who-avatar {
  width: 40px; height: 40px; border-radius: 50%; flex-shrink: 0;
  background: var(--tyt-gradient-brand); color: #fff;
  font-size: 15px; font-weight: 600;
  display: flex; align-items: center; justify-content: center;
}
.who-avatar.has-img {
  background-size: cover; background-position: center; background-repeat: no-repeat; font-size: 0;
}
.who-meta { display: flex; align-items: center; gap: 10px; }
.who-name { font-size: 15px; font-weight: 700; color: var(--tyt-text); }
.who-status {
  margin-left: auto; font-size: 12.5px; color: var(--tyt-text-dim);
  display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
}
.who-status b { color: var(--tyt-primary-dark); }

.noneed {
  padding: 18px; text-align: center; font-size: 13.5px; color: var(--tyt-text-dim);
  border: 1px dashed var(--tyt-border); border-radius: 12px;
}

/* ===== 计费周期切换（图片：连续包月 9折 / 单月购买） ===== */
.cycle-row { display: flex; align-items: center; gap: 10px; }
.cycle-btn {
  position: relative; padding: 9px 22px; border-radius: 10px; cursor: pointer;
  border: 1.5px solid var(--tyt-border); background: var(--tyt-bg-soft);
  font-size: 13.5px; font-weight: 600; color: var(--tyt-text-dim);
  transition: all 0.18s ease;
}
.cycle-btn:hover { border-color: var(--tyt-primary-light); color: var(--tyt-text); }
.cycle-btn.active {
  background: #fff; border-color: var(--tyt-primary); color: var(--tyt-primary-dark);
  box-shadow: 0 3px 12px rgba(99, 102, 241, 0.16);
}
.cycle-btn em {
  font-style: normal; margin-left: 6px; padding: 2px 8px; border-radius: 999px;
  background: var(--tyt-gradient-brand); color: #fff; font-size: 11px;
}
.cycle-note { margin-left: auto; font-size: 12px; color: var(--tyt-text-tertiary); }

/* ===== 高级会员卡片 ===== */
.member-card {
  position: relative; border-radius: 14px; padding: 20px 22px;
  background: linear-gradient(135deg, #0b0e27 0%, #312e81 78%, #4f46e5 130%);
  color: #fff; box-shadow: var(--tyt-shadow-md);
}
.mc-badge {
  position: absolute; top: 0; right: 18px; transform: translateY(-40%);
  font-size: 11.5px; font-weight: 600; padding: 4px 12px; border-radius: 999px;
  background: var(--tyt-gradient-brand); color: #fff;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
}
.mc-head { display: flex; align-items: baseline; gap: 14px; flex-wrap: wrap; margin-bottom: 14px; }
.mc-name {
  display: inline-flex; align-items: center; gap: 8px;
  font-size: 18px; font-weight: 800; letter-spacing: -0.02em;
}
.mc-name svg { width: 19px; height: 19px; color: #fbbf24; }
.mc-price { display: flex; align-items: baseline; gap: 6px; }
.mc-price .cur { font-size: 32px; font-weight: 800; letter-spacing: -0.03em; }
.mc-price .unit { font-size: 13px; color: rgba(255, 255, 255, 0.72); }
.mc-price .origin { font-size: 14px; color: rgba(255, 255, 255, 0.45); }
.mc-note { margin: 0 0 0 auto; font-size: 12px; color: rgba(255, 255, 255, 0.68); }

.mc-benefits { display: grid; grid-template-columns: 1fr 1fr; gap: 10px 20px; }
.mc-benefit {
  display: flex; align-items: center; gap: 8px; min-width: 0;
  background: rgba(255, 255, 255, 0.07); border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 9px; padding: 9px 12px;
}
.mc-benefit .ck { width: 13px; height: 13px; color: #fbbf24; flex-shrink: 0; }
.mc-benefit .bt { font-size: 12.5px; font-weight: 600; white-space: nowrap; flex-shrink: 0; }
.mc-benefit .bd {
  font-size: 11px; color: rgba(255, 255, 255, 0.62); white-space: nowrap;
  overflow: hidden; text-overflow: ellipsis; min-width: 0;
}

/* ===== 支付区 ===== */
.pay-zone {
  display: flex; gap: 22px; padding: 18px 20px;
  border: 1px solid var(--tyt-border); border-radius: 14px; background: var(--tyt-card);
}
.pay-left { display: flex; flex-direction: column; align-items: center; gap: 12px; flex-shrink: 0; }
.channel-row { display: flex; gap: 8px; }
.channel-btn {
  padding: 6px 16px; border-radius: 8px; border: 1.5px solid var(--tyt-border);
  background: #fff; font-size: 12.5px; color: var(--tyt-text-dim); cursor: pointer;
  transition: all 0.15s ease;
}
.channel-btn.alipay.active { border-color: #1677ff; color: #1677ff; background: rgba(22, 119, 255, 0.06); }
.channel-btn.wechat.active { border-color: #07c160; color: #07c160; background: rgba(7, 193, 96, 0.06); }

.qr-wrap { position: relative; }
.qr-wrap canvas { display: block; border-radius: 10px; border: 1px solid var(--tyt-border); }
.qr-wrap.paying canvas { border-color: var(--tyt-primary-light); box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.12); }
.qr-lock {
  position: absolute; inset: 0; border-radius: 10px;
  background: rgba(248, 250, 252, 0.72); backdrop-filter: blur(2.5px);
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px;
  color: var(--tyt-text-dim); font-size: 12px;
}
.qr-lock svg { width: 26px; height: 26px; color: var(--tyt-text-tertiary); }
.qr-tip { margin: 0; font-size: 11.5px; color: var(--tyt-text-tertiary); text-align: center; max-width: 200px; }

.pay-right { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 12px; }
.amount-row { display: flex; align-items: baseline; gap: 10px; }
.amount-label { font-size: 12.5px; color: var(--tyt-text-dim); }
.amount { font-size: 30px; font-weight: 800; color: var(--tyt-text); letter-spacing: -0.02em; }
.amount-first {
  font-size: 11.5px; font-weight: 600; padding: 3px 10px; border-radius: 999px;
  background: var(--tyt-primary-soft); color: var(--tyt-primary-dark);
  border: 1px solid rgba(99, 102, 241, 0.25);
}
.price-note { margin: 0; font-size: 12px; color: var(--tyt-text-tertiary); line-height: 1.7; }
.agree-line { display: flex; align-items: flex-start; gap: 7px; font-size: 12.5px; color: var(--tyt-text-dim); cursor: pointer; }
.agree-line input { accent-color: var(--tyt-primary); width: 15px; height: 15px; margin-top: 1px; cursor: pointer; flex-shrink: 0; }
.agree-line a { color: var(--tyt-primary); cursor: pointer; }
.pay-actions { display: flex; align-items: center; gap: 12px; margin-top: 2px; }
.pay-btn {
  background: var(--tyt-gradient-brand); border: none; font-weight: 700;
  box-shadow: 0 6px 18px -4px rgba(99, 102, 241, 0.5);
}
.pay-btn:hover { opacity: 0.92; }

/* ===== 订阅记录 ===== */
.orders-sec :deep(.el-collapse) { border-top: none; border-bottom: none; }
.orders-sec :deep(.el-collapse-item__header) { font-size: 13.5px; font-weight: 600; color: var(--tyt-text-dim); }

@media (max-width: 720px) {
  .pay-zone { flex-direction: column; align-items: stretch; }
  .pay-left { flex-direction: row; flex-wrap: wrap; justify-content: center; }
  .mc-benefits { grid-template-columns: 1fr; }
  .who-status { margin-left: 0; width: 100%; }
}
</style>

<style>
/* 协议弹窗挂载于 body（append-to-body），需全局样式 */
.tyt-member-dialog + .agreement-body p,
.el-dialog .agreement-body p {
  font-size: 13px; line-height: 1.9; color: var(--tyt-text-dim); margin: 0 0 6px;
}
</style>
