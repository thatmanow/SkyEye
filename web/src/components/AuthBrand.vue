<template>
  <div class="auth-left">
    <div class="auth-left-inner">
      <router-link to="/" class="auth-logo">
        <img src="/skyeye-logo.jpg" alt="天眼通" class="logo-img">
        <span class="logo-text">天眼通</span>
      </router-link>
      <div class="auth-hero">
        <div class="sphere-container">
          <div class="particle-field">
            <span class="particle p1"></span><span class="particle p2"></span>
            <span class="particle p3"></span><span class="particle p4"></span>
            <span class="particle p5"></span><span class="particle p6"></span>
            <span class="particle p7"></span><span class="particle p8"></span>
            <span class="particle p9"></span><span class="particle p10"></span>
            <span class="particle p11"></span><span class="particle p12"></span>
          </div>
          <div class="sphere">
            <div v-for="i in 13" :key="'lat' + i" class="sphere-ring lat" :class="'lat-' + i"></div>
            <div v-for="i in 12" :key="'lng' + i" class="sphere-ring lng" :class="'lng-' + i"></div>
            <div class="sphere-ring tilt tilt-1"></div>
            <div class="sphere-ring tilt tilt-2"></div>
            <div class="sphere-ring tilt tilt-3"></div>
            <div class="sphere-dots">
              <span class="dot d1"></span><span class="dot d2"></span>
              <span class="dot d3"></span><span class="dot d4"></span>
              <span class="dot d5"></span><span class="dot d6"></span>
              <span class="dot d7"></span><span class="dot d8"></span>
            </div>
            <div class="sphere-core"></div>
            <div class="sphere-core-ring"></div>
          </div>
          <div class="orbit orbit-1"><div class="orbit-satellite"></div></div>
          <div class="orbit orbit-2"><div class="orbit-satellite orbit-satellite--sm"></div></div>
          <div class="orbit orbit-3"><div class="orbit-satellite orbit-satellite--lg"></div></div>
          <div class="sphere-glow"></div>
          <div class="sphere-glow sphere-glow--inner"></div>
        </div>
        <h1 class="auth-hero-title">看见更远的世界</h1>
      </div>
      <div class="auth-features">
        <div class="auth-feature">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
          </svg>
          <span>数据来源公开合法，隐私安全可控</span>
        </div>
        <div class="auth-feature">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="20 6 9 17 4 12"></polyline>
          </svg>
          <span>生活避坑 · 商业尽调 · 一站式查询</span>
        </div>
        <div class="auth-feature">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="3"></circle>
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
          </svg>
          <span>风险洞察 · 关系图谱 · 尽调报告</span>
        </div>
      </div>
      <div class="auth-footer-brand">© 2026 天眼通 TianYanTong. All rights reserved.</div>
    </div>
  </div>
</template>

<style scoped>
.auth-left {
  position: relative;
  background: linear-gradient(160deg, #0b0e27 0%, #1a1f4b 42%, #2b2a78 75%, #3d3a9e 100%);
  color: white;
  overflow: hidden;
}
.auth-left::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background-image:
    radial-gradient(circle at 18% 16%, rgba(34, 211, 238, 0.16), transparent 42%),
    radial-gradient(circle at 82% 82%, rgba(167, 139, 250, 0.22), transparent 44%),
    radial-gradient(circle at 60% 30%, rgba(99, 102, 241, 0.12), transparent 50%);
  animation: auroraShift 18s ease-in-out infinite alternate;
}
@keyframes auroraShift {
  from { transform: translate(0, 0) scale(1); opacity: 0.9; }
  to   { transform: translate(-3%, 2%) scale(1.06); opacity: 1; }
}
.auth-left::after {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.045) 1px, transparent 1px);
  background-size: 44px 44px;
  mask-image: radial-gradient(ellipse at center, black 38%, transparent 80%);
  -webkit-mask-image: radial-gradient(ellipse at center, black 38%, transparent 80%);
}
.auth-left-inner {
  position: relative;
  z-index: 1;
  padding: 44px 60px;
  height: 100vh;
  display: flex;
  flex-direction: column;
}
.auth-logo {
  display: flex;
  align-items: center;
  gap: 12px;
  text-decoration: none;
  color: white;
  font-weight: 800;
  font-size: 19px;
  cursor: pointer;
  transition: opacity 0.2s ease;
  animation: riseIn 0.7s 0.05s cubic-bezier(0.22, 1, 0.36, 1) backwards;
}
.auth-logo:hover { opacity: 0.85; }
.auth-logo .logo-img {
  width: 36px;
  height: 36px;
  border-radius: 9px;
  object-fit: cover;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35);
}
.auth-logo .logo-text { font-size: 19px; color: white; letter-spacing: -0.02em; }
.auth-hero {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  max-width: 500px;
  gap: 42px;
  animation: riseIn 0.8s 0.18s cubic-bezier(0.22, 1, 0.36, 1) backwards;
}
.auth-features {
  display: flex;
  flex-direction: column;
  gap: 12px;
  animation: riseIn 0.8s 0.32s cubic-bezier(0.22, 1, 0.36, 1) backwards;
}
@keyframes riseIn {
  from { opacity: 0; transform: translateY(26px); }
  to   { opacity: 1; transform: translateY(0); }
}

.sphere-container {
  position: relative;
  width: 360px;
  height: 360px;
  perspective: 1200px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.particle-field {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  pointer-events: none;
}
.particle {
  position: absolute;
  width: 3px;
  height: 3px;
  background: rgba(34, 211, 238, 0.6);
  border-radius: 50%;
  box-shadow: 0 0 6px rgba(34, 211, 238, 0.8);
}
.particle.p1  { top: 8%;  left: 20%; animation: floatParticle 6s ease-in-out infinite; }
.particle.p2  { top: 15%; left: 75%; animation: floatParticle 8s ease-in-out infinite 0.5s; }
.particle.p3  { top: 30%; left: 10%; animation: floatParticle 7s ease-in-out infinite 1s; }
.particle.p4  { top: 45%; left: 90%; animation: floatParticle 9s ease-in-out infinite 1.5s; }
.particle.p5  { top: 60%; left: 15%; animation: floatParticle 6.5s ease-in-out infinite 2s; }
.particle.p6  { top: 70%; left: 80%; animation: floatParticle 7.5s ease-in-out infinite 0.8s; }
.particle.p7  { top: 85%; left: 25%; animation: floatParticle 8.5s ease-in-out infinite 1.2s; }
.particle.p8  { top: 25%; left: 50%; animation: floatParticle 5.5s ease-in-out infinite 0.3s; }
.particle.p9  { top: 55%; left: 5%;  animation: floatParticle 7s ease-in-out infinite 1.8s; }
.particle.p10 { top: 90%; left: 65%; animation: floatParticle 6s ease-in-out infinite 2.2s; }
.particle.p11 { top: 5%;  left: 60%; animation: floatParticle 8s ease-in-out infinite 0.7s; }
.particle.p12 { top: 75%; left: 45%; animation: floatParticle 9.5s ease-in-out infinite 1.5s; }
@keyframes floatParticle {
  0%, 100% { transform: translate(0, 0) scale(1); opacity: 0.4; }
  25%      { transform: translate(10px, -8px) scale(1.2); opacity: 0.8; }
  50%      { transform: translate(-5px, 5px) scale(0.8); opacity: 0.6; }
  75%      { transform: translate(8px, 6px) scale(1.1); opacity: 0.9; }
}

.sphere {
  position: relative;
  width: 280px;
  height: 280px;
  transform-style: preserve-3d;
  animation: sphereRotate 25s linear infinite;
}
@keyframes sphereRotate {
  from { transform: rotateY(0deg) rotateX(20deg) rotateZ(0deg); }
  to   { transform: rotateY(360deg) rotateX(20deg) rotateZ(0deg); }
}
.sphere-ring {
  position: absolute;
  top: 50%;
  left: 50%;
  border: 1px solid rgba(34, 211, 238, 0.5);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  box-shadow:
    0 0 12px rgba(34, 211, 238, 0.2),
    inset 0 0 12px rgba(34, 211, 238, 0.08);
}
.lat { width: 280px; height: 280px; }
.lat-1  { transform: translate(-50%, -50%) rotateX(90deg) translateZ(0px); }
.lat-2  { transform: translate(-50%, -50%) rotateX(90deg) translateZ(25px)  scale(0.987); width: 276px; height: 276px; }
.lat-3  { transform: translate(-50%, -50%) rotateX(90deg) translateZ(50px)  scale(0.95);  width: 266px; height: 266px; }
.lat-4  { transform: translate(-50%, -50%) rotateX(90deg) translateZ(75px)  scale(0.89);  width: 249px; height: 249px; }
.lat-5  { transform: translate(-50%, -50%) rotateX(90deg) translateZ(100px) scale(0.8);   width: 224px; height: 224px; }
.lat-6  { transform: translate(-50%, -50%) rotateX(90deg) translateZ(120px) scale(0.68);  width: 190px; height: 190px; }
.lat-7  { transform: translate(-50%, -50%) rotateX(90deg) translateZ(135px) scale(0.52);  width: 146px; height: 146px; }
.lat-8  { transform: translate(-50%, -50%) rotateX(90deg) translateZ(-25px)  scale(0.987); width: 276px; height: 276px; }
.lat-9  { transform: translate(-50%, -50%) rotateX(90deg) translateZ(-50px)  scale(0.95);  width: 266px; height: 266px; }
.lat-10 { transform: translate(-50%, -50%) rotateX(90deg) translateZ(-75px)  scale(0.89);  width: 249px; height: 249px; }
.lat-11 { transform: translate(-50%, -50%) rotateX(90deg) translateZ(-100px) scale(0.8);   width: 224px; height: 224px; }
.lat-12 { transform: translate(-50%, -50%) rotateX(90deg) translateZ(-120px) scale(0.68);  width: 190px; height: 190px; }
.lat-13 { transform: translate(-50%, -50%) rotateX(90deg) translateZ(-135px) scale(0.52);  width: 146px; height: 146px; }

.lng { width: 280px; height: 280px; }
.lng-1  { transform: translate(-50%, -50%) rotateY(0deg); }
.lng-2  { transform: translate(-50%, -50%) rotateY(15deg); }
.lng-3  { transform: translate(-50%, -50%) rotateY(30deg); }
.lng-4  { transform: translate(-50%, -50%) rotateY(45deg); }
.lng-5  { transform: translate(-50%, -50%) rotateY(60deg); }
.lng-6  { transform: translate(-50%, -50%) rotateY(75deg); }
.lng-7  { transform: translate(-50%, -50%) rotateY(90deg); }
.lng-8  { transform: translate(-50%, -50%) rotateY(105deg); }
.lng-9  { transform: translate(-50%, -50%) rotateY(120deg); }
.lng-10 { transform: translate(-50%, -50%) rotateY(135deg); }
.lng-11 { transform: translate(-50%, -50%) rotateY(150deg); }
.lng-12 { transform: translate(-50%, -50%) rotateY(165deg); }

.tilt {
  width: 280px;
  height: 280px;
  border-color: rgba(167, 139, 250, 0.4);
  box-shadow:
    0 0 12px rgba(167, 139, 250, 0.2),
    inset 0 0 12px rgba(167, 139, 250, 0.08);
}
.tilt-1 { transform: translate(-50%, -50%) rotateX(45deg) rotateY(30deg); }
.tilt-2 { transform: translate(-50%, -50%) rotateX(-30deg) rotateY(60deg); }
.tilt-3 { transform: translate(-50%, -50%) rotateX(60deg) rotateY(-45deg); }

.sphere-dots {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  transform-style: preserve-3d;
}
.dot {
  position: absolute;
  width: 5px;
  height: 5px;
  background: rgba(34, 211, 238, 0.9);
  border-radius: 50%;
  box-shadow:
    0 0 8px rgba(34, 211, 238, 1),
    0 0 16px rgba(34, 211, 238, 0.6);
  animation: dotPulse 2s ease-in-out infinite;
}
.dot.d1 { transform: translate3d(-3px, -3px, 140px); animation-delay: 0s; }
.dot.d2 { transform: translate3d(-3px, -3px, -140px); animation-delay: 0.5s; }
.dot.d3 { transform: translate3d(140px, -3px, -3px); animation-delay: 1s; }
.dot.d4 { transform: translate3d(-140px, -3px, -3px); animation-delay: 1.5s; }
.dot.d5 { transform: translate3d(-3px, 100px, 90px); animation-delay: 0.3s; }
.dot.d6 { transform: translate3d(-3px, -100px, -90px); animation-delay: 0.8s; }
.dot.d7 { transform: translate3d(90px, 60px, 80px); animation-delay: 1.2s; }
.dot.d8 { transform: translate3d(-90px, -60px, -80px); animation-delay: 1.7s; }
@keyframes dotPulse {
  0%, 100% { opacity: 0.6; transform: scale(1); }
  50%      { opacity: 1;   transform: scale(1.4); }
}

.sphere-core {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 16px;
  height: 16px;
  background: radial-gradient(circle, rgba(255,255,255,1) 0%, rgba(34,211,238,1) 40%, rgba(99,102,241,0.8) 100%);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  box-shadow:
    0 0 30px rgba(34, 211, 238, 0.9),
    0 0 60px rgba(34, 211, 238, 0.6),
    0 0 100px rgba(99, 102, 241, 0.4);
  animation: corePulse 3s ease-in-out infinite;
}
.sphere-core-ring {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 40px;
  height: 40px;
  border: 1px solid rgba(34, 211, 238, 0.5);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  animation: coreRingPulse 3s ease-in-out infinite;
}
@keyframes corePulse {
  0%, 100% {
    box-shadow:
      0 0 30px rgba(34, 211, 238, 0.9),
      0 0 60px rgba(34, 211, 238, 0.6),
      0 0 100px rgba(99, 102, 241, 0.4);
  }
  50% {
    box-shadow:
      0 0 40px rgba(34, 211, 238, 1),
      0 0 80px rgba(34, 211, 238, 0.8),
      0 0 130px rgba(99, 102, 241, 0.6);
  }
}
@keyframes coreRingPulse {
  0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: 0.6; }
  50%      { transform: translate(-50%, -50%) scale(1.5); opacity: 0.2; }
}

.orbit {
  position: absolute;
  top: 50%;
  left: 50%;
  border: 1px dashed rgba(34, 211, 238, 0.25);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  transform-style: preserve-3d;
}
.orbit-1 {
  width: 340px;
  height: 340px;
  animation: orbitRotate 12s linear infinite;
}
.orbit-2 {
  width: 300px;
  height: 300px;
  animation: orbitRotate2 8s linear infinite reverse;
}
.orbit-3 {
  width: 380px;
  height: 380px;
  animation: orbitRotate3 18s linear infinite;
}
@keyframes orbitRotate {
  from { transform: translate(-50%, -50%) rotateX(70deg) rotateZ(0deg); }
  to   { transform: translate(-50%, -50%) rotateX(70deg) rotateZ(360deg); }
}
@keyframes orbitRotate2 {
  from { transform: translate(-50%, -50%) rotateX(50deg) rotateY(30deg) rotateZ(0deg); }
  to   { transform: translate(-50%, -50%) rotateX(50deg) rotateY(30deg) rotateZ(360deg); }
}
@keyframes orbitRotate3 {
  from { transform: translate(-50%, -50%) rotateX(-60deg) rotateY(-20deg) rotateZ(0deg); }
  to   { transform: translate(-50%, -50%) rotateX(-60deg) rotateY(-20deg) rotateZ(360deg); }
}
.orbit-satellite {
  position: absolute;
  top: 0;
  left: 50%;
  width: 8px;
  height: 8px;
  background: rgba(34, 211, 238, 1);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  box-shadow:
    0 0 10px rgba(34, 211, 238, 1),
    0 0 20px rgba(34, 211, 238, 0.6);
}
.orbit-satellite--sm {
  width: 5px;
  height: 5px;
  background: rgba(167, 139, 250, 1);
  box-shadow:
    0 0 8px rgba(167, 139, 250, 1),
    0 0 16px rgba(167, 139, 250, 0.6);
}
.orbit-satellite--lg {
  width: 10px;
  height: 10px;
  background: rgba(255, 255, 255, 0.9);
  box-shadow:
    0 0 12px rgba(34, 211, 238, 1),
    0 0 24px rgba(99, 102, 241, 0.7);
}

.sphere-glow {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 420px;
  height: 420px;
  transform: translate(-50%, -50%);
  background: radial-gradient(circle, rgba(34, 211, 238, 0.12) 0%, rgba(99, 102, 241, 0.06) 40%, transparent 70%);
  border-radius: 50%;
  pointer-events: none;
  animation: glowPulse 5s ease-in-out infinite;
}
.sphere-glow--inner {
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, rgba(34, 211, 238, 0.18) 0%, rgba(167, 139, 250, 0.08) 50%, transparent 75%);
  animation: glowPulse 4s ease-in-out infinite reverse;
}
@keyframes glowPulse {
  0%, 100% { opacity: 0.8; transform: translate(-50%, -50%) scale(1); }
  50%      { opacity: 1;   transform: translate(-50%, -50%) scale(1.08); }
}

.auth-hero-title {
  font-size: 42px;
  font-weight: 800;
  line-height: 1.2;
  letter-spacing: -0.028em;
  margin: 0;
  text-align: center;
  background: linear-gradient(120deg, #ffffff 25%, #c7d2fe 55%, #a5f3fc 85%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.auth-feature {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 13px 20px;
  font-size: 13.5px;
  color: rgba(255, 255, 255, 0.88);
  background: rgba(255, 255, 255, 0.055);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 13px;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}
.auth-feature svg { flex-shrink: 0; color: #34d399; }
.auth-footer-brand {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
}

@media (max-width: 1024px) {
  .auth-left { display: none; }
}
@media (max-width: 768px) {
  .sphere-container { transform: scale(0.85); }
  .auth-hero-title { font-size: 34px; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
  }
}
</style>
