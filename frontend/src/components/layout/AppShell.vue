<template>
  <div
    class="shell"
    :class="{ resizing: isResizing }"
    :style="{
      '--sidebar-width': `${effectiveSidebarWidth}px`,
      '--sidebar-collapsed-width': `${SIDEBAR_COLLAPSED_WIDTH}px`,
    }"
  >
    <aside class="sidebar" :class="{ collapsed }">
      <button class="brand" type="button" :aria-label="collapsed ? '返回工学智链首页' : undefined" @click="router.push('/')">
        <img class="brand-mark" src="/app-icon.png" alt="" width="46" height="46" />
        <div v-if="!collapsed" class="brand-copy">
          <strong>工学智链</strong>
          <span>计算机能力成长与智能协同平台</span>
        </div>
      </button>

      <nav>
        <span v-if="!collapsed" class="nav-caption">主要任务</span>
        <RouterLink v-for="item in primaryMenu" :key="item.path" :to="item.path" :title="item.label" class="nav-item">
          <el-icon><component :is="item.icon" /></el-icon>
          <span v-if="!collapsed">{{ item.label }}</span>
        </RouterLink>
        <details v-if="!collapsed" class="more-nav" :open="moreOpen" @toggle="rememberMoreState">
          <summary><span>更多工具</span><i>⌄</i></summary>
          <RouterLink v-for="item in visibleToolMenu" :key="item.path" :to="item.path" class="tool-link">
            <el-icon><component :is="item.icon" /></el-icon><span>{{ item.label }}</span>
          </RouterLink>
        </details>
      </nav>

      <section v-if="!collapsed" class="brand-promo">
        <div class="promo-orbit"><i></i><i></i><img src="/app-icon.png" alt="" width="43" height="43" /></div>
        <b>工学智链</b>
        <p>让学习更智能、精准、可验证</p>
        <button @click="router.push('/tracks')">探索方向 →</button>
      </section>

      <button class="collapse" @click="toggleCollapsed" :aria-label="collapsed ? '展开导航' : '收起导航'">
        <el-icon><Fold v-if="!collapsed" /><Expand v-else /></el-icon>
        <span v-if="!collapsed">收起导航</span>
      </button>

      <div
        v-if="!collapsed"
        class="sidebar-resizer"
        role="separator"
        aria-label="调整导航栏宽度"
        aria-orientation="vertical"
        aria-controls="main-workspace"
        :aria-valuemin="SIDEBAR_MIN_WIDTH"
        :aria-valuemax="SIDEBAR_MAX_WIDTH"
        :aria-valuenow="sidebarWidth"
        :aria-valuetext="`${sidebarWidth} 像素`"
        tabindex="0"
        @dblclick="resetSidebarWidth"
        @keydown="resizeWithKeyboard"
        @pointerdown="startResize"
        @pointermove="continueResize"
        @pointerup="finishResize"
        @pointercancel="finishResize"
        @lostpointercapture="finishResize"
      >
        <span class="resizer-grip" aria-hidden="true"></span>
      </div>
    </aside>

    <section id="main-workspace" class="workspace">
      <header class="topbar">
        <div class="page-heading">
          <h1>{{ route.meta.title || '工学智链' }}</h1>
          <p>{{ route.meta.eyebrow || '计算机能力成长闭环' }}</p>
        </div>
        <div class="top-actions">
          <el-input v-model="search" placeholder="搜索知识点、资源、报告…" :prefix-icon="Search" clearable @keyup.enter="goSearch" />
          <el-badge :value="unreadCount" :hidden="!unreadCount">
            <el-button circle class="icon-button" aria-label="消息中心" @click="router.push('/messages')"><el-icon><Bell /></el-icon></el-button>
          </el-badge>
          <el-dropdown>
            <el-button text class="user-chip">
              <span class="user-chip-content">
                <el-avatar :size="38" :src="user.current?.avatar">{{ user.displayName[0] }}</el-avatar>
                <span class="user-name">{{ user.displayName }}</span>
                <em>{{ user.current?.role === 'admin' ? '管理员' : '学习者' }}</em>
                <el-icon><ArrowDown /></el-icon>
              </span>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="router.push('/profile')">学习画像</el-dropdown-item>
                <el-dropdown-item @click="router.push('/settings')">个人设置</el-dropdown-item>
                <el-dropdown-item @click="router.push('/integrations')">外部 API 配置</el-dropdown-item>
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
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Aim, ArrowDown, Bell, Collection, Connection, DataAnalysis, Document,
  EditPen, Expand, Fold, Grid, Guide, Histogram, HomeFilled, List,
  MagicStick, Message, Reading, Search, Setting, Share,
} from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { getData } from '@/api'

const router = useRouter()
const route = useRoute()
const user = useUserStore()
const SIDEBAR_DEFAULT_WIDTH = 254
const SIDEBAR_MIN_WIDTH = 220
const SIDEBAR_MAX_WIDTH = 360
const SIDEBAR_COLLAPSED_WIDTH = 76
const SIDEBAR_WIDTH_STORAGE_KEY = 'gx_sidebar_width'

function clampSidebarWidth(width: number) {
  return Math.min(SIDEBAR_MAX_WIDTH, Math.max(SIDEBAR_MIN_WIDTH, width))
}

function loadSidebarWidth() {
  try {
    const storedWidth = Number(localStorage.getItem(SIDEBAR_WIDTH_STORAGE_KEY))
    return Number.isFinite(storedWidth) && storedWidth > 0
      ? clampSidebarWidth(storedWidth)
      : SIDEBAR_DEFAULT_WIDTH
  } catch {
    return SIDEBAR_DEFAULT_WIDTH
  }
}

const collapsed = ref(false)
const sidebarWidth = ref(loadSidebarWidth())
const effectiveSidebarWidth = computed(() => collapsed.value ? SIDEBAR_COLLAPSED_WIDTH : sidebarWidth.value)
const isResizing = ref(false)
let activePointerId: number | null = null
const moreOpen = ref(sessionStorage.getItem('gx_more_tools_open') === '1')
const search = ref('')
const unreadCount = ref(0)

const primaryMenu = [
  { path: '/', label: '今天', icon: HomeFilled },
  { path: '/tracks', label: '方向与路线', icon: Aim },
  { path: '/plan', label: '学习中心', icon: Reading },
  { path: '/practice', label: '实践与测评', icon: Guide },
  { path: '/profile', label: '我的成长', icon: Histogram },
]
const toolMenu = [
  { path: '/career-target', label: '目标岗位与 JD', icon: Aim },
  { path: '/generate', label: '生成学习资料', icon: MagicStick },
  { path: '/resources?type=lecture', label: '讲义与资源', icon: Reading },
  { path: '/assessment', label: '分阶测试', icon: EditPen },
  { path: '/knowledge', label: '知识检索', icon: Collection },
  { path: '/skills', label: '技能图谱', icon: Share },
  { path: '/report', label: '成长报告', icon: DataAnalysis },
  { path: '/records', label: '学习记录', icon: List },
  { path: '/agents', label: 'Agent 证据', icon: Connection },
  { path: '/messages', label: '消息中心', icon: Message },
  { path: '/settings', label: '账户设置', icon: Setting },
  { path: '/integrations', label: '外部 API', icon: Connection },
  { path: '/admin', label: '评测与治理', icon: Document, adminOnly: true },
]
const visibleToolMenu = computed(() => toolMenu.filter(item => !item.adminOnly || user.current?.role === 'admin'))

function persistSidebarWidth() {
  try {
    localStorage.setItem(SIDEBAR_WIDTH_STORAGE_KEY, String(sidebarWidth.value))
  } catch {
    // 浏览器禁用持久存储时仍保留当前会话内的宽度。
  }
}

function setSidebarWidth(width: number, persist = false) {
  sidebarWidth.value = clampSidebarWidth(Math.round(width))
  if (persist) persistSidebarWidth()
}

function toggleCollapsed() {
  isResizing.value = false
  activePointerId = null
  collapsed.value = !collapsed.value
}

function startResize(event: PointerEvent) {
  if (event.button !== 0 || collapsed.value) return
  event.preventDefault()
  activePointerId = event.pointerId
  isResizing.value = true
  ;(event.currentTarget as HTMLElement).setPointerCapture(event.pointerId)
  setSidebarWidth(event.clientX)
}

function continueResize(event: PointerEvent) {
  if (!isResizing.value || event.pointerId !== activePointerId) return
  event.preventDefault()
  setSidebarWidth(event.clientX)
}

function finishResize(event: PointerEvent) {
  if (event.pointerId !== activePointerId) return
  const target = event.currentTarget as HTMLElement
  if (target.hasPointerCapture(event.pointerId)) target.releasePointerCapture(event.pointerId)
  activePointerId = null
  isResizing.value = false
  persistSidebarWidth()
}

function resizeWithKeyboard(event: KeyboardEvent) {
  const step = event.shiftKey ? 24 : 8
  let nextWidth: number | null = null
  if (event.key === 'ArrowLeft') nextWidth = sidebarWidth.value - step
  if (event.key === 'ArrowRight') nextWidth = sidebarWidth.value + step
  if (event.key === 'Home') nextWidth = SIDEBAR_MIN_WIDTH
  if (event.key === 'End') nextWidth = SIDEBAR_MAX_WIDTH
  if (nextWidth === null) return
  event.preventDefault()
  setSidebarWidth(nextWidth, true)
}

function resetSidebarWidth() {
  setSidebarWidth(SIDEBAR_DEFAULT_WIDTH, true)
}

function rememberMoreState(event: Event) {
  const open = (event.currentTarget as HTMLDetailsElement).open
  moreOpen.value = open
  sessionStorage.setItem('gx_more_tools_open', open ? '1' : '0')
}

onMounted(async () => {
  try {
    const result = await getData<{items:any[]}>('/messages')
    unreadCount.value = result.items.filter(item => !item.read).length
  } catch {
    unreadCount.value = 0
  }
})
function goSearch() {
  if (search.value.trim()) router.push({ path: '/knowledge', query: { q: search.value.trim() } })
}
async function signOut() {
  try {
    await ElMessageBox.confirm('退出后需要重新登录，确认退出吗？', '退出登录', {
      type: 'warning',
      confirmButtonText: '确认退出',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  await user.logout()
  router.replace('/login')
}
</script>

<style scoped>
.shell{min-height:100vh;display:flex}.sidebar{position:fixed;inset:0 auto 0 0;z-index:30;width:var(--sidebar-width);padding:18px 14px 14px;background:rgba(255,255,255,.97);border-right:1px solid #e4ebf5;display:flex;flex-direction:column;transition:width .24s ease}.brand{width:100%;height:65px;border:0;background:transparent;display:flex;align-items:center;gap:12px;padding:0 7px;text-align:left}.brand:hover{background:#f5f8fd;border-radius:12px}.brand-mark{display:block;min-width:46px;height:46px;object-fit:cover;border-radius:13px;box-shadow:0 9px 22px rgba(25,64,120,.2)}.brand-copy{min-width:0}.brand-copy strong,.brand-copy span{display:block;white-space:nowrap}.brand-copy strong{font-size:22px;letter-spacing:.03em;color:#121a2b}.brand-copy span{max-width:158px;overflow:hidden;text-overflow:ellipsis;font-size:9px;color:#7c879a;margin-top:4px}nav{flex:1;overflow-y:auto;padding:13px 0;scrollbar-gutter:stable}.nav-item{height:41px;margin:2px 0;padding:0 15px;border-radius:9px;display:flex;align-items:center;gap:13px;color:#303b50;text-decoration:none;font-size:14px;transition:.16s ease;white-space:nowrap}.nav-item .el-icon{flex:0 0 auto;font-size:17px}.sidebar.collapsed nav{scrollbar-gutter:auto}.sidebar.collapsed .nav-item{justify-content:center;gap:0;padding-inline:0}.nav-item:hover{color:#245fe5;background:#f1f5ff}.nav-item.router-link-active{color:white;background:linear-gradient(115deg,#175df1,#4c7dff);box-shadow:0 8px 18px rgba(43,101,240,.22)}.brand-promo{margin:8px 4px 10px;padding:16px;border-radius:14px;background:linear-gradient(155deg,#f4f8ff,#eaf2ff);border:1px solid #e1eaff}.promo-orbit{height:72px;position:relative;display:grid;place-items:center}.promo-orbit:before,.promo-orbit:after{content:'';position:absolute;border:1px solid #bdd2ff;border-radius:50%}.promo-orbit:before{width:80px;height:35px;transform:rotate(18deg)}.promo-orbit:after{width:60px;height:60px}.promo-orbit img{z-index:2;display:block;object-fit:cover;border-radius:12px;box-shadow:0 7px 18px rgba(25,64,120,.18)}.promo-orbit i{position:absolute;width:7px;height:7px;background:#4e7cf4;border-radius:50%;z-index:3}.promo-orbit i:first-child{left:35px;top:22px}.promo-orbit i:nth-child(2){right:34px;bottom:16px}.brand-promo b{display:block;margin-top:5px}.brand-promo p{font-size:11px;color:#6f7b91;margin:6px 0 12px}.brand-promo button{border:0;background:#dce8ff;color:#2460db;border-radius:7px;padding:6px 10px;cursor:pointer}.collapse{border:0;background:#f5f7fb;color:#68748a;height:36px;border-radius:9px;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:8px}.workspace{min-width:0;flex:1;margin-left:var(--sidebar-width);transition:margin-left .24s ease}.topbar{height:66px;padding:0 28px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:20;background:rgba(255,255,255,.93);backdrop-filter:blur(18px);border-bottom:1px solid #e7edf6}.page-heading h1{margin:0;font-size:20px}.page-heading p{display:none}.top-actions{display:flex;align-items:center;gap:12px}.top-actions>.el-input{width:300px}.icon-button{border-color:#e4eaf3}.user-chip{height:44px;border:0;background:transparent;color:#25314a}.user-chip:hover{background:#f4f7fb}.user-chip-content{display:flex;align-items:center;gap:8px}.user-name{font-weight:600}.user-chip em{font-size:11px;font-style:normal;color:#2460db;background:#edf3ff;padding:3px 7px;border-radius:6px}.page{padding:20px 26px 42px;max-width:1680px;margin:0 auto}@media(max-width:900px){.sidebar{width:var(--sidebar-collapsed-width)}.sidebar:not(.collapsed) .brand-copy,.sidebar:not(.collapsed) .nav-item span,.brand-promo,.sidebar-resizer{display:none}.sidebar nav{scrollbar-gutter:auto}.sidebar .nav-item{justify-content:center;gap:0;padding-inline:0}.workspace{margin-left:var(--sidebar-collapsed-width)}.top-actions>.el-input{display:none}.topbar,.page{padding-left:16px;padding-right:16px}.user-name,.user-chip em{display:none}}@media(max-width:560px){.sidebar{display:none}.workspace{margin-left:0}.page-heading h1{font-size:17px}}
.sidebar-resizer{position:absolute;top:0;right:-12px;z-index:31;width:24px;height:100%;display:grid;place-items:center;cursor:col-resize;touch-action:none;outline:none}.sidebar-resizer:before{content:'';position:absolute;inset:0 11px;background:#e4ebf5;transition:background-color .16s ease}.resizer-grip{position:relative;width:6px;height:44px;border:1px solid #d6e0ed;border-radius:999px;background:#fff;box-shadow:0 4px 12px rgba(28,65,116,.1);opacity:.52;transition:opacity .16s ease,border-color .16s ease,box-shadow .16s ease}.resizer-grip:before,.resizer-grip:after{content:'';position:absolute;top:13px;width:1px;height:16px;background:#9aacbf}.resizer-grip:before{left:1px}.resizer-grip:after{right:1px}.sidebar-resizer:hover:before,.shell.resizing .sidebar-resizer:before{background:var(--primary)}.sidebar-resizer:hover .resizer-grip,.sidebar-resizer:focus-visible .resizer-grip,.shell.resizing .resizer-grip{opacity:1;border-color:#9fbaff;box-shadow:0 0 0 3px rgba(76,130,255,.22),0 6px 16px rgba(28,65,116,.16)}.shell.resizing,.shell.resizing *{cursor:col-resize;user-select:none}.shell.resizing .sidebar,.shell.resizing .workspace{transition:none}
.nav-caption{display:block;padding:6px 15px;color:#9aa5b7;font-size:10px;font-weight:800;letter-spacing:.12em}.more-nav{margin-top:10px;border-top:1px solid #edf1f7;padding-top:8px}.more-nav summary{list-style:none;padding:9px 15px;color:#718097;font-size:12px;font-weight:700;display:flex;justify-content:space-between;cursor:pointer}.more-nav summary::-webkit-details-marker{display:none}.more-nav summary i{font-style:normal;transition:.2s}.more-nav[open] summary i{transform:rotate(180deg)}.tool-link{height:41px;margin:2px 0;padding:0 15px;border-radius:9px;display:flex;align-items:center;gap:13px;color:#4b5870;text-decoration:none;font-size:15px;font-weight:500;transition:.16s ease;white-space:nowrap}.tool-link .el-icon{flex:0 0 auto;font-size:17px}.tool-link span{min-width:0;overflow:hidden;text-overflow:ellipsis}.tool-link:hover,.tool-link.router-link-active{background:#eef4ff;color:#245fe5}.compact-tool{height:36px;justify-content:center;padding:0}
@media(prefers-reduced-motion:reduce){.sidebar,.workspace,.nav-item,.clickable,.more-nav summary i,.sidebar-resizer:before,.resizer-grip{transition:none}}
@media(forced-colors:active){.sidebar-resizer:before{background:CanvasText}.sidebar-resizer:focus-visible .resizer-grip{outline:2px solid Highlight;outline-offset:3px}}
</style>
