<template>
  <div class="resource-content">
    <template v-if="type === 'lecture'">
      <section class="lead">
        <span>本讲义将帮助你</span>
        <p>{{ content.summary || '围绕当前路线补齐关键知识并形成可验证能力。' }}</p>
      </section>
      <section v-if="content.ai_enhancement" class="ai-note">
        <div><el-tag type="success">AI 个性化补充</el-tag><el-tag type="info">{{ content.ai_enhancement.model }}</el-tag></div>
        <p>{{ content.ai_enhancement.personalized_summary }}</p>
        <ul><li v-for="tip in content.ai_enhancement.project_tips || []" :key="tip">{{ tip }}</li></ul>
      </section>
      <section v-if="content.objectives?.length">
        <h3>完成后你能够</h3>
        <ul class="check-list"><li v-for="item in content.objectives" :key="item">{{ item }}</li></ul>
      </section>
      <section>
        <h3>学习内容</h3>
        <article v-for="(section, index) in content.sections || []" :key="section.skill_code" class="lesson">
          <div class="lesson-index">{{ index + 1 }}</div>
          <div>
            <div class="tag-row"><el-tag>{{ routeSkill(section.skill_code) }}</el-tag><el-tag type="warning">难度 {{ section.difficulty }}/5</el-tag></div>
            <h3>{{ section.title }}</h3>
            <p class="objective">{{ section.objective }}</p>
            <p>{{ section.explanation }}</p>
            <div v-if="section.why_this_matters" class="why"><b>为什么要学</b><span>{{ section.why_this_matters }}</span></div>
            <div v-if="section.learning_tasks?.length" class="learning-tasks">
              <b>动手完成</b>
              <ol><li v-for="task in section.learning_tasks" :key="task">{{ task }}</li></ol>
            </div>
            <div v-if="section.common_mistakes?.length" class="mistakes">
              <b>常见误区</b><span v-for="mistake in section.common_mistakes" :key="mistake">{{ mistake }}</span>
            </div>
            <div v-if="section.verification" class="verification"><b>验证方式</b><span>{{ section.verification }}</span></div>
            <div class="checkpoint"><b>掌握检查</b><span>{{ section.checkpoint }}</span></div>
            <small>知识依据：{{ section.citation_ids?.join('、') || '待补充来源' }}</small>
          </div>
        </article>
      </section>
    </template>

    <template v-else-if="type === 'practice'">
      <section class="lead">
        <span>项目目标</span>
        <h2>{{ content.title }}</h2>
        <p>{{ content.acceptance }}</p>
      </section>
      <section><h3>需要交付</h3><div class="deliverables"><span v-for="item in content.deliverables || []" :key="item">✓ {{ item }}</span></div></section>
      <section><h3>实施路径</h3>
        <div class="step-list">
          <article v-for="(step,index) in content.steps || []" :key="step.id">
            <span>{{ index + 1 }}</span>
            <div><h4>{{ step.title }}</h4><p>{{ step.instructions || `完成与“${routeSkill(step.skill_code)}”相关的可运行增量。` }}</p><small>验收证据：{{ step.proof_required }}</small></div>
          </article>
        </div>
      </section>
    </template>

    <template v-else-if="type === 'assessment'">
      <section class="lead"><span>测试说明</span><p>请写出具体任务、实施步骤、验证方法和失败边界。系统会按评分点逐项给分，而不是只按字数判断。</p><b>通过分数：{{ content.pass_score || 70 }}</b></section>
      <section><h3>题目预览</h3>
        <article v-for="(question,index) in content.questions || []" :key="question.id" class="question">
          <span>{{ index + 1 }}</span>
          <div><h4>{{ question.question }}</h4><p>考察技能：{{ routeSkill(question.skill_code) }}</p><div class="tag-row"><el-tag v-for="item in question.rubric || []" :key="item" type="info">{{ item }}</el-tag></div></div>
        </article>
      </section>
    </template>

    <template v-else-if="type === 'plan'">
      <section class="lead"><span>计划依据</span><p>每周投入 {{ content.learner_fit?.weekly_hours || 8 }} 小时，采用“{{ valueLabel(content.learner_fit?.style) }}”方式推进。</p></section>
      <section><h3>阶段安排</h3>
        <div class="phase-list">
          <article v-for="phase in content.phases || []" :key="phase.id">
            <div><span>第 {{ phase.week_start }}–{{ phase.week_end }} 周</span><el-tag :type="phase.status === 'active' ? 'success' : 'info'">{{ valueLabel(phase.status) }}</el-tag></div>
            <h3>{{ phase.name }}</h3>
            <p>{{ phase.milestone }}</p>
            <ul v-if="phase.tasks?.length" class="phase-tasks"><li v-for="task in phase.tasks" :key="task.id">{{ task.title }}</li></ul>
            <div class="tag-row"><el-tag v-for="skill in phase.skills || []" :key="skill">{{ routeSkill(skill) }}</el-tag></div>
          </article>
        </div>
      </section>
    </template>

    <HumanDetail v-else :value="content" />
  </div>
</template>

<script setup lang="ts">
import HumanDetail from '@/components/common/HumanDetail.vue'
import { valueLabel } from '@/utils/presentation'

defineProps<{ type: string; content: any }>()

function routeSkill(code?: string) {
  if (!code) return '综合能力'
  const tail = code.split('.').pop() || code
  return ({
    workflow: '状态机与工作流',
    tools: '工具与上下文工程',
    eval: '智能体评测与治理',
    programming: '程序设计',
    database: '数据库',
    network: '计算机网络',
    os: '操作系统',
    git: 'Git 协作',
  } as Record<string,string>)[tail] || code
}
</script>

<style scoped>
.resource-content{display:grid;gap:24px}.resource-content section>h3{margin:0 0 14px}.lead{padding:20px;border-radius:17px;background:linear-gradient(135deg,#eef4ff,#f5f1ff);border:1px solid #dce6ff}.lead>span{color:#3168ee;font-weight:700;font-size:12px}.lead h2{margin:8px 0}.lead p{line-height:1.8;margin:8px 0}.ai-note{padding:18px;border:1px solid #bce6d6;background:#f1fbf7;border-radius:16px}.ai-note>div{display:flex;gap:8px}.ai-note p,.ai-note li{line-height:1.75}.check-list{display:grid;gap:9px;padding:0;list-style:none}.check-list li{padding:12px 14px;background:#f6f9ff;border-radius:12px}.check-list li:before{content:'✓';color:#18a673;font-weight:800;margin-right:10px}.lesson{display:grid;grid-template-columns:42px 1fr;gap:15px;padding:19px 0;border-bottom:1px solid var(--line)}.lesson-index{width:38px;height:38px;border-radius:12px;display:grid;place-items:center;background:#3168ee;color:white;font-weight:800}.lesson h3{margin:10px 0 6px}.lesson p{line-height:1.75}.lesson .objective{color:#3168ee}.checkpoint{display:flex;gap:10px;padding:12px 14px;background:#fff8e9;border-radius:12px;margin:12px 0}.checkpoint span{line-height:1.6}.lesson small{color:#76839a}.deliverables{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}.deliverables span{padding:13px;background:#f3f8ff;border-radius:12px}.step-list,.phase-list{display:grid;gap:12px}.step-list article{display:grid;grid-template-columns:38px 1fr;gap:13px;padding:15px;border:1px solid var(--line);border-radius:14px}.step-list article>span{width:34px;height:34px;border-radius:11px;display:grid;place-items:center;background:#edf3ff;color:#3168ee;font-weight:700}.step-list h4,.step-list p{margin:3px 0 8px}.step-list p{line-height:1.65}.step-list small{color:#6f7c93}.question{display:grid;grid-template-columns:36px 1fr;gap:12px;padding:16px;border-bottom:1px solid var(--line)}.question>span{width:32px;height:32px;border-radius:10px;display:grid;place-items:center;background:#3168ee;color:white}.question h4{margin:3px 0 8px}.question p{color:var(--muted)}.phase-list article{padding:17px;border:1px solid var(--line);border-radius:15px}.phase-list article>div:first-child{display:flex;justify-content:space-between;color:#3168ee}.phase-list h3{margin:10px 0 6px}.phase-list p{line-height:1.7;color:#56637b}.phase-tasks{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:7px;padding:0;list-style:none}.phase-tasks li{padding:8px 10px;border-radius:9px;background:#f5f8fd;color:#48556d;font-size:12px}@media(max-width:680px){.deliverables{grid-template-columns:1fr}.checkpoint{display:block}.checkpoint b{display:block;margin-bottom:5px}.phase-tasks{grid-template-columns:1fr}}
.why,.verification{display:flex;gap:10px;padding:11px 13px;border-radius:11px;margin:9px 0;background:#f2f7ff}.why b,.verification b{flex:0 0 auto;color:#275cc8}.why span,.verification span{line-height:1.6}.learning-tasks{padding:13px;background:#f6f9ff;border-radius:12px}.learning-tasks ol{margin:8px 0 0;padding-left:20px}.learning-tasks li{margin:5px 0}.mistakes{display:flex;gap:6px;flex-wrap:wrap;margin:10px 0}.mistakes b{width:100%;color:#b45c36}.mistakes span{font-size:12px;padding:5px 9px;border-radius:20px;background:#fff1eb;color:#9c4d2d}
</style>
