<template>
  <AppShell>
    <section class="panel">
      <div class="panel-title">
        <div>
          <span class="eyebrow">PROJECT PRACTICE</span>
          <h3>项目实操任务</h3>
          <p>完成步骤不等于通过。平台会检查步骤覆盖、证据关联与证据质量，形成可复核的能力记录。</p>
        </div>
        <el-button type="primary" @click="router.push('/generate')">生成新任务</el-button>
      </div>

      <div v-if="items.length" class="cards">
        <article v-for="item in items" :key="item.id" class="card clickable" @click="open(item)">
          <div class="card-top"><span>项目实操</span><el-tag effect="plain">V{{ item.version }}</el-tag></div>
          <h3>{{ cleanTitle(item.title) }}</h3>
          <p>{{ routeLabel(item.track_code) }} · {{ item.source_traces.length }} 条知识来源</p>
          <el-button text>开始 / 继续任务 →</el-button>
        </article>
      </div>
      <div v-else class="empty">尚无实操任务，请先运行智能生成。</div>
    </section>

    <DetailModal v-model="detail.visible" :title="detail.item?.content?.title || '项目实操'">
      <template v-if="detail.loading"><el-skeleton :rows="8" animated /></template>
      <template v-else-if="detail.item">
        <el-alert type="success" :closable="false">
          <template #title><b>最终验收：</b>{{ detail.item.content.acceptance }}</template>
        </el-alert>

        <h4>需要交付</h4>
        <div class="tag-row"><el-tag v-for="value in detail.item.content.deliverables" :key="value">{{ value }}</el-tag></div>

        <h4>执行步骤</h4>
        <el-checkbox-group v-model="submission.completed_step_ids" class="steps">
          <el-checkbox v-for="step in detail.item.content.steps" :key="step.id" :value="step.id">
            <span class="step-copy">
              <b>{{ step.title }}</b>
              <small v-if="step.instructions">{{ step.instructions }}</small>
              <small>所需证据：{{ step.proof_required }}</small>
            </span>
          </el-checkbox>
        </el-checkbox-group>

        <div class="evidence-heading">
          <div><h4>运行证据</h4><p>每条证据关联一个步骤。链接和提交哈希只做格式检查，不冒充人工验真。</p></div>
          <el-button @click="addEvidence">添加证据</el-button>
        </div>
        <div class="evidence-list">
          <div v-for="(row,index) in evidence" :key="row.localId" class="evidence-row">
            <el-select v-model="row.step_id" placeholder="关联步骤">
              <el-option v-for="step in detail.item.content.steps" :key="step.id" :label="step.title" :value="step.id" />
            </el-select>
            <el-select v-model="row.type" placeholder="证据类型">
              <el-option v-for="option in evidenceTypes" :key="option.value" :label="option.label" :value="option.value" />
            </el-select>
            <el-input v-model="row.value" :placeholder="evidencePlaceholder(row.type)" />
            <el-button text type="danger" @click="removeEvidence(index)">移除</el-button>
          </div>
        </div>

        <section v-if="result" class="review">
          <div class="score-result">
            <strong>{{ result.score }}</strong>
            <div><b>{{ result.passed ? '验收通过' : '证据不足' }}</b><p>{{ result.next_action }}</p></div>
          </div>
          <div class="score-grid">
            <div><span>步骤完成度</span><b>{{ percent(result.score_breakdown?.step_completion) }}</b></div>
            <div><span>证据覆盖率</span><b>{{ percent(result.score_breakdown?.evidence_coverage) }}</b></div>
            <div><span>证据质量</span><b>{{ percent(result.score_breakdown?.evidence_quality) }}</b></div>
          </div>
          <div class="review-list">
            <article v-for="(row,index) in result.evidence_review" :key="index" :class="{good:row.accepted}">
              <el-icon><CircleCheck v-if="row.accepted" /><Warning v-else /></el-icon>
              <div><b>{{ row.label }}</b><p>{{ row.reason }}</p></div>
            </article>
          </div>
        </section>
      </template>
      <template #footer>
        <el-button @click="detail.visible=false">稍后继续</el-button>
        <el-button type="primary" :loading="submitting" @click="submit">提交证据并评估</el-button>
      </template>
    </DetailModal>
  </AppShell>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { CircleCheck, Warning } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import AppShell from '@/components/layout/AppShell.vue'
import DetailModal from '@/components/common/DetailModal.vue'
import { getData, postData } from '@/api'
import { percent, routeLabel } from '@/utils/presentation'
import type { LearningResource } from '@/types/domain'

type EvidenceRow = { localId: number; step_id: string; type: string; value: string }
const evidenceTypes = [
  { value: 'repository', label: '代码仓库地址' },
  { value: 'commit', label: '提交哈希' },
  { value: 'test', label: '测试结果' },
  { value: 'deployment', label: '部署地址' },
  { value: 'screenshot_note', label: '截图说明' },
]
const router = useRouter()
const items = ref<LearningResource[]>([])
const submitting = ref(false)
const result = ref<any>(null)
const submission = reactive({ completed_step_ids: [] as string[] })
const evidence = ref<EvidenceRow[]>([])
const detail = reactive({ visible: false, loading: false, item: null as any })
let evidenceId = 0

onMounted(async () => {
  items.value = (await getData<{items: LearningResource[]}>('/resources', { params: { resource_type: 'practice' } })).items
})

function cleanTitle(title: string) {
  return title.replace(/^.+?\s*[·|]\s*/, '')
}
function addEvidence() {
  const firstPending = detail.item?.content?.steps?.find((step: any) => !evidence.value.some(row => row.step_id === step.id))
  evidence.value.push({ localId: ++evidenceId, step_id: firstPending?.id || '', type: 'test', value: '' })
}
function removeEvidence(index: number) {
  evidence.value.splice(index, 1)
}
function evidencePlaceholder(type: string) {
  return ({
    repository: 'https://github.com/your-name/project',
    commit: '例如 a1b2c3d',
    test: '例如：12 项测试全部通过，附关键输出',
    deployment: 'https://your-demo.example.com',
    screenshot_note: '说明截图展示了什么运行结果',
  } as Record<string,string>)[type] || '填写可复核证据'
}
async function open(item: LearningResource) {
  detail.visible = true
  detail.loading = true
  result.value = null
  submission.completed_step_ids = []
  evidence.value = []
  try {
    detail.item = await getData(`/resources/${item.id}`)
    addEvidence()
  } finally {
    detail.loading = false
  }
}
async function submit() {
  if (!detail.item) return
  if (!submission.completed_step_ids.length) {
    ElMessage.warning('请先勾选已经实际完成的步骤')
    return
  }
  const usable = evidence.value.filter(row => row.step_id && row.value.trim())
  if (!usable.length) {
    ElMessage.warning('请至少提交一条与步骤关联的运行证据')
    return
  }
  submitting.value = true
  try {
    result.value = await postData(`/practice/${detail.item.id}/submit`, {
      completed_step_ids: submission.completed_step_ids,
      evidence: usable.map(({ step_id, type, value }) => ({ step_id, type, value: value.trim() })),
    })
    ElMessage.success('实操证据已完成结构化评估')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.eyebrow{font-size:11px;letter-spacing:.14em;color:#3168ee;font-weight:800}.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.card{padding:20px;border:1px solid var(--line);border-radius:17px;transition:.2s;background:linear-gradient(145deg,#fff,#f8fbff)}.card:hover{transform:translateY(-3px);box-shadow:0 14px 35px rgba(34,72,130,.1)}.card-top{display:flex;justify-content:space-between;align-items:center}.card-top>span{font-size:12px;color:#3168ee}.card p,.evidence-heading p{color:var(--muted)}.steps{display:grid;gap:9px}.steps .el-checkbox{height:auto;margin:0;padding:13px;background:#f7f9fd;border:1px solid transparent;border-radius:12px}.steps .el-checkbox.is-checked{background:#eef4ff;border-color:#aac3ff}.step-copy{display:block;white-space:normal}.step-copy b,.step-copy small{display:block}.step-copy small{color:var(--muted);font-size:12px;margin-top:5px}.evidence-heading{display:flex;align-items:end;justify-content:space-between;margin-top:18px}.evidence-heading h4,.evidence-heading p{margin:4px 0}.evidence-heading p{font-size:12px}.evidence-list{display:grid;gap:10px}.evidence-row{display:grid;grid-template-columns:1.1fr 140px 2fr auto;gap:8px;padding:10px;background:#f7f9fd;border-radius:12px}.review{margin-top:18px}.score-result{display:flex;align-items:center;gap:18px;background:#eef8f4;border-radius:14px;padding:16px}.score-result>strong{font-size:38px;color:#17a673}.score-result p{margin:5px 0;color:#5f706a}.score-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:10px 0}.score-grid div{padding:12px;background:#f7f9fd;border-radius:12px}.score-grid span,.score-grid b{display:block}.score-grid span{font-size:12px;color:var(--muted);margin-bottom:5px}.review-list{display:grid;gap:8px}.review-list article{display:flex;gap:10px;padding:11px;border-radius:11px;background:#fff5f0;color:#a54628}.review-list article.good{background:#eef8f4;color:#16805d}.review-list p{margin:4px 0 0;font-size:12px;color:var(--muted)}@media(max-width:900px){.cards{grid-template-columns:1fr}.evidence-row{grid-template-columns:1fr}.score-grid{grid-template-columns:1fr}}
</style>
