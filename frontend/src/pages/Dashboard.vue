<template>
  <AppShell>
    <div v-loading="loading" class="dashboard-state">
      <section v-if="!loading && !dashboard.onboarding?.profile_ready" class="first-use panel">
        <div class="first-copy">
          <span class="state-label">你的数据还是空白的</span>
          <h2>{{ greeting }}，{{ user.displayName }}。先让系统真正了解你。</h2>
          <p>目前没有画像、路线、进度或能力结论，因此这里不会展示演示数字。完成约 3 分钟的引导后，系统才会根据你的阶段、真实经历、目标和时间生成结果。</p>
          <el-button type="primary" size="large" @click="router.push('/onboarding')">开始建立成长档案 →</el-button>
          <small>无需写自我介绍 · 不确定的问题可以选择“不了解” · 后续证据会自动修正</small>
        </div>
        <div class="first-flow">
          <div><i>1</i><p><b>说明真实情况</b><span>阶段、经历、目标、时间</span></p></div>
          <div><i>2</i><p><b>比较适合方向</b><span>岗位、缺口、学历、周期</span></p></div>
          <div><i>3</i><p><b>获得第一周任务</b><span>具体学习、项目和验收标准</span></p></div>
        </div>
      </section>

      <section v-else-if="!loading && !dashboard.onboarding?.track_selected" class="decision-state">
        <article class="decision-main panel">
          <span class="state-label">初始画像已建立</span>
          <h2>下一步只做一件事：确认学习方向</h2>
          <p>系统已经根据你的输入形成初步能力基线，但还没有替你选择方向。进入比较页后，可以查看不同方向的匹配依据、能力缺口、预计投入、岗位与薪资参考。</p>
          <div class="profile-facts">
            <div><span>初始能力</span><b>{{ dashboard.profile?.score }} 分</b><small>仍以主观选择为主</small></div>
            <div><span>每周投入</span><b>{{ dashboard.profile?.weekly_hours }} 小时</b><small>用于计算路线周期</small></div>
            <div><span>优先补证据</span><b>{{ dashboard.profile?.blind_spots?.[0]?.name || '完成一次测评' }}</b><small>结果会持续校准</small></div>
          </div>
          <el-button type="primary" size="large" @click="router.push('/tracks')">比较并确认方向 →</el-button>
          <el-button size="large" @click="router.push('/onboarding?edit=1')">修改我的情况</el-button>
        </article>
        <aside class="evidence-rule panel">
          <h3>结果可信度说明</h3>
          <p>当前推荐只能作为决策参考，不会伪装成确定结论。</p>
          <ul><li>你的选择形成初始画像</li><li>分阶测试补充客观能力证据</li><li>项目提交验证真实工程能力</li><li>每次更新保留画像版本</li></ul>
        </aside>
      </section>

      <div v-else class="dashboard-layout">
      <main class="dashboard-main">
        <section class="hero panel">
          <div class="hero-copy">
            <p>{{ greeting }}，{{ user.displayName }}！ 👋</p>
            <h2>{{ dashboard.selected_track ? `继续你的「${dashboard.selected_track.name}」路线` : '先比较方向，再投入学习' }}</h2>
            <span>{{ heroCopy }}</span>
          </div>
          <div class="hero-visual" aria-hidden="true">
            <i></i><i></i><i></i><div>AI</div>
          </div>
          <div class="hero-metrics">
            <button @click="openMetric('能力画像',dashboard.profile)"><span>综合能力</span><strong>{{ dashboard.profile?.score || 0 }}</strong><small>画像 V{{ dashboard.profile?.version || 0 }}</small></button>
            <button @click="openMetric('路线匹配',dashboard.route_match)"><span>路线匹配</span><strong>{{ dashboard.route_match?.score || 0 }}%</strong><small>{{ dashboard.selected_track?.role || '待选择方向' }}</small></button>
            <button @click="openMetric('学习资源',dashboard.resources)"><span>生成资源</span><strong>{{ dashboard.resources?.total || 0 }}</strong><small>讲义 / 实操 / 测评</small></button>
            <button @click="openMetric('学习计划',dashboard.plan)"><span>计划进度</span><strong>{{ dashboard.plan?.progress || 0 }}%</strong><small>{{ dashboard.plan ? '持续更新中' : '尚未创建' }}</small></button>
          </div>
        </section>

        <div class="content-grid">
          <section class="panel diagnosis">
            <div class="panel-title"><div><h3>学习诊断</h3><p>自评会被测试和实操证据持续校准</p></div><el-button text @click="router.push('/profile')">更新画像 →</el-button></div>
            <div class="diagnosis-body">
              <EChart :option="radarOption" height="255px" @click="openChartDetail" />
              <div class="gaps">
                <b>优先补齐 TOP3</b>
                <button v-for="(item,index) in dashboard.profile?.blind_spots||[]" :key="item.skill_code" @click="openMetric(item.name,item)">
                  <span>{{ index+1 }}. {{ item.name }}</span><el-tag :type="item.score < 40 ? 'danger' : 'warning'">{{ item.score }} 分</el-tag>
                </button>
                <p v-if="!dashboard.profile?.blind_spots?.length">完成画像后给出具体建议</p>
              </div>
            </div>
          </section>

          <section class="panel route-card">
            <div class="panel-title"><div><h3>学习路径</h3><p>{{ dashboard.selected_track?.name || '尚未选择方向' }}</p></div><el-button text @click="router.push('/plan')">查看全部 →</el-button></div>
            <template v-if="dashboard.plan">
              <div class="phase-rail">
                <div v-for="(phase,index) in dashboard.plan.phases" :key="phase.id" :class="{active:phase.status==='active',done:phase.status==='completed'}">
                  <span>{{ phase.status==='completed' ? '✓' : index+1 }}</span><b>{{ phase.name }}</b>
                </div>
              </div>
              <div class="current-task">
                <div><small>当前目标</small><b>{{ dashboard.plan.goal }}</b></div>
                <el-progress :percentage="dashboard.plan.progress" />
                <el-button type="primary" @click="router.push('/plan')">继续学习</el-button>
              </div>
            </template>
            <div v-else class="empty compact"><el-button type="primary" @click="router.push(nextAction.path)">{{ nextAction.label }}</el-button></div>
          </section>
        </div>

        <section class="panel resources-panel">
          <div class="panel-title"><div><h3>智能生成资源</h3><p>所有数量来自当前账号真实生成记录</p></div><el-button text @click="router.push('/resources')">全部资源 →</el-button></div>
          <div class="resource-grid">
            <button @click="router.push('/resources?type=lecture')"><i class="blue">讲</i><div><b>个性化讲义</b><span>基于画像与引用生成</span></div><strong>{{ dashboard.resources?.lecture || 0 }}</strong></button>
            <button @click="router.push('/practice')"><i class="green">练</i><div><b>项目实操</b><span>步骤、交付与证据验收</span></div><strong>{{ dashboard.resources?.practice || 0 }}</strong></button>
            <button @click="router.push('/assessment')"><i class="purple">测</i><div><b>分阶测评</b><span>四维评分并回写画像</span></div><strong>{{ dashboard.resources?.assessment || 0 }}</strong></button>
            <button @click="router.push('/report')"><i class="orange">报</i><div><b>成长报告</b><span>能力、路线与质量证据</span></div><strong>查看</strong></button>
          </div>
        </section>

        <section class="panel data-panel">
          <div class="panel-title"><div><h3>学习数据概览</h3><p>测评成绩与当前知识掌握分布</p></div></div>
          <div class="chart-grid">
            <EChart :option="trendOption" height="260px" @click="openChartDetail" />
            <EChart :option="distributionOption" height="260px" @click="openChartDetail" />
          </div>
        </section>
      </main>

      <aside class="dashboard-rail">
        <section class="panel agent-status">
          <div class="panel-title"><div><h3>多智能体协同状态</h3></div><el-button text @click="router.push('/agents')">查看详情 →</el-button></div>
          <button v-for="agent in agents.items||[]" :key="agent.code" @click="openMetric(agent.name,agent)">
            <i>{{ agent.code.toUpperCase().slice(0,2) }}</i>
            <div><b>{{ agent.name }}</b><span>{{ agent.summary }}</span></div>
            <el-tag :type="agent.status==='completed'?'success':'info'">{{ valueLabel(agent.status) }}</el-tag>
          </button>
          <footer><span></span>{{ valueLabel(agents.workflow_status) }}</footer>
        </section>

        <section class="panel latest">
          <div class="panel-title"><div><h3>最新消息</h3></div><el-button text @click="router.push('/messages')">查看全部 →</el-button></div>
          <button v-for="item in messages.slice(0,4)" :key="item.id" @click="router.push(item.action_url || '/messages')">
            <i :class="item.type">•</i><div><b>{{ item.title }}</b><span>{{ item.content }}</span></div><small>{{ relativeTime(item.created_at) }}</small>
          </button>
          <div v-if="!messages.length" class="empty compact">暂无消息</div>
        </section>

        <section class="panel quick-actions">
          <div class="panel-title"><div><h3>下一步建议</h3><p>依据当前业务状态生成</p></div></div>
          <button @click="router.push(nextAction.path)"><span>01</span><div><b>{{ nextAction.label }}</b><small>{{ nextActionHint }}</small></div>→</button>
          <button @click="router.push('/practice')"><span>02</span><div><b>提交项目证据</b><small>让能力画像不只依赖自评</small></div>→</button>
          <button @click="router.push('/report')"><span>03</span><div><b>查看成长报告</b><small>检查路线、趋势与质量门</small></div>→</button>
        </section>
      </aside>
      </div>
    </div>

    <DetailModal v-model="detail.visible" :title="detail.title"><HumanDetail :value="detail.data" /></DetailModal>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '@/components/layout/AppShell.vue'
import DetailModal from '@/components/common/DetailModal.vue'
import EChart from '@/components/common/EChart.vue'
import HumanDetail from '@/components/common/HumanDetail.vue'
import { getData } from '@/api'
import { useUserStore } from '@/stores/user'
import { valueLabel } from '@/utils/presentation'

const router = useRouter()
const user = useUserStore()
const loading = ref(true)
const dashboard = reactive<any>({})
const agents = reactive<any>({ items: [] })
const messages = ref<any[]>([])
const detail = reactive({ visible:false, title:'', data:null as any })
const greeting = computed(() => new Date().getHours() < 12 ? '上午好' : new Date().getHours() < 18 ? '下午好' : '晚上好')
const heroCopy = computed(() => dashboard.profile?.blind_spots?.length ? `当前最需要补齐：${dashboard.profile.blind_spots.map((item:any)=>item.name).join('、')}` : '完成画像后，系统会比较不同方向的适配度、成本与关键缺口。')
const nextAction = computed(() => !dashboard.onboarding?.profile_ready ? {label:'开始建立成长档案',path:'/onboarding'} : !dashboard.onboarding?.track_selected ? {label:'开始路线比较',path:'/tracks'} : {label:'生成下一阶段资源',path:'/generate'})
const nextActionHint = computed(() => !dashboard.onboarding?.profile_ready ? '建立可持续更新的能力基线' : !dashboard.onboarding?.track_selected ? '对比时间成本和技能差距' : '由六 Agent 生成完整学习闭环')
const dimensions = computed(() => dashboard.profile?.dimensions || {})
const radarOption = computed(() => ({tooltip:{},radar:{indicator:Object.keys(dimensions.value).map(name=>({name:metricLabel(name),max:100})),radius:'57%',splitArea:{areaStyle:{color:['#fbfcff','#f2f6ff']}},axisName:{fontSize:11}},series:[{type:'radar',data:[{value:Object.values(dimensions.value),name:'当前能力',areaStyle:{color:'rgba(49,104,238,.22)'},lineStyle:{color:'#3168ee',width:2}}]}]}))
const trendOption = computed(() => ({title:{text:'测评成长趋势',textStyle:{fontSize:14}},tooltip:{trigger:'axis'},grid:{left:38,right:20,top:48,bottom:30},xAxis:{type:'category',data:(dashboard.assessment_trend||[]).map((item:any)=>new Date(item.date).toLocaleDateString())},yAxis:{type:'value',min:0,max:100},series:[{type:'line',smooth:true,data:(dashboard.assessment_trend||[]).map((item:any)=>item.score),lineStyle:{color:'#3168ee',width:3},areaStyle:{color:'rgba(49,104,238,.11)'},symbolSize:8}]}))
const distributionOption = computed(() => {
  const values = Object.values(dimensions.value).map(Number)
  const buckets = [
    {name:'优势（80–100）',value:values.filter(v=>v>=80).length,itemStyle:{color:'#3168ee'}},
    {name:'良好（60–79）',value:values.filter(v=>v>=60&&v<80).length,itemStyle:{color:'#17b996'}},
    {name:'成长（40–59）',value:values.filter(v=>v>=40&&v<60).length,itemStyle:{color:'#f3a83b'}},
    {name:'待补（0–39）',value:values.filter(v=>v<40).length,itemStyle:{color:'#ef6271'}},
  ]
  return {title:{text:'能力分布',textStyle:{fontSize:14}},tooltip:{trigger:'item'},legend:{orient:'vertical',right:0,top:55,textStyle:{fontSize:11}},series:[{type:'pie',radius:['42%','66%'],center:['35%','56%'],label:{show:false},data:buckets}]}
})

onMounted(async () => {
  const [dashboardResult, agentResult, messageResult] = await Promise.allSettled([
    getData('/dashboard'),
    getData('/agents/status'),
    getData<{items:any[]}>('/messages'),
  ])
  if (dashboardResult.status === 'fulfilled') Object.assign(dashboard, dashboardResult.value)
  if (agentResult.status === 'fulfilled') Object.assign(agents, agentResult.value)
  if (messageResult.status === 'fulfilled') messages.value = messageResult.value.items
  loading.value = false
})
function openMetric(title:string,data:any){detail.title=title;detail.data=data;detail.visible=true}
function openChartDetail(params:any){openMetric(`图表数据 · ${params.name||params.seriesName}`,params)}
function metricLabel(key:string){return ({programming_and_algorithms:'编程与算法',systems_foundation:'系统基础',software_engineering:'软件工程',architecture_and_security:'架构与安全',engineering_delivery:'工程交付',route_specific:'方向专项'} as Record<string,string>)[key]||key}
function relativeTime(value:string){const delta=Math.max(0,Date.now()-new Date(value).getTime());const minutes=Math.floor(delta/60000);return minutes<60?`${minutes||1} 分钟前`:minutes<1440?`${Math.floor(minutes/60)} 小时前`:`${Math.floor(minutes/1440)} 天前`}
</script>

<style scoped>
.dashboard-layout{display:grid;grid-template-columns:minmax(0,1fr) 340px;gap:16px}.dashboard-main,.dashboard-rail{display:grid;gap:16px;align-content:start}.hero{position:relative;min-height:220px;padding:24px;overflow:hidden;background:linear-gradient(112deg,#f9fbff 0,#edf4ff 65%,#e2edff 100%)}.hero-copy{position:relative;z-index:2}.hero-copy p{font-size:22px;color:#111827;font-weight:800;margin:0 0 8px}.hero-copy h2{font-size:15px;margin:0 0 8px}.hero-copy>span{color:var(--muted);font-size:13px}.hero-visual{position:absolute;width:290px;height:170px;right:8px;top:0}.hero-visual>div{position:absolute;right:78px;top:38px;width:72px;height:78px;border-radius:17px;display:grid;place-items:center;color:white;font-weight:900;font-size:26px;background:linear-gradient(145deg,#5f9eff,#2459e8);box-shadow:0 18px 40px rgba(39,94,221,.3);transform:rotateY(-12deg)}.hero-visual:before,.hero-visual:after{content:'';position:absolute;border:1px solid rgba(81,128,230,.25);border-radius:50%;right:22px;top:20px}.hero-visual:before{width:220px;height:130px}.hero-visual:after{width:180px;height:105px;right:42px;top:33px}.hero-visual i{position:absolute;width:16px;height:16px;border-radius:5px;background:#7aaaff;box-shadow:0 6px 14px rgba(60,105,220,.2)}.hero-visual i:nth-child(1){right:235px;top:70px}.hero-visual i:nth-child(2){right:28px;top:92px}.hero-visual i:nth-child(3){right:180px;top:22px}.hero-metrics{position:absolute;z-index:3;left:24px;right:24px;bottom:14px;display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}.hero-metrics button{border:1px solid rgba(222,231,247,.9);background:rgba(255,255,255,.91);border-radius:11px;padding:11px 13px;text-align:left;cursor:pointer}.hero-metrics span,.hero-metrics strong,.hero-metrics small{display:block}.hero-metrics span{font-size:11px;color:#69758b}.hero-metrics strong{font-size:21px;margin:3px 0}.hero-metrics small{font-size:10px;color:#748198;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.content-grid{display:grid;grid-template-columns:1.1fr .9fr;gap:16px}.diagnosis-body{display:grid;grid-template-columns:1fr 190px;align-items:center}.gaps{display:grid;gap:8px}.gaps>button{border:0;background:#f7f9fd;border-radius:8px;padding:8px;display:flex;align-items:center;justify-content:space-between;cursor:pointer;text-align:left}.gaps>p{color:var(--muted);font-size:12px}.phase-rail{display:flex;align-items:start;justify-content:space-between;position:relative;margin:24px 0}.phase-rail:before{content:'';position:absolute;left:8%;right:8%;top:15px;border-top:2px solid #d9e2f2}.phase-rail>div{z-index:1;text-align:center;flex:1}.phase-rail span,.phase-rail b{display:block}.phase-rail span{width:30px;height:30px;margin:auto;border-radius:50%;display:grid;place-items:center;background:#b8c2d7;color:white}.phase-rail .active span,.phase-rail .done span{background:#2866ed}.phase-rail b{font-size:11px;margin-top:7px}.current-task{padding:13px;border-radius:11px;background:#f6f9ff}.current-task>div small,.current-task>div b{display:block}.current-task>div small{color:var(--muted)}.current-task>div b{font-size:12px;margin:4px 0 8px}.current-task .el-button{width:100%;margin-top:8px}.resource-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.resource-grid button{border:1px solid var(--line);background:#fbfcff;border-radius:11px;padding:13px;display:grid;grid-template-columns:38px 1fr auto;gap:10px;align-items:center;text-align:left;cursor:pointer}.resource-grid i{width:36px;height:36px;border-radius:9px;display:grid;place-items:center;color:white;font-style:normal}.blue{background:#3679ef}.green{background:#24bd88}.purple{background:#865fea}.orange{background:#f59443}.resource-grid b,.resource-grid span{display:block}.resource-grid span{font-size:10px;color:var(--muted);margin-top:4px}.resource-grid strong{font-size:12px;color:#3168ee}.chart-grid{display:grid;grid-template-columns:1.2fr .8fr;gap:12px}.dashboard-rail .panel{padding:16px}.dashboard-rail .panel-title{margin-bottom:10px}.dashboard-rail .panel-title h3{font-size:15px}.agent-status>button,.latest>button{width:100%;border:0;background:transparent;display:grid;grid-template-columns:38px 1fr auto;gap:9px;align-items:center;padding:9px 0;border-bottom:1px solid #edf1f7;text-align:left;cursor:pointer}.agent-status>button>i{width:34px;height:34px;border-radius:10px;display:grid;place-items:center;background:#edf3ff;color:#3168ee;font-style:normal;font-size:10px;font-weight:800}.agent-status button b,.agent-status button span,.latest button b,.latest button span{display:block}.agent-status button b,.latest button b{font-size:12px}.agent-status button span,.latest button span{font-size:10px;color:var(--muted);margin-top:3px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:175px}.agent-status footer{font-size:11px;color:#17a673;margin-top:11px}.agent-status footer span{display:inline-block;width:7px;height:7px;border-radius:50%;background:#17a673;margin-right:7px}.latest>button>i{width:30px;height:30px;border-radius:9px;display:grid;place-items:center;background:#edf3ff;color:#3168ee;font-style:normal;font-size:18px}.latest small{font-size:9px;color:var(--muted);white-space:nowrap}.quick-actions>button{width:100%;border:1px solid var(--line);background:#fbfcff;border-radius:10px;padding:11px;margin-top:8px;display:grid;grid-template-columns:30px 1fr auto;align-items:center;gap:8px;text-align:left;cursor:pointer}.quick-actions>button>span{width:28px;height:28px;border-radius:8px;display:grid;place-items:center;background:#edf3ff;color:#3168ee;font-size:10px}.quick-actions b,.quick-actions small{display:block}.quick-actions b{font-size:12px}.quick-actions small{font-size:10px;color:var(--muted);margin-top:3px}.compact{padding:18px}@media(max-width:1250px){.dashboard-layout{grid-template-columns:1fr}.dashboard-rail{grid-template-columns:repeat(3,1fr)}.content-grid{grid-template-columns:1fr}.resource-grid{grid-template-columns:repeat(2,1fr)}}@media(max-width:800px){.dashboard-rail,.chart-grid{grid-template-columns:1fr}.hero-visual{display:none}.hero-metrics{position:relative;left:auto;right:auto;bottom:auto;margin-top:28px;grid-template-columns:repeat(2,1fr)}.diagnosis-body{grid-template-columns:1fr}.resource-grid{grid-template-columns:1fr}}
.dashboard-state{min-height:520px}.first-use{min-height:560px;display:grid;grid-template-columns:1.15fr .85fr;gap:60px;align-items:center;padding:54px;background:radial-gradient(circle at 85% 20%,#dfeaff,transparent 38%),linear-gradient(135deg,#fff,#f3f7ff)}.state-label{color:#2a62df;font-size:12px;font-weight:800;letter-spacing:.08em}.first-copy h2,.decision-main h2{font-size:32px;line-height:1.35;margin:10px 0}.first-copy>p,.decision-main>p{font-size:15px;line-height:1.9;color:#65738b;max-width:700px}.first-copy .el-button{margin-top:14px}.first-copy>small{display:block;color:#8190a6;margin-top:13px}.first-flow{display:grid;gap:12px}.first-flow>div{display:grid;grid-template-columns:45px 1fr;gap:13px;align-items:center;padding:17px;border:1px solid #dce6f8;border-radius:15px;background:rgba(255,255,255,.88)}.first-flow i{width:43px;height:43px;border-radius:13px;display:grid;place-items:center;background:#2e66e8;color:white;font-style:normal;font-weight:800}.first-flow p,.first-flow b,.first-flow span{display:block;margin:0}.first-flow span{font-size:11px;color:var(--muted);margin-top:4px}.decision-state{display:grid;grid-template-columns:1fr 330px;gap:18px;align-items:start}.decision-main{padding:34px;background:linear-gradient(135deg,#fff,#f5f8ff)}.profile-facts{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:24px 0}.profile-facts>div{padding:15px;border:1px solid var(--line);border-radius:12px;background:white}.profile-facts span,.profile-facts b,.profile-facts small{display:block}.profile-facts span,.profile-facts small{font-size:11px;color:var(--muted)}.profile-facts b{font-size:18px;margin:6px 0}.evidence-rule h3{margin-top:0}.evidence-rule p,.evidence-rule li{font-size:12px;line-height:1.75;color:#65738a}.evidence-rule ul{padding-left:20px}@media(max-width:900px){.first-use,.decision-state{grid-template-columns:1fr}.first-use{padding:28px}.first-copy h2,.decision-main h2{font-size:25px}.profile-facts{grid-template-columns:1fr}}
</style>
