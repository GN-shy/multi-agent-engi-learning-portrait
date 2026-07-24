<template>
  <AppShell>
    <section class="panel">
      <div class="panel-title">
        <div><span class="eyebrow">EVIDENCE ASSESSMENT</span><h3>分阶段能力测评</h3><p>不靠选择题猜答案；用行动、验证、边界和取舍四类证据判断是否真正会做。</p></div>
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
        <el-alert title="评分会逐项检查：可执行行动、客观验证、异常边界、技术取舍。单纯堆字数不会得到高分。" type="info" :closable="false" />
        <div v-for="(question,index) in detail.item?.content?.questions||[]" :key="question.id" class="question">
          <div><span>{{ index+1 }}</span><h4>{{ question.question }}</h4><el-tag>满分 {{ question.max_score }}</el-tag></div>
          <p>评分点：{{ question.rubric.join('；') }}</p>
          <div v-if="question.answer_requirements" class="requirements">
            <span v-for="requirement in question.answer_requirements" :key="requirement">{{ requirement }}</span>
          </div>
          <el-input v-model="answers[question.id]" type="textarea" :rows="6" placeholder="请写出：做什么 → 如何验证 → 失败时如何定位 → 为什么这样取舍" />
        </div>

        <section v-if="result" class="result-area">
          <div class="result" :class="{failed:!result.passed}">
            <strong>{{ result.score }}</strong>
            <div><h3>{{ result.passed ? '测评通过' : '需要巩固' }}</h3><p>本次结果已作为新证据回写学习画像。</p></div>
          </div>
          <article v-for="row in result.details" :key="row.question_id" class="detail-card">
            <div class="detail-title"><b>{{ row.skill_name || row.skill_code }}</b><strong>{{ row.score }}/{{ row.max_score }}</strong></div>
            <div class="dimension-grid">
              <div v-for="(value,key) in row.rubric_scores" :key="key"><span>{{ dimensionLabel(String(key)) }}</span><b>{{ value }}/2.5</b></div>
            </div>
            <p>{{ row.feedback }}</p>
            <div v-if="row.missing_dimensions?.length" class="missing">建议补充：{{ row.missing_dimensions.map(dimensionLabel).join('、') }}</div>
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
const answers = reactive<Record<string,string>>({})
const result = ref<any>(null)
const submitting = ref(false)
const detail = reactive({ visible: false, loading: false, item: null as any })

onMounted(async () => {
  items.value = (await getData<{items: LearningResource[]}>('/resources', { params: { resource_type: 'assessment' } })).items
})
function dimensionLabel(key: string) {
  return ({ action:'可执行行动', validation:'客观验证', boundary:'异常边界', reasoning:'技术取舍' } as Record<string,string>)[key] || key
}
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
  if (questions.some((question:any) => !answers[question.id]?.trim())) {
    ElMessage.warning('请完成全部题目后再提交')
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
.eyebrow{font-size:11px;letter-spacing:.14em;color:#3168ee;font-weight:800}.question{padding:20px 0;border-bottom:1px solid var(--line)}.question>div:first-child{display:grid;grid-template-columns:34px 1fr auto;gap:10px;align-items:center}.question>div:first-child>span{width:30px;height:30px;border-radius:10px;background:#3168ee;color:white;display:grid;place-items:center}.question h4{margin:0}.question p{color:var(--muted);font-size:13px}.requirements{display:flex;gap:6px;flex-wrap:wrap;margin:8px 0 12px}.requirements span{font-size:12px;padding:5px 9px;border-radius:20px;background:#eef4ff;color:#2859c5}.result-area{margin-top:20px}.result{padding:18px;background:#eef8f4;border-radius:16px;display:flex;gap:18px;align-items:center}.result.failed{background:#fff5f0}.result>strong{font-size:42px;color:#17a673}.result.failed>strong{color:#df7048}.result h3,.result p{margin:3px}.detail-card{padding:16px;margin-top:10px;border:1px solid var(--line);border-radius:14px}.detail-title{display:flex;justify-content:space-between}.detail-title strong{color:#3168ee}.dimension-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:7px;margin:12px 0}.dimension-grid div{padding:9px;background:#f7f9fd;border-radius:9px}.dimension-grid span,.dimension-grid b{display:block;font-size:12px}.dimension-grid span{color:var(--muted);margin-bottom:3px}.detail-card p{color:var(--muted)}.missing{padding:9px;border-radius:9px;background:#fff5f0;color:#a94d2d;font-size:13px}@media(max-width:700px){.dimension-grid{grid-template-columns:repeat(2,1fr)}}
</style>
