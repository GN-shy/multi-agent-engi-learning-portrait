<template>
  <AppShell>
    <section class="agent-hero">
      <div>
        <span>SIX-AGENT WORKFLOW</span>
        <h2>不是六个名称，而是一条可审计的协作链</h2>
        <p>画像、检索、双策略生成、仲裁和导学各自承担明确职责；页面只展示输入摘要、外部证据和产出，不展示隐藏思维链。</p>
      </div>
      <div class="hero-status"><strong>{{ completedCount }}/6</strong><span>{{ valueLabel(status.workflow_status) }}</span></div>
    </section>

    <section class="panel agent-panel">
      <div class="panel-title">
        <div><h3>本次协作状态</h3><p>{{ status.session_id ? `会话 …${status.session_id.slice(-8)}` : '生成一次学习闭环后即可查看' }}</p></div>
        <el-button @click="load">刷新状态</el-button>
      </div>
      <div class="network-wrap">
        <div class="network-lines" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i></div>
        <div class="pipeline">
          <article v-for="agent in status.items||[]" :key="agent.code" class="agent-card clickable" :class="[agent.code,{done:agent.status==='completed'}]" @click="open(agent)">
            <div class="avatar">{{ agent.code.toUpperCase().slice(0,2) }}</div>
            <div class="agent-copy">
              <div><h3>{{ agent.name }}</h3><el-tag :type="agent.status==='completed'?'success':'info'">{{ valueLabel(agent.status) }}</el-tag></div>
              <p>{{ agent.summary }}</p>
              <span>{{ agent.duration_ms ? `${agent.duration_ms} 毫秒` : '等待任务' }}</span>
            </div>
          </article>
        </div>
      </div>
    </section>

    <section class="panel tasks">
      <div class="panel-title"><div><h3>可审计任务记录</h3><p>记录真实后端事件，可按 Agent 筛选并用于答辩复现</p></div>
        <el-select v-model="agentFilter" clearable placeholder="全部 Agent"><el-option v-for="item in status.items||[]" :key="item.code" :label="item.name" :value="item.code" /></el-select>
      </div>
      <el-table :data="filteredTasks">
        <el-table-column label="时间" width="180"><template #default="{row}">{{ dateTime(row.created_at) }}</template></el-table-column>
        <el-table-column label="Agent" width="160"><template #default="{row}">{{ agentLabel(row.agent_code) }}</template></el-table-column>
        <el-table-column label="事件" width="150"><template #default="{row}">{{ eventLabel(row.event_type) }}</template></el-table-column>
        <el-table-column prop="summary" label="执行结果" min-width="360" />
        <el-table-column label="耗时" width="100"><template #default="{row}">{{ row.duration_ms }} ms</template></el-table-column>
      </el-table>
      <div v-if="!filteredTasks.length" class="empty">暂无协作事件</div>
    </section>

    <DetailModal v-model="detail.visible" :title="detail.agent?.name || 'Agent 详情'">
      <AgentEvidencePanel :agent="detail.agent" />
    </DetailModal>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import AppShell from '@/components/layout/AppShell.vue'
import DetailModal from '@/components/common/DetailModal.vue'
import AgentEvidencePanel from '@/components/business/AgentEvidencePanel.vue'
import { getData } from '@/api'
import { agentLabel, dateTime, valueLabel } from '@/utils/presentation'

const status = reactive<any>({ items: [] })
const tasks = ref<any[]>([])
const agentFilter = ref('')
const detail = reactive({ visible: false, agent: null as any })
const completedCount = computed(() => (status.items || []).filter((item:any) => item.status === 'completed').length)
const filteredTasks = computed(() => agentFilter.value ? tasks.value.filter(row => row.agent_code === agentFilter.value) : tasks.value)

onMounted(load)
async function load() {
  Object.assign(status, await getData('/agents/status'))
  tasks.value = (await getData<{items:any[]}>('/agents/tasks')).items
}
function open(agent:any) {
  detail.agent = agent
  detail.visible = true
}
function eventLabel(type:string) {
  return ({
    'profile.updated':'画像建模',
    'retrieval.completed':'知识检索',
    'generation.candidate':'方案生成',
    'arbitration.completed':'仲裁审核',
    'tutoring.ready':'导学就绪',
  } as Record<string,string>)[type] || type
}
</script>

<style scoped>
.agent-hero{display:flex;align-items:center;justify-content:space-between;gap:24px;padding:28px;border-radius:22px;color:white;background:radial-gradient(circle at 80% 20%,rgba(255,255,255,.18),transparent 26%),linear-gradient(135deg,#1f55d4,#7254dc);box-shadow:0 22px 55px rgba(44,73,160,.22)}.agent-hero>div:first-child{max-width:720px}.agent-hero span{font-size:11px;letter-spacing:.16em;font-weight:800;opacity:.8}.agent-hero h2{margin:8px 0}.agent-hero p{margin:0;line-height:1.75;opacity:.86}.hero-status{text-align:center}.hero-status strong,.hero-status span{display:block}.hero-status strong{font-size:40px}.agent-panel{margin-top:18px}.pipeline{display:grid;gap:0;max-width:900px;margin:auto}.agent-card{display:grid;grid-template-columns:54px 1fr;gap:14px;align-items:center;border:1px solid var(--line);border-radius:16px;padding:17px;transition:.2s;background:#fbfcff}.agent-card.done{border-color:#c8e9dc;background:linear-gradient(120deg,#fff,#f2fbf7)}.avatar{width:50px;height:50px;border-radius:16px;background:linear-gradient(145deg,#3168ee,#7355eb);color:white;display:grid;place-items:center;font-weight:800}.agent-copy>div{display:flex;align-items:center;justify-content:space-between}.agent-card h3,.agent-card p{margin:3px}.agent-card p,.agent-card span{color:var(--muted);font-size:13px}.connector{height:22px;display:grid;place-items:center;color:#91a4ca;font-weight:800}.tasks{margin-top:18px}.panel-title .el-select{width:190px}@media(max-width:700px){.agent-hero{align-items:flex-start;flex-direction:column}.hero-status{text-align:left}.panel-title{align-items:flex-start}.panel-title .el-select{width:145px}}
.network-wrap{position:relative;min-height:510px;padding:15px;background:radial-gradient(circle at 50% 50%,#f1f5ff,transparent 42%)}.network-wrap .pipeline{position:relative;z-index:2;display:grid;grid-template-columns:repeat(3,1fr);grid-template-rows:repeat(3,145px);gap:20px;max-width:1020px}.network-wrap .agent-card{display:grid;grid-template-columns:48px 1fr;gap:11px;padding:14px;border-radius:13px;background:rgba(255,255,255,.97);box-shadow:0 9px 24px rgba(47,78,139,.07)}.agent-card.lms{grid-column:2;grid-row:1}.agent-card.krs{grid-column:1;grid-row:2}.agent-card.dgs_a{grid-column:2;grid-row:2}.agent-card.dgs_b{grid-column:3;grid-row:2}.agent-card.ars{grid-column:2;grid-row:3}.agent-card.tis{grid-column:3;grid-row:3}.network-wrap .avatar{width:44px;height:44px;border-radius:14px}.krs .avatar{background:linear-gradient(145deg,#16a675,#34c394)}.dgs_b .avatar{background:linear-gradient(145deg,#7955e9,#9a72ef)}.ars .avatar{background:linear-gradient(145deg,#f08a35,#f6aa4c)}.tis .avatar{background:linear-gradient(145deg,#2f70e9,#51a1f0)}.network-wrap .agent-card h3{font-size:13px}.network-wrap .agent-card p,.network-wrap .agent-card span{font-size:10px}.network-lines{position:absolute;inset:0;z-index:1}.network-lines:before,.network-lines:after,.network-lines i{content:'';position:absolute;border-top:2px dashed #9bb9f2;transform-origin:left center}.network-lines:before{width:29%;left:21%;top:39%;transform:rotate(-31deg)}.network-lines:after{width:29%;left:50%;top:39%;transform:rotate(31deg)}.network-lines i:nth-child(1){width:25%;left:25%;top:52%}.network-lines i:nth-child(2){width:25%;left:50%;top:52%}.network-lines i:nth-child(3){width:18%;left:50%;top:54%;transform:rotate(90deg)}.network-lines i:nth-child(4){width:25%;left:50%;top:82%}@media(max-width:850px){.network-wrap{min-height:0}.network-wrap .pipeline{display:grid;grid-template-columns:1fr;grid-template-rows:auto}.agent-card.lms,.agent-card.krs,.agent-card.dgs_a,.agent-card.dgs_b,.agent-card.ars,.agent-card.tis{grid-column:1;grid-row:auto}.network-lines{display:none}}
</style>
