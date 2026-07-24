<template>
  <div class="shell">
    <aside class="sidebar" :class="{ collapsed }">
      <div class="brand" @click="router.push('/')">
        <div class="brand-mark">GX</div>
        <div v-if="!collapsed">
          <strong>工学智链</strong>
          <span>计算机成长导航</span>
        </div>
      </div>
      <nav>
        <RouterLink
          v-for="item in visibleMenu"
          :key="item.path"
          :to="item.path"
          :title="item.label"
          class="nav-item"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <span v-if="!collapsed">{{ item.label }}</span>
        </RouterLink>
      </nav>
      <button class="collapse" @click="collapsed = !collapsed">
        <el-icon><Fold v-if="!collapsed" /><Expand v-else /></el-icon>
        <span v-if="!collapsed">收起导航</span>
      </button>
    </aside>

    <section class="workspace">
      <header class="topbar">
        <div>
          <p class="eyebrow">{{ route.meta.eyebrow || '计算机能力成长闭环' }}</p>
          <h1>{{ route.meta.title || '工学智链' }}</h1>
        </div>
        <div class="top-actions">
          <el-input
            v-model="search"
            placeholder="搜索路线、技能、资源…"
            :prefix-icon="Search"
            clearable
            @keyup.enter="goSearch"
          />
          <el-button circle @click="router.push('/messages')"><el-icon><Bell /></el-icon></el-button>
          <el-dropdown>
            <button class="user-chip">
              <el-avatar :size="34" :src="user.current?.avatar">{{ user.displayName[0] }}</el-avatar>
              <span>{{ user.displayName }}</span>
              <el-icon><ArrowDown /></el-icon>
            </button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="router.push('/settings')">个人设置</el-dropdown-item>
                <el-dropdown-item divided @click="signOut">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>
      <main class="page"><slot /></main>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Aim, ArrowDown, Bell, Collection, Connection, DataAnalysis, Document,
  EditPen, Expand, Fold, Grid, Guide, Histogram, HomeFilled, List,
  MagicStick, Message, Reading, Search, Setting, Share,
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const user = useUserStore()
const collapsed = ref(false)
const search = ref('')

const menu = [
  { path: '/', label: '首页总览', icon: HomeFilled },
  { path: '/tracks', label: '方向探索', icon: Aim },
  { path: '/skills', label: '技能图谱', icon: Share },
  { path: '/profile', label: '能力画像', icon: Histogram },
  { path: '/knowledge', label: '知识检索', icon: Collection },
  { path: '/generate', label: '智能生成', icon: MagicStick },
  { path: '/resources?type=lecture', label: '个性化讲义', icon: Reading },
  { path: '/practice', label: '项目实操', icon: Guide },
  { path: '/assessment', label: '分阶测试', icon: EditPen },
  { path: '/report', label: '成长报告', icon: DataAnalysis },
  { path: '/agents', label: '多智能体', icon: Connection },
  { path: '/plan', label: '学习计划', icon: Grid },
  { path: '/records', label: '学习记录', icon: List },
  { path: '/messages', label: '消息中心', icon: Message },
  { path: '/settings', label: '系统设置', icon: Setting },
  { path: '/integrations', label: 'AI 与搜索', icon: Connection },
  { path: '/admin', label: '评测与治理', icon: Document, adminOnly: true },
]
const visibleMenu = computed(() => menu.filter((item) => !item.adminOnly || user.current?.role === 'admin'))

function goSearch() {
  if (search.value.trim()) router.push({ path: '/knowledge', query: { q: search.value.trim() } })
}
async function signOut() {
  await user.logout()
  router.replace('/login')
}
</script>

<style scoped>
.shell { min-height: 100vh; display: flex; }
.sidebar {
  position: fixed; inset: 0 auto 0 0; z-index: 30; width: 244px; padding: 18px 14px;
  background: rgba(255,255,255,.92); border-right: 1px solid #e7edf7; backdrop-filter: blur(18px);
  display: flex; flex-direction: column; transition: width .25s ease;
}
.sidebar.collapsed { width: 76px; }
.brand { height: 58px; display: flex; align-items: center; gap: 12px; padding: 0 7px; cursor: pointer; }
.brand-mark {
  min-width: 42px; height: 42px; border-radius: 14px; display:grid; place-items:center;
  color:white; font-weight:800; background: linear-gradient(145deg,#2768ff,#694cff);
  box-shadow: 0 10px 24px rgba(54,103,255,.28);
}
.brand strong,.brand span { display:block; white-space:nowrap; }
.brand strong { font-size: 18px; }.brand span { font-size: 11px; color:#8792a7; margin-top:3px; }
nav { flex:1; overflow-y:auto; padding:14px 0; }
.nav-item {
  height: 42px; margin: 3px 0; padding:0 14px; border-radius:12px; display:flex; align-items:center;
  gap:12px; color:#58647a; text-decoration:none; font-size:14px; transition:.18s ease; white-space:nowrap;
}
.nav-item:hover { color:#245fe5; background:#f0f5ff; transform:translateX(2px); }
.nav-item.router-link-active { color:white; background:linear-gradient(120deg,#2f69f5,#5865ee); box-shadow:0 8px 20px rgba(54,102,240,.22); }
.collapse { border:0; background:#f5f7fb; color:#68748a; height:40px; border-radius:12px; cursor:pointer; display:flex; align-items:center; justify-content:center; gap:8px; }
.workspace { min-width:0; flex:1; margin-left:244px; transition:margin-left .25s ease; }
.sidebar.collapsed + .workspace { margin-left:76px; }
.topbar {
  height:82px; padding:0 30px; display:flex; align-items:center; justify-content:space-between;
  position:sticky; top:0; z-index:20; background:rgba(246,249,253,.84); backdrop-filter:blur(18px);
  border-bottom:1px solid rgba(219,228,242,.8);
}
.eyebrow { margin:0 0 3px; font-size:11px; color:#71809a; letter-spacing:.08em; }
.topbar h1 { margin:0; font-size:20px; }
.top-actions { display:flex; align-items:center; gap:12px; }.top-actions .el-input { width:280px; }
.user-chip { border:0; background:transparent; display:flex; align-items:center; gap:8px; cursor:pointer; color:#25314a; }
.page { padding:28px 30px 48px; max-width:1600px; margin:0 auto; }
@media (max-width: 900px) {
  .sidebar { width:76px }.sidebar:not(.collapsed) span,.sidebar:not(.collapsed) .brand>div:last-child { display:none }
  .workspace,.sidebar.collapsed + .workspace { margin-left:76px }.top-actions .el-input { display:none }
  .topbar,.page { padding-left:18px; padding-right:18px }
}
</style>
