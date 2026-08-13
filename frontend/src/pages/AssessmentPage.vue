<template>
  <AppShell>
    <section class="panel">
      <div class="panel-title">
        <div><span class="eyebrow">WORK-SAMPLE ASSESSMENT</span><h3>工作样本能力测评</h3><p>用真实情境判断你会不会做：分别提交实施方案、验收方法、失败处理、技术取舍和成果证据。</p></div>
        <el-button type="primary" @click="router.push('/generate')">生成新测评</el-button>
      </div>
      <el-table :data="items" @row-click="open">
        <el-table-column prop="title" label="测评" min-width="300" />
        <el-table-column label="路线" width="180"><template #default="{row}">{{ routeLabel(row.track_code) }}</template></el-table-column>
        <el-table-column prop="version" label="版本" width="90" />
        <el-table-column label="操作" width="120"><template #default><el-button text>开始测评</el-button></template></el-table-column>
      </el-table>
      <div v-if="!items.length" class="empty">尚无测评，请先运行智能生成。</div>
    </section>

    <DetailModal v-model="detail.visible" :title="detail.item?.title || '分阶段测评'">
      <template v-if="detail.loading"><el-skeleton :rows="8" animated /></template>
      <template v-else>
        <el-alert title="本测评不按关键词和字数给分。系统会检查方案结构、可判定标准、失败恢复、方案权衡和成果证据；没有成果证据时只给形成性反馈，不会抬高能力画像。" type="info" :closable="false" />
        <div v-for="(question,index) in detail.item?.content?.questions||[]" :key="question.id" class="question">
          <div><span>{{ index+1 }}</span><h4>{{ question.question }}</h4><el-tag>满分 {{ question.max_score }}</el-tag></div>
          <p class="scenario">{{ question.question }}</p>
          <div class="requirements">
            <span v-for="requirement in question.rubric" :key="requirement">{{ requirement }}</span>
          </div>
          <div class="answer-fields">
            <el-form-item v-for="field in question.response_fields || fallbackFields" :key="field.code" :label="field.label" required>
              <el-input :model-value="fieldValue(question.id, field.code)" type="textarea" :rows="3" :placeholder="field.hint" @update:model-value="setFieldValue(question.id, field.code, String($event))" />
            </el-form-item>
          </div>
          <div class="evidence-box">
            <div><b>成果证据</b><span>可添加多项。链接只做格式检查，平台不会冒充已访问或已人工验真。</span></div>
            <div v-for="(evidence,evidenceIndex) in answerFor(question.id).evidence" :key="evidenceIndex" class="evidence-row">
              <el-select v-model="evidence.type" placeholder="证据类型">
                <el-option v-for="item in evidenceTypes" :key="item.code" :label="item.label" :value="item.code" />
              </el-select>
              <el-input v-model="evidence.value" :placeholder="evidenceHint(evidence.type)" />
              <el-button text type="danger" @click="removeEvidence(question.id,evidenceIndex)">移除</el-button>
            </div>
            <el-button plain type="primary" @click="addEvidence(question.id)">+ 添加成果证据</el-button>
          </div>
          <el-alert v-if="question.scoring_notice" :title="question.scoring_notice" type="warning" :closable="false" />
        </div>

        <section v-if="result" class="result-area">
          <div class="result" :class="{failed:!result.passed}">
            <strong>{{ result.score }}</strong>
            <div><h3>{{ result.passed ? '证据测评通过' : result.result_type === 'formative' ? '已完成形成性测评' : '需要巩固' }}</h3><p>{{ result.result_notice }}</p></div>
          </div>
          <article v-for="row in result.details" :key="row.question_id" class="detail-card">
            <div class="detail-title"><b>{{ row.skill_name || row.skill_code }}</b><strong>{{ row.score }}/{{ row.max_score }}</strong></div>
            <div class="dimension-grid">
              <div v-for="(value,key) in row.rubric_scores" :key="key"><span>{{ dimensionLabel(String(key)) }}</span><b>{{ value }}/2</b></div>
              <div><span>成果证据</span><b>{{ row.evidence_score }}/2</b></div>
            </div>
            <p>{{ row.feedback }}</p>
            <div class="confidence"><span>证据可信度：{{ evidenceLevel(row.evidence_level) }}</span><span>画像回写：{{ row.eligible_for_profile_update ? '允许' : '暂不回写' }}</span></div>
            <div v-if="row.missing_dimensions?.length" class="missing">建议补充：{{ row.missing_dimensions.map(dimensionLabel).join('、') }}</div>
            <ul v-if="guidanceItems(row).length" class="guidance"><li v-for="item in guidanceItems(row)" :key="item">{{ item }}</li></ul>
          </article>
        </section>
      </template>
      <template #footer>
        <el-button @click="detail.visible=false">退出</el-button>
        <el-button type="primary" :loading="submitting" @click="submit">提交并回写画像</el-button>
      </template>
    </DetailModal>
  </AppShell>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import AppShell from '@/components/layout/AppShell.vue'
import DetailModal from '@/components/common/DetailModal.vue'
import { getData, postData } from '@/api'
import { routeLabel } from '@/utils/presentation'
import type { LearningResource } from '@/types/domain'

const router = useRouter()
const items = ref<LearningResource[]>([])
type Evidence = { type: string; value: string }
type AnswerField = 'action' | 'validation' | 'boundary' | 'reasoning'
type StructuredAnswer = { action: string; validation: string; boundary: string; reasoning: string; evidence: Evidence[] }
const answers = reactive<Record<string,StructuredAnswer>>({})
const result = ref<any>(null)
const submitting = ref(false)
const detail = reactive({ visible: false, loading: false, item: null as any })
const fallbackFields = [
  { code:'action', label:'实施方案', hint:'按顺序说明做什么、输入输出和技术对象' },
  { code:'validation', label:'验收与验证', hint:'给出测试方法、预期结果和通过标准' },
  { code:'boundary', label:'失败处理', hint:'给出异常场景及定位、恢复办法' },
  { code:'reasoning', label:'技术取舍', hint:'比较主方案与备选方案，说明选择依据和代价' },
]
const evidenceTypes = [
  {code:'repository',label:'代码仓库'}, {code:'commit',label:'提交哈希'}, {code:'test',label:'测试结果'},
  {code:'deployment',label:'部署地址'}, {code:'screenshot_note',label:'截图说明'}, {code:'note',label:'复盘说明'},
]

onMounted(async () => {
  items.value = (await getData<{items: LearningResource[]}>('/resources', { params: { resource_type: 'assessment' } })).items
})
function dimensionLabel(key: string) {
  return ({ action:'实施方案', validation:'验收与验证', boundary:'失败处理', reasoning:'技术取舍', evidence:'成果证据' } as Record<string,string>)[key] || key
}
function answerFor(questionId:string): StructuredAnswer {
  if (!answers[questionId]) answers[questionId] = {action:'',validation:'',boundary:'',reasoning:'',evidence:[]}
  return answers[questionId]
}
function fieldValue(questionId:string, code:string) { return answerFor(questionId)[code as AnswerField] }
function setFieldValue(questionId:string, code:string, value:string) { answerFor(questionId)[code as AnswerField] = value }
function addEvidence(questionId:string) { answerFor(questionId).evidence.push({type:'test',value:''}) }
function removeEvidence(questionId:string,index:number) { answerFor(questionId).evidence.splice(index,1) }
function evidenceHint(type:string) {
  return ({repository:'https://github.com/...',commit:'7–40 位 Git 提交哈希',test:'测试命令、通过数量和关键输出',deployment:'https://可访问地址',screenshot_note:'说明截图对应的验收标准',note:'说明成果、失败修正和复盘结论'} as Record<string,string>)[type] || '填写证据内容'
}
function evidenceLevel(level:string) { return ({strong:'强',moderate:'中等',formative:'形成性'} as Record<string,string>)[level] || '待判断' }
function guidanceItems(row:any) { return Object.values(row.guidance || {}).flat() as string[] }
async function open(item: LearningResource) {
  detail.visible = true
  detail.loading = true
  result.value = null
  Object.keys(answers).forEach(key => delete answers[key])
  try { detail.item = await getData(`/resources/${item.id}`) } finally { detail.loading = false }
}
async function submit() {
  if (!detail.item) return
  const questions = detail.item.content?.questions || []
  if (questions.some((question:any) => fallbackFields.some(field => !answerFor(question.id)[field.code as keyof StructuredAnswer]))) {
    ElMessage.warning('请分别完成实施方案、验收、失败处理和技术取舍')
    return
  }
  submitting.value = true
  try {
    result.value = await postData(`/assessments/${detail.item.id}/submit`, { answers })
    ElMessage.success('评分完成，学习画像已更新')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.eyebrow{font-size:11px;letter-spacing:.14em;color:#3168ee;font-weight:800}.question{padding:20px 0;border-bottom:1px solid var(--line)}.question>div:first-child{display:grid;grid-template-columns:34px 1fr auto;gap:10px;align-items:center}.question>div:first-child>span{width:30px;height:30px;border-radius:10px;background:#3168ee;color:white;display:grid;place-items:center}.question h4{margin:0}.question p{color:var(--muted);font-size:13px}.scenario{padding:12px;border-radius:12px;background:#f7f9fd;line-height:1.7}.requirements{display:flex;gap:6px;flex-wrap:wrap;margin:8px 0 12px}.requirements span{font-size:12px;padding:5px 9px;border-radius:20px;background:#eef4ff;color:#2859c5}.answer-fields{display:grid;grid-template-columns:repeat(2,1fr);gap:4px 14px}.evidence-box{padding:14px;margin:8px 0 12px;border:1px solid #d9e4f8;border-radius:13px;background:#f8faff}.evidence-box>div:first-child{display:flex;justify-content:space-between;gap:14px;margin-bottom:10px}.evidence-box>div:first-child span{font-size:12px;color:var(--muted)}.evidence-row{display:grid;grid-template-columns:150px 1fr 60px;gap:8px;margin-bottom:8px}.result-area{margin-top:20px}.result{padding:18px;background:#eef8f4;border-radius:16px;display:flex;gap:18px;align-items:center}.result.failed{background:#fff5f0}.result>strong{font-size:42px;color:#17a673}.result.failed>strong{color:#df7048}.result h3,.result p{margin:3px}.detail-card{padding:16px;margin-top:10px;border:1px solid var(--line);border-radius:14px}.detail-title{display:flex;justify-content:space-between}.detail-title strong{color:#3168ee}.dimension-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:7px;margin:12px 0}.dimension-grid div{padding:9px;background:#f7f9fd;border-radius:9px}.dimension-grid span,.dimension-grid b{display:block;font-size:12px}.dimension-grid span{color:var(--muted);margin-bottom:3px}.detail-card p{color:var(--muted)}.confidence{display:flex;gap:8px}.confidence span{padding:5px 8px;border-radius:8px;background:#edf8f3;color:#15734c;font-size:12px}.missing{padding:9px;border-radius:9px;background:#fff5f0;color:#a94d2d;font-size:13px}.guidance{color:#6d788b;font-size:12px;line-height:1.7}@media(max-width:700px){.answer-fields,.dimension-grid{grid-template-columns:1fr}.evidence-row{grid-template-columns:1fr}.evidence-box>div:first-child{display:block}}
</style>
