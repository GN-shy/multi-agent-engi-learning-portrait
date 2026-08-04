<template>
  <AppShell>
    <section class="profile-banner panel">
      <div class="identity">
        <el-avatar :size="76" :src="user.current?.avatar">{{ user.displayName[0] }}</el-avatar>
        <div><div class="name-row"><h2>{{ user.displayName }}</h2><el-tag>画像 V{{ profile?.version || 0 }}</el-tag></div><p>{{ profile?.background || '补充你的学习背景，让诊断更准确' }}</p><span>学习方式：{{ valueLabel(profile?.learning_style) }} · 每周投入 {{ profile?.weekly_hours || form.weekly_hours }} 小时</span></div>
      </div>
      <div class="banner-stats">
        <div><span>综合能力</span><strong>{{ profile?.comprehensive_score || 0 }}</strong><small>{{ levelText }}</small></div>
        <div><span>优势能力</span><strong>{{ profile?.strengths?.length || 0 }}</strong><small>来自有效证据</small></div>
        <div><span>待补盲区</span><strong>{{ profile?.blind_spots?.length || 0 }}</strong><small>按目标阈值排序</small></div>
        <div class="level"><span>当前阶段</span><strong>{{ levelText }}</strong><small>随新证据动态变化</small></div>
      </div>
      <el-button type="primary" @click="editorVisible=true">更新画像证据</el-button>
    </section>

    <section v-if="profile?.analysis_summary" class="panel interpretation">
      <div class="interpret-title">
        <span class="interpret-icon">析</span>
        <div><h3>画像解读</h3><p>{{ profile.analysis_summary.overview }}</p></div>
      </div>
      <div class="interpret-metrics">
        <p><span>当前优势</span><b>{{ label(profile.analysis_summary.strongest_dimension.code) }} · {{ profile.analysis_summary.strongest_dimension.score }} 分</b></p>
        <p><span>优先补齐</span><b>{{ label(profile.analysis_summary.weakest_dimension.code) }} · {{ profile.analysis_summary.weakest_dimension.score }} 分</b></p>
        <p><span>可信程度</span><b>{{ profile.analysis_summary.confidence_level }} · {{ profile.analysis_summary.evidence_count }} 项证据</b></p>
      </div>
      <ul><li v-for="action in profile.analysis_summary.next_actions" :key="action">{{ action }}</li></ul>
    </section>

    <div class="profile-grid">
      <main>
        <div class="analysis-grid">
          <section class="panel radar-card">
            <div class="panel-title"><div><h3>六维能力雷达图</h3><p>当前水平由自评、测评和项目证据融合</p></div></div>
            <EChart :option="radarOption" height="360px" @click="openDetail('画像图表数据',$event)" />
            <div class="score-summary"><span>能力综合得分：<b>{{ profile?.comprehensive_score || 0 }}</b> /100</span><span>画像可信度会随客观证据增加</span></div>
          </section>

          <div class="middle-column">
            <section class="panel">
              <div class="panel-title"><div><h3>技能掌握情况</h3><p>点击技能查看证据详情</p></div><el-button text @click="router.push('/skills')">查看图谱 →</el-button></div>
              <div class="skill-matrix">
                <button v-for="skill in coreSkills" :key="skill.code" :class="skillLevel(profile?.skill_scores?.[skill.code])" @click="openDetail(skill.name,{name:skill.name,description:skill.description,score:profile?.skill_scores?.[skill.code]||0})">
                  <span>{{ skill.name }}</span><b>{{ levelLabel(profile?.skill_scores?.[skill.code]) }}</b>
                </button>
              </div>
            </section>

            <section class="panel maturity">
              <div class="panel-title"><div><h3>当前学习水平</h3><p>距离下一阶段还需补齐的证据</p></div></div>
              <div class="level-line"><span v-for="(name,index) in ['初学者','探索者','应用者','进阶探索者','精通者']" :key="name" :class="{active:index===levelIndex}">{{ name }}</span></div>
              <div class="level-progress"><el-progress :percentage="profile?.comprehensive_score || 0" :show-text="false" /><strong>{{ levelText }}</strong></div>
            </section>
          </div>
        </div>

        <div class="bottom-grid">
          <section class="panel">
            <div class="panel-title"><div><h3>知识掌握强弱分布</h3><p>基于当前路线目标阈值</p></div></div>
            <div class="strength-groups">
              <div><el-tag type="success">优势领域</el-tag><button v-for="item in profile?.strengths||[]" :key="item.skill_code" @click="openDetail(item.name,item)"><span>{{ item.name }}</span><el-progress :percentage="item.score" :show-text="false" /><b>{{ item.score }}%</b></button><p v-if="!profile?.strengths?.length">暂无稳定优势证据</p></div>
              <div><el-tag type="warning">待提升领域</el-tag><button v-for="item in profile?.blind_spots?.slice(0,4)||[]" :key="item.skill_code" @click="openDetail(item.name,item)"><span>{{ item.name }}</span><el-progress :percentage="item.score" :show-text="false" color="#f08b4f" /><b>{{ item.score }}%</b></button><p v-if="!profile?.blind_spots?.length">暂无明显盲区</p></div>
            </div>
          </section>
          <section class="panel preferences">
            <div class="panel-title"><div><h3>学习偏好</h3><p>用于生成策略与难度适配</p></div></div>
            <div class="preference-ring"><el-progress type="dashboard" :percentage="preferencePercent" :width="128"><template #default><b>{{ valueLabel(profile?.learning_style) }}</b></template></el-progress></div>
            <div class="tag-row"><el-tag v-for="item in profile?.preferences||[]" :key="item">{{ item }}</el-tag></div>
          </section>
          <section class="panel recent-evidence">
            <div class="panel-title"><div><h3>画像形成依据</h3><p>不只依赖一次自评</p></div></div>
            <div><span>01</span><p><b>背景与目标</b>专业经历、目标岗位和兴趣关键词</p></div>
            <div><span>02</span><p><b>分阶测评</b>行动、验证、边界和取舍四维评分</p></div>
            <div><span>03</span><p><b>项目实操</b>步骤关联的代码、测试与部署证据</p></div>
          </section>
        </div>
      </main>

      <aside class="profile-rail">
        <section class="panel recommendations">
          <div class="panel-title"><div><h3>个性化学习建议</h3><p>基于当前画像实时生成</p></div></div>
          <article>
            <header><span>优先提升领域</span><el-tag type="danger">重点关注</el-tag></header>
            <ul><li v-for="item in profile?.blind_spots?.slice(0,3)||[]" :key="item.skill_code"><b>{{ item.name }}</b> · 当前 {{ item.score }} 分</li></ul>
            <p v-if="!profile?.blind_spots?.length">先完成一次画像分析，系统将识别优先盲区。</p>
            <el-button plain type="primary" @click="router.push('/tracks')">比较适合的方向 →</el-button>
          </article>
          <article><header><span>下一步学习路径</span></header><p>{{ profile?.learning_goals?.[0] || '先建立学习目标，再生成个性化路径。' }}</p><el-button plain type="primary" @click="router.push('/generate')">生成学习闭环 →</el-button></article>
          <article><header><span>证据补强建议</span></header><p>完成一次项目实操并提交测试或代码证据，可以显著降低画像对主观自评的依赖。</p><el-button plain type="primary" @click="router.push('/practice')">进入项目实操 →</el-button></article>
        </section>
      </aside>
    </div>

    <el-dialog v-model="editorVisible" title="更新画像证据" width="min(820px,92vw)" class="profile-editor">
      <el-steps :active="profile ? 2 : 0" simple class="onboarding-steps">
        <el-step title="填写背景" />
        <el-step title="能力自评" />
        <el-step title="获得解读" />
      </el-steps>
      <el-alert v-if="!profile" title="首次画像只需 3–5 分钟：先填写真实背景和目标，再按当前实际能力自评；后续测评与项目证据会自动修正分数。" type="success" :closable="false" show-icon />
      <el-form label-position="top">
        <el-form-item label="学习背景"><el-input v-model="form.background" type="textarea" :rows="3" placeholder="专业、年级、做过的项目、常用语言…" /></el-form-item>
        <div class="grid two">
          <el-form-item label="每周可投入时间"><el-input-number v-model="form.weekly_hours" :min="1" :max="80" /> 小时</el-form-item>
          <el-form-item label="偏好方式"><el-select v-model="form.learning_style"><el-option label="理论先行" value="theory_first" /><el-option label="实操先行" value="practice_first" /><el-option label="均衡" value="balanced" /></el-select></el-form-item>
        </div>
        <el-form-item label="学习目标"><el-select v-model="form.learning_goals" multiple filterable allow-create default-first-option placeholder="例如：成为 Agent 全栈工程师" /></el-form-item>
        <el-form-item label="兴趣关键词"><el-select v-model="form.preferences" multiple filterable allow-create default-first-option placeholder="例如：后端、LLM、嵌入式" /></el-form-item>
        <h4>通用能力自评</h4>
        <div v-for="skill in coreSkills" :key="skill.code" class="slider-row">
          <div><b>{{ skill.name }}</b><span>{{ skill.description }}</span></div><el-slider v-model="form.self_assessment[skill.code]" :step="5" show-input />
        </div>
        <el-alert title="自评只占较低权重；诊断、测评和实操证据会逐步替换主观分数。" type="info" :closable="false" show-icon />
      </el-form>
      <template #footer><el-button @click="editorVisible=false">取消</el-button><el-button type="primary" :loading="saving" @click="analyze">分析并保存画像</el-button></template>
    </el-dialog>
    <DetailModal v-model="detail.visible" :title="detail.title"><HumanDetail :value="detail.data" /></DetailModal>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import AppShell from '@/components/layout/AppShell.vue'
import DetailModal from '@/components/common/DetailModal.vue'
import EChart from '@/components/common/EChart.vue'
import HumanDetail from '@/components/common/HumanDetail.vue'
import { getData, putData } from '@/api'
import { useUserStore } from '@/stores/user'
import { valueLabel } from '@/utils/presentation'
import type { Profile } from '@/types/domain'

const router=useRouter(),user=useUserStore(),profile=ref<Profile|null>(null),saving=ref(false),editorVisible=ref(false),detail=reactive({visible:false,title:'',data:null as any})
const coreSkills=[
  {code:'core.programming',name:'程序设计',description:'编码、调试与抽象'},{code:'core.data_structures',name:'数据结构与算法',description:'结构选择与复杂度'},
  {code:'core.os',name:'操作系统',description:'进程、内存与并发'},{code:'core.network',name:'计算机网络',description:'TCP/IP、HTTP 与定位'},
  {code:'core.database',name:'数据库',description:'SQL、索引与事务'},{code:'core.software_engineering',name:'软件工程',description:'需求、测试与交付'},
  {code:'core.linux',name:'Linux',description:'命令行、服务与日志'},{code:'core.git',name:'Git 协作',description:'版本管理与评审'},
]
const form=reactive<any>({background:'',learning_goals:[],preferences:[],weekly_hours:8,learning_style:'balanced',self_assessment:Object.fromEntries(coreSkills.map(s=>[s.code,30])),diagnostic_results:{}})
const levelText=computed(()=>{const s=profile.value?.comprehensive_score||0;return s>=80?'精通者':s>=65?'进阶探索者':s>=50?'应用者':s>=30?'探索者':'初学者'})
const levelIndex=computed(()=>Math.min(4,Math.floor((profile.value?.comprehensive_score||0)/20)))
const preferencePercent=computed(() => ({theory_first:35,balanced:55,practice_first:75} as Record<string,number>)[profile.value?.learning_style||'balanced'])
const radarOption=computed(()=>({tooltip:{},radar:{indicator:Object.keys(profile.value?.dimension_scores||{}).map(name=>({name:label(name),max:100})),radius:'61%',splitArea:{areaStyle:{color:['#fbfcff','#f1f5ff']}},axisName:{fontSize:11}},series:[{type:'radar',data:[{value:Object.values(profile.value?.dimension_scores||{}),areaStyle:{color:'rgba(49,104,238,.2)'},lineStyle:{color:'#3168ee',width:2}}]}]}))

onMounted(load)
async function load(){try{profile.value=await getData<Profile>('/profiles/me');Object.assign(form,{background:profile.value.background,learning_goals:profile.value.learning_goals,preferences:profile.value.preferences,weekly_hours:profile.value.weekly_hours,learning_style:profile.value.learning_style});for(const skill of coreSkills)form.self_assessment[skill.code]=profile.value.skill_scores[skill.code]||30}catch{editorVisible.value=true}}
async function analyze(){saving.value=true;try{profile.value=await putData<Profile>('/profiles/me/analyze',form);editorVisible.value=false;ElMessage.success('画像已保存，路线比较将使用新版本')}finally{saving.value=false}}
function openDetail(title:string,data:any){detail.title=title;detail.data=data;detail.visible=true}
function label(key:string){return ({programming_and_algorithms:'编程与算法',systems_foundation:'系统基础',software_engineering:'软件工程',architecture_and_security:'架构与安全',engineering_delivery:'工程交付',route_specific:'方向专项'} as Record<string,string>)[key]||key}
function skillLevel(score=0){return score>=70?'mastered':score>=45?'growing':'starter'}
function levelLabel(score=0){return score>=70?'熟练':score>=45?'掌握':'入门'}
</script>

<style scoped>
.profile-banner{display:grid;grid-template-columns:minmax(360px,1.2fr) 1fr auto;gap:24px;align-items:center;background:linear-gradient(115deg,#fff,#f0f5ff)}.identity{display:flex;gap:17px;align-items:center}.name-row{display:flex;gap:10px;align-items:center}.name-row h2{margin:0}.identity p{margin:7px 0;color:#4e5b70}.identity span{font-size:11px;color:var(--muted)}.banner-stats{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}.banner-stats>div{padding:12px;border-left:1px solid var(--line)}.banner-stats span,.banner-stats strong,.banner-stats small{display:block}.banner-stats span,.banner-stats small{font-size:10px;color:var(--muted)}.banner-stats strong{font-size:22px;color:#2461e3;margin:3px 0}.banner-stats .level strong{font-size:14px}.profile-grid{display:grid;grid-template-columns:minmax(0,1fr) 310px;gap:16px;margin-top:16px}.profile-grid>main{display:grid;gap:16px}.analysis-grid{display:grid;grid-template-columns:.9fr 1.1fr;gap:16px}.middle-column{display:grid;gap:16px}.score-summary{display:flex;justify-content:space-between;padding:13px;background:#f6f9ff;border-radius:10px;font-size:12px;color:var(--muted)}.score-summary b{font-size:20px;color:#3168ee}.skill-matrix{display:grid;grid-template-columns:repeat(3,1fr);gap:9px}.skill-matrix button{border:1px solid var(--line);border-radius:9px;background:#f8faff;padding:10px;display:flex;justify-content:space-between;cursor:pointer}.skill-matrix span,.skill-matrix b{font-size:11px}.skill-matrix.mastered{border-color:#bce7d7;background:#f1fbf7;color:#16815d}.skill-matrix.growing{border-color:#cddcff;background:#f2f6ff;color:#2862dc}.skill-matrix.starter{border-color:#f3d1bc;background:#fff6ef;color:#c76737}.level-line{display:flex;justify-content:space-between;position:relative}.level-line:before{content:'';position:absolute;top:8px;left:4%;right:4%;border-top:2px solid #d8e1f0}.level-line span{z-index:1;padding-top:23px;font-size:10px;color:var(--muted);position:relative}.level-line span:before{content:'';position:absolute;width:13px;height:13px;border-radius:50%;background:#b7c2d8;top:2px;left:50%;transform:translateX(-50%)}.level-line span.active{color:#3168ee;font-weight:700}.level-line span.active:before{background:#3168ee;box-shadow:0 0 0 5px #e8efff}.level-progress{display:flex;gap:12px;align-items:center;margin-top:18px}.level-progress .el-progress{flex:1}.level-progress strong{font-size:12px;color:#3168ee}.bottom-grid{display:grid;grid-template-columns:1.1fr .7fr .8fr;gap:16px}.strength-groups{display:grid;grid-template-columns:repeat(2,1fr);gap:15px}.strength-groups>div{display:grid;gap:7px}.strength-groups button{display:grid;grid-template-columns:95px 1fr 36px;gap:7px;align-items:center;border:0;background:transparent;text-align:left;cursor:pointer;font-size:11px}.strength-groups p{font-size:11px;color:var(--muted)}.preference-ring{text-align:center}.preferences .tag-row{justify-content:center}.recent-evidence>div:not(.panel-title){display:grid;grid-template-columns:28px 1fr;gap:8px}.recent-evidence>div>span{width:25px;height:25px;border-radius:8px;display:grid;place-items:center;background:#edf3ff;color:#3168ee;font-size:9px}.recent-evidence p{margin:0 0 12px;font-size:10px;color:var(--muted)}.recent-evidence p b{display:block;font-size:12px;color:var(--text);margin-bottom:3px}.profile-rail{display:grid;align-content:start}.recommendations article{border:1px solid var(--line);border-radius:11px;padding:13px;margin-top:10px}.recommendations article header{display:flex;align-items:center;justify-content:space-between}.recommendations article header span{font-weight:700;font-size:12px}.recommendations article p,.recommendations article li{font-size:11px;line-height:1.7;color:#59667b}.recommendations article .el-button{width:100%}.slider-row{display:grid;grid-template-columns:190px 1fr;gap:18px;align-items:center;padding:9px 0;border-bottom:1px solid var(--line)}.slider-row b,.slider-row span{display:block}.slider-row span{font-size:11px;color:var(--muted);margin-top:3px}@media(max-width:1250px){.profile-banner{grid-template-columns:1fr auto}.banner-stats{grid-row:2;grid-column:1/-1}.profile-grid{grid-template-columns:1fr}.recommendations{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.recommendations>.panel-title{grid-column:1/-1}}@media(max-width:900px){.analysis-grid,.bottom-grid{grid-template-columns:1fr}.recommendations{display:block}}@media(max-width:650px){.profile-banner{grid-template-columns:1fr}.banner-stats{grid-template-columns:repeat(2,1fr)}.skill-matrix{grid-template-columns:repeat(2,1fr)}.strength-groups{grid-template-columns:1fr}.slider-row{grid-template-columns:1fr}}
.skill-matrix button.mastered{border-color:#bce7d7;background:#f1fbf7;color:#16815d}.skill-matrix button.growing{border-color:#cddcff;background:#f2f6ff;color:#2862dc}.skill-matrix button.starter{border-color:#f3d1bc;background:#fff6ef;color:#c76737}
.interpretation{margin-top:16px;display:grid;grid-template-columns:1.1fr 1.3fr 1.2fr;gap:18px;align-items:center;background:linear-gradient(120deg,#f8fbff,#fff)}.interpret-title{display:flex;gap:12px;align-items:center}.interpretation h3,.interpretation p{margin:3px 0}.interpretation p,.interpretation li{font-size:11px;line-height:1.65;color:var(--muted)}.interpret-icon{width:42px;height:42px;border-radius:13px;background:#3168ee;color:white;display:grid;place-items:center;font-weight:800}.interpret-metrics{display:grid;gap:7px}.interpret-metrics p{margin:0;padding:8px 10px;border-radius:9px;background:#f4f7fd}.interpret-metrics span,.interpret-metrics b{display:block}.interpret-metrics b{color:#35445e;margin-top:3px}.interpretation ul{margin:0;padding-left:18px}@media(max-width:900px){.interpretation{grid-template-columns:1fr}}
.onboarding-steps{margin-bottom:14px}.profile-editor .el-alert{margin-bottom:16px}
</style>
