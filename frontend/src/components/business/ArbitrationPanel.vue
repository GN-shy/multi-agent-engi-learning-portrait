<template>
  <div class="arbitration">
    <div class="decision">
      <span>最终采用</span>
      <h3>{{ agentLabel(data?.winner) }}</h3>
      <p>{{ data?.decision_summary || '系统依据知识覆盖、引用、画像适配和前置关系完成融合。' }}</p>
    </div>
    <div class="candidate-grid">
      <article v-for="(score, code) in data?.candidate_scores || {}" :key="code">
        <div><b>{{ agentLabel(String(code)) }}</b><strong>{{ score.total }}</strong></div>
        <el-progress :percentage="Math.round(score.knowledge_coverage * 100)" :stroke-width="7"><span>知识覆盖 {{ percent(score.knowledge_coverage) }}</span></el-progress>
        <el-progress :percentage="Math.round(score.citation_coverage * 100)" :stroke-width="7" color="#17a673"><span>引用覆盖 {{ percent(score.citation_coverage) }}</span></el-progress>
        <el-progress :percentage="Math.round(score.profile_fit * 100)" :stroke-width="7" color="#8257e6"><span>画像适配 {{ percent(score.profile_fit) }}</span></el-progress>
      </article>
    </div>
    <section v-if="data?.quality_gate" class="quality-gate" :class="{passed:data.quality_gate.passed}">
      <div>
        <span>发布质量门</span>
        <h3>{{ data.quality_gate.passed ? '已通过，可交付' : '未通过，需要补证' }}</h3>
      </div>
      <div class="gate-rules">
        <span v-for="(passed,rule) in data.quality_gate.rules" :key="rule" :class="{ok:passed}">
          {{ passed ? '✓' : '!' }} {{ ruleLabel(String(rule)) }}
        </span>
      </div>
      <p>{{ data.quality_gate.notice }}</p>
    </section>
    <section v-if="data?.debate_triggered">
      <div class="section-title"><h3>交叉验证记录</h3><el-tag type="warning">{{ data.debate_rounds }} 轮</el-tag></div>
      <article v-for="round in data.debate || []" :key="round.round" class="debate">
        <h4>{{ round.topic }}</h4>
        <div><span>严谨方案</span><p>{{ round.dgs_a }}</p></div>
        <div><span>项目方案</span><p>{{ round.dgs_b }}</p></div>
        <div class="verdict"><span>审核裁定</span><p>{{ round.ars_decision }}</p><small>采用证据：{{ round.evidence_ids?.join('、') }}</small></div>
      </article>
    </section>
    <el-alert v-else title="两个候选方案在关键事实和学习顺序上保持一致，本次无需追加辩论。" type="success" :closable="false" show-icon />
  </div>
</template>

<script setup lang="ts">
import { agentLabel, percent } from '@/utils/presentation'
defineProps<{ data: any }>()
function ruleLabel(code:string) {
  return ({
    citation_coverage_at_least_95_percent:'引用覆盖不低于 95%',
    no_prerequisite_violation:'无前置依赖冲突',
    unreferenced_risk_below_5_percent:'未引用风险估计低于 5%',
  } as Record<string,string>)[code] || code
}
</script>

<style scoped>
.arbitration{display:grid;gap:18px}.decision{padding:20px;border-radius:17px;background:linear-gradient(135deg,#eef4ff,#f3efff);border:1px solid #dce4ff}.decision span{color:#3168ee;font-size:12px;font-weight:700}.decision h3{margin:7px 0}.decision p{margin:0;line-height:1.75}.candidate-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}.candidate-grid article{padding:16px;border:1px solid var(--line);border-radius:15px}.candidate-grid article>div{display:flex;justify-content:space-between;margin-bottom:14px}.candidate-grid strong{font-size:26px;color:#3168ee}.candidate-grid .el-progress{margin:10px 0}.quality-gate{padding:17px;border:1px solid #f0c5ae;background:#fff6f1;border-radius:15px}.quality-gate.passed{border-color:#b8e3d2;background:#f0faf6}.quality-gate>div:first-child{display:flex;justify-content:space-between;align-items:center}.quality-gate h3{margin:0}.quality-gate>div:first-child span{font-size:12px;color:var(--muted)}.gate-rules{display:flex;gap:8px;flex-wrap:wrap;margin:13px 0}.gate-rules span{padding:6px 9px;border-radius:20px;background:#fff;color:#a04b2d;font-size:12px}.gate-rules span.ok{color:#157c59}.quality-gate p{margin:0;color:var(--muted);font-size:12px}.section-title{display:flex;align-items:center;justify-content:space-between}.debate{padding:17px;border:1px solid var(--line);border-radius:15px}.debate>div{display:grid;grid-template-columns:88px 1fr;gap:10px;margin:9px 0}.debate span{color:#6e7b92;font-size:12px}.debate p{margin:0;line-height:1.65}.verdict{padding:12px;background:#f1fbf7;border-radius:12px}.verdict small{grid-column:2;color:#16845e}@media(max-width:680px){.candidate-grid{grid-template-columns:1fr}.debate>div{grid-template-columns:1fr}.verdict small{grid-column:1}}
</style>
