<template>
  <div class="auth-page">
    <AuthBrand />
    <div class="auth-right">
      <div class="auth-right-inner">
        <div class="auth-form-container">
          <div class="auth-form-header">
            <h2>欢迎回来</h2>
            <p>登录你的天眼通账户</p>
          </div>

          <form class="auth-form" @submit.prevent="onLogin">
            <div class="form-group" :class="{ 'has-error': !!errors.account }">
              <label for="login-account">手机号 / 邮箱</label>
              <input type="text" id="login-account" v-model="form.account"
                     placeholder="请输入手机号或邮箱" autocomplete="username">
              <div class="form-error">{{ errors.account }}</div>
            </div>

            <div class="form-group" :class="{ 'has-error': !!errors.password }">
              <div class="form-label-row">
                <label for="login-password">密码</label>
              </div>
              <div class="input-wrap">
                <input :type="showPwd ? 'text' : 'password'" id="login-password" v-model="form.password"
                       placeholder="请输入密码" autocomplete="current-password">
                <button type="button" class="pwd-toggle" :class="{ 'show-pwd': showPwd }" @click="showPwd = !showPwd"
                        aria-label="切换密码可见性">
                  <svg v-if="!showPwd" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                    <circle cx="12" cy="12" r="3"></circle>
                  </svg>
                  <svg v-else width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                    <line x1="1" y1="1" x2="23" y2="23"></line>
                  </svg>
                </button>
              </div>
              <div class="form-error">{{ errors.password }}</div>
            </div>

            <div class="form-group">
              <label class="form-checkbox">
                <input type="checkbox" v-model="form.agree">
                <span>我已阅读并同意<a href="#" @click.prevent>《用户协议》</a>与<a href="#" @click.prevent>《隐私政策》</a></span>
              </label>
            </div>

            <button type="submit" class="btn-primary btn-block btn-lg" :disabled="loading">
              {{ loading ? '登录中...' : '登录' }}
            </button>
          </form>

          <div class="auth-divider"><span>或</span></div>

          <div class="auth-footer-text">
            还没有账户？
            <router-link to="/register" class="link-primary">立即注册</router-link>
          </div>

          <div class="auth-guest-entry">
            <router-link to="/life" class="guest-link">先随便逛逛 →</router-link>
          </div>

          <div class="test-accounts">
            <div class="test-accounts-title">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line>
              </svg>
              演示账号 · 一键填充
            </div>
            <button v-for="d in demos" :key="d.a" type="button" class="test-account-card" @click="fill(d.a)">
              <span class="ta-role" :class="d.admin ? 'ta-role--admin' : 'ta-role--user'">{{ d.label }}</span>
              <span class="ta-info">
                <span class="ta-acc">{{ d.a }}</span>
                <span class="ta-pwd">SkyEye@123456</span>
              </span>
              <svg class="ta-fill-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="9 11 12 14 22 4"></polyline>
                <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import AuthBrand from '@/components/AuthBrand.vue'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const form = reactive({ account: '', password: '', agree: false })
const errors = reactive({ account: '', password: '' })
const loading = ref(false)
const showPwd = ref(false)

const demos = [
  { label: '普通用户', a: 'demo@tyt.demo', admin: false },
  { label: '高级会员', a: 'premium@tyt.demo', admin: false },
  { label: '企业管理员', a: 'entadmin@tyt.demo', admin: false },
  { label: '平台管理员', a: 'admin@tyt.demo', admin: true },
]

function fill(account: string) {
  form.account = account
  form.password = 'SkyEye@123456'
  errors.account = ''
  errors.password = ''
}

async function onLogin() {
  errors.account = ''
  errors.password = ''
  if (!form.account.trim()) { errors.account = '请输入手机号或邮箱'; return }
  if (!form.password) { errors.password = '请输入密码'; return }
  if (!form.agree) { ElMessage.warning('请先阅读并同意用户协议与隐私政策'); return }
  loading.value = true
  try {
    await auth.login(form.account.trim(), form.password)
    ElMessage.success('登录成功')
    router.push((route.query.redirect as string) || '/life')
  } catch (e: any) {
    errors.password = e?.response?.data?.message || '登录失败，请检查账号与密码'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 1fr 1fr;
  background: #fff;
}

.auth-right {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 56px;
  background:
    radial-gradient(900px 520px at 100% 0%, rgba(99, 102, 241, 0.055), transparent 60%),
    radial-gradient(rgba(15, 23, 42, 0.045) 1px, transparent 1px);
  background-size: auto, 26px 26px;
}
.auth-right-inner {
  width: 100%;
  max-width: 410px;
  animation: formIn 0.7s 0.15s cubic-bezier(0.22, 1, 0.36, 1) backwards;
}
@keyframes formIn {
  from { opacity: 0; transform: translateY(18px) scale(0.99); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}

.auth-form-header h2 {
  font-size: 27px;
  font-weight: 800;
  letter-spacing: -0.025em;
  color: var(--tyt-text);
  margin: 0 0 6px;
}
.auth-form-header p {
  font-size: 14.5px;
  color: var(--tyt-text-dim);
  margin: 0 0 30px;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.form-group > label,
.form-label-row label {
  font-size: 13px;
  font-weight: 600;
  color: var(--tyt-text);
  letter-spacing: 0.01em;
}
.form-label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.auth-form input[type="text"],
.auth-form input[type="password"] {
  width: 100%;
  height: 44px;
  padding: 0 4px;
  border: none;
  border-bottom: 1.5px solid var(--tyt-border);
  border-radius: 0;
  font-size: 14px;
  font-family: inherit;
  transition: border-color 0.2s ease;
  background: transparent;
  color: var(--tyt-text);
  box-sizing: border-box;
}
.input-wrap { position: relative; }
.input-wrap input { padding-right: 46px; }
.auth-form input:focus {
  outline: none;
  border-bottom-color: var(--tyt-primary);
}
.auth-form input::placeholder {
  color: var(--tyt-text-tertiary);
  opacity: 0.45;
}
.form-group.has-error input {
  border-bottom-color: var(--tyt-red);
  animation: inputShake 0.32s ease;
}
@keyframes inputShake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-5px); }
  75% { transform: translateX(5px); }
}

.pwd-toggle {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  color: var(--tyt-text-tertiary);
  padding: 7px;
  border-radius: 8px;
  display: grid;
  place-items: center;
  transition: color 0.2s ease, background 0.2s ease;
}
.pwd-toggle:hover {
  color: var(--tyt-text-dim);
  background: var(--tyt-bg-soft);
}

.form-error {
  font-size: 12px;
  color: var(--tyt-red);
  min-height: 0;
  margin-top: -2px;
}

.form-checkbox {
  display: flex;
  align-items: flex-start;
  gap: 9px;
  font-size: 13px;
  color: var(--tyt-text-dim);
  cursor: pointer;
  font-weight: 400;
  line-height: 1.5;
}
.form-checkbox input[type="checkbox"] {
  margin-top: 2px;
  width: 15px;
  height: 15px;
  accent-color: var(--tyt-primary);
  cursor: pointer;
  flex-shrink: 0;
}
.form-checkbox a {
  color: var(--tyt-primary);
  text-decoration: none;
  font-weight: 500;
}
.form-checkbox a:hover { text-decoration: underline; }

.btn-primary {
  position: relative;
  overflow: hidden;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 15px 32px;
  font-size: 15px;
  font-weight: 600;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  font-family: inherit;
  white-space: nowrap;
  background: var(--tyt-gradient-brand);
  background-size: 160% 160%;
  background-position: 0% 0%;
  color: white;
  box-shadow: 0 4px 16px -4px rgba(99, 102, 241, 0.45);
  transition: all 0.25s cubic-bezier(0.22, 1, 0.36, 1);
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
.btn-primary:hover:not(:disabled) {
  background-position: 95% 0%;
  transform: translateY(-2px);
  box-shadow: 0 10px 28px -6px rgba(99, 102, 241, 0.55);
}
.btn-primary:hover:not(:disabled)::after { transform: translateX(130%); }
.btn-primary:active:not(:disabled) { transform: translateY(0); }
.btn-primary:disabled {
  background: var(--tyt-primary-light);
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}
.btn-block { width: 100%; }

.auth-divider {
  display: flex;
  align-items: center;
  gap: 16px;
  margin: 22px 0 4px;
}
.auth-divider::before,
.auth-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--tyt-border-light);
}
.auth-divider span {
  font-size: 12.5px;
  color: var(--tyt-text-tertiary);
}

.auth-footer-text {
  text-align: center;
  font-size: 13.5px;
  color: var(--tyt-text-dim);
}
.link-primary {
  color: var(--tyt-primary);
  font-weight: 600;
  text-decoration: none;
}
.link-primary:hover { color: var(--tyt-primary-dark); }

.auth-guest-entry {
  text-align: center;
  margin-top: 14px;
}
.guest-link {
  font-size: 13px;
  color: var(--tyt-text-tertiary);
  text-decoration: none;
  transition: color 0.2s ease;
}
.guest-link:hover { color: var(--tyt-primary); }

.test-accounts {
  margin-top: 26px;
  padding: 14px;
  border: 1px dashed var(--tyt-border);
  border-radius: 12px;
  background: var(--tyt-bg);
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.test-accounts-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: var(--tyt-text-tertiary);
  letter-spacing: 0.02em;
}
.test-account-card {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 9px 12px;
  border: 1px solid var(--tyt-border);
  border-radius: 8px;
  background: var(--tyt-card);
  cursor: pointer;
  font-family: inherit;
  text-align: left;
  transition: border-color 0.2s cubic-bezier(0.22, 1, 0.36, 1), box-shadow 0.2s cubic-bezier(0.22, 1, 0.36, 1), transform 0.2s cubic-bezier(0.22, 1, 0.36, 1);
}
.test-account-card:hover {
  border-color: var(--tyt-primary-light);
  box-shadow: 0 0 0 3px var(--tyt-primary-soft);
  transform: translateY(-1px);
}
.ta-role {
  flex-shrink: 0;
  font-size: 11px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 999px;
  line-height: 1;
}
.ta-role--admin {
  color: #b45309;
  background: rgba(245, 158, 11, 0.12);
  border: 1px solid rgba(245, 158, 11, 0.35);
}
.ta-role--user {
  color: var(--tyt-primary-dark);
  background: var(--tyt-primary-soft);
  border: 1px solid rgba(99, 102, 241, 0.3);
}
.ta-info {
  flex: 1;
  display: flex;
  align-items: baseline;
  gap: 10px;
  min-width: 0;
}
.ta-acc {
  font-family: var(--tyt-font-mono);
  font-size: 12.5px;
  font-weight: 600;
  color: var(--tyt-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.ta-pwd {
  font-family: var(--tyt-font-mono);
  font-size: 11.5px;
  color: var(--tyt-text-tertiary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.ta-fill-icon {
  flex-shrink: 0;
  color: var(--tyt-text-tertiary);
  transition: color 0.2s cubic-bezier(0.22, 1, 0.36, 1);
}
.test-account-card:hover .ta-fill-icon { color: var(--tyt-primary); }

@media (max-width: 1024px) {
  .auth-page { grid-template-columns: 1fr; }
  .auth-right {
    min-height: 100vh;
    padding: 40px 24px;
  }
}
</style>
