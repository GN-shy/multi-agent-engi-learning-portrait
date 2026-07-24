<template>
  <div class="agent-pipeline">
    <el-steps :active="activeStep" align-center finish-status="success">
      <el-step
        v-for="agent in agents"
        :key="agent.key"
        :title="agent.name"
        :description="agent.description"
        :status="agentStatus(agent.key)"
      />
    </el-steps>
    <div class="agent-detail" v-if="activeAgent">
      <el-alert
        :title="`${activeAgent.name} — ${activeAgent.status}`"
        :type="activeAgent.statusType"
        :description="activeAgent.detail"
        show-icon
        :closable="false"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'

const props = defineProps<{ events: any[] }>()

const agents = [
  { key: 'lms', name: '学情建模', description: '五维画像构建' },
  { key: 'krs', name: '知识检索', description: '多路召回' },
  { key: 'dgs', name: '双生成', description: 'A/B独立生成' },
  { key: 'ars', name: '仲裁审核', description: '辩论+评分' },
  { key: 'fusion', name: '融合输出', description: '智能合成' },
  { key: 'tis', name: '导学交互', description: '适应性反馈' },
]

const activeStep = ref(0)

const agentStatusMap = ref<Record<string, string>>({})

watch(() => props.events, (events) => {
  for (const ev of events) {
    if (ev.agent && ev.status) {
      agentStatusMap.value[ev.agent] = ev.status
    }
    if (ev.event === 'fusion.complete') {
      activeStep.value = 5
    }
  }
  // 根据事件计算步骤
  const agentOrder = ['lms', 'krs', 'gen_a', 'ars', 'fusion']
  for (let i = agentOrder.length - 1; i >= 0; i--) {
    if (agentStatusMap.value[agentOrder[i]] === 'completed') {
      activeStep.value = Math.max(activeStep.value, i + 1)
      break
    }
  }
}, { deep: true })

const activeAgent = computed(() => {
  const statuses = Object.entries(agentStatusMap.value)
  if (!statuses.length) return null
  const [key, status] = statuses[statuses.length - 1]
  const agent = agents.find(a => a.key === key || (key === 'gen_a' && a.key === 'dgs'))
  return {
    name: agent?.name || key,
    status,
    statusType: status === 'completed' ? 'success' : status === 'error' ? 'error' : 'info',
    detail: `Agent当前状态: ${status}`,
  }
})

function agentStatus(key: string): string {
  const status = agentStatusMap.value[key]
  if (!status) return 'wait'
  if (status === 'completed') return 'success'
  if (status === 'error') return 'error'
  return 'process'
}
</script>

<style scoped>
.agent-pipeline { padding: 20px; }
.agent-detail { margin-top: 20px; }
</style>
