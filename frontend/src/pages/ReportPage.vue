<template>
  <AppShell>
    <div v-loading="loading">
      <section class="report-hero panel"><div><span>画像版本 v{{ report.profile_version }}</span><h2>{{ user.displayName }} 的计算机能力成长报告</h2><p>路线适配、知识盲区、能力趋势与生成质量都来自可追溯证据。</p></div><div class="report-score"><strong>{{ report.comprehensive_score || 0 }}</strong><span>综合能力</span></div><el-button type="primary" :loading="printing" @click="printReport">打印 / 保存 PDF</el-button></section>
      <div class="grid two section">
        <section class="panel"><div class="panel-title"><div><h3>六维能力</h3><p>点击图表查看指标详情</p></div></div><EChart :option="radarOption" height="350px" @click="open('能力指标',$event)" /></section>
        <section class="panel"><div class="panel-title"><div><h3>测试趋势</h3><p>测试证据会更新画像版本</p></div></div><EChart :option="trendOption" height="350px" @click="open('测试记录',$event)" /></section>
      </div>
      <div class="grid two section">
        <section class="panel"><div class="panel-title"><div><h3>路线决策</h3><p>推荐依据与时间成本</p></div></div><template v-if="report.route?.track_name"><h2>{{ report.route.track_name }}</h2><el-progress :percentage="report.route.score" /><p v-for="reason in report.route.why" :key="reason">✓ {{ reason }}</p><el-button plain type="primary" @click="open('完整路线依据',report.route)">展开详情</el-button></template><div v-else class="empty">尚未选择路线</div></section>
        <section class="panel"><div class="panel-title"><div><h3>可信生成质量</h3><p>竞赛指标可直接核验</p></div></div><div class="quality"><button v-for="(value,key) in report.quality_metrics||{}" :key="key" @click="open(label(String(key)),{key,value})"><span>{{ label(String(key)) }}</span><strong>{{ format(String(key),value) }}</strong></button></div></section>
      </div>
      <section class="panel section"><div class="panel-title"><div><h3>优先补齐的知识盲区</h3><p>按当前路线目标阈值排序</p></div></div><div class="blind-grid"><article v-for="item in report.blind_spots||[]" :key="item.skill_code" class="clickable" @click="open(item.name,item)"><b>{{ item.name }}</b><el-progress :percentage="item.score" /><span>目标 75 · 当前 {{ item.score }}</span></article></div></section>
    </div>
    <DetailModal v-model="detail.visible" :title="detail.title"><HumanDetail :value="detail.data" /></DetailModal>
  </AppShell>
</template>

<script setup lang="ts">
import { computed,onMounted,reactive,ref } from 'vue';import { ElMessage } from 'element-plus'
import AppShell from '@/components/layout/AppShell.vue';import DetailModal from '@/components/common/DetailModal.vue';import EChart from '@/components/common/EChart.vue';import HumanDetail from '@/components/common/HumanDetail.vue';import { api,getData } from '@/api';import { useUserStore } from '@/stores/user'
const user=useUserStore(),report=reactive<any>({}),loading=ref(true),printing=ref(false),detail=reactive({visible:false,title:'',data:null as any})
const radarOption=computed(()=>({tooltip:{},radar:{indicator:Object.keys(report.dimensions||{}).map(k=>({name:label(k),max:100}))},series:[{type:'radar',data:[{value:Object.values(report.dimensions||{}),areaStyle:{color:'rgba(49,104,238,.23)'},lineStyle:{color:'#3168ee'}}]}]}))
const trendOption=computed(()=>({tooltip:{trigger:'axis'},xAxis:{type:'category',data:(report.assessment_trend||[]).map((i:any)=>new Date(i.date).toLocaleDateString())},yAxis:{type:'value',min:0,max:100},series:[{type:'line',smooth:true,data:(report.assessment_trend||[]).map((i:any)=>i.score),lineStyle:{color:'#17a673',width:3},areaStyle:{color:'rgba(23,166,115,.14)'}}]}))
onMounted(async()=>{try{Object.assign(report,await getData('/reports/latest'))}finally{loading.value=false}})
async function printReport(){printing.value=true;try{const response=await api.get('/reports/latest/print',{responseType:'blob'});const url=URL.createObjectURL(response.data);window.open(url,'_blank','width=980,height=760');setTimeout(()=>URL.revokeObjectURL(url),60000)}catch{ElMessage.error('报告生成失败')}finally{printing.value=false}}
function open(title:string,data:any){detail.title=title;detail.data=data;detail.visible=true}
function label(key:string){return ({programming_and_algorithms:'编程与算法',systems_foundation:'系统基础',software_engineering:'软件工程',architecture_and_security:'架构与安全',engineering_delivery:'工程交付',route_specific:'方向专项',total:'质量总分',knowledge_coverage:'知识覆盖',citation_coverage:'引用覆盖',citation_integrity:'引用完整性',profile_fit:'画像适配',prerequisite_violations:'前置冲突',hallucination_risk:'未引用风险估计'} as any)[key]||key}
function format(key:string,value:any){return ['knowledge_coverage','citation_coverage','citation_integrity','profile_fit','hallucination_risk'].includes(key)?`${Math.round(Number(value)*100)}%`:value}
</script>

<style scoped>
.report-hero{display:grid;grid-template-columns:1fr 130px auto;gap:26px;align-items:center;background:linear-gradient(120deg,#fff,#edf3ff)}.report-hero h2{margin:8px 0}.report-hero p,.report-hero>div>span{color:var(--muted)}.report-score{text-align:center}.report-score strong,.report-score span{display:block}.report-score strong{font-size:42px;color:#3168ee}.section{margin-top:18px}.quality{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}.quality button{border:1px solid var(--line);background:#f7f9fd;padding:15px;border-radius:14px;cursor:pointer}.quality span,.quality strong{display:block}.quality span{color:var(--muted)}.quality strong{font-size:24px;margin-top:6px}.blind-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.blind-grid article{padding:15px;border:1px solid var(--line);border-radius:14px;transition:.2s}.blind-grid span{font-size:12px;color:var(--muted)}pre{white-space:pre-wrap;background:#f7f9fd;padding:16px;border-radius:12px}@media(max-width:850px){.report-hero{grid-template-columns:1fr}.blind-grid{grid-template-columns:1fr}}
</style>
