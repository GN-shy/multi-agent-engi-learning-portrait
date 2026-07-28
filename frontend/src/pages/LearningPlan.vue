<template>
  <AppShell>
    <section v-if="plan" class="plan-hero panel">
      <div><el-tag>{{ plan.track_name }}</el-tag><h2>{{ plan.goal }}</h2><p>计划版本 v{{ plan.version }} · 打卡和反馈会持续调整路径</p></div>
      <div class="progress"><el-progress type="dashboard" :percentage="plan.progress" :width="120" /></div>
    </section>
    <section v-if="plan" class="timeline">
      <article v-for="phase in plan.phases" :key="phase.id" class="phase panel" :class="phase.status">
        <header><span>{{ phase.week_start }}–{{ phase.week_end }} 周</span><el-tag :type="phase.status==='completed'?'success':phase.status==='active'?'primary':'info'">{{ valueLabel(phase.status) }}</el-tag></header>
        <h3>{{ phase.name }}</h3><p v-if="phase.pathway_names?.length || phase.pathway_name" class="pathway-name">{{ phase.pathway_names?.join(' + ') || phase.pathway_name }}<template v-if="phase.source_duration"> · 原路线周期 {{ phase.source_duration }}</template></p><p>阶段里程碑：{{ phase.milestone }}</p>
        <el-progress :percentage="phase.progress || 0" />
        <div class="tasks">
          <el-checkbox v-for="task in phaseTasks(phase)" :key="task.id" :model-value="checked(taskKey(phase,task))" @change="toggle(taskKey(phase,task),$event)">{{ task.title }}</el-checkbox>
        </div>
        <el-button text @click="openPhase(phase)">查看阶段详情</el-button>
      </article>
    </section>
    <section v-if="plan" class="panel checkin"><div><h3>保存今日进度</h3><p>勾选完成的技能任务，系统计算阶段和总进度。</p></div><el-button type="primary" :loading="saving" @click="save">提交打卡</el-button></section>
    <section v-else class="panel empty"><p>尚未生成学习计划</p><el-button type="primary" @click="router.push('/generate')">生成个性化计划</el-button></section>
    <DetailModal v-model="detail.visible" :title="detail.phase?.name || '阶段详情'"><el-descriptions :column="2" border><el-descriptions-item label="周期">第 {{ detail.phase?.week_start }}–{{ detail.phase?.week_end }} 周</el-descriptions-item><el-descriptions-item label="每周投入">{{ detail.phase?.hours_per_week }} 小时</el-descriptions-item><el-descriptions-item label="生成策略">{{ valueLabel(detail.phase?.strategy) }}</el-descriptions-item><el-descriptions-item label="状态">{{ valueLabel(detail.phase?.status) }}</el-descriptions-item></el-descriptions><h4>阶段学习任务</h4><div class="detail-tasks"><div v-for="task in phaseTasks(detail.phase||{})" :key="task.id"><header><b>{{ task.title }}</b><el-tag v-if="task.pathway_name" size="small" effect="plain">{{ task.pathway_name }}</el-tag></header><p v-if="task.learning_action">{{ task.learning_action }}</p><span v-if="task.evidence_required"><b>提交证据：</b>{{ task.evidence_required }}</span><span v-if="task.acceptance"><b>验收标准：</b>{{ task.acceptance }}</span></div></div><h4>覆盖核心能力</h4><div class="tag-row"><el-tag v-for="skill in detail.phase?.skills||[]" :key="skill">{{ skillLabel(skill) }}</el-tag></div><h4>验收里程碑</h4><p>{{ detail.phase?.milestone }}</p></DetailModal>
  </AppShell>
</template>

<script setup lang="ts">
import { onMounted,reactive,ref } from 'vue';import { useRouter } from 'vue-router';import { ElMessage } from 'element-plus'
import AppShell from '@/components/layout/AppShell.vue';import DetailModal from '@/components/common/DetailModal.vue';import { getData,postData } from '@/api';import { valueLabel } from '@/utils/presentation'
const router=useRouter(),plan=ref<any>(null),selected=ref(new Set<string>()),saving=ref(false),detail=reactive({visible:false,phase:null as any})
onMounted(load)
async function load(){try{plan.value=await getData('/plans/current');const previous=(plan.value.checkins||[]).flatMap((i:any)=>i.completed_task_ids);selected.value=new Set(previous)}catch{plan.value=null;ElMessage.error('学习计划加载失败，请稍后重试')}}
function checked(id:string){return selected.value.has(id)}
function toggle(id:string,value:any){const next=new Set(selected.value);value?next.add(id):next.delete(id);selected.value=next}
async function save(){saving.value=true;try{const result=await postData<any>(`/plans/${plan.value.id}/checkin`,{completed_task_ids:[...selected.value]});plan.value.progress=result.progress;plan.value.phases=result.phases;ElMessage.success('学习进度已保存')}finally{saving.value=false}}
function openPhase(phase:any){detail.phase=phase;detail.visible=true}
function skillLabel(code:string){return code.split('.').pop()?.replace(/_/g,' ') || code}
function phaseTasks(phase:any){return phase.tasks?.length?phase.tasks:(phase.skills||[]).map((skill:string)=>({id:skill,title:skillLabel(skill)}))}
function taskKey(phase:any,task:any){return `${phase.id}:${task.id}`}
</script>

<style scoped>
.plan-hero{display:flex;align-items:center;justify-content:space-between;background:linear-gradient(120deg,#fff,#edf3ff)}.plan-hero h2{font-size:28px;margin:12px 0 8px}.plan-hero p{color:var(--muted)}.timeline{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-top:18px}.phase{position:relative}.phase.active{border-color:#3168ee}.phase.completed{border-color:#8bd6bb}.phase header{display:flex;justify-content:space-between}.phase header>span{color:var(--muted);font-size:12px}.phase p{color:var(--muted);min-height:44px}.phase .pathway-name{min-height:0;color:#3168ee;font-size:12px}.tasks{display:grid;gap:8px;margin:18px 0}.tasks .el-checkbox{margin:0;height:auto;align-items:flex-start}.tasks :deep(.el-checkbox__label){white-space:normal;line-height:1.5}.detail-tasks{display:grid;gap:9px}.detail-tasks>div{padding:12px;border-radius:11px;background:#f6f8fc}.detail-tasks header{display:flex;justify-content:space-between;gap:10px}.detail-tasks p{margin:8px 0;font-size:13px;line-height:1.65;color:#3f4f68}.detail-tasks span{display:block;color:var(--muted);font-size:12px;margin-top:5px;line-height:1.6}.detail-tasks span b{display:inline;color:#40516c}.checkin{margin-top:18px;display:flex;justify-content:space-between;align-items:center}.checkin h3,.checkin p{margin:5px}.checkin p{color:var(--muted)}@media(max-width:1100px){.timeline{grid-template-columns:repeat(2,1fr)}}@media(max-width:650px){.timeline{grid-template-columns:1fr}.plan-hero,.checkin{align-items:flex-start;flex-direction:column;gap:15px}}
</style>
