<template>
  <div class="agent-evidence">
    <section class="result">
      <span>{{ agentLabel(agent?.code) }}完成了什么</span>
      <p>{{ agent?.summary || '暂无执行摘要' }}</p>
    </section>
    <div class="facts">
      <article><span>运行状态</span><b>{{ valueLabel(agent?.status) }}</b></article>
      <article><span>处理耗时</span><b>{{ agent?.duration_ms || 0 }} 毫秒</b></article>
      <article v-if="agent?.evidence?.retrieved !== undefined"><span>检索到的证据</span><b>{{ agent.evidence.retrieved }} 条</b></article>
      <article v-if="agent?.evidence?.profile_score !== undefined"><span>画像综合分</span><b>{{ agent.evidence.profile_score }}</b></article>
    </div>
    <section>
      <h3>本步骤采用的依据</h3>
      <HumanDetail :value="agent?.evidence" />
    </section>
    <el-alert title="这里只展示可核验的输入摘要、证据和结果，不展示模型隐藏思维链。" type="info" :closable="false" show-icon />
  </div>
</template>

<script setup lang="ts">
import HumanDetail from '@/components/common/HumanDetail.vue'
import { agentLabel, valueLabel } from '@/utils/presentation'
defineProps<{ agent: any }>()
</script>

<style scoped>
.agent-evidence{display:grid;gap:18px}.result{padding:18px;border-radius:15px;background:linear-gradient(135deg,#eef4ff,#f7f9ff)}.result span{font-size:12px;color:#3168ee;font-weight:700}.result p{font-size:16px;line-height:1.8;margin:7px 0 0}.facts{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.facts article{padding:14px;border:1px solid var(--line);border-radius:13px}.facts span,.facts b{display:block}.facts span{font-size:12px;color:var(--muted);margin-bottom:5px}@media(max-width:680px){.facts{grid-template-columns:1fr}}
</style>
