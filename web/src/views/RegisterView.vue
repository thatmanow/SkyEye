<template>
  <div class="auth-page">
    <AuthBrand />
    <div class="auth-right">
      <div class="auth-right-inner">
        <div class="auth-form-container">
          <div class="auth-form-header">
            <h2>创建账户</h2>
            <p>开始使用天眼通的全部功能</p>
          </div>

          <form class="auth-form" @submit.prevent="onRegister">
            <div class="form-group" :class="{ 'has-error': !!errors.nickname }">
              <label for="reg-nickname">昵称</label>
              <input type="text" id="reg-nickname" v-model="form.nickname"
                     placeholder="2-16 个字符" autocomplete="nickname">
              <div class="form-error">{{ errors.nickname }}</div>
            </div>

            <div class="form-group" :class="{ 'has-error': !!errors.account }">
              <label for="reg-account">手机号 / 邮箱</label>
              <input type="text" id="reg-account" v-model="form.account"
                     placeholder="用于登录与找回密码" autocomplete="username">
              <div class="form-error">{{ errors.account }}</div>
            </div>

            <div class="form-group" :class="{ 'has-error': !!errors.password }">
              <label for="reg-password">设置密码</label>
              <div class="input-wrap">
                <input :type="showPwd ? 'text' : 'password'" id="reg-password" v-model="form.password"
                       placeholder="8-32 位，须含字母和数字" autocomplete="new-password" @input="onPwdInput">
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
              <div class="form-strength">
                <span class="strength-bar" :class="{ s1: pwdLevel >= 1, s2: pwdLevel >= 2, s3: pwdLevel >= 3 }"></span>
                <span class="strength-bar" :class="{ s2: pwdLevel >= 2, s3: pwdLevel >= 3 }"></span>
                <span class="strength-bar" :class="{ s3: pwdLevel >= 3 }"></span>
                <span class="strength-text">{{ strengthText }}</span>
              </div>
              <div class="form-error">{{ errors.password }}</div>
            </div>

            <div class="form-group" :class="{ 'has-error': !!errors.confirm }">
              <label for="reg-password2">确认密码</label>
              <input type="password" id="reg-password2" v-model="form.confirm"
                     placeholder="再次输入密码" autocomplete="new-password">
              <div class="form-error">{{ errors.confirm }}</div>
            </div>

            <div class="form-group">
              <label class="form-checkbox">
                <input type="checkbox" v-model="form.agree">
                <span>我已阅读并同意<a href="#" @click.prevent>《用户协议》</a>与<a href="#" @click.prevent>《隐私政策》</a></span>
              </label>
            </div>

            <button type="submit" class="btn-primary btn-block btn-lg" :disabled="loading">
              {{ loading ? '注册中...' : '注册' }}
            </button>
          </form>

          <div class="auth-divider"><span>或</span></div>

          <div class="auth-footer-text">
            已有账户？
            <router-link to="/login" class="link-primary">返回登录</router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authApi } from '@/api/modules'
import AuthBrand from '@/components/AuthBrand.vue'

const router = useRouter()
const loading = ref(false)
const showPwd = ref(false)

const form = reactive({ account: '', nickname: '', password: '', confirm: '', agree: false })
const errors = reactive({ nickname: '', account: '', password: '', confirm: '' })

const pwdLevel = computed(() => {
  const val = form.password
  let level = 0
  if (val.length >= 8) level++
  if (/[a-zA-Z]/.test(val) && /\d/.test(val)) level++
  if (val.length >= 12 && /[^a-zA-Z0-9]/.test(val)) level++
  return level
})
const strengthText = computed(() => ['密码强度', '弱', '中', '强'][pwdLevel.value] || '密码强度')

function onPwdInput() { errors.password = '' }

async function onRegister() {
  errors.nickname = ''; errors.account = ''; errors.password = ''; errors.confirm = ''
  const nickname = form.nickname.trim()
  if (nickname.length < 2 || nickname.length > 16) { errors.nickname = '昵称需 2-16 个字符'; return }
  if (!form.account.trim()) { errors.account = '请输入手机号或邮箱'; return }
  const pwd = form.password
  if (pwd.length < 8 || pwd.length > 32 || !(/[a-zA-Z]/.test(pwd) && /\d/.test(pwd))) {
    errors.password = '密码须 8-32 位且同时包含字母与数字'
    return
  }
  if (pwd !== form.confirm) { errors.confirm = '两次输入的密码不一致'; return }
  if (!form.agree) { ElMessage.warning('请先阅读并同意用户协议与隐私政策'); return }

  loading.value = true
  try {
    await authApi.register({
      account: form.account.trim(), nickname,
      password: pwd, confirm_password: form.confirm,
    })
    ElMessage.success('注册成功，请登录')
    router.push('/login')
  } catch (e: any) {
    errors.account = e?.response?.data?.message || '注册失败，请稍后重试'
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
.form-group > label {
  font-size: 13px;
  font-weight: 600;
  color: var(--tyt-text);
  letter-spacing: 0.01em;
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
  margin-top: -2px;
}

.form-strength {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-top: 2px;
}
.strength-bar {
  width: 38px;
  height: 4px;
  border-radius: 2px;
  background: var(--tyt-border);
  transition: background 0.3s ease;
}
.strength-bar.s1 { background: #f87171; }
.strength-bar.s2 { background: #fbbf24; }
.strength-bar.s3 { background: #34d399; }
.strength-text {
  font-size: 12px;
  color: var(--tyt-text-tertiary);
  margin-left: 5px;
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

@media (max-width: 1024px) {
  .auth-page { grid-template-columns: 1fr; }
  .auth-right {
    min-height: 100vh;
    padding: 40px 24px;
  }
}
</style>
