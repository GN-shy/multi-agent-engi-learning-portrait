<template>
  <div class="login-page">
    <section class="story">
      <div class="logo">GX</div>
      <p class="kicker">工学智链 · 计算机成长导航</p>
      <h1>不是再给你一份课程清单，<br />而是帮你做出<span>路线决策</span>。</h1>
      <p class="lead">画像诊断、方向比较、技能图谱、可信生成、项目实操、测试反馈和动态重规划形成一个闭环。</p>
      <div class="proofs">
        <div><strong>15</strong><span>条正式计算机路线</span></div>
        <div><strong>6</strong><span>个协作 Agent</span></div>
        <div><strong>4</strong><span>类个性化资源</span></div>
      </div>
    </section>

    <section class="auth-card">
      <el-segmented v-model="mode" :options="[{label:'登录',value:'login'},{label:'注册',value:'register'}]" />
      <div class="auth-title">
        <h2>{{ mode === 'login' ? '欢迎回来' : '建立成长档案' }}</h2>
        <p>{{ mode === 'login' ? '继续你的计算机能力成长路径' : '注册后先完成画像与路线比较' }}</p>
      </div>
      <el-form label-position="top" @submit.prevent="submit">
        <el-form-item v-if="mode === 'register'" label="用户名">
          <el-input v-model="form.username" maxlength="40" placeholder="页面将动态显示该名称" />
        </el-form-item>
        <el-form-item :label="mode === 'login' ? '账号或邮箱' : '邮箱'">
          <el-input v-model="form.account" autocomplete="username" placeholder="demo@gongxue.local" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" show-password autocomplete="current-password" />
        </el-form-item>
        <el-alert v-if="user.error" :title="user.error" type="error" :closable="false" show-icon />
        <el-button class="submit" type="primary" native-type="submit" :loading="user.loading">
          {{ mode === 'login' ? '进入学习空间' : '注册并开始诊断' }}
        </el-button>
      </el-form>
      <button class="demo" @click="useDemo">使用演示账号：demo@gongxue.local / demo12345</button>
      <p class="privacy">刷新令牌保存在 HttpOnly Cookie；系统只展示可审计执行摘要，不展示模型隐藏思维链。</p>
    </section>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const user = useUserStore()
const router = useRouter()
const route = useRoute()
const mode = ref<'login' | 'register'>('login')
const form = reactive({ username: '', account: '', password: '' })

function useDemo() {
  mode.value = 'login'
  form.account = 'demo@gongxue.local'
  form.password = 'demo12345'
}
async function submit() {
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
.auth-title { margin:28px 0 20px }.auth-title h2 { margin:0 0 8px;font-size:26px }.auth-title p,.privacy { color:#7b8799;font-size:13px;line-height:1.6 }.submit { width:100%;height:44px;margin-top:10px }.demo { border:0;background:none;color:#3168ee;cursor:pointer;width:100%;margin:18px 0 8px }
@media(max-width:900px){.login-page{grid-template-columns:1fr;padding:24px}.story{display:none}}
</style>
