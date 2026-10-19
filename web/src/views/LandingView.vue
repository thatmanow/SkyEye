<template>
  <div class="landing">
    <!-- 顶部导航栏 -->
    <nav class="navbar" :class="{ 'navbar-scrolled': scrolled }">
      <div class="nav-container">
        <div class="nav-left">
          <router-link to="/" class="logo">
            <img src="/skyeye-logo.jpg" alt="天眼通" class="logo-img">
            <span class="logo-text">天眼通</span>
          </router-link>
          <div class="nav-links">
            <a href="#features">产品功能</a>
            <a href="#life">生活避坑</a>
            <a href="#biz">商业尽调</a>
            <a href="#compliance">数据合规</a>
          </div>
        </div>
        <div class="nav-right">
          <router-link to="/login" class="nav-link-login">登录</router-link>
          <router-link to="/register" class="btn btn-primary btn-sm">开始使用</router-link>
        </div>
      </div>
    </nav>

    <!-- Hero 区域 -->
    <section class="hero">
      <div class="hero-bg">
        <div class="hero-gradient"></div>
        <div class="hero-grid"></div>
      </div>
      <div class="hero-container">
        <div class="hero-content">
          <div class="hero-badge">
            <span class="badge-dot"></span>
            天眼通 2.0 · 公开数据 · 合规溯源
          </div>
          <h1 class="hero-title">
            构建你的<br>
            <span class="gradient-text">信息查询与风险洞察平台</span>
          </h1>
          <p class="hero-desc">
            面向普通人的「生活避坑」与面向企业的「商业尽调」一站式平台。
            商家口碑、小区投诉、求职公司、企业风险、股权图谱、尽调报告 ——
            数据全部来自公开合法渠道，可溯源、可核验。
          </p>
          <div class="hero-actions">
            <router-link to="/register" class="btn btn-primary btn-lg">免费开始使用</router-link>
            <a href="#features" class="btn btn-outline btn-lg">了解更多 →</a>
          </div>
          <div class="hero-note">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
            </svg>
            不采集个人隐私 · 不做自动化爬虫 · 全部先审后发
          </div>
        </div>
        <div class="hero-visual">
          <div class="video-placeholder">
            <video class="hero-video" src="/hero-demo.mp4" autoplay muted loop playsinline preload="metadata"></video>
            <div class="hero-video-mask"></div>
          </div>
        </div>
      </div>
    </section>

    <!-- 公开数据源墙 -->
    <section class="partners">
      <div class="container reveal">
        <p class="partners-label">全部数据来自公开合法渠道 · 逐条可溯源</p>
        <div class="partners-logos">
          <div class="partner-logo">国家企业信用信息公示系统 · 工商数据</div>
          <div class="partner-logo">中国执行信息公开网 · 司法数据</div>
          <div class="partner-logo">信用中国 · 行政处罚</div>
          <div class="partner-logo">人民法院公告网 · 开庭公告</div>
          <div class="partner-logo">国家知识产权局 · 商标专利</div>
        </div>
      </div>
    </section>

    <!-- 核心功能 -->
    <section class="features" id="features">
      <div class="container reveal">
        <div class="section-header">
          <h2 class="section-title">天眼通能做什么</h2>
          <p class="section-desc">一站式信息查询与风险洞察平台，覆盖生活与商业双场景</p>
        </div>
        <div class="features-grid" id="life">
          <div class="feature-card">
            <div class="feature-icon feature-icon--cyan">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle>
              </svg>
            </div>
            <h3 class="feature-title">商家查询</h3>
            <p class="feature-desc">查商家工商状态与真实评价聚合，预付卡充值前先看看投诉记录。</p>
            <router-link to="/login" class="feature-link">立即体验 →</router-link>
          </div>
          <div class="feature-card">
            <div class="feature-icon feature-icon--purple">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline>
              </svg>
            </div>
            <h3 class="feature-title">房源查询</h3>
            <p class="feature-desc">小区物业投诉、房东押金纠纷、中介套路，租房前心中有数。</p>
            <router-link to="/login" class="feature-link">立即体验 →</router-link>
          </div>
          <div class="feature-card">
            <div class="feature-icon feature-icon--green">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="2" y="7" width="20" height="14" rx="2"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path>
              </svg>
            </div>
            <h3 class="feature-title">求职避坑</h3>
            <p class="feature-desc">入职前查公司经营状态、欠薪与劳动仲裁公开记录。</p>
            <router-link to="/login" class="feature-link">立即体验 →</router-link>
          </div>
          <div class="feature-card">
            <div class="feature-icon feature-icon--orange">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
              </svg>
            </div>
            <h3 class="feature-title">生活圈</h3>
            <p class="feature-desc">匿名分享避坑经验，全部先审后发，拒绝造谣与隐私猎取。</p>
            <router-link to="/login" class="feature-link">立即体验 →</router-link>
          </div>
        </div>
        <div class="features-grid features-grid--second" id="biz">
          <div class="feature-card">
            <div class="feature-icon feature-icon--purple">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M3 21h18"></path><path d="M5 21V7l7-4 7 4v14"></path><path d="M9 21v-6h6v6"></path>
              </svg>
            </div>
            <h3 class="feature-title">企业查询</h3>
            <p class="feature-desc">工商信息、股东高管、对外投资、分支与变更记录一站聚合。</p>
            <router-link to="/login" class="feature-link">立即体验 →</router-link>
          </div>
          <div class="feature-card">
            <div class="feature-icon feature-icon--cyan">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="5" cy="6" r="3"></circle><circle cx="19" cy="6" r="3"></circle><circle cx="12" cy="18" r="3"></circle>
                <line x1="7.5" y1="8" x2="10" y2="15.5"></line><line x1="16.5" y1="8" x2="14" y2="15.5"></line><line x1="8" y1="6" x2="16" y2="6"></line>
              </svg>
            </div>
            <h3 class="feature-title">关系图谱</h3>
            <p class="feature-desc">股权穿透、疑似实控人、关联路径，图数据库逐层展开。</p>
            <router-link to="/login" class="feature-link">立即体验 →</router-link>
          </div>
          <div class="feature-card">
            <div class="feature-icon feature-icon--green">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"></path>
              </svg>
            </div>
            <h3 class="feature-title">商业监控</h3>
            <p class="feature-desc">关注企业司法/经营/处罚动态，日报周报主动推送。</p>
            <router-link to="/login" class="feature-link">立即体验 →</router-link>
          </div>
          <div class="feature-card">
            <div class="feature-icon feature-icon--orange">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line>
              </svg>
            </div>
            <h3 class="feature-title">尽调报告</h3>
            <p class="feature-desc">一键生成 PDF/Excel 尽调报告，风险分级与来源清单齐全。</p>
            <router-link to="/login" class="feature-link">立即体验 →</router-link>
          </div>
        </div>
      </div>
    </section>

    <!-- 双场景展示（深色带） -->
    <section class="ai-section" id="scenes">
      <div class="container reveal">
        <div class="section-header">
          <h2 class="section-title">生活 + 商业双场景</h2>
          <p class="section-desc">一份公开数据，两种洞察视角，在避坑与尽调之间自由切换</p>
        </div>
        <div class="ai-grid">
          <div class="ai-card ai-card--local">
            <div class="ai-card-header">
              <span class="ai-card-badge">生活场景</span>
              <h3 class="ai-card-title">帮普通人避坑</h3>
            </div>
            <p class="ai-card-desc">消费、租房、求职前的三分钟核查，把风险挡在决定之前。</p>
            <div class="ai-card-features">
              <span>商家口碑</span><span>小区投诉</span><span>求职公司</span><span>脱敏个人风险</span>
            </div>
          </div>
          <div class="ai-card-vs">VS</div>
          <div class="ai-card ai-card--cloud">
            <div class="ai-card-header">
              <span class="ai-card-badge">商业场景</span>
              <h3 class="ai-card-title">帮企业做尽调</h3>
            </div>
            <p class="ai-card-desc">合作、投资、投标前的标准动作，风险分级与来源清单齐全。</p>
            <div class="ai-card-features">
              <span>企业风险</span><span>股权图谱</span><span>商业监控</span><span>尽调报告</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 数据合规 -->
    <section class="deploy-section" id="compliance">
      <div class="container reveal">
        <div class="section-header">
          <h2 class="section-title">数据合规红线</h2>
          <p class="section-desc">严格遵循《个人信息保护法》《数据安全法》《网络安全法》</p>
        </div>
        <div class="deploy-grid">
          <div class="deploy-card">
            <div class="deploy-icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <ellipse cx="12" cy="5" rx="9" ry="3"></ellipse>
                <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path>
                <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path>
              </svg>
            </div>
            <h3>公开渠道采集</h3>
            <p>数据全部来自国家企业信用信息公示系统、执行信息公开网、信用中国等公开渠道，不做自动化爬虫。</p>
            <ul class="deploy-list">
              <li>官方渠道人工导入</li>
              <li>导入全程留痕</li>
              <li>来源逐条可溯源</li>
            </ul>
          </div>
          <div class="deploy-card deploy-card--featured">
            <div class="deploy-badge">核心原则</div>
            <div class="deploy-icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
              </svg>
            </div>
            <h3>个人信息脱敏</h3>
            <p>个人查询仅返回脱敏姓名与公开风险记录，不提供身份证/手机号检索。</p>
            <ul class="deploy-list">
              <li>不建人肉档案</li>
              <li>不做画像聚合页</li>
              <li>逐条展示公开记录</li>
            </ul>
          </div>
          <div class="deploy-card">
            <div class="deploy-icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="20 6 9 17 4 12"></polyline>
              </svg>
            </div>
            <h3>先审后发 · 全程审计</h3>
            <p>评价/帖子/投诉全部人工审核后展示，敏感词初审拦截。</p>
            <ul class="deploy-list">
              <li>UGC 先审后发</li>
              <li>查询写入审计日志</li>
              <li>拒绝任何违法查询</li>
            </ul>
          </div>
        </div>
      </div>
    </section>

    <!-- CTA 区域 -->
    <section class="cta-section">
      <div class="container reveal">
        <div class="cta-card">
          <div class="cta-content">
            <h2>准备好开始使用了吗？</h2>
            <p>免费注册，立即体验公开数据驱动的风险洞察平台</p>
          </div>
          <div class="cta-actions">
            <router-link to="/register" class="btn btn-white btn-lg">免费开始</router-link>
            <a href="#features" class="btn btn-outline btn-lg btn-outline--onDark">查看功能</a>
          </div>
        </div>
      </div>
    </section>

    <!-- 页脚 -->
    <footer class="footer">
      <div class="container">
        <div class="footer-grid">
          <div class="footer-brand">
            <div class="logo">
              <img src="/skyeye-logo.jpg" alt="天眼通" class="logo-img">
              <span class="logo-text">天眼通</span>
            </div>
            <p>看见更远的世界<br>公开数据驱动的信息查询与风险洞察平台</p>
          </div>
          <div class="footer-col">
            <h4>生活避坑</h4>
            <router-link to="/life/merchants">商家查询</router-link>
            <router-link to="/life/housing">房源查询</router-link>
            <router-link to="/life/jobs">求职避坑</router-link>
            <router-link to="/community">生活圈</router-link>
          </div>
          <div class="footer-col">
            <h4>商业尽调</h4>
            <router-link to="/biz/companies">企业查询</router-link>
            <router-link to="/biz/graph">关系图谱</router-link>
            <router-link to="/biz/monitor">商业监控</router-link>
            <router-link to="/biz/reports">尽调报告</router-link>
          </div>
          <div class="footer-col">
            <h4>关于</h4>
            <a href="#compliance">数据合规</a>
            <a href="#">用户协议</a>
            <a href="#">隐私政策</a>
            <a href="#">联系方式</a>
          </div>
        </div>
        <div class="footer-bottom">
          <p>© 2026 天眼通 TianYanTong · 演示数据仅用于功能验证 · 严格数据合规 · 拒绝任何违法查询</p>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'

const scrolled = ref(false)

let revealObserver: IntersectionObserver | null = null

function onScroll() {
  scrolled.value = window.scrollY > 20
}

function smoothScroll(e: Event) {
  const target = e.target as HTMLElement
  const anchor = target.closest('a[href^="#"]') as HTMLAnchorElement | null
  if (!anchor) return
  const el = document.querySelector(anchor.getAttribute('href') || '')
  if (el) {
    e.preventDefault()
    el.scrollIntoView({ behavior: 'smooth' })
  }
}

// 滚动渐显（参考第一版：进入视口 12% 且高于底部 40px 时触发，一次性动画）
function initReveal() {
  const els = document.querySelectorAll<HTMLElement>('.landing .reveal')
  if (!els.length) return
  if (!('IntersectionObserver' in window)) {
    els.forEach((el) => el.classList.add('revealed'))
    return
  }
  revealObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('revealed')
          revealObserver?.unobserve(entry.target)
        }
      })
    },
    { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
  )
  els.forEach((el) => revealObserver!.observe(el))
}

onMounted(() => {
  window.addEventListener('scroll', onScroll, { passive: true })
  document.addEventListener('click', smoothScroll)
  onScroll()
  initReveal()
})
onUnmounted(() => {
  window.removeEventListener('scroll', onScroll)
  document.removeEventListener('click', smoothScroll)
  revealObserver?.disconnect()
  revealObserver = null
})
</script>

<style scoped>
.container { max-width: 1200px; margin: 0 auto; padding: 0 24px; }

/* ========== Navbar ========== */
.navbar {
  position: fixed;
  top: 0; left: 0; right: 0;
  z-index: 1000;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(16px) saturate(1.6);
  -webkit-backdrop-filter: blur(16px) saturate(1.6);
  border-bottom: 1px solid transparent;
  transition: background 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease;
}
.navbar-scrolled {
  background: rgba(255, 255, 255, 0.92);
  border-bottom-color: var(--tyt-border-light);
  box-shadow: 0 4px 24px -8px rgba(15, 23, 42, 0.08);
}
.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.nav-left { display: flex; align-items: center; gap: 48px; }
.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: var(--tyt-text);
  font-weight: 700;
  font-size: 18px;
}
.logo-img {
  width: 32px;
  height: 32px;
  border-radius: 9px;
  object-fit: cover;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.12);
}
.logo-text { font-size: 18px; font-weight: 800; letter-spacing: -0.02em; }
.nav-links { display: flex; align-items: center; gap: 32px; }
.nav-links a {
  position: relative;
  color: var(--tyt-text-dim);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: color 0.2s ease;
  padding: 4px 0;
}
.nav-links a::after {
  content: '';
  position: absolute;
  left: 0; right: 100%; bottom: -2px;
  height: 2px;
  border-radius: 2px;
  background: var(--tyt-gradient-brand);
  transition: right 0.3s cubic-bezier(0.22, 1, 0.36, 1);
}
.nav-links a:hover { color: var(--tyt-text); }
.nav-links a:hover::after { right: 0; }
.nav-right { display: flex; align-items: center; gap: 20px; }
.nav-link-login {
  color: var(--tyt-text-dim);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  padding: 8px 4px;
  transition: color 0.2s ease;
}
.nav-link-login:hover { color: var(--tyt-text); }

/* ========== Buttons ========== */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
  border: none;
  transition: all 0.25s cubic-bezier(0.22, 1, 0.36, 1);
  font-family: inherit;
  white-space: nowrap;
}
.btn-sm { padding: 9px 18px; font-size: 13px; }
.btn-lg { padding: 15px 32px; font-size: 15px; border-radius: 12px; }
.btn-primary {
  position: relative;
  overflow: hidden;
  background: var(--tyt-gradient-brand);
  background-size: 160% 160%;
  background-position: 0% 0%;
  color: white;
  box-shadow: 0 4px 16px -4px rgba(99, 102, 241, 0.45);
}
.btn-primary::after {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: linear-gradient(105deg, transparent 40%, rgba(255, 255, 255, 0.35) 50%, transparent 60%);
  transform: translateX(-130%);
  transition: transform 0.65s cubic-bezier(0.22, 1, 0.36, 1);
  pointer-events: none;
}
.btn-primary:hover {
  background-position: 95% 0%;
  transform: translateY(-2px);
  box-shadow: 0 10px 28px -6px rgba(99, 102, 241, 0.55);
}
.btn-primary:hover::after { transform: translateX(130%); }
.btn-outline {
  background: rgba(255, 255, 255, 0.7);
  color: var(--tyt-text);
  border: 1.5px solid var(--tyt-border);
  backdrop-filter: blur(8px);
}
.btn-outline:hover {
  border-color: var(--tyt-primary);
  color: var(--tyt-primary-dark);
  background: var(--tyt-primary-soft);
  transform: translateY(-2px);
}
.btn-outline--onDark {
  background: rgba(255, 255, 255, 0.12);
  color: white;
  border-color: rgba(255, 255, 255, 0.35);
}
.btn-outline--onDark:hover {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border-color: rgba(255, 255, 255, 0.6);
}
.btn-white {
  background: white;
  color: var(--tyt-ink);
  box-shadow: 0 4px 20px -4px rgba(0, 0, 0, 0.3);
}
.btn-white:hover {
  background: #f8fafc;
  transform: translateY(-2px);
  box-shadow: 0 10px 32px -6px rgba(0, 0, 0, 0.35);
}

/* ========== Hero ========== */
.hero {
  position: relative;
  padding: 172px 0 110px;
  overflow: hidden;
}
.hero-bg {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  z-index: 0;
  pointer-events: none;
  background: url('/skyeye.jpg') center center / cover no-repeat;
}
.hero-bg::after {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.82) 0%, rgba(248, 250, 252, 0.75) 50%, rgba(255, 255, 255, 0.88) 100%);
}
.hero-gradient {
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 720px;
  background: linear-gradient(180deg, rgba(99, 102, 241, 0.07) 0%, rgba(34, 211, 238, 0.035) 50%, transparent 100%);
}
.hero-gradient::before,
.hero-gradient::after {
  content: '';
  position: absolute;
  border-radius: 50%;
  filter: blur(52px);
  will-change: transform;
}
.hero-gradient::before {
  width: 580px; height: 580px;
  left: -140px; top: -100px;
  background: radial-gradient(circle, rgba(99, 102, 241, 0.17), transparent 65%);
  animation: blobDriftA 16s ease-in-out infinite alternate;
}
.hero-gradient::after {
  width: 520px; height: 520px;
  right: -120px; top: 40px;
  background: radial-gradient(circle, rgba(34, 211, 238, 0.13), transparent 65%);
  animation: blobDriftB 19s ease-in-out infinite alternate;
}
@keyframes blobDriftA {
  from { transform: translate(0, 0) scale(1); }
  to   { transform: translate(48px, 36px) scale(1.1); }
}
@keyframes blobDriftB {
  from { transform: translate(0, 0) scale(1); }
  to   { transform: translate(-42px, 28px) scale(1.08); }
}
.hero-grid {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background-image:
    linear-gradient(rgba(148, 163, 184, 0.09) 1px, transparent 1px),
    linear-gradient(90deg, rgba(148, 163, 184, 0.09) 1px, transparent 1px);
  background-size: 52px 52px;
  mask-image: radial-gradient(ellipse 90% 70% at center top, black 20%, transparent 72%);
  -webkit-mask-image: radial-gradient(ellipse 90% 70% at center top, black 20%, transparent 72%);
}
.hero-container {
  position: relative;
  z-index: 1;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  display: grid;
  grid-template-columns: 1.05fr 0.95fr;
  gap: 64px;
  align-items: center;
}
.hero-content > * {
  animation: riseIn 0.75s cubic-bezier(0.22, 1, 0.36, 1) backwards;
}
.hero-badge { animation-delay: 0.05s; }
.hero-title { animation-delay: 0.14s; }
.hero-desc { animation-delay: 0.24s; }
.hero-actions { animation-delay: 0.34s; }
.hero-note { animation-delay: 0.44s; }
.hero-visual { animation: riseIn 0.85s 0.3s cubic-bezier(0.22, 1, 0.36, 1) backwards; }
@keyframes riseIn {
  from { opacity: 0; transform: translateY(26px); }
  to   { opacity: 1; transform: translateY(0); }
}
.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  padding: 7px 16px;
  background: rgba(255, 255, 255, 0.75);
  border: 1px solid rgba(99, 102, 241, 0.22);
  color: var(--tyt-primary-dark);
  border-radius: 999px;
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 28px;
  backdrop-filter: blur(8px);
  box-shadow: 0 2px 12px -2px rgba(99, 102, 241, 0.15);
}
.badge-dot {
  width: 7px;
  height: 7px;
  background: var(--tyt-primary);
  border-radius: 50%;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
  animation: pulse 2s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.45; }
}
.hero-title {
  font-size: 60px;
  font-weight: 800;
  line-height: 1.12;
  letter-spacing: -0.032em;
  margin: 0 0 26px;
  color: var(--tyt-text);
}
.gradient-text {
  background: var(--tyt-gradient-hero-text);
  background-size: 200% 100%;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: gradientFlow 7s ease-in-out infinite alternate;
}
@keyframes gradientFlow {
  from { background-position: 0% 50%; }
  to   { background-position: 100% 50%; }
}
.hero-desc {
  font-size: 17px;
  line-height: 1.75;
  color: var(--tyt-text-dim);
  margin: 0 0 36px;
  max-width: 540px;
}
.hero-actions {
  display: flex;
  gap: 16px;
  margin-bottom: 26px;
  flex-wrap: wrap;
}
.hero-note {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--tyt-text-tertiary);
}
.hero-note svg { color: var(--tyt-green); }

/* ========== Hero 视觉：雷达舞台 ========== */
.hero-visual { position: relative; }
.video-placeholder {
  position: relative;
  aspect-ratio: 16 / 10;
  border-radius: 22px;
  background: linear-gradient(150deg, #10142e 0%, #1a1f4b 46%, #0e2a3c 100%);
  overflow: hidden;
  box-shadow:
    0 32px 72px -20px rgba(23, 20, 78, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.09);
  border: 1px solid rgba(255, 255, 255, 0.1);
}
.video-placeholder::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background:
    radial-gradient(circle at 22% 24%, rgba(99, 102, 241, 0.28), transparent 48%),
    radial-gradient(circle at 78% 72%, rgba(34, 211, 238, 0.2), transparent 48%);
  pointer-events: none;
  z-index: 0;
}
.video-placeholder::after {
  content: '';
  position: absolute;
  top: 0; left: 8%; right: 8%;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.32), transparent);
  z-index: 2;
}
.hero-video {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  z-index: 1;
}
.hero-video-mask {
  position: absolute;
  inset: 0;
  z-index: 2;
  pointer-events: none;
  background:
    linear-gradient(180deg, rgba(16, 20, 46, 0.15) 0%, transparent 30%, transparent 70%, rgba(14, 42, 60, 0.35) 100%);
}
.radar-stage {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  z-index: 1;
}
.radar-ring {
  position: absolute;
  border-radius: 50%;
  border: 1px solid rgba(148, 163, 184, 0.22);
}
.radar-ring--1 { width: 66%; aspect-ratio: 1; }
.radar-ring--2 { width: 46%; aspect-ratio: 1; border-color: rgba(148, 163, 184, 0.32); }
.radar-ring--3 { width: 26%; aspect-ratio: 1; border-color: rgba(148, 163, 184, 0.45); }
.radar-cross::before,
.radar-cross::after {
  content: '';
  position: absolute;
  background: rgba(148, 163, 184, 0.16);
}
.radar-cross::before {
  left: 50%; top: 17%; bottom: 17%; width: 1px;
}
.radar-cross::after {
  top: 50%; left: 17%; right: 17%; height: 1px;
}
.radar-sweep {
  position: absolute;
  width: 46%;
  aspect-ratio: 1;
  border-radius: 50%;
  background: conic-gradient(from 0deg, rgba(34, 211, 238, 0.42) 0deg, rgba(34, 211, 238, 0.08) 55deg, transparent 75deg);
  animation: radarSpin 4.5s linear infinite;
  will-change: transform;
}
@keyframes radarSpin {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}
.radar-core {
  position: absolute;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: radial-gradient(circle, #ffffff 0%, #67e8f9 60%);
  box-shadow:
    0 0 16px rgba(103, 232, 249, 0.95),
    0 0 42px rgba(34, 211, 238, 0.55);
  animation: radarCorePulse 2.6s ease-in-out infinite;
}
@keyframes radarCorePulse {
  0%, 100% { opacity: 0.75; transform: scale(1); }
  50%      { opacity: 1;    transform: scale(1.22); }
}
.radar-blip {
  position: absolute;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #67e8f9;
  box-shadow: 0 0 10px rgba(103, 232, 249, 0.9);
}
.radar-blip::after {
  content: '';
  position: absolute;
  inset: -5px;
  border-radius: 50%;
  border: 1.5px solid rgba(103, 232, 249, 0.65);
  animation: blipPing 2.6s ease-out infinite;
}
.radar-blip--1 { top: 28%; left: 36%; }
.radar-blip--2 { top: 58%; left: 66%; animation-delay: 0.8s; }
.radar-blip--3 { top: 66%; left: 30%; animation-delay: 1.5s; }
.radar-blip--4 { top: 22%; left: 62%; animation-delay: 2s; }
.radar-blip--2,
.radar-blip--4 {
  background: #a5b4fc;
  box-shadow: 0 0 10px rgba(165, 180, 252, 0.9);
}
.radar-blip--2::after,
.radar-blip--4::after {
  border-color: rgba(165, 180, 252, 0.6);
}
@keyframes blipPing {
  0%   { transform: scale(0.5); opacity: 1; }
  100% { transform: scale(2.8); opacity: 0; }
}

/* ========== Partners ========== */
.partners {
  padding: 56px 0;
  background: var(--tyt-bg);
  border-top: 1px solid var(--tyt-border-light);
  border-bottom: 1px solid var(--tyt-border-light);
}
.partners-label {
  text-align: center;
  font-size: 12.5px;
  color: var(--tyt-text-tertiary);
  margin: 0 0 28px;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  font-weight: 600;
}
.partners-logos {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 18px;
  flex-wrap: wrap;
}
.partner-logo {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 11px 22px;
  font-size: 14px;
  color: var(--tyt-text-tertiary);
  font-weight: 600;
  background: var(--tyt-card);
  border: 1px solid var(--tyt-border-light);
  border-radius: 999px;
  transition: all 0.25s cubic-bezier(0.22, 1, 0.36, 1);
}
.partner-logo:hover {
  transform: translateY(-3px);
  border-color: var(--tyt-border);
  box-shadow: var(--tyt-shadow-md);
  color: var(--tyt-text-dim);
}

/* ========== Section 通用 ========== */
.section-header {
  text-align: center;
  margin-bottom: 64px;
}
.section-title {
  font-size: 40px;
  font-weight: 800;
  letter-spacing: -0.028em;
  margin: 0 0 16px;
  color: var(--tyt-text);
  line-height: 1.2;
}
.section-desc {
  font-size: 17px;
  color: var(--tyt-text-dim);
  max-width: 620px;
  margin: 0 auto;
  line-height: 1.7;
}

/* ========== 滚动渐显动画（参考第一版 reveal 体系） ========== */
.reveal {
  opacity: 0;
  transform: translateY(30px);
  transition: opacity 0.75s cubic-bezier(0.22, 1, 0.36, 1), transform 0.75s cubic-bezier(0.22, 1, 0.36, 1);
}
.reveal.revealed {
  opacity: 1;
  transform: translateY(0);
}
.reveal > * {
  opacity: 0;
  transform: translateY(22px);
  transition: opacity 0.6s cubic-bezier(0.22, 1, 0.36, 1), transform 0.6s cubic-bezier(0.22, 1, 0.36, 1);
}
.reveal.revealed > * {
  opacity: 1;
  transform: translateY(0);
}
.reveal.revealed > *:nth-child(1) { transition-delay: 0.04s; }
.reveal.revealed > *:nth-child(2) { transition-delay: 0.12s; }
.reveal.revealed > *:nth-child(3) { transition-delay: 0.2s; }

/* 卡片级错峰：滚动到位后逐张浮现（动画方式，不干扰 hover 过渡） */
.reveal:not(.revealed) .feature-card,
.reveal:not(.revealed) .deploy-card,
.reveal:not(.revealed) .ai-card,
.reveal:not(.revealed) .ai-card-vs,
.reveal:not(.revealed) .partner-logo {
  opacity: 0;
}
.reveal.revealed .feature-card,
.reveal.revealed .deploy-card,
.reveal.revealed .ai-card,
.reveal.revealed .partner-logo {
  animation: cardRise 0.6s cubic-bezier(0.22, 1, 0.36, 1) backwards;
}
.reveal.revealed .ai-card-vs {
  animation: vsPop 0.55s cubic-bezier(0.22, 1, 0.36, 1) backwards;
}
@keyframes cardRise {
  from { opacity: 0; transform: translateY(22px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes vsPop {
  from { opacity: 0; transform: scale(0.4) rotate(-90deg); }
  to   { opacity: 1; transform: scale(1) rotate(0deg); }
}
.reveal.revealed .partners-logos > *:nth-child(1) { animation-delay: 0.08s; }
.reveal.revealed .partners-logos > *:nth-child(2) { animation-delay: 0.14s; }
.reveal.revealed .partners-logos > *:nth-child(3) { animation-delay: 0.2s; }
.reveal.revealed .partners-logos > *:nth-child(4) { animation-delay: 0.26s; }
.reveal.revealed .partners-logos > *:nth-child(5) { animation-delay: 0.32s; }
.reveal.revealed .features-grid > *:nth-child(1) { animation-delay: 0.16s; }
.reveal.revealed .features-grid > *:nth-child(2) { animation-delay: 0.24s; }
.reveal.revealed .features-grid > *:nth-child(3) { animation-delay: 0.32s; }
.reveal.revealed .features-grid > *:nth-child(4) { animation-delay: 0.4s; }
.reveal.revealed .features-grid--second > *:nth-child(1) { animation-delay: 0.44s; }
.reveal.revealed .features-grid--second > *:nth-child(2) { animation-delay: 0.52s; }
.reveal.revealed .features-grid--second > *:nth-child(3) { animation-delay: 0.6s; }
.reveal.revealed .features-grid--second > *:nth-child(4) { animation-delay: 0.68s; }
.reveal.revealed .ai-grid > *:nth-child(1) { animation-delay: 0.16s; }
.reveal.revealed .ai-grid > *:nth-child(2) { animation-delay: 0.3s; }
.reveal.revealed .ai-grid > *:nth-child(3) { animation-delay: 0.44s; }
.reveal.revealed .deploy-grid > *:nth-child(1) { animation-delay: 0.16s; }
.reveal.revealed .deploy-grid > *:nth-child(2) { animation-delay: 0.28s; }
.reveal.revealed .deploy-grid > *:nth-child(3) { animation-delay: 0.4s; }

/* ========== Features ========== */
.features { padding: 116px 0 96px; }
.features-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 22px;
}
.features-grid--second { margin-top: 22px; }
.feature-card {
  --card-accent: var(--tyt-gradient-brand);
  --card-shadow: rgba(99, 102, 241, 0.18);
  position: relative;
  padding: 30px 26px;
  background: var(--tyt-card);
  border: 1px solid var(--tyt-border-light);
  border-radius: 18px;
  transition: transform 0.35s cubic-bezier(0.22, 1, 0.36, 1), box-shadow 0.35s cubic-bezier(0.22, 1, 0.36, 1), border-color 0.35s ease;
  overflow: hidden;
}
.feature-card::before {
  content: '';
  position: absolute;
  top: 0; left: 26px; right: 26px;
  height: 3px;
  border-radius: 0 0 3px 3px;
  background: var(--card-accent);
  opacity: 0;
  transform: scaleX(0.35);
  transition: opacity 0.35s ease, transform 0.4s cubic-bezier(0.22, 1, 0.36, 1);
}
.feature-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 26px 52px -14px var(--card-shadow);
  border-color: transparent;
}
.feature-card:hover::before {
  opacity: 1;
  transform: scaleX(1);
}
.feature-icon {
  position: relative;
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  margin-bottom: 20px;
  color: white;
  transition: transform 0.35s cubic-bezier(0.22, 1, 0.36, 1);
}
.feature-icon svg { width: 24px; height: 24px; }
.feature-card:hover .feature-icon { transform: scale(1.08) rotate(-4deg); }
.feature-icon--cyan {
  background: linear-gradient(135deg, #22d3ee 0%, #0891b2 100%);
  box-shadow: 0 8px 20px -6px rgba(8, 145, 178, 0.5);
  --card-accent: linear-gradient(90deg, #22d3ee, #0891b2);
  --card-shadow: rgba(8, 145, 178, 0.16);
}
.feature-icon--purple {
  background: linear-gradient(135deg, #818cf8 0%, #7c3aed 100%);
  box-shadow: 0 8px 20px -6px rgba(124, 58, 237, 0.45);
  --card-accent: linear-gradient(90deg, #818cf8, #7c3aed);
  --card-shadow: rgba(124, 58, 237, 0.15);
}
.feature-icon--green {
  background: linear-gradient(135deg, #34d399 0%, #059669 100%);
  box-shadow: 0 8px 20px -6px rgba(5, 150, 105, 0.45);
  --card-accent: linear-gradient(90deg, #34d399, #059669);
  --card-shadow: rgba(5, 150, 105, 0.15);
}
.feature-icon--orange {
  background: linear-gradient(135deg, #fbbf24 0%, #f97316 100%);
  box-shadow: 0 8px 20px -6px rgba(249, 115, 22, 0.45);
  --card-accent: linear-gradient(90deg, #fbbf24, #f97316);
  --card-shadow: rgba(249, 115, 22, 0.15);
}
.feature-title {
  font-size: 19px;
  font-weight: 700;
  margin: 0 0 10px;
  color: var(--tyt-text);
  letter-spacing: -0.01em;
}
.feature-desc {
  font-size: 13.5px;
  line-height: 1.7;
  color: var(--tyt-text-dim);
  margin: 0 0 18px;
}
.feature-link {
  font-size: 13.5px;
  color: var(--tyt-primary);
  text-decoration: none;
  font-weight: 600;
  transition: color 0.2s ease, letter-spacing 0.25s cubic-bezier(0.22, 1, 0.36, 1);
}
.feature-link:hover {
  color: var(--tyt-primary-dark);
  letter-spacing: 0.03em;
}

/* ========== 双场景（深色带） ========== */
.ai-section {
  position: relative;
  padding: 116px 0;
  background:
    radial-gradient(900px 480px at 18% 0%, rgba(99, 102, 241, 0.22), transparent 60%),
    radial-gradient(800px 460px at 85% 100%, rgba(34, 211, 238, 0.13), transparent 60%),
    linear-gradient(165deg, #0d1029 0%, #141945 55%, #0c1830 100%);
  color: white;
  overflow: hidden;
}
.ai-section::after {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.035) 1px, transparent 1px);
  background-size: 48px 48px;
  mask-image: radial-gradient(ellipse 85% 80% at center, black 30%, transparent 75%);
  -webkit-mask-image: radial-gradient(ellipse 85% 80% at center, black 30%, transparent 75%);
  pointer-events: none;
}
.ai-section .section-title { color: white; }
.ai-section .section-desc { color: rgba(255, 255, 255, 0.62); }
.ai-grid {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 32px;
  align-items: stretch;
  max-width: 960px;
  margin: 0 auto;
}
.ai-card {
  position: relative;
  padding: 38px 36px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.045);
  border: 1px solid rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  transition: transform 0.35s cubic-bezier(0.22, 1, 0.36, 1), background 0.35s ease, border-color 0.35s ease, box-shadow 0.35s ease;
  overflow: hidden;
}
.ai-card--local::before,
.ai-card--cloud::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
}
.ai-card--local::before { background: linear-gradient(90deg, #818cf8, #6366f1); }
.ai-card--cloud::before { background: linear-gradient(90deg, #22d3ee, #0891b2); }
.ai-card:hover {
  transform: translateY(-6px);
  background: rgba(255, 255, 255, 0.07);
  border-color: rgba(255, 255, 255, 0.18);
}
.ai-card--local:hover { box-shadow: 0 28px 56px -16px rgba(99, 102, 241, 0.4); }
.ai-card--cloud:hover { box-shadow: 0 28px 56px -16px rgba(34, 211, 238, 0.32); }
.ai-card-header { margin-bottom: 12px; }
.ai-card-badge {
  display: inline-block;
  padding: 5px 13px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 14px;
  letter-spacing: 0.05em;
}
.ai-card--local .ai-card-badge {
  background: rgba(129, 140, 248, 0.16);
  color: #c7d2fe;
  border: 1px solid rgba(129, 140, 248, 0.3);
}
.ai-card--cloud .ai-card-badge {
  background: rgba(34, 211, 238, 0.13);
  color: #a5f3fc;
  border: 1px solid rgba(34, 211, 238, 0.28);
}
.ai-card-title {
  font-size: 23px;
  font-weight: 700;
  color: white;
  margin: 0;
  letter-spacing: -0.015em;
}
.ai-card-desc {
  font-size: 14px;
  line-height: 1.75;
  color: rgba(255, 255, 255, 0.68);
  margin: 0 0 24px;
}
.ai-card-features {
  display: flex;
  flex-wrap: wrap;
  gap: 9px;
}
.ai-card-features span {
  padding: 6px 13px;
  border-radius: 999px;
  font-size: 12.5px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.85);
  background: rgba(255, 255, 255, 0.07);
  border: 1px solid rgba(255, 255, 255, 0.13);
}
.ai-card-vs {
  align-self: center;
  width: 62px;
  height: 62px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  font-size: 15px;
  font-weight: 800;
  font-family: var(--tyt-font-mono);
  letter-spacing: 0.04em;
  color: white;
  background: rgba(13, 16, 41, 0.85);
  border: 1.5px solid rgba(255, 255, 255, 0.22);
  box-shadow:
    0 0 0 6px rgba(255, 255, 255, 0.04),
    0 0 34px rgba(99, 102, 241, 0.35);
  flex-shrink: 0;
}

/* ========== 合规 ========== */
.deploy-section { padding: 116px 0; }
.deploy-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 22px;
  max-width: 980px;
  margin: 0 auto;
}
.deploy-card {
  position: relative;
  padding: 38px 32px;
  background: var(--tyt-card);
  border: 1px solid var(--tyt-border-light);
  border-radius: 18px;
  transition: transform 0.35s cubic-bezier(0.22, 1, 0.36, 1), box-shadow 0.35s cubic-bezier(0.22, 1, 0.36, 1), border-color 0.35s ease;
}
.deploy-card:hover {
  transform: translateY(-6px);
  box-shadow: var(--tyt-shadow-lg);
  border-color: var(--tyt-border);
}
.deploy-card--featured {
  border: 1.5px solid transparent;
  background:
    linear-gradient(var(--tyt-card), var(--tyt-card)) padding-box,
    linear-gradient(135deg, #6366f1, #22d3ee) border-box;
  box-shadow: 0 18px 44px -14px rgba(99, 102, 241, 0.28);
}
.deploy-badge {
  position: absolute;
  top: -13px;
  left: 50%;
  transform: translateX(-50%);
  padding: 5px 16px;
  background: var(--tyt-gradient-brand);
  color: white;
  font-size: 12px;
  font-weight: 700;
  border-radius: 999px;
  letter-spacing: 0.05em;
  box-shadow: 0 4px 14px -2px rgba(99, 102, 241, 0.5);
  white-space: nowrap;
}
.deploy-icon {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  background: var(--tyt-primary-soft);
  color: var(--tyt-primary);
  display: grid;
  place-items: center;
  margin-bottom: 22px;
  transition: transform 0.35s cubic-bezier(0.22, 1, 0.36, 1);
}
.deploy-icon svg { width: 24px; height: 24px; }
.deploy-card:hover .deploy-icon { transform: scale(1.08) rotate(-4deg); }
.deploy-card h3 {
  font-size: 20px;
  font-weight: 700;
  margin: 0 0 10px;
  color: var(--tyt-text);
  letter-spacing: -0.01em;
}
.deploy-card > p {
  font-size: 14px;
  line-height: 1.7;
  color: var(--tyt-text-dim);
  margin: 0 0 16px;
}
.deploy-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.deploy-list li {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13.5px;
  color: var(--tyt-text-dim);
}
.deploy-list li::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--tyt-primary);
  flex-shrink: 0;
}

/* ========== CTA ========== */
.cta-section { padding: 24px 0 120px; }
.cta-card {
  position: relative;
  padding: 68px 72px;
  background:
    radial-gradient(640px 320px at 12% 0%, rgba(129, 140, 248, 0.4), transparent 60%),
    radial-gradient(560px 300px at 92% 100%, rgba(34, 211, 238, 0.22), transparent 60%),
    linear-gradient(135deg, #312e81 0%, #4338ca 55%, #3730a3 100%);
  border-radius: 26px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 40px;
  overflow: hidden;
  box-shadow: 0 36px 80px -22px rgba(49, 46, 129, 0.55);
}
.cta-card::before {
  content: '';
  position: absolute;
  top: 0; left: 10%; right: 10%;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
}
.cta-card::after {
  content: '';
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.04) 1px, transparent 1px);
  background-size: 44px 44px;
  mask-image: radial-gradient(ellipse 80% 90% at center, black 30%, transparent 78%);
  -webkit-mask-image: radial-gradient(ellipse 80% 90% at center, black 30%, transparent 78%);
  pointer-events: none;
}
.cta-content { position: relative; z-index: 1; }
.cta-content h2 {
  font-size: 34px;
  font-weight: 800;
  color: white;
  margin: 0 0 10px;
  letter-spacing: -0.025em;
}
.cta-content p {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.75);
  margin: 0;
}
.cta-actions {
  position: relative;
  z-index: 1;
  display: flex;
  gap: 14px;
  flex-shrink: 0;
}

/* ========== Footer ========== */
.footer {
  background: var(--tyt-bg);
  padding: 72px 0 28px;
  border-top: 1px solid var(--tyt-border-light);
}
.footer-grid {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr;
  gap: 48px;
  margin-bottom: 56px;
}
.footer-brand .logo { margin-bottom: 18px; }
.footer-brand > p {
  font-size: 13.5px;
  color: var(--tyt-text-dim);
  line-height: 1.8;
  margin: 0;
}
.footer-col h4 {
  font-size: 13px;
  font-weight: 700;
  color: var(--tyt-text);
  margin: 0 0 20px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.footer-col a {
  display: block;
  font-size: 14px;
  color: var(--tyt-text-dim);
  text-decoration: none;
  margin-bottom: 13px;
  transition: color 0.2s ease, transform 0.2s cubic-bezier(0.22, 1, 0.36, 1);
  width: fit-content;
}
.footer-col a:hover {
  color: var(--tyt-primary);
  transform: translateX(3px);
}
.footer-bottom {
  padding-top: 26px;
  border-top: 1px solid var(--tyt-border-light);
  text-align: center;
  font-size: 13px;
  color: var(--tyt-text-tertiary);
}
.footer-bottom p { margin: 0; }

/* ========== Responsive ========== */
@media (max-width: 1024px) {
  .hero { padding: 140px 0 80px; }
  .hero-container { grid-template-columns: 1fr; gap: 56px; }
  .hero-title { font-size: 46px; }
  .hero-desc { max-width: 100%; }
  .section-title { font-size: 32px; }
  .features-grid { grid-template-columns: repeat(2, 1fr); }
  .ai-grid { grid-template-columns: 1fr; max-width: 520px; }
  .ai-card-vs { justify-self: center; }
  .deploy-grid { grid-template-columns: 1fr; max-width: 480px; margin: 0 auto; }
  .footer-grid { grid-template-columns: 1fr 1fr; gap: 36px; }
  .cta-card {
    flex-direction: column;
    text-align: center;
    padding: 52px 36px;
  }
}
@media (max-width: 768px) {
  .nav-links { display: none; }
  .nav-right { gap: 12px; }
  .hero { padding: 116px 0 64px; }
  .hero-title { font-size: 36px; }
  .hero-actions .btn { width: 100%; }
  .section-title { font-size: 27px; }
  .section-desc { font-size: 15px; }
  .features { padding: 80px 0 64px; }
  .features-grid { grid-template-columns: 1fr; }
  .ai-section { padding: 80px 0; }
  .ai-card { padding: 30px 26px; }
  .deploy-section { padding: 80px 0; }
  .cta-section { padding: 8px 0 80px; }
  .cta-content h2 { font-size: 25px; }
  .footer-grid { grid-template-columns: 1fr; gap: 32px; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    animation-delay: 0s !important;
    transition-duration: 0.01ms !important;
    transition-delay: 0s !important;
    scroll-behavior: auto !important;
  }
  .reveal,
  .reveal > * {
    opacity: 1;
    transform: none;
  }
}
</style>
