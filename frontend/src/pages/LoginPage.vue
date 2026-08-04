<template>
  <div class="login-page">
    <section class="story">
      <div class="logo">GX</div>
      <p class="kicker">工学智链 · 计算机成长导航</p>
      <h1>不是再给你一份课程清单，<br />而是帮你做出<span>路线决策</span>。</h1>
      <p class="lead">画像诊断、方向比较、技能图谱、可信生成、项目实操、测试反馈和动态重规划形成一个闭环。</p>
      <div class="proofs">
        <div><strong>{{ proofCounts.tracks }}</strong><span>个计算机主方向</span></div>
        <div><strong>{{ proofCounts.pathways }}</strong><span>条细分学习路线</span></div>
        <div><strong>{{ proofCounts.agents }}</strong><span>个协作 Agent</span></div>
      </div>
    </section>

    <section class="auth-card">
      <el-segmented v-model="mode" :options="[{label:'登录',value:'login'},{label:'注册',value:'register'}]" />
      <div class="auth-title">
        <h2>{{ mode === 'login' ? '欢迎回来' : '建立成长档案' }}</h2>
        <p>{{ mode === 'login' ? '继续你的计算机能力成长路径' : '注册后先完成画像与路线比较' }}</p>
      </div>
      <el-form ref="loginFormRef" :model="form" :rules="rules" label-position="top" @submit.prevent="submit">
        <el-form-item v-if="mode === 'register'" prop="username" label="用户名">
          <el-input v-model="form.username" maxlength="40" placeholder="页面将动态显示该名称" />
        </el-form-item>
        <el-form-item prop="account" :label="mode === 'login' ? '账号或邮箱' : '邮箱'">
          <el-input v-model="form.account" autocomplete="off" placeholder="请输入你的邮箱" />
        </el-form-item>
        <el-form-item prop="password" label="密码">
          <el-input v-model="form.password" type="password" show-password :autocomplete="mode === 'register' ? 'new-password' : 'off'" />
        </el-form-item>
        <div v-if="mode === 'register'" class="password-strength">
          <el-progress :percentage="passwordStrength" :show-text="false" :status="passwordStrength >= 100 ? 'success' : undefined" />
          <span>至少 8 位，并包含大写、小写、数字、特殊字符中的三类</span>
        </div>
        <el-alert v-if="user.error" :title="user.error" type="error" :closable="false" show-icon />
        <el-button class="submit" type="primary" native-type="submit" :loading="user.loading">
          {{ mode === 'login' ? '进入学习空间' : '注册并开始诊断' }}
        </el-button>
      </el-form>
      <div class="login-tools"><button @click="clearForm">清空输入</button><button @click="useDemo">使用演示账号</button></div>
      <p class="privacy">刷新令牌保存在 HttpOnly Cookie；系统只展示可审计执行摘要，不展示模型隐藏思维链。</p>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'
import { api } from '@/api'
import { useUserStore } from '@/stores/user'

const user = useUserStore()
const router = useRouter()
const route = useRoute()
const loginFormRef = ref<FormInstance>()
const mode = ref<'login' | 'register'>('login')
const form = reactive({ username: '', account: '', password: '' })
const proofCounts = reactive({ tracks: 16, pathways: 29, agents: 6 })
const rules = computed<FormRules>(() => ({
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 40, message: '用户名长度为 2 到 40 个字符', trigger: 'blur' },
  ],
  account: [
    { required: true, message: mode.value === 'login' ? '请输入账号或邮箱' : '请输入邮箱', trigger: 'blur' },
    ...(mode.value === 'register' ? [{ type: 'email' as const, message: '请输入有效的邮箱地址', trigger: 'blur' }] : []),
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, message: '密码至少需要 8 位', trigger: 'blur' },
  ],
}))
const passwordStrength = computed(() => {
  const value = form.password
  const categories = [/[a-z]/.test(value), /[A-Z]/.test(value), /\d/.test(value), /[^A-Za-z0-9]/.test(value)].filter(Boolean).length
  return Math.min(100, (value.length >= 8 ? 25 : Math.round(value.length / 8 * 25)) + categories * 25)
})

onMounted(async () => {
  if (route.query.reset === '1') {
    await user.logout()
    mode.value = 'register'
    clearForm()
    await router.replace('/login')
  }
  try {
    const { data: healthData } = await api.get('/health')
    const catalog = healthData.data
    proofCounts.tracks = catalog.track_count || 16
  } catch { /* 保持默认数字 */ }
})
watch(mode, () => {
  clearForm()
})
function clearForm() {
  form.username = ''
  form.account = ''
  form.password = ''
  user.error = ''
}
function useDemo() {
  mode.value = 'login'
  form.account = 'demo@gongxue.local'
  form.password = 'demo12345'
}
async function submit() {
  if (!loginFormRef.value) return
  try {
    await loginFormRef.value.validate()
  } catch {
    return
  }
  if (mode.value === 'register' && (!form.username.trim() || passwordStrength.value < 100)) {
    user.error = '请填写用户名，并使用至少 8 位且包含三类字符的密码'
    return
  }
  const ok = mode.value === 'login'
    ? await user.login(form.account, form.password)
    : await user.register({ username: form.username, email: form.account, password: form.password })
  if (ok) router.replace(String(route.query.redirect || '/'))
}
</script>

<style scoped>
.login-page { min-height:100vh; display:grid; grid-template-columns:1.2fr .8fr; padding:52px; gap:50px; align-items:center; background:radial-gradient(circle at 18% 20%,#dce9ff,transparent 34%),#f7f9fd; }
.story { max-width:720px; padding:30px; }.logo { width:58px;height:58px;border-radius:18px;display:grid;place-items:center;color:white;font-weight:800;background:linear-gradient(145deg,#2768ff,#6c4cf4);box-shadow:0 16px 34px rgba(50,94,230,.3); }
.kicker { margin:22px 0 14px;color:#3566dc;font-weight:700;letter-spacing:.08em; }.story h1 { font-size:48px;line-height:1.22;margin:0;color:#152039; }.story h1 span { color:#3269ee; }.lead { font-size:17px;line-height:1.85;color:#66738a;max-width:650px; }
.proofs { display:flex;gap:34px;margin-top:38px }.proofs div { display:flex;flex-direction:column }.proofs strong { font-size:30px;color:#285fe2 }.proofs span { color:#778399;font-size:13px }
.auth-card { background:rgba(255,255,255,.94);border:1px solid #e3eaf5;border-radius:26px;padding:34px;box-shadow:0 28px 80px rgba(32,63,112,.14);max-width:480px;width:100%;justify-self:center; }
.auth-title { margin:28px 0 20px }.auth-title h2 { margin:0 0 8px;font-size:26px }.auth-title p,.privacy { color:#7b8799;font-size:13px;line-height:1.6 }.submit { width:100%;height:44px;margin-top:10px }.login-tools{display:flex;justify-content:center;gap:18px;margin:18px 0 8px}.login-tools button{border:0;background:none;color:#3168ee;cursor:pointer}
.password-strength{margin:-8px 0 14px}.password-strength span{display:block;color:#7b8799;font-size:11px;margin-top:6px;line-height:1.5}
@media(max-width:900px){.login-page{grid-template-columns:1fr;padding:24px}.story{display:none}}
</style>
