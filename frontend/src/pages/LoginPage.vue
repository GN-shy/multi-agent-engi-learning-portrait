<template>
  <main class="login-page">
    <div class="login-shell">
      <section class="story" aria-labelledby="story-title">
        <header class="story-header">
          <div class="brand-lockup">
            <img src="/app-icon.png" alt="" width="46" height="46" />
            <div>
              <strong>工学智链</strong>
              <span>ENGINEERING INTELLIGENCE CHAIN</span>
            </div>
          </div>
          <span class="system-badge"><i></i> 多智能体协作在线</span>
        </header>

        <div class="agent-stage" aria-hidden="true">
          <svg viewBox="0 0 720 610" role="presentation">
            <defs>
              <pattern id="blueprint-grid" width="30" height="30" patternUnits="userSpaceOnUse">
                <g class="grid-shift">
                  <path d="M 30 0 L 0 0 0 30" fill="none" stroke="rgba(112,190,255,.085)" stroke-width="1" />
                </g>
              </pattern>
              <radialGradient id="core-halo" cx="50%" cy="50%" r="50%">
                <stop offset="0" stop-color="#00AEEF" stop-opacity=".28" />
                <stop offset="1" stop-color="#00AEEF" stop-opacity="0" />
              </radialGradient>
              <linearGradient id="flow-gradient" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0" stop-color="#00AEEF" />
                <stop offset=".55" stop-color="#7CDFFF" />
                <stop offset="1" stop-color="#FFD500" />
              </linearGradient>
              <path
                id="agent-loop-path"
                pathLength="100"
                d="M385.95 81.06 L532.05 165.94 Q558 181 558 211 L558 379 Q558 409 532.05 424.06 L385.95 508.94 Q360 524 334.05 508.94 L187.95 424.06 Q162 409 162 379 L162 211 Q162 181 187.95 165.94 L334.05 81.06 Q360 66 385.95 81.06 Z"
              />
              <filter id="meteor-blur" x="-160%" y="-160%" width="420%" height="420%">
                <feGaussianBlur stdDeviation="2.6" />
              </filter>
              <clipPath id="core-clip"><rect x="321" y="266" width="78" height="78" rx="20" /></clipPath>
            </defs>

            <rect x="0" y="0" width="720" height="610" fill="url(#blueprint-grid)" />
            <circle cx="360" cy="305" r="152" fill="url(#core-halo)" class="core-halo" />
            <circle cx="360" cy="305" r="112" fill="none" stroke="rgba(98,190,255,.12)" stroke-width="1" stroke-dasharray="4 9" />
            <use href="#agent-loop-path" class="flow-guide" />
            <use href="#agent-loop-path" class="flow-path" />

            <g class="spokes">
              <path d="M360 113 L360 260" /><path d="M517 205 L405 270" />
              <path d="M517 385 L405 320" /><path d="M360 477 L360 350" />
              <path d="M203 385 L315 320" /><path d="M203 205 L315 270" />
            </g>

            <g class="agent-node node-one" transform="translate(360 66)">
              <circle r="47" /><path d="M-17 -8 H17 M-12 1 H12 M-7 10 H7" />
              <text y="-20">01</text><text class="node-label" y="69">学情建模</text>
            </g>
            <g class="agent-node node-two" transform="translate(558 181)">
              <circle r="47" /><path d="M-16 11 L-4 -9 L8 4 L18 -13 M-16 15 H18" />
              <text y="-20">02</text><text class="node-label" y="69">领域检索</text>
            </g>
            <g class="agent-node node-three" transform="translate(558 409)">
              <circle r="47" /><path d="M-16 -10 H16 V12 H-16 Z M-9 -3 H9 M-9 4 H4" />
              <text y="-20">03</text><text class="node-label" y="69">严谨生成</text>
            </g>
            <g class="agent-node node-four" transform="translate(360 524)">
              <circle r="47" /><path d="M-16 10 C-5 -14 7 -14 16 10 M-8 10 C0 -2 8 -2 12 10" />
              <text y="-20">04</text><text class="node-label" y="69">创意生成</text>
            </g>
            <g class="agent-node node-five" transform="translate(162 409)">
              <circle r="47" /><path d="M-17 -4 L-5 9 L18 -14 M-15 16 H16" />
              <text y="-20">05</text><text class="node-label" y="69">仲裁审核</text>
            </g>
            <g class="agent-node node-six" transform="translate(162 181)">
              <circle r="47" /><path d="M-17 -10 H13 V8 H-5 L-14 16 V8 H-17 Z" />
              <text y="-20">06</text><text class="node-label" y="69">导学反馈</text>
            </g>

            <g class="core-module">
              <rect x="305" y="250" width="110" height="110" rx="30" />
              <rect x="316" y="261" width="88" height="88" rx="23" class="core-frame" />
              <image href="/app-icon.png" x="321" y="266" width="78" height="78" clip-path="url(#core-clip)" />
              <text x="360" y="384">可验证知识核心</text>
              <text class="core-status" x="360" y="406">EVIDENCE GROUNDED</text>
            </g>

            <g class="reg-marks" fill="none" stroke="rgba(126,186,233,.34)" stroke-width="1">
              <path d="M24 24 v15 M16.5 31.5 h15" />
              <path d="M696 24 v15 M688.5 31.5 h15" />
              <path d="M24 586 v15 M16.5 593.5 h15" />
              <path d="M696 586 v15 M688.5 593.5 h15" />
            </g>

            <g class="meteor-wake wake-a">
              <use href="#agent-loop-path" class="wake-haze" stroke-dasharray="16 84" stroke-dashoffset="16">
                <animate attributeName="stroke-dashoffset" from="16" to="-84" dur="9.6s" repeatCount="indefinite" />
              </use>
              <use href="#agent-loop-path" class="wake-body" stroke-dasharray="10 90" stroke-dashoffset="10">
                <animate attributeName="stroke-dashoffset" from="10" to="-90" dur="9.6s" repeatCount="indefinite" />
              </use>
              <use href="#agent-loop-path" class="wake-core" stroke-dasharray="5.5 94.5" stroke-dashoffset="5.5">
                <animate attributeName="stroke-dashoffset" from="5.5" to="-94.5" dur="9.6s" repeatCount="indefinite" />
              </use>
            </g>
            <g class="meteor-wake wake-b">
              <use href="#agent-loop-path" class="wake-haze" stroke-dasharray="16 84" stroke-dashoffset="16">
                <animate attributeName="stroke-dashoffset" from="16" to="-84" dur="9.6s" begin="-3.2s" repeatCount="indefinite" />
              </use>
              <use href="#agent-loop-path" class="wake-body" stroke-dasharray="10 90" stroke-dashoffset="10">
                <animate attributeName="stroke-dashoffset" from="10" to="-90" dur="9.6s" begin="-3.2s" repeatCount="indefinite" />
              </use>
              <use href="#agent-loop-path" class="wake-core" stroke-dasharray="5.5 94.5" stroke-dashoffset="5.5">
                <animate attributeName="stroke-dashoffset" from="5.5" to="-94.5" dur="9.6s" begin="-3.2s" repeatCount="indefinite" />
              </use>
            </g>
            <g class="meteor-wake wake-c">
              <use href="#agent-loop-path" class="wake-haze" stroke-dasharray="16 84" stroke-dashoffset="16">
                <animate attributeName="stroke-dashoffset" from="16" to="-84" dur="9.6s" begin="-6.4s" repeatCount="indefinite" />
              </use>
              <use href="#agent-loop-path" class="wake-body" stroke-dasharray="10 90" stroke-dashoffset="10">
                <animate attributeName="stroke-dashoffset" from="10" to="-90" dur="9.6s" begin="-6.4s" repeatCount="indefinite" />
              </use>
              <use href="#agent-loop-path" class="wake-core" stroke-dasharray="5.5 94.5" stroke-dashoffset="5.5">
                <animate attributeName="stroke-dashoffset" from="5.5" to="-94.5" dur="9.6s" begin="-6.4s" repeatCount="indefinite" />
              </use>
            </g>

            <g class="meteor meteor-a">
              <animateMotion dur="9.6s" repeatCount="indefinite" rotate="auto"><mpath href="#agent-loop-path" /></animateMotion>
              <path class="meteor-rock" d="M-7 -3 L-4 -8 L2 -9 L8 -5 L11 1 L7 7 L1 9 L-6 5 L-9 1 Z" />
              <path class="meteor-hot-edge" d="M2 -8 L8 -5 L11 1 L7 7" />
              <path class="meteor-crater" d="M-3 -3 C-1 -5 2 -4 2 -1 C1 1 -2 1 -3 -1 Z M1 4 C3 2 6 3 6 5" />
            </g>
            <g class="meteor meteor-b">
              <animateMotion dur="9.6s" begin="-3.2s" repeatCount="indefinite" rotate="auto"><mpath href="#agent-loop-path" /></animateMotion>
              <path class="meteor-rock" d="M-7 -3 L-4 -8 L2 -9 L8 -5 L11 1 L7 7 L1 9 L-6 5 L-9 1 Z" />
              <path class="meteor-hot-edge" d="M2 -8 L8 -5 L11 1 L7 7" />
              <path class="meteor-crater" d="M-3 -3 C-1 -5 2 -4 2 -1 C1 1 -2 1 -3 -1 Z M1 4 C3 2 6 3 6 5" />
            </g>
            <g class="meteor meteor-c">
              <animateMotion dur="9.6s" begin="-6.4s" repeatCount="indefinite" rotate="auto"><mpath href="#agent-loop-path" /></animateMotion>
              <path class="meteor-rock" d="M-7 -3 L-4 -8 L2 -9 L8 -5 L11 1 L7 7 L1 9 L-6 5 L-9 1 Z" />
              <path class="meteor-hot-edge" d="M2 -8 L8 -5 L11 1 L7 7" />
              <path class="meteor-crater" d="M-3 -3 C-1 -5 2 -4 2 -1 C1 1 -2 1 -3 -1 Z M1 4 C3 2 6 3 6 5" />
            </g>
          </svg>
          <div class="scan-sweep" aria-hidden="true"></div>
        </div>

        <footer class="story-footer">
          <div class="story-copy">
            <p class="kicker">从知识到能力，不走黑箱捷径</p>
            <h1 id="story-title">运用多智能体协作，<br />让每一步都有<span>证据链</span><span class="nowrap">支撑。</span></h1>
            <p class="lead">画像诊断、领域检索、双策略生成、仲裁审核与导学反馈持续闭环，把理论转化为可执行、可验证的工程能力。</p>
          </div>
          <div class="proofs" aria-label="平台能力概览">
            <div><strong>{{ proofCounts.tracks }}</strong><span>个计算机主方向</span></div>
            <div><strong>{{ proofCounts.pathways }}</strong><span>条细分学习路线</span></div>
            <div><strong>{{ proofCounts.agents }}</strong><span>个协作 Agent</span></div>
          </div>
        </footer>
      </section>

      <section class="auth-card" aria-labelledby="auth-heading">
        <div class="auth-inner">
          <div class="auth-brand">
            <img src="/app-icon.png" alt="" width="38" height="38" />
            <div><strong>工学智链</strong><span>个性化工程能力成长系统</span></div>
          </div>

          <div class="mode-switch" role="group" aria-label="选择登录或注册">
            <el-segmented v-model="mode" :options="[{label:'登录',value:'login'},{label:'注册',value:'register'}]" />
          </div>

          <div class="auth-title">
            <p class="auth-kicker">{{ mode === 'login' ? 'CONTINUE YOUR PATH' : 'CREATE YOUR PROFILE' }}</p>
            <h2 id="auth-heading">{{ mode === 'login' ? '欢迎回来' : '建立成长档案' }}</h2>
            <p>{{ mode === 'login' ? '登录后继续今天真正需要完成的任务。' : '注册后用选择题建立初始档案，无需撰写自我介绍。' }}</p>
          </div>

          <el-form
            ref="loginFormRef"
            :model="form"
            :rules="rules"
            label-position="top"
            novalidate
            scroll-to-error
            :aria-busy="user.loading"
            @submit.prevent="submit"
          >
            <el-form-item v-if="mode === 'register'" prop="username" label="用户名">
              <el-input v-model="form.username" maxlength="40" autocomplete="name" placeholder="页面将动态显示该名称" />
            </el-form-item>
            <el-form-item prop="account" :label="mode === 'login' ? '账号或邮箱' : '邮箱'">
              <el-input
                v-model="form.account"
                :autocomplete="mode === 'login' ? 'username' : 'email'"
                :inputmode="mode === 'register' ? 'email' : 'text'"
                placeholder="请输入你的邮箱"
              />
            </el-form-item>
            <el-form-item prop="password" label="密码">
              <el-input
                v-model="form.password"
                type="password"
                show-password
                :autocomplete="mode === 'register' ? 'new-password' : 'current-password'"
              />
            </el-form-item>
            <div v-if="mode === 'register'" class="password-strength">
              <el-progress :percentage="passwordStrength" :show-text="false" :status="passwordStrength >= 100 ? 'success' : undefined" />
              <span>至少 8 位，并包含大写、小写、数字、特殊字符中的三类</span>
            </div>
            <div class="form-status" aria-live="polite">
              <el-alert v-if="user.error" :title="user.error" type="error" :closable="false" show-icon />
            </div>
            <el-button class="submit" type="primary" native-type="submit" :loading="user.loading">
              {{ mode === 'login' ? '进入学习空间' : '注册并开始诊断' }}
            </el-button>
          </el-form>

          <div class="login-tools">
            <button type="button" @click="clearForm">清空输入</button>
            <span v-if="demoEnabled" aria-hidden="true"></span>
            <button v-if="demoEnabled" type="button" @click="useDemo">使用演示账号</button>
          </div>
          <p class="privacy"><i aria-hidden="true">✓</i> 刷新令牌保存在 HttpOnly Cookie；系统只展示可审计执行摘要，不展示模型隐藏思维链。</p>
        </div>
      </section>
    </div>
  </main>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
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
const demoEnabled = import.meta.env.DEV
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
  loginFormRef.value?.clearValidate()
}
async function useDemo() {
  mode.value = 'login'
  await nextTick()
  form.account = 'demo@gongxue.local'
  form.password = 'demo12345'
  user.error = ''
  loginFormRef.value?.clearValidate()
}
async function submit() {
  if (!loginFormRef.value || user.loading) return
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
  if (ok) router.replace(mode.value === 'register' ? '/onboarding' : String(route.query.redirect || '/'))
}
</script>

<style scoped>
.login-page {
  min-height: 100svh;
  display: grid;
  place-items: center;
  padding: clamp(16px, 3.2vw, 48px);
  overflow: auto;
  background:
    radial-gradient(circle at 12% 18%, rgba(0, 174, 239, .14), transparent 26%),
    radial-gradient(circle at 89% 82%, rgba(255, 213, 0, .08), transparent 22%),
    var(--canvas-deep);
  isolation: isolate;
}
.login-page::before {
  content: '';
  position: fixed;
  inset: 0;
  z-index: -1;
  opacity: .2;
  background-image: linear-gradient(rgba(126, 183, 238, .08) 1px, transparent 1px), linear-gradient(90deg, rgba(126, 183, 238, .08) 1px, transparent 1px);
  background-size: 52px 52px;
  mask-image: linear-gradient(to bottom, black, transparent 92%);
  animation: grid-drift 26s linear infinite;
}
.login-shell {
  width: min(100%, var(--auth-shell-max));
  min-height: min(840px, calc(100svh - clamp(32px, 6.4vw, 96px)));
  display: grid;
  grid-template-columns: minmax(0, 1.16fr) minmax(420px, .84fr);
  overflow: hidden;
  border: 1px solid rgba(154, 202, 243, .18);
  border-radius: var(--radius-auth-shell);
  background: #071831;
  box-shadow: 0 34px 100px rgba(0, 8, 24, .48), 0 0 0 1px rgba(255, 255, 255, .025) inset;
}
.story {
  position: relative;
  min-width: 0;
  padding: 30px clamp(28px, 3vw, 50px) 34px;
  display: grid;
  grid-template-rows: auto minmax(330px, 1fr) auto;
  color: #F5FAFF;
  background:
    radial-gradient(120% 95% at 50% 42%, transparent 60%, rgba(2, 8, 22, .55) 100%),
    linear-gradient(145deg, rgba(11, 44, 99, .62), rgba(6, 19, 40, .3)),
    radial-gradient(circle at 48% 40%, rgba(0, 174, 239, .13), transparent 44%);
  border-right: 1px solid rgba(153, 201, 244, .14);
}
.story::after {
  content: '';
  position: absolute;
  inset: 0;
  z-index: 3;
  pointer-events: none;
  opacity: .055;
  mix-blend-mode: soft-light;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.82' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
}
.story-header,
.brand-lockup,
.auth-brand {
  display: flex;
  align-items: center;
}
.story-header { justify-content: space-between; gap: 24px; }
.brand-lockup,
.auth-brand { gap: 12px; }
.brand-lockup img,
.auth-brand img {
  object-fit: cover;
  border-radius: 12px;
  box-shadow: 0 9px 24px rgba(0, 8, 24, .28);
}
.brand-lockup strong,
.brand-lockup span,
.auth-brand strong,
.auth-brand span { display: block; }
.brand-lockup strong { font-size: 18px; letter-spacing: .08em; }
.brand-lockup span {
  margin-top: 4px;
  color: #87A9CC;
  font: 10px/1 var(--font-utility);
  letter-spacing: .13em;
}
.system-badge {
  padding: 8px 11px;
  border: 1px solid rgba(85, 190, 242, .28);
  border-radius: 999px;
  color: #B8DBF3;
  background: rgba(6, 22, 47, .58);
  font-size: 11px;
  white-space: nowrap;
}
.system-badge i {
  width: 7px;
  height: 7px;
  margin-right: 7px;
  display: inline-block;
  border-radius: 50%;
  background: var(--brand-cyan);
  box-shadow: 0 0 0 5px rgba(0, 174, 239, .11);
  animation: status-pulse 2.2s ease-in-out infinite;
}
.agent-stage {
  position: relative;
  min-height: 0;
  display: grid;
  place-items: center;
}
.agent-stage svg { width: min(100%, 650px); height: 100%; max-height: 520px; overflow: visible; }
.scan-sweep {
  position: absolute;
  left: 7%;
  right: 7%;
  top: 6%;
  height: 1px;
  pointer-events: none;
  opacity: 0;
  background: linear-gradient(90deg, transparent, rgba(0, 174, 239, .55), rgba(124, 223, 255, .9), rgba(0, 174, 239, .55), transparent);
  box-shadow: 0 0 16px 1px rgba(0, 174, 239, .42);
  animation: scan-sweep 6.5s cubic-bezier(.4, 0, .2, 1) infinite;
}
@keyframes scan-sweep {
  0% { top: 6%; opacity: 0; }
  10% { opacity: .72; }
  50% { opacity: .55; }
  90% { opacity: 0; }
  100% { top: 94%; opacity: 0; }
}
.flow-path {
  fill: none;
  stroke: url(#flow-gradient);
  stroke-width: 2.3;
  stroke-dasharray: .7 .9;
  opacity: .75;
  animation: flow-dash 13s linear infinite;
}
.flow-guide { fill: none; stroke: rgba(123, 194, 248, .16); stroke-width: 12; }
.spokes path { fill: none; stroke: rgba(73, 168, 230, .2); stroke-width: 1.2; stroke-dasharray: 3 7; }
.agent-node { color: #8FDFFF; animation: node-breathe 4.8s ease-in-out infinite; transform-box: fill-box; transform-origin: center; }
.agent-node circle { fill: rgba(8, 35, 74, .94); stroke: rgba(92, 198, 251, .52); stroke-width: 1.5; }
.agent-node > path { fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.agent-node text { fill: #7FA5C9; font: 700 10px var(--font-utility); text-anchor: middle; letter-spacing: .12em; }
.agent-node .node-label { fill: #DCEEFF; font: 600 15px var(--font-body); letter-spacing: .06em; }
.node-two { animation-delay: -.8s; }.node-three { animation-delay: -1.6s; }.node-four { animation-delay: -2.4s; }
.node-five { animation-delay: -3.2s; }.node-six { animation-delay: -4s; }
.core-module > rect:first-child { fill: rgba(0, 174, 239, .08); stroke: rgba(0, 174, 239, .23); }
.core-module .core-frame { fill: #081E41; stroke: rgba(255, 213, 0, .42); stroke-width: 1; }
.core-module text { fill: #F6FBFF; font: 700 15px var(--font-body); text-anchor: middle; letter-spacing: .06em; }
.core-module .core-status { fill: #71BFE9; font: 9px var(--font-utility); letter-spacing: .18em; }
.grid-shift { animation: grid-shift 16s linear infinite; }
.reg-marks { opacity: .8; }
.meteor,
.meteor-wake {
  --meteor-color: #FFD500;
  --meteor-rock: #6B5414;
  --meteor-rock-dark: #2D2C27;
}
.meteor-b,
.wake-b {
  --meteor-color: #00AEEF;
  --meteor-rock: #176484;
  --meteor-rock-dark: #17364A;
}
.meteor-c,
.wake-c {
  --meteor-color: #DCEEFF;
  --meteor-rock: #7E98AC;
  --meteor-rock-dark: #334A5D;
}
.meteor-wake use {
  fill: none;
  stroke: var(--meteor-color);
  stroke-linecap: round;
  pointer-events: none;
}
.wake-haze {
  stroke-width: 8;
  opacity: .13;
  filter: url(#meteor-blur);
}
.wake-body {
  stroke-width: 4.2;
  opacity: .28;
  filter: url(#meteor-blur);
}
.wake-core { stroke-width: 1.8; opacity: .86; }
.meteor-rock {
  fill: var(--meteor-rock);
  stroke: var(--meteor-color);
  stroke-width: 1.25;
  stroke-linejoin: round;
  filter: drop-shadow(0 0 4px var(--meteor-color));
}
.meteor-hot-edge {
  fill: none;
  stroke: #FFFFFF;
  stroke-width: 2.1;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.meteor-crater {
  fill: var(--meteor-rock-dark);
  stroke: rgba(255, 255, 255, .28);
  stroke-width: .65;
  stroke-linecap: round;
}
.story-footer { display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: end; gap: 28px; }
.story-copy { max-width: 610px; }
.kicker {
  margin: 0 0 10px;
  color: #78CEF4;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: .13em;
}
.story h1 {
  margin: 0;
  color: #F9FCFF;
  font: 650 clamp(30px, 3vw, 48px)/1.18 var(--font-display);
  letter-spacing: -.025em;
}
.story h1 span { color: var(--brand-yellow); }
.story h1 .nowrap { white-space: nowrap; }
.lead { max-width: 610px; margin: 13px 0 0; color: #A9C1D8; font-size: 14px; line-height: 1.8; }
.proofs {
  display: grid;
  grid-template-columns: repeat(3, auto);
  gap: clamp(13px, 1.5vw, 24px);
  padding-left: 24px;
  border-left: 1px solid rgba(126, 186, 233, .19);
}
.proofs div { min-width: 72px; }
.proofs strong,
.proofs span { display: block; }
.proofs strong { color: #F8FCFF; font: 600 25px/1 var(--font-utility); }
.proofs span { margin-top: 8px; color: #7897B6; font-size: 10px; white-space: nowrap; }
.auth-card {
  min-width: 0;
  display: grid;
  place-items: center;
  padding: clamp(30px, 4vw, 64px);
  color: var(--text);
  background:
    radial-gradient(circle at 100% 0, rgba(0, 174, 239, .07), transparent 27%),
    var(--surface);
}
.auth-inner { width: min(100%, 440px); }
.auth-brand { margin-bottom: clamp(30px, 5vh, 54px); }
.auth-brand img { box-shadow: 0 8px 20px rgba(18, 54, 103, .16); }
.auth-brand strong { font-size: 15px; letter-spacing: .06em; }
.auth-brand span { margin-top: 3px; color: var(--muted); font-size: 10px; }
.mode-switch { width: 100%; }
.mode-switch :deep(.el-segmented) { width: 100%; padding: 4px; background: #EEF3F9; }
.mode-switch :deep(.el-segmented__item) { min-height: 38px; border-radius: 8px; color: #5D6B82; font-weight: 650; }
.mode-switch :deep(.el-segmented__item-selected) { background: #FFFFFF; box-shadow: 0 2px 10px rgba(24, 52, 88, .09); }
.auth-title { margin: 30px 0 24px; }
.auth-kicker { margin: 0 0 9px; color: var(--primary); font: 700 10px/1 var(--font-utility); letter-spacing: .15em; }
.auth-title h2 { margin: 0 0 9px; font: 650 30px/1.22 var(--font-display); letter-spacing: -.02em; }
.auth-title > p:last-child { margin: 0; color: var(--muted); font-size: 13px; line-height: 1.65; }
.auth-card :deep(.el-form-item) { margin-bottom: 19px; }
.auth-card :deep(.el-form-item__label) { height: auto; margin-bottom: 8px; color: #354258; font-size: 12px; font-weight: 650; line-height: 1.3; }
.auth-card :deep(.el-input__wrapper) {
  min-height: 46px;
  border: 1px solid #D9E2EE;
  border-radius: var(--radius-control);
  background: #FBFCFE;
  box-shadow: none;
  transition: border-color .18s ease, box-shadow .18s ease, background-color .18s ease;
}
.auth-card :deep(.el-input__wrapper:hover) { border-color: #9FB6D0; background: #FFFFFF; }
.auth-card :deep(.el-input__wrapper.is-focus) { border-color: var(--focus); background: #FFFFFF; box-shadow: 0 0 0 3px rgba(76, 130, 255, .14); }
.auth-card :deep(.el-input__inner) { color: var(--text); font-size: 14px; }
.auth-card :deep(.el-form-item__error) { position: static; padding-top: 6px; line-height: 1.45; }
.password-strength { margin: -6px 0 17px; }
.password-strength span { display: block; margin-top: 7px; color: var(--muted); font-size: 11px; line-height: 1.5; }
.password-strength :deep(.el-progress-bar__outer) { background: #E9EEF5; }
.form-status { min-height: 0; }
.form-status:has(.el-alert) { margin-bottom: 16px; }
.form-status :deep(.el-alert) { align-items: flex-start; border: 1px solid rgba(226, 79, 100, .2); border-radius: 10px; }
.submit { width: 100%; height: 46px; margin-top: 4px; border-radius: var(--radius-control); font-weight: 700; letter-spacing: .03em; }
.submit:hover { transform: translateY(-1px); box-shadow: 0 10px 24px rgba(37, 99, 235, .2); }
.submit:active { transform: translateY(0); }
.login-tools { min-height: 28px; margin: 18px 0 14px; display: flex; align-items: center; justify-content: center; gap: 14px; }
.login-tools button { min-height: 28px; padding: 2px 5px; border: 0; border-radius: 6px; color: #3C65A8; background: transparent; cursor: pointer; font-size: 12px; }
.login-tools button:hover { color: var(--primary); background: #EEF4FF; }
.login-tools button:active { color: var(--primary-dark); }
.login-tools span { width: 1px; height: 12px; background: #D8E0EA; }
.privacy { margin: 0; padding-top: 16px; border-top: 1px solid #E9EEF4; color: var(--muted); font-size: 11px; line-height: 1.65; }
.privacy i { margin-right: 5px; color: var(--success); font-style: normal; font-weight: 800; }

@keyframes flow-dash { to { stroke-dashoffset: -19.2; } }
@keyframes node-breathe { 0%, 100% { opacity: .8; } 50% { opacity: 1; } }
@keyframes status-pulse { 0%, 100% { opacity: .62; } 50% { opacity: 1; box-shadow: 0 0 0 7px rgba(0, 174, 239, .06); } }
@keyframes grid-shift { to { transform: translate(30px, 30px); } }
@keyframes grid-drift { to { background-position: 52px 52px; } }

@media (max-width: 1180px) {
  .login-shell { grid-template-columns: minmax(0, 1fr) minmax(390px, .8fr); }
  .story-footer { grid-template-columns: 1fr; }
  .proofs { padding: 0; border-left: 0; }
  .agent-stage svg { max-height: 470px; }
}
@media (max-width: 900px) {
  .login-page { place-items: start center; overflow: visible; }
  .login-shell { min-height: 0; grid-template-columns: 1fr; }
  .story { min-height: 560px; padding: 24px; grid-template-rows: auto minmax(300px, 1fr) auto; border-right: 0; border-bottom: 1px solid rgba(153, 201, 244, .14); }
  .story-footer { grid-template-columns: minmax(0, 1fr) auto; }
  .agent-stage svg { width: min(100%, 590px); max-height: 390px; }
  .auth-card { padding: 44px 28px 50px; }
  .auth-brand { margin-bottom: 30px; }
}
@media (max-width: 640px) {
  .login-page { padding: 10px; }
  .login-shell { border-radius: 20px; }
  .story { min-height: 410px; grid-template-rows: auto 245px auto; }
  .story-header { gap: 12px; }
  .brand-lockup img { width: 39px; height: 39px; border-radius: 10px; }
  .brand-lockup span, .system-badge { display: none; }
  .agent-stage { margin: -12px 0 -20px; overflow: hidden; }
  .agent-stage svg { width: 430px; max-width: none; height: 350px; }
  .agent-node .node-label { display: none; }
  .story-footer { grid-template-columns: 1fr; gap: 18px; }
  .story h1 { font-size: 30px; }
  .lead { display: none; }
  .proofs { grid-template-columns: repeat(3, 1fr); gap: 8px; }
  .proofs div { min-width: 0; }
  .proofs strong { font-size: 20px; }
  .proofs span { margin-top: 5px; font-size: 9px; white-space: normal; }
  .auth-card { padding: 34px 20px 40px; }
  .auth-title { margin-top: 25px; }
  .auth-title h2 { font-size: 27px; }
}
@media (prefers-reduced-motion: reduce) {
  .flow-path,
  .agent-node,
  .system-badge i,
  .grid-shift,
  .login-page::before,
  .scan-sweep { animation: none; }
  .meteor,
  .meteor-wake { display: none; }
  .scan-sweep { opacity: 0; }
  .submit,
  .auth-card :deep(.el-input__wrapper) { transition-duration: .01ms; }
}
</style>
