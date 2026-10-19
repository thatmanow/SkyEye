<template>
  <div class="page narrow">
    <h1 class="page-title">个人中心</h1>
    <p class="page-sub">账号信息 · 每日配额 · 密码修改</p>

    <div class="grid">
      <div class="tyt-card">
        <h3>账号信息</h3>
        <div class="profile-head" v-if="auth.user">
          <div class="profile-avatar-wrap">
            <div class="profile-avatar" :class="{ 'has-img': !!auth.user.avatar }"
                 :style="auth.user.avatar ? { backgroundImage: `url(${auth.user.avatar})` } : undefined">
              <span v-if="!auth.user.avatar">{{ avatarChar }}</span>
            </div>
            <button class="avatar-edit-btn" title="修改头像" @click="avatarFileInput?.click()" :disabled="uploadingAvatar">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
                <circle cx="12" cy="13" r="4"></circle>
              </svg>
            </button>
            <input ref="avatarFileInput" type="file" accept="image/jpeg,image/png,image/webp,image/gif"
                   class="sr-only-input" @change="onAvatarFile" />
          </div>
          <div class="profile-head-info">
            <div class="profile-nickname">{{ auth.user.nickname }}</div>
            <p class="text-dim avatar-tip">支持 jpg/png/webp/gif，大小不超过 2MB</p>
            <el-button size="small" :loading="uploadingAvatar" @click="avatarFileInput?.click()">更换头像</el-button>
          </div>
        </div>
        <div class="desc-grid" v-if="auth.user">
          <div class="desc-item"><span class="k">昵称</span><span class="v">{{ auth.user.nickname }}</span></div>
          <div class="desc-item"><span class="k">账号</span><span class="v">{{ auth.user.account }}</span></div>
          <div class="desc-item"><span class="k">角色</span>
            <span class="v">
              <el-tag size="small" effect="dark" :type="auth.role === 'premium' ? 'success' : auth.role === 'user' ? 'info' : 'warning'">
                {{ roleName }}
              </el-tag>
            </span>
          </div>
          <div class="desc-item"><span class="k">注册时间</span><span class="v">{{ auth.user.created_at }}</span></div>
        </div>
      </div>

      <div class="tyt-card">
        <h3>每日配额</h3>
        <div class="quota-list">
          <QuotaBar v-for="(label, key) in quotaLabels" :key="key" :label="label"
                    :used="auth.quotas[key]?.used" :limit="auth.quotas[key]?.limit" />
        </div>
        <p class="text-dim quota-tip">配额每日 0 点重置；高级会员享受更高额度，企业管理员可查看团队数据。</p>
      </div>
    </div>

    <div class="tyt-card" style="margin-top: 16px">
      <h3>修改密码</h3>
      <el-form label-position="top" style="max-width: 420px">
        <el-form-item label="当前密码">
          <el-input v-model="pwdForm.old_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码（8-32 位）">
          <el-input v-model="pwdForm.new_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认新密码">
          <el-input v-model="pwdConfirm" type="password" show-password />
        </el-form-item>
        <el-button type="primary" :loading="changing" @click="changePwd"
                   style="background:linear-gradient(135deg,#6366f1,#8b5cf6);border:none">修改密码</el-button>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { authApi } from '@/api/modules'
import { useAuthStore } from '@/stores/auth'
import QuotaBar from '@/components/QuotaBar.vue'

const auth = useAuthStore()
const changing = ref(false)
const pwdForm = reactive({ old_password: '', new_password: '' })
const pwdConfirm = ref('')

const avatarChar = computed(() => (auth.user?.nickname || '用')[0])
const avatarFileInput = ref<HTMLInputElement | null>(null)
const uploadingAvatar = ref(false)

async function onAvatarFile(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''  // 允许重复选择同一文件
  if (!file) return
  if (file.size > 2 * 1024 * 1024) return ElMessage.warning('图片大小不能超过 2MB')
  uploadingAvatar.value = true
  try {
    const data = await authApi.updateAvatar(file)
    auth.user = { ...auth.user, avatar: data.avatar }
    ElMessage.success('头像更新成功')
  } catch { /* 错误提示由拦截器统一处理 */ } finally {
    uploadingAvatar.value = false
  }
}

const roleNames: Record<string, string> = {
  user: '普通用户', premium: '高级会员', enterprise_admin: '企业管理员', platform_admin: '平台管理员',
}
const roleName = computed(() => roleNames[auth.role] || auth.role)

const quotaLabels: Record<string, string> = {
  life_query: '生活类查询', biz_basic: '企业基础查询', biz_risk: '风险查询',
  biz_graph: '图谱查询', report: '报告生成', ai_chat: 'AI 问答', post: '发帖',
}

async function changePwd() {
  if (!pwdForm.old_password || !pwdForm.new_password) return ElMessage.warning('请填写完整')
  if (pwdForm.new_password.length < 8 || pwdForm.new_password.length > 32) return ElMessage.warning('新密码 8-32 位')
  if (pwdForm.new_password !== pwdConfirm.value) return ElMessage.warning('两次新密码不一致')
  changing.value = true
  try {
    await authApi.changePassword(pwdForm)
    ElMessage.success('密码修改成功，请重新登录')
    await auth.logout()
    location.href = '/login'
  } finally {
    changing.value = false
  }
}
</script>

<style scoped>
.narrow { max-width: 900px; }
.grid { display: grid; grid-template-columns: 1fr 1.2fr; gap: 16px; }
h3 { margin: 0 0 14px; font-size: 15px; }
.quota-list { display: flex; flex-direction: column; gap: 12px; }
.quota-tip { font-size: 12px; margin: 14px 0 0; line-height: 1.8; }

.profile-head { display: flex; align-items: center; gap: 18px; padding: 4px 4px 16px; margin-bottom: 14px; border-bottom: 1px solid var(--tyt-border-light); }
.profile-avatar-wrap { position: relative; flex-shrink: 0; }
.profile-avatar {
  width: 72px; height: 72px; border-radius: 50%;
  background: var(--tyt-gradient-brand); color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-weight: 600; font-size: 26px;
}
.profile-avatar.has-img { background-size: cover; background-position: center; background-repeat: no-repeat; }
.avatar-edit-btn {
  position: absolute; right: -4px; bottom: -4px;
  width: 26px; height: 26px; border-radius: 50%; border: 2px solid #fff;
  background: var(--tyt-primary); color: #fff; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: transform 0.2s ease;
}
.avatar-edit-btn:hover { transform: scale(1.12); }
.avatar-edit-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.avatar-edit-btn svg { width: 13px; height: 13px; }
.profile-head-info { display: flex; flex-direction: column; gap: 8px; align-items: flex-start; }
.profile-nickname { font-size: 17px; font-weight: 700; color: var(--tyt-text); }
.avatar-tip { font-size: 12px; margin: 0; }
/* 视觉隐藏但保留在可访问性树中（不要用 hidden 属性，浏览器自动化与读屏均无法触达） */
.sr-only-input {
  position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px;
  overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0;
}
</style>
