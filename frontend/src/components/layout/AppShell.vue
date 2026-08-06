<template>
  <div class="shell">
    <aside class="sidebar" :class="{ collapsed }">
      <div class="brand" @click="router.push('/')">
        <div class="brand-mark"><span></span><span></span></div>
        <div v-if="!collapsed" class="brand-copy">
          <strong>工学智链</strong>
          <span>计算机能力成长与智能协同平台</span>
        </div>
      </div>

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
        <div class="promo-orbit"><i></i><i></i><strong>GX</strong></div>
        <b>工学智链</b>
        <p>让学习更智能、精准、可验证</p>
        <button @click="router.push('/tracks')">探索方向 →</button>
      </section>

      <button class="collapse" @click="collapsed = !collapsed" :aria-label="collapsed ? '展开导航' : '收起导航'">
        <el-icon><Fold v-if="!collapsed" /><Expand v-else /></el-icon>
        <span v-if="!collapsed">收起导航</span>
      </button>
    </aside>

    <section class="workspace">
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
            <button class="user-chip">
              <el-avatar :size="38" :src="user.current?.avatar">{{ user.displayName[0] }}</el-avatar>
              <span>{{ user.displayName }}</span>
              <em>{{ user.current?.role === 'admin' ? '管理员' : '学习者' }}</em>
              <el-icon><ArrowDown /></el-icon>
            </button>
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
const collapsed = ref(false)
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
.shell{min-height:100vh;display:flex}.sidebar{position:fixed;inset:0 auto 0 0;z-index:30;width:254px;padding:18px 14px 14px;background:rgba(255,255,255,.97);border-right:1px solid #e4ebf5;display:flex;flex-direction:column;transition:width .24s ease}.sidebar.collapsed{width:76px}.brand{height:65px;display:flex;align-items:center;gap:12px;padding:0 7px;cursor:pointer}.brand-mark{position:relative;min-width:46px;height:46px;border-radius:15px;transform:rotate(-10deg);background:linear-gradient(145deg,#2871ff,#5849ec);box-shadow:0 10px 24px rgba(54,103,255,.26)}.brand-mark span{position:absolute;width:20px;height:12px;border:4px solid white;border-radius:9px;top:13px}.brand-mark span:first-child{left:5px}.brand-mark span:last-child{right:5px}.brand-copy strong,.brand-copy span{display:block;white-space:nowrap}.brand-copy strong{font-size:22px;letter-spacing:.03em;color:#121a2b}.brand-copy span{max-width:158px;overflow:hidden;text-overflow:ellipsis;font-size:9px;color:#7c879a;margin-top:4px}nav{flex:1;overflow-y:auto;padding:13px 0;scrollbar-width:none}.nav-item{height:41px;margin:2px 0;padding:0 15px;border-radius:9px;display:flex;align-items:center;gap:13px;color:#303b50;text-decoration:none;font-size:14px;transition:.16s ease;white-space:nowrap}.nav-item .el-icon{font-size:17px}.nav-item:hover{color:#245fe5;background:#f1f5ff}.nav-item.router-link-active{color:white;background:linear-gradient(115deg,#175df1,#4c7dff);box-shadow:0 8px 18px rgba(43,101,240,.22)}.brand-promo{margin:8px 4px 10px;padding:16px;border-radius:14px;background:linear-gradient(155deg,#f4f8ff,#eaf2ff);border:1px solid #e1eaff}.promo-orbit{height:72px;position:relative;display:grid;place-items:center}.promo-orbit:before,.promo-orbit:after{content:'';position:absolute;border:1px solid #bdd2ff;border-radius:50%}.promo-orbit:before{width:80px;height:35px;transform:rotate(18deg)}.promo-orbit:after{width:60px;height:60px}.promo-orbit strong{z-index:2;width:43px;height:43px;display:grid;place-items:center;border-radius:14px;background:linear-gradient(145deg,#3781ff,#6250ed);color:white}.promo-orbit i{position:absolute;width:7px;height:7px;background:#4e7cf4;border-radius:50%;z-index:3}.promo-orbit i:first-child{left:35px;top:22px}.promo-orbit i:nth-child(2){right:34px;bottom:16px}.brand-promo b{display:block;margin-top:5px}.brand-promo p{font-size:11px;color:#6f7b91;margin:6px 0 12px}.brand-promo button{border:0;background:#dce8ff;color:#2460db;border-radius:7px;padding:6px 10px;cursor:pointer}.collapse{border:0;background:#f5f7fb;color:#68748a;height:36px;border-radius:9px;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:8px}.workspace{min-width:0;flex:1;margin-left:254px;transition:margin-left .24s ease}.sidebar.collapsed+.workspace{margin-left:76px}.topbar{height:66px;padding:0 28px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:20;background:rgba(255,255,255,.93);backdrop-filter:blur(18px);border-bottom:1px solid #e7edf6}.page-heading h1{margin:0;font-size:20px}.page-heading p{display:none}.top-actions{display:flex;align-items:center;gap:12px}.top-actions>.el-input{width:300px}.icon-button{border-color:#e4eaf3}.user-chip{border:0;background:transparent;display:flex;align-items:center;gap:8px;cursor:pointer;color:#25314a}.user-chip>span{font-weight:600}.user-chip em{font-size:11px;font-style:normal;color:#2460db;background:#edf3ff;padding:3px 7px;border-radius:6px}.page{padding:20px 26px 42px;max-width:1680px;margin:0 auto}@media(max-width:900px){.sidebar{width:76px}.sidebar:not(.collapsed) .brand-copy,.sidebar:not(.collapsed) .nav-item span,.brand-promo{display:none}.workspace,.sidebar.collapsed+.workspace{margin-left:76px}.top-actions>.el-input{display:none}.topbar,.page{padding-left:16px;padding-right:16px}.user-chip>span,.user-chip em{display:none}}@media(max-width:560px){.sidebar{display:none}.workspace,.sidebar.collapsed+.workspace{margin-left:0}.page-heading h1{font-size:17px}}
.nav-caption{display:block;padding:6px 15px;color:#9aa5b7;font-size:10px;font-weight:800;letter-spacing:.12em}.more-nav{margin-top:10px;border-top:1px solid #edf1f7;padding-top:8px}.more-nav summary{list-style:none;padding:9px 15px;color:#718097;font-size:12px;font-weight:700;display:flex;justify-content:space-between;cursor:pointer}.more-nav summary::-webkit-details-marker{display:none}.more-nav summary i{font-style:normal;transition:.2s}.more-nav[open] summary i{transform:rotate(180deg)}.tool-link{display:flex;align-items:center;gap:10px;margin:2px 6px;padding:8px 10px;border-radius:8px;color:#657187;text-decoration:none;font-size:12px}.tool-link:hover,.tool-link.router-link-active{background:#eef4ff;color:#245fe5}.compact-tool{height:36px!important;justify-content:center;padding:0!important}
</style>
