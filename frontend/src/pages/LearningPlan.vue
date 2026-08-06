<template>
  <AppShell>
    <template v-if="plan">
      <section class="plan-hero panel">
        <div>
          <span class="eyebrow">可执行学习工作台</span>
          <div class="hero-title"><h2>{{ plan.goal }}</h2><el-tag>路线 v{{ plan.version }}</el-tag></div>
          <p>{{ plan.track_name }} · 学习不是勾选目录，而是完成任务并提交可复核成果。</p>
          <div class="target-line" v-if="workspace.target">
            <b>目标岗位：{{ workspace.target.title }}</b>
            <span>{{ workspace.target.company || '公司未填写' }} · {{ workspace.target.city || '城市未填写' }}</span>
            <el-button link type="primary" @click="router.push('/career-target')">更新 JD</el-button>
          </div>
          <el-button v-else type="primary" plain @click="router.push('/career-target')">先粘贴真实 JD，校准学习终点</el-button>
        </div>
        <el-progress type="dashboard" :percentage="plan.progress" :width="124"><template #default><b>{{ plan.progress }}%</b><span>总进度</span></template></el-progress>
      </section>

      <section v-if="pendingRevision" class="revision-alert panel">
        <div><span class="eyebrow">路线调整待确认</span><h3>{{ pendingRevision.reason }}</h3><p>系统只生成建议，确认前不会修改当前路线。</p></div>
        <div class="change-list"><span v-for="change in pendingRevision.changes" :key="change.label">{{ change.label }}</span></div>
        <div class="revision-actions"><el-button @click="openRevision(pendingRevision)">比较版本</el-button><el-button @click="decide(pendingRevision,'reject')">暂不调整</el-button><el-button type="primary" @click="decide(pendingRevision,'accept')">应用 v{{ pendingRevision.to_version }}</el-button></div>
      </section>

      <section class="work-grid">
        <article class="panel weekly-board">
          <header class="section-head"><div><span class="eyebrow">本周执行</span><h3>{{ activePhase?.name || '等待下一阶段' }}</h3></div><el-tag type="success">{{ activeTasks.length }} 个任务</el-tag></header>
          <p class="phase-copy">{{ activePhase?.milestone || '当前路线全部阶段已完成，可以复盘成果或重新校准目标。' }}</p>
          <div v-if="activeTasks.length" class="task-list">
            <article v-for="task in activeTasks" :key="task.id" :class="['task-card',{done:checked(taskKey(activePhase,task))}]">
              <el-checkbox :model-value="checked(taskKey(activePhase,task))" @change="toggle(taskKey(activePhase,task),$event)" />
              <div><div class="task-title"><b>{{ task.title }}</b><el-tag v-if="task.priority==='job_required'" type="danger" size="small">JD 高优先级</el-tag></div><p>{{ task.learning_action || '完成该技能的学习与最小实践。' }}</p><span>验收：{{ task.acceptance || activePhase?.milestone }}</span></div>
              <el-button type="primary" plain @click="openEvidence(activePhase,task)">提交成果</el-button>
            </article>
          </div>
          <el-empty v-else description="暂无待办任务" :image-size="76" />
        </article>

        <aside class="panel checkin-card">
          <span class="eyebrow">学习反馈</span><h3>用真实状态调整路线</h3>
          <el-radio-group v-model="checkin.feedback_type" class="feedback-options">
            <el-radio-button value="normal">进展正常</el-radio-button><el-radio-button value="too_hard">太难</el-radio-button><el-radio-button value="blocked">卡住了</el-radio-button><el-radio-button value="too_easy">太简单</el-radio-button><el-radio-button value="no_time">时间不足</el-radio-button>
          </el-radio-group>
          <el-input-number v-model="checkin.hours_spent" :min="0" :max="80" :step="0.5" /><span class="field-hint">本周实际投入（小时）</span>
          <el-input v-model="checkin.note" type="textarea" :rows="3" maxlength="240" show-word-limit placeholder="说清具体难点、变化或原因，路线调整才有依据" />
          <div v-if="checkin.feedback_type==='no_time'" class="hours-row"><span>以后每周可投入</span><el-input-number v-model="checkin.weekly_hours" :min="1" :max="60" /></div>
          <el-button type="primary" :loading="saving" @click="save">保存本周进展</el-button>
          <p class="safe-note">勾选只保存进度；能力画像必须由测试或成果证据更新。</p>
        </aside>
      </section>

      <section class="panel route-section">
        <el-tabs v-model="activeTab">
          <el-tab-pane label="完整路线" name="route">
            <div class="timeline">
              <article v-for="phase in plan.phases" :key="phase.id" :class="['phase',phase.status]">
                <header><span>第 {{ phase.week_start }}–{{ phase.week_end }} 周</span><el-tag :type="phase.status==='completed'?'success':phase.status==='active'?'primary':'info'">{{ valueLabel(phase.status) }}</el-tag></header>
                <h3>{{ phase.name }}</h3><p class="pathway-name">{{ phase.pathway_names?.join(' + ') || phase.pathway_name || plan.track_name }}</p><p>{{ phase.milestone }}</p>
                <el-progress :percentage="phase.progress || 0" />
                <div class="mini-tasks"><span v-for="task in phaseTasks(phase).slice(0,4)" :key="task.id">{{ task.title }}</span></div>
                <el-button link type="primary" @click="openPhase(phase)">查看任务与验收标准</el-button>
              </article>
            </div>
          </el-tab-pane>
          <el-tab-pane :label="`成果证据 ${workspace.evidence.length}`" name="evidence">
            <div v-if="workspace.evidence.length" class="evidence-list"><article v-for="item in workspace.evidence" :key="item.id"><div><b>{{ evidenceLabel(item.evidence_type) }}</b><span>{{ item.description || item.value }}</span></div><el-tag :type="item.status==='accepted'?'success':'warning'">{{ item.score }} 分 · {{ item.status==='accepted'?'已接收':'需补充' }}</el-tag></article></div>
            <el-empty v-else description="尚未提交成果。完成本周任务后，从任务卡片提交代码、测试或部署证据。" />
          </el-tab-pane>
          <el-tab-pane :label="`路线版本 ${workspace.revisions.length}`" name="versions">
            <div v-if="workspace.revisions.length" class="revision-list"><article v-for="revision in workspace.revisions" :key="revision.id"><div><b>v{{ revision.from_version }} → v{{ revision.to_version }}</b><span>{{ revision.reason }}</span><small>{{ revision.created_at.slice(0,16).replace('T',' ') }}</small></div><el-tag :type="revisionType(revision.status)">{{ revisionLabel(revision.status) }}</el-tag><el-button @click="openRevision(revision)">查看差异</el-button><el-button v-if="revision.status==='accepted'" type="warning" plain @click="decide(revision,'revert')">撤销此版</el-button></article></div>
            <el-empty v-else description="反馈、JD 或成果证据发生变化时，系统会生成可确认的路线版本。" />
          </el-tab-pane>
        </el-tabs>
      </section>
    </template>

    <section v-else class="panel empty"><h3>还没有学习路线</h3><p>先选择方向并生成一条可执行路线。</p><el-button type="primary" @click="router.push('/tracks')">选择方向</el-button></section>

    <DetailModal v-model="detail.visible" :title="detail.phase?.name || '阶段详情'">
      <el-descriptions :column="2" border><el-descriptions-item label="周期">第 {{ detail.phase?.week_start }}–{{ detail.phase?.week_end }} 周</el-descriptions-item><el-descriptions-item label="每周投入">{{ detail.phase?.hours_per_week }} 小时</el-descriptions-item><el-descriptions-item label="状态">{{ valueLabel(detail.phase?.status) }}</el-descriptions-item><el-descriptions-item label="里程碑">{{ detail.phase?.milestone }}</el-descriptions-item></el-descriptions>
      <div class="detail-tasks"><article v-for="task in phaseTasks(detail.phase||{})" :key="task.id"><b>{{ task.title }}</b><p>{{ task.learning_action || '完成该技能的学习与实践。' }}</p><span><strong>成果：</strong>{{ task.evidence_required || '学习记录与最小实践' }}</span><span><strong>验收：</strong>{{ task.acceptance || detail.phase?.milestone }}</span></article></div>
    </DetailModal>

    <el-dialog v-model="evidenceDialog.visible" title="提交任务成果" width="680px" destroy-on-close>
      <div class="submission-head"><span>对应任务</span><b>{{ evidenceDialog.task?.title }}</b><p>{{ evidenceDialog.task?.evidence_required || '至少提交一项可复核成果，并说明它如何满足任务验收标准。' }}</p></div>
      <div class="artifact-editor" v-for="(item,index) in evidenceForm.evidence" :key="index">
        <el-select v-model="item.evidence_type"><el-option v-for="option in evidenceOptions" :key="option.value" :label="option.label" :value="option.value" /></el-select>
        <el-input v-model="item.value" :placeholder="evidencePlaceholder(item.evidence_type)" />
        <el-input v-model="item.description" placeholder="说明成果与验收标准的对应关系（至少 8 个字）" />
        <el-button v-if="evidenceForm.evidence.length>1" link type="danger" @click="evidenceForm.evidence.splice(index,1)">移除</el-button>
      </div>
      <el-button link type="primary" @click="addEvidence">+ 再添加一项证据</el-button>
      <el-input v-model="evidenceForm.reflection" type="textarea" :rows="3" placeholder="复盘：做成了什么、遇到什么问题、下一步是什么" />
      <template #footer><el-button @click="evidenceDialog.visible=false">取消</el-button><el-button type="primary" :loading="submittingEvidence" @click="submitEvidence">提交并校验</el-button></template>
    </el-dialog>

    <el-dialog v-model="revisionDialog.visible" title="路线版本差异" width="760px">
      <template v-if="revisionDialog.item"><el-alert :title="revisionDialog.item.reason" type="info" :closable="false" /><div class="version-compare"><article><span>当前版本 v{{ revisionDialog.item.from_version }}</span><b>{{ phaseCount(revisionDialog.item.old_phases) }} 个阶段 · {{ totalWeeks(revisionDialog.item.old_phases) }} 周</b></article><i>→</i><article><span>建议版本 v{{ revisionDialog.item.to_version }}</span><b>{{ phaseCount(revisionDialog.item.new_phases) }} 个阶段 · {{ totalWeeks(revisionDialog.item.new_phases) }} 周</b></article></div><div class="change-list wide"><span v-for="change in revisionDialog.item.changes" :key="change.label">{{ change.label }}</span></div></template>
      <template #footer><el-button @click="revisionDialog.visible=false">关闭</el-button><template v-if="revisionDialog.item?.status==='pending'"><el-button @click="decide(revisionDialog.item,'reject')">暂不调整</el-button><el-button type="primary" @click="decide(revisionDialog.item,'accept')">确认应用</el-button></template></template>
    </el-dialog>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import AppShell from '@/components/layout/AppShell.vue'
import DetailModal from '@/components/common/DetailModal.vue'
import { getData, postData } from '@/api'
import { valueLabel } from '@/utils/presentation'

const router = useRouter()
const plan = ref<any>(null)
const workspace = reactive<any>({ target:null, evidence:[], revisions:[] })
const selected = ref(new Set<string>())
const saving = ref(false)
const submittingEvidence = ref(false)
const activeTab = ref('route')
const detail = reactive({ visible:false, phase:null as any })
const evidenceDialog = reactive({ visible:false, phase:null as any, task:null as any })
const revisionDialog = reactive({ visible:false, item:null as any })
const checkin = reactive({ feedback_type:'normal', hours_spent:0, note:'', weekly_hours:8 })
const evidenceForm = reactive<any>({ evidence:[], reflection:'' })
const evidenceOptions = [
  {value:'repository',label:'代码仓库链接'},{value:'commit',label:'Git 提交哈希'},{value:'test',label:'测试结果'},{value:'deployment',label:'部署地址'},{value:'document',label:'设计/复盘文档'},{value:'screenshot_note',label:'截图说明'},{value:'note',label:'文字说明'},
]

const activePhase = computed(() => plan.value?.phases?.find((item:any)=>item.status==='active') || plan.value?.phases?.find((item:any)=>item.status!=='completed') || null)
const activeTasks = computed(() => activePhase.value ? phaseTasks(activePhase.value) : [])
const pendingRevision = computed(() => workspace.revisions.find((item:any)=>item.status==='pending'))

onMounted(load)
async function load(){
  try{
    plan.value=await getData('/plans/current')
    const previous=(plan.value.checkins||[]).flatMap((item:any)=>item.completed_task_ids||[])
    selected.value=new Set(previous)
    Object.assign(workspace,await getData(`/plans/${plan.value.id}/workspace`))
    checkin.weekly_hours=activePhase.value?.hours_per_week || 8
  }catch{plan.value=null}
}
function checked(id:string){return selected.value.has(id)}
function toggle(id:string,value:any){const next=new Set(selected.value);value?next.add(id):next.delete(id);selected.value=next}
function phaseTasks(phase:any){return phase.tasks?.length?phase.tasks:(phase.skills||[]).map((skill:string)=>({id:skill,title:skillLabel(skill),skill_code:skill}))}
function taskKey(phase:any,task:any){return `${phase.id}:${task.id}`}
function skillLabel(code:string){return code.split('.').pop()?.replace(/_/g,' ') || code}
function openPhase(phase:any){detail.phase=phase;detail.visible=true}
async function save(){
  saving.value=true
  try{
    const result=await postData<any>(`/plans/${plan.value.id}/checkin`,{completed_task_ids:[...selected.value],feedback_type:checkin.feedback_type,hours_spent:checkin.hours_spent,note:checkin.note})
    plan.value.progress=result.progress;plan.value.phases=result.phases
    if(result.recalibration_recommended){
      const revision=await postData<any>(`/plans/${plan.value.id}/recalibrate`,{trigger:checkin.feedback_type,note:checkin.note,weekly_hours:checkin.feedback_type==='no_time'?checkin.weekly_hours:null})
      workspace.revisions.unshift(revision)
      ElMessage.success('进度已保存，并生成了一份待确认的路线调整建议')
    }else ElMessage.success('本周进展已保存')
    checkin.note=''
  }catch(error:any){ElMessage.error(error?.response?.data?.detail || '保存失败，请稍后重试')}finally{saving.value=false}
}
function openEvidence(phase:any,task:any){evidenceDialog.phase=phase;evidenceDialog.task=task;evidenceForm.evidence=[{evidence_type:'repository',value:'',description:''}];evidenceForm.reflection='';evidenceDialog.visible=true}
function addEvidence(){evidenceForm.evidence.push({evidence_type:'test',value:'',description:''})}
function evidencePlaceholder(type:string){return type==='commit'?'7–40 位 Git 提交哈希':type==='test'?'例如：pytest 42 passed，0 failed':['repository','deployment','document'].includes(type)?'https://...':'填写可复核内容'}
async function submitEvidence(){
  if(evidenceForm.evidence.some((item:any)=>!item.value.trim() || item.description.trim().length<8)) return ElMessage.warning('请填写每项成果，并用至少 8 个字说明与验收标准的关系')
  submittingEvidence.value=true
  try{
    const key=taskKey(evidenceDialog.phase,evidenceDialog.task)
    const result=await postData<any>(`/plans/${plan.value.id}/tasks/${encodeURIComponent(key)}/evidence`,{evidence:evidenceForm.evidence,reflection:evidenceForm.reflection,hours_spent:checkin.hours_spent})
    evidenceDialog.visible=false
    ElMessage[result.passed?'success':'warning'](`${result.passed?'成果已通过基础校验':'成果证据还不充分'}：${result.score} 分`)
    await load();activeTab.value='evidence'
  }catch(error:any){ElMessage.error(error?.response?.data?.detail || '成果提交失败')}finally{submittingEvidence.value=false}
}
function openRevision(item:any){revisionDialog.item=item;revisionDialog.visible=true}
async function decide(item:any,action:'accept'|'reject'|'revert'){
  if(action==='revert') await ElMessageBox.confirm('撤销会恢复该版本调整前的路线，但保留学习记录和成果证据。确定继续吗？','撤销路线版本',{type:'warning'})
  try{
    await postData(`/plans/${plan.value.id}/revisions/${item.id}/decision`,{action})
    revisionDialog.visible=false
    ElMessage.success(action==='accept'?'新路线已应用':action==='reject'?'已保留当前路线':'路线版本已撤销')
    await load()
  }catch(error:any){ElMessage.error(error?.response?.data?.detail || '版本操作失败')}
}
function evidenceLabel(type:string){return evidenceOptions.find(item=>item.value===type)?.label || type}
function revisionLabel(status:string){return ({pending:'待确认',accepted:'已应用',rejected:'已拒绝',reverted:'已撤销',superseded:'已被新建议替代'} as any)[status] || status}
function revisionType(status:string){return status==='accepted'?'success':status==='pending'?'warning':status==='rejected'?'info':'info'}
function totalWeeks(phases:any[]){return Math.max(0,...(phases||[]).map(item=>Number(item.week_end)||0))}
function phaseCount(phases:any[]){return (phases||[]).length}
</script>

<style scoped>
.eyebrow{color:#2e66e8;font-size:11px;font-weight:800;letter-spacing:.08em}.plan-hero{display:flex;align-items:center;justify-content:space-between;background:linear-gradient(120deg,#fff,#edf3ff)}.hero-title{display:flex;align-items:center;gap:12px}.hero-title h2{font-size:27px;margin:8px 0}.plan-hero p,.phase-copy,.safe-note{color:var(--muted)}.plan-hero :deep(.el-progress__text){display:grid;place-items:center}.plan-hero :deep(.el-progress__text) b{font-size:22px}.plan-hero :deep(.el-progress__text) span{font-size:10px;color:var(--muted)}.target-line{display:flex;align-items:center;gap:10px;margin-top:14px;padding:10px 12px;border-radius:10px;background:rgba(255,255,255,.72);font-size:12px}.target-line span{color:var(--muted)}.revision-alert{margin-top:16px;display:grid;grid-template-columns:1fr 1.2fr auto;gap:20px;align-items:center;border-color:#f0c36b;background:#fffaf0}.revision-alert h3{margin:6px 0;font-size:15px}.revision-alert p{margin:0;color:var(--muted);font-size:12px}.change-list{display:flex;gap:7px;flex-wrap:wrap}.change-list span{padding:7px 9px;border-radius:8px;background:white;border:1px solid #f2d99c;font-size:12px}.revision-actions{display:flex;gap:8px}.work-grid{display:grid;grid-template-columns:minmax(0,1fr) 330px;gap:16px;margin-top:16px}.section-head{display:flex;justify-content:space-between;align-items:center}.section-head h3,.checkin-card h3{margin:6px 0 2px}.task-list{display:grid;gap:10px;margin-top:16px}.task-card{display:grid;grid-template-columns:auto 1fr auto;gap:12px;align-items:start;border:1px solid var(--line);border-radius:13px;padding:14px;transition:.18s}.task-card:hover{border-color:#abc3fb;box-shadow:0 8px 20px rgba(41,83,170,.07)}.task-card.done{background:#f3fbf7;border-color:#b9e4d2}.task-title{display:flex;gap:8px;align-items:center}.task-card p{margin:5px 0;color:#546279;line-height:1.55;font-size:13px}.task-card span{font-size:11px;color:var(--muted)}.checkin-card{display:flex;flex-direction:column;gap:12px}.feedback-options{display:grid;grid-template-columns:repeat(2,1fr);gap:6px}.feedback-options :deep(.el-radio-button__inner){width:100%;border:1px solid #dfe6f1!important;border-radius:8px!important;box-shadow:none!important;padding:9px 4px}.field-hint{font-size:11px;color:var(--muted);margin-top:-8px}.hours-row{display:flex;justify-content:space-between;align-items:center;font-size:12px}.safe-note{font-size:11px;line-height:1.6;margin:0}.route-section{margin-top:16px}.timeline{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.phase{border:1px solid var(--line);border-radius:14px;padding:15px}.phase.active{border-color:#3168ee;background:#fbfcff}.phase.completed{border-color:#8bd6bb}.phase header{display:flex;justify-content:space-between;align-items:center}.phase header>span{color:var(--muted);font-size:11px}.phase h3{margin:12px 0 5px}.phase>p{color:var(--muted);font-size:12px;line-height:1.55;min-height:38px}.phase .pathway-name{min-height:0;color:#3168ee}.mini-tasks{display:grid;gap:6px;margin:12px 0}.mini-tasks span{padding:7px 8px;background:#f6f8fc;border-radius:7px;font-size:11px}.evidence-list,.revision-list{display:grid;gap:9px}.evidence-list article,.revision-list article{display:flex;align-items:center;gap:12px;border-bottom:1px solid var(--line);padding:11px}.evidence-list article>div,.revision-list article>div{display:grid;gap:4px;flex:1}.evidence-list span,.revision-list span,.revision-list small{color:var(--muted);font-size:12px}.detail-tasks{display:grid;gap:9px;margin-top:14px}.detail-tasks article{padding:12px;border-radius:11px;background:#f6f8fc}.detail-tasks p{color:#536179}.detail-tasks span{display:block;font-size:12px;color:var(--muted);margin-top:5px}.submission-head{padding:12px;border-radius:10px;background:#f5f8ff;margin-bottom:12px}.submission-head span,.submission-head b{display:block}.submission-head p{color:var(--muted);font-size:12px}.artifact-editor{display:grid;grid-template-columns:160px 1fr auto;gap:8px;margin-bottom:10px}.artifact-editor .el-input:nth-of-type(2){grid-column:1/3}.version-compare{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:16px;margin:18px 0}.version-compare article{display:grid;gap:5px;padding:16px;background:#f6f8fc;border-radius:12px}.version-compare article:last-child{background:#edf4ff}.version-compare span{color:var(--muted);font-size:12px}.version-compare i{font-style:normal;color:#3168ee;font-size:22px}.change-list.wide span{background:#fff8e8}.empty{text-align:center;padding:70px 20px}.empty p{color:var(--muted)}@media(max-width:1100px){.work-grid{grid-template-columns:1fr}.timeline{grid-template-columns:repeat(2,1fr)}.revision-alert{grid-template-columns:1fr}}@media(max-width:700px){.timeline{grid-template-columns:1fr}.plan-hero,.target-line,.task-card,.revision-list article{align-items:flex-start;flex-direction:column}.task-card{display:flex}.artifact-editor{grid-template-columns:1fr}.artifact-editor .el-input:nth-of-type(2){grid-column:auto}.version-compare{grid-template-columns:1fr}.version-compare i{transform:rotate(90deg)}}
</style>
