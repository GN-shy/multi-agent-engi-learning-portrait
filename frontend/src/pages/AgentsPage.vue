<template>
  <AppShell>
    <el-alert title="这里展示执行步骤、工具结果、检索证据、评分与裁定摘要，不展示或持久化模型隐藏思维链。" type="info" :closable="false" show-icon />
    <section class="panel agent-panel">
      <div class="panel-title"><div><h3>六 Agent 协作状态</h3><p>会话 {{ status.session_id || '暂无' }} · {{ status.workflow_status }}</p></div><el-button @click="load">刷新</el-button></div>
      <div class="agent-grid"><article v-for="agent in status.items||[]" :key="agent.code" class="agent-card clickable" @click="open(agent)"><div class="avatar">{{ agent.code.toUpperCase().slice(0,2) }}</div><div><h3>{{ agent.name }}</h3><p>{{ agent.summary }}</p><span>耗时 {{ agent.duration_ms }} ms</span></div><el-tag :type="agent.status==='completed'?'success':'info'">{{ agent.status }}</el-tag></article></div>
    </section>
    <section class="panel tasks"><div class="panel-title"><div><h3>可审计任务记录</h3><p>按时间倒序保存，可用于答辩复现</p></div></div><el-table :data="tasks"><el-table-column prop="created_at" label="时间" width="190" /><el-table-column prop="agent_code" label="Agent" width="110" /><el-table-column prop="event_type" label="事件" width="190" /><el-table-column prop="summary" label="摘要" min-width="360" /><el-table-column prop="duration_ms" label="耗时/ms" width="100" /></el-table></section>
    <DetailModal v-model="detail.visible" :title="detail.agent?.name || 'Agent 详情'"><p class="summary">{{ detail.agent?.summary }}</p><h4>结构化证据</h4><pre>{{ JSON.stringify(detail.agent?.evidence,null,2) }}</pre><el-descriptions :column="2" border><el-descriptions-item label="Agent 编码">{{ detail.agent?.code }}</el-descriptions-item><el-descriptions-item label="状态">{{ detail.agent?.status }}</el-descriptions-item><el-descriptions-item label="耗时">{{ detail.agent?.duration_ms }} ms</el-descriptions-item><el-descriptions-item label="会话">{{ status.session_id }}</el-descriptions-item></el-descriptions></DetailModal>
  </AppShell>
</template>

<script setup lang="ts">
import { onMounted,reactive,ref } from 'vue';import AppShell from '@/components/layout/AppShell.vue';import DetailModal from '@/components/common/DetailModal.vue';import { getData } from '@/api'
const status=reactive<any>({items:[]}),tasks=ref<any[]>([]),detail=reactive({visible:false,agent:null as any})
onMounted(load)
async function load(){Object.assign(status,await getData('/agents/status'));tasks.value=(await getData<{items:any[]}>('/agents/tasks')).items}
function open(agent:any){detail.agent=agent;detail.visible=true}
</script>

<style scoped>
.agent-panel{margin-top:18px}.agent-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:13px}.agent-card{display:grid;grid-template-columns:54px 1fr auto;gap:14px;align-items:center;border:1px solid var(--line);border-radius:16px;padding:17px;transition:.2s}.avatar{width:50px;height:50px;border-radius:16px;background:linear-gradient(145deg,#3168ee,#7355eb);color:white;display:grid;place-items:center;font-weight:800}.agent-card h3,.agent-card p{margin:3px}.agent-card p,.agent-card span{color:var(--muted);font-size:13px}.tasks{margin-top:18px}.summary{font-size:16px;line-height:1.8}pre{white-space:pre-wrap;background:#f7f9fd;padding:16px;border-radius:12px}@media(max-width:850px){.agent-grid{grid-template-columns:1fr}}
</style>
