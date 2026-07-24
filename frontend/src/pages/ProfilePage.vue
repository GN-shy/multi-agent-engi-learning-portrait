<template>
  <AppShell>
    <div class="grid two profile-layout">
      <section class="panel">
        <div class="panel-title"><div><h3>画像证据输入</h3><p>先用自评启动，后续由测试与项目证据自动校准</p></div></div>
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
            <div><b>{{ skill.name }}</b><span>{{ skill.description }}</span></div>
            <el-slider v-model="form.self_assessment[skill.code]" :step="5" show-input />
          </div>
          <el-alert title="自评只占较低权重；诊断、测试和实操证据会逐步替换主观分数。" type="info" :closable="false" show-icon />
          <el-button class="analyze" type="primary" :loading="saving" @click="analyze">分析并保存画像</el-button>
        </el-form>
      </section>

      <div class="result-column">
        <section class="panel score-panel">
          <div class="score-ring"><strong>{{ profile?.comprehensive_score || 0 }}</strong><span>综合能力</span></div>
          <div><h2>{{ levelText }}</h2><p class="muted">画像版本 v{{ profile?.version || 0 }} · 每次有效证据都会产生新版本</p><div class="tag-row"><el-tag v-for="item in profile?.strengths || []" :key="item.skill_code" type="success">{{ item.name }} {{ item.score }}</el-tag></div></div>
        </section>
        <section class="panel chart-panel"><div class="panel-title"><div><h3>六维计算机能力</h3><p>点击图形可查看具体数据</p></div></div><EChart :option="radarOption" height="340px" @click="openDetail('画像图表数据',$event)" /></section>
        <section class="panel"><div class="panel-title"><div><h3>关键盲区</h3><p>低于路线目标阈值的优先能力</p></div></div>
          <div v-if="profile?.blind_spots?.length" class="blind-list"><button v-for="item in profile.blind_spots" :key="item.skill_code" @click="openDetail(item.name,item)"><span>{{ item.name }}</span><el-progress :percentage="item.score" :stroke-width="7" /><b>{{ item.score }}</b></button></div>
          <div v-else class="empty">完成首次分析后显示</div>
        </section>
      </div>
    </div>
    <DetailModal v-model="detail.visible" :title="detail.title"><pre>{{ JSON.stringify(detail.data,null,2) }}</pre></DetailModal>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import AppShell from '@/components/layout/AppShell.vue';import DetailModal from '@/components/common/DetailModal.vue';import EChart from '@/components/common/EChart.vue'
import { getData, putData } from '@/api';import type { Profile } from '@/types/domain'
const profile=ref<Profile|null>(null),saving=ref(false),detail=reactive({visible:false,title:'',data:null as any})
const coreSkills=[
  {code:'core.programming',name:'程序设计',description:'编码、调试与抽象'},
  {code:'core.data_structures',name:'数据结构与算法',description:'结构选择与复杂度'},
  {code:'core.os',name:'操作系统',description:'进程、内存与并发'},
  {code:'core.network',name:'计算机网络',description:'TCP/IP、HTTP 与定位'},
  {code:'core.database',name:'数据库',description:'SQL、索引与事务'},
  {code:'core.software_engineering',name:'软件工程',description:'需求、测试与交付'},
  {code:'core.linux',name:'Linux',description:'命令行、服务与日志'},
  {code:'core.git',name:'Git 协作',description:'版本管理与评审'},
]
const form=reactive<any>({background:'',learning_goals:[],preferences:[],weekly_hours:8,learning_style:'balanced',self_assessment:Object.fromEntries(coreSkills.map(s=>[s.code,30])),diagnostic_results:{}})
const levelText=computed(()=>{const s=profile.value?.comprehensive_score||0;return s>=75?'可独立交付':s>=55?'具备项目基础':s>=30?'正在建立底座':'等待更多证据'})
const radarOption=computed(()=>({tooltip:{},radar:{indicator:Object.keys(profile.value?.dimension_scores||{}).map(name=>({name:label(name),max:100})),radius:'64%'},series:[{type:'radar',data:[{value:Object.values(profile.value?.dimension_scores||{}),areaStyle:{color:'rgba(49,104,238,.22)'},lineStyle:{color:'#3168ee'}}]}]}))
onMounted(load)
async function load(){try{profile.value=await getData<Profile>('/profiles/me');Object.assign(form,{background:profile.value.background,learning_goals:profile.value.learning_goals,preferences:profile.value.preferences,weekly_hours:profile.value.weekly_hours,learning_style:profile.value.learning_style});for(const skill of coreSkills)form.self_assessment[skill.code]=profile.value.skill_scores[skill.code]||30}catch{}}
async function analyze(){saving.value=true;try{profile.value=await putData<Profile>('/profiles/me/analyze',form);ElMessage.success('画像已保存，路线比较将使用新版本')}finally{saving.value=false}}
function openDetail(title:string,data:any){detail.title=title;detail.data=data;detail.visible=true}
function label(key:string){return ({programming_and_algorithms:'编程与算法',systems_foundation:'系统基础',software_engineering:'软件工程',architecture_and_security:'架构与安全',engineering_delivery:'工程交付',route_specific:'方向专项'} as any)[key]||key}
</script>

<style scoped>
.profile-layout{grid-template-columns:minmax(520px,1.05fr) minmax(420px,.95fr)}.result-column{display:grid;gap:18px;align-content:start}.slider-row{display:grid;grid-template-columns:190px 1fr;gap:18px;align-items:center;padding:10px 0;border-bottom:1px solid var(--line)}.slider-row b,.slider-row span{display:block}.slider-row span{font-size:12px;color:var(--muted);margin-top:3px}.analyze{width:100%;height:44px;margin-top:20px}.score-panel{display:flex;align-items:center;gap:24px;background:linear-gradient(120deg,#fff,#eef4ff)}.score-ring{min-width:112px;height:112px;border-radius:50%;display:grid;place-content:center;text-align:center;background:conic-gradient(#3168ee 70%,#e5ebf5 0);position:relative;color:white}.score-ring:before{content:'';position:absolute;inset:9px;background:#3168ee;border-radius:50%}.score-ring strong,.score-ring span{position:relative}.score-ring strong{font-size:30px}.score-ring span{font-size:11px}.blind-list{display:grid;gap:8px}.blind-list button{border:0;background:#f7f9fd;border-radius:12px;padding:12px;display:grid;grid-template-columns:140px 1fr 34px;gap:12px;align-items:center;text-align:left;cursor:pointer}pre{white-space:pre-wrap;background:#f7f9fd;padding:16px;border-radius:12px}@media(max-width:1050px){.profile-layout{grid-template-columns:1fr}}@media(max-width:650px){.slider-row{grid-template-columns:1fr}}
</style>
