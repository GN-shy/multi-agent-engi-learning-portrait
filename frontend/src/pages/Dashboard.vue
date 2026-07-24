<template>
  <AppShell>
    <div v-loading="loading">
      <section class="hero panel">
        <div>
          <p>你好，{{ user.displayName }} 👋</p>
          <h2>{{ dashboard.selected_track ? `继续你的「${dashboard.selected_track.name}」路线` : '先比较方向，再投入学习' }}</h2>
          <span>{{ heroCopy }}</span>
          <div class="hero-actions">
            <el-button type="primary" @click="router.push(nextAction.path)">{{ nextAction.label }}</el-button>
            <el-button @click="router.push('/tracks')">比较全部方向</el-button>
          </div>
        </div>
        <div class="hero-orbit"><span>画像</span><span>路线</span><span>证据</span><strong>AI</strong></div>
      </section>

      <div class="metric-grid">
        <article class="metric" @click="openMetric('能力画像', dashboard.profile)">
          <span class="muted">综合能力</span><strong>{{ dashboard.profile?.score || 0 }}</strong><small>点击查看六维能力</small>
        </article>
        <article class="metric" @click="openMetric('路线匹配', dashboard.route_match)">
          <span class="muted">当前路线匹配</span><strong>{{ dashboard.route_match?.score || 0 }}%</strong><small>{{ dashboard.selected_track?.role || '尚未选择' }}</small>
        </article>
        <article class="metric" @click="openMetric('学习资源', dashboard.resources)">
          <span class="muted">已生成资源</span><strong>{{ dashboard.resources?.total || 0 }}</strong><small>讲义 / 实操 / 测试 / 计划</small>
        </article>
        <article class="metric" @click="openMetric('学习计划', dashboard.plan)">
          <span class="muted">计划进度</span><strong>{{ dashboard.plan?.progress || 0 }}%</strong><small>{{ dashboard.plan?.goal || '尚未创建' }}</small>
        </article>
      </div>

      <div class="grid two section-gap">
        <section class="panel">
          <div class="panel-title"><div><h3>六维能力画像</h3><p>来自自评、诊断、测试和实操证据</p></div><el-button text @click="router.push('/profile')">更新画像</el-button></div>
          <EChart :option="radarOption" height="330px" @click="openChartDetail" />
        </section>
        <section class="panel">
          <div class="panel-title"><div><h3>测试成长趋势</h3><p>每次测试都会回写画像</p></div><el-button text @click="router.push('/assessment')">去测试</el-button></div>
          <EChart :option="trendOption" height="330px" @click="openChartDetail" />
        </section>
      </div>

      <div class="grid two section-gap">
        <section class="panel">
          <div class="panel-title"><div><h3>当前路线</h3><p>推荐理由和反事实投入比较</p></div></div>
          <template v-if="dashboard.route_match">
            <div class="route-head"><strong>{{ dashboard.route_match.track_name }}</strong><el-tag>{{ dashboard.route_match.estimated_weeks }} 周</el-tag></div>
            <p v-for="reason in dashboard.route_match.why" :key="reason" class="reason">✓ {{ reason }}</p>
            <el-button type="primary" plain @click="openMetric('路线完整依据', dashboard.route_match)">查看全部依据</el-button>
          </template>
          <div v-else class="empty">尚未完成路线比较</div>
        </section>
        <section class="panel">
          <div class="panel-title"><div><h3>最新 Agent 闭环</h3><p>状态、质量指标与证据可审计</p></div></div>
          <template v-if="dashboard.latest_session">
            <div class="route-head"><strong>{{ dashboard.latest_session.goal }}</strong><el-tag type="success">{{ dashboard.latest_session.status }}</el-tag></div>
            <div class="quality-list">
              <span v-for="(value,key) in dashboard.latest_session.quality_metrics" :key="key">{{ metricLabel(String(key)) }} <b>{{ formatMetric(String(key), value) }}</b></span>
            </div>
            <el-button type="primary" plain @click="router.push(`/session/${dashboard.latest_session.id}`)">查看完整轨迹</el-button>
          </template>
          <div v-else class="empty">尚未运行个性化生成</div>
        </section>
      </div>
    </div>

    <DetailModal v-model="detail.visible" :title="detail.title">
      <pre class="json-detail">{{ pretty(detail.data) }}</pre>
    </DetailModal>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '@/components/layout/AppShell.vue'
import DetailModal from '@/components/common/DetailModal.vue'
import EChart from '@/components/common/EChart.vue'
import { getData } from '@/api'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const user = useUserStore()
const loading = ref(true)
const dashboard = reactive<any>({})
const detail = reactive({ visible: false, title: '', data: null as any })

const heroCopy = computed(() => dashboard.profile?.blind_spots?.length
  ? `当前最需要补齐：${dashboard.profile.blind_spots.map((item:any)=>item.name).join('、')}`
  : '完成画像后，系统会比较不同方向的适配度、成本与关键缺口。')
const nextAction = computed(() => !dashboard.onboarding?.profile_ready
  ? { label: '开始能力诊断', path: '/profile' }
  : !dashboard.onboarding?.track_selected
    ? { label: '开始路线比较', path: '/tracks' }
    : { label: '生成下一阶段资源', path: '/generate' })
const dimensions = computed(() => dashboard.profile?.dimensions || {})
const radarOption = computed(() => ({
  tooltip: {},
  radar: { indicator: Object.keys(dimensions.value).map(name => ({ name: metricLabel(name), max: 100 })), radius: '66%', splitArea: { areaStyle: { color: ['#fbfcff','#f2f6ff'] } } },
  series: [{ type:'radar', data:[{ value:Object.values(dimensions.value), name:'当前能力', areaStyle:{color:'rgba(49,104,238,.22)'}, lineStyle:{color:'#3168ee'} }] }],
}))
const trendOption = computed(() => ({
  tooltip:{trigger:'axis'}, grid:{left:38,right:20,top:25,bottom:34},
  xAxis:{type:'category',data:(dashboard.assessment_trend||[]).map((item:any)=>new Date(item.date).toLocaleDateString())},
  yAxis:{type:'value',min:0,max:100},
  series:[{type:'line',smooth:true,data:(dashboard.assessment_trend||[]).map((item:any)=>item.score),lineStyle:{color:'#17a673',width:3},areaStyle:{color:'rgba(23,166,115,.12)'},symbolSize:9}],
}))

onMounted(async () => {
  try { Object.assign(dashboard, await getData('/dashboard')) } finally { loading.value = false }
})
function openMetric(title:string,data:any){ detail.title=title;detail.data=data;detail.visible=true }
function openChartDetail(params:any){ openMetric(`图表数据 · ${params.name || params.seriesName}`, params) }
function pretty(value:any){ return JSON.stringify(value ?? { message:'暂无数据' },null,2) }
function metricLabel(key:string){ return ({programming_and_algorithms:'编程与算法',systems_foundation:'系统基础',software_engineering:'软件工程',architecture_and_security:'架构与安全',engineering_delivery:'工程交付',route_specific:'方向专项',knowledge_coverage:'知识覆盖',citation_coverage:'引用覆盖',profile_fit:'画像适配',prerequisite_violations:'前置冲突',hallucination_risk:'幻觉风险',total:'质量总分'} as any)[key] || key }
function formatMetric(key:string,value:any){ return key.includes('coverage')||key.includes('fit')||key.includes('risk') ? `${Math.round(Number(value)*100)}%` : value }
</script>

<style scoped>
.hero { min-height:250px; display:flex;align-items:center;justify-content:space-between;overflow:hidden;background:linear-gradient(120deg,#fff 35%,#edf3ff); }.hero p{color:#3168ee;font-weight:700}.hero h2{font-size:30px;margin:8px 0 12px}.hero span{color:#68758c}.hero-actions{margin-top:26px}
.hero-orbit { width:220px;height:220px;border:1px solid #cddcff;border-radius:50%;position:relative;display:grid;place-items:center;margin-right:40px;animation:float 4s ease-in-out infinite }.hero-orbit strong{width:82px;height:82px;border-radius:24px;display:grid;place-items:center;color:white;font-size:28px;background:linear-gradient(145deg,#3168ee,#7957ee);box-shadow:0 20px 45px rgba(52,94,220,.3)}.hero-orbit span{position:absolute;background:white;padding:8px 12px;border-radius:20px;box-shadow:var(--shadow);font-size:12px}.hero-orbit span:nth-child(1){top:12px}.hero-orbit span:nth-child(2){bottom:28px;left:0}.hero-orbit span:nth-child(3){right:-10px;top:90px}
.metric-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-top:18px}.metric small{display:block;color:#7b8799;margin-top:8px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.section-gap{margin-top:18px}.route-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px}.route-head strong{font-size:20px}.reason{color:#5d6980}.quality-list{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin:16px 0}.quality-list span{padding:11px;background:#f5f8fd;border-radius:10px;display:flex;justify-content:space-between}.json-detail{white-space:pre-wrap;word-break:break-word;background:#f7f9fd;padding:18px;border-radius:12px;line-height:1.65}@keyframes float{50%{transform:translateY(-8px)}}@media(max-width:1100px){.metric-grid{grid-template-columns:repeat(2,1fr)}.hero-orbit{display:none}}@media(max-width:650px){.metric-grid{grid-template-columns:1fr}.hero h2{font-size:24px}}
</style>
