<template>
  <AppShell>
    <el-alert
      v-if="!isAdmin"
      title="当前账号是学习者账号"
      description="治理操作需要管理员身份。管理员账号只能通过服务端显式环境变量初始化，不提供默认弱口令。"
      type="warning"
      :closable="false"
      show-icon
    />

    <template v-else>
      <div class="metric-grid">
        <article v-for="item in metrics" :key="item.label" class="metric clickable" @click="open(item.label, item)">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
          <small>{{ item.note }}</small>
        </article>
      </div>

      <section class="panel section">
        <div class="panel-title">
          <div>
            <h3>冻结评测与冲奖证据</h3>
            <p>6 类合成画像、60 个冻结任务、15 条路线；结果由当前代码现场复算</p>
          </div>
          <el-button type="primary" :loading="evaluationRunning" @click="runEvaluation">
            运行 60 项离线评测
          </el-button>
        </div>
        <div v-if="evaluationSummary.dataset" class="evaluation-overview">
          <el-statistic title="差异化画像" :value="evaluationSummary.dataset.profile_count" suffix=" 类" />
          <el-statistic title="冻结任务" :value="evaluationSummary.dataset.task_count" suffix=" 项" />
          <el-statistic title="正式路线覆盖" :value="evaluationSummary.dataset.track_count" suffix=" 条" />
          <el-statistic title="冻结版本" :value="evaluationSummary.dataset.task_dataset_version" />
        </div>
        <el-alert
          v-if="!evaluationRun"
          title="当前只展示数据集完整性；点击运行后才展示系统实测指标。外部模型对照组尚未运行时会明确标记，不用估算值冒充结果。"
          type="info"
          :closable="false"
          show-icon
        />
        <template v-else>
          <div class="metric-grid evaluation-results">
            <article v-for="(value, key) in evaluationRun.system.metrics" :key="key" class="metric">
              <span>{{ evaluationMetricLabel(String(key)) }}</span>
              <strong>{{ formatEvaluationMetric(String(key), value) }}</strong>
              <small v-if="key in evaluationRun.system.target_status">
                {{ evaluationRun.system.target_status[key] ? '达到目标' : '未达到目标' }}
              </small>
            </article>
          </div>
          <el-alert
            v-for="baseline in evaluationRun.baselines"
            :key="baseline.name"
            class="baseline-alert"
            :title="`${baseline.name}：${baseline.status}`"
            :description="baseline.reason"
            type="warning"
            :closable="false"
            show-icon
          />
        </template>
      </section>

      <div class="grid two section">
        <section class="panel">
          <div class="panel-title">
            <div><h3>系统健康</h3><p>运行配置与知识目录版本</p></div>
            <el-button :loading="loading" @click="load">重新检查</el-button>
          </div>
          <el-descriptions :column="1" border>
            <el-descriptions-item v-for="(value, key) in health" :key="key" :label="healthLabel(String(key))">
              {{ value }}
            </el-descriptions-item>
          </el-descriptions>
        </section>

        <section class="panel">
          <div class="panel-title">
            <div><h3>路线完整性</h3><p>正式路线均具备技能、项目和验收标准</p></div>
          </div>
          <el-table :data="tracks" max-height="420">
            <el-table-column prop="name" label="路线" />
            <el-table-column prop="skill_count" label="专项技能" width="100" />
            <el-table-column prop="project" label="代表项目" />
          </el-table>
        </section>
      </div>

      <section class="panel section">
        <div class="panel-title">
          <div>
            <h3>知识共建审核</h3>
            <p>审核通过后才会进入检索和六 Agent 生成证据链</p>
          </div>
          <div class="tag-row">
            <el-radio-group v-model="documentStatus" @change="loadDocuments">
              <el-radio-button label="pending">待审核</el-radio-button>
              <el-radio-button label="approved">已通过</el-radio-button>
              <el-radio-button label="rejected">已驳回</el-radio-button>
            </el-radio-group>
            <el-button :loading="documentLoading" @click="loadDocuments">刷新</el-button>
          </div>
        </div>
        <el-table :data="documents" empty-text="当前没有对应状态的知识贡献">
          <el-table-column prop="title" label="标题" min-width="180" />
          <el-table-column label="路线" min-width="140">
            <template #default="{ row }">{{ trackName(row.track_code) }}</template>
          </el-table-column>
          <el-table-column prop="content_version" label="版本" width="110" />
          <el-table-column prop="license_type" label="许可" width="150" />
          <el-table-column label="来源" width="90">
            <template #default="{ row }">
              <a :href="row.source_url" target="_blank" rel="noreferrer">核验</a>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180">
            <template #default="{ row }">
              <el-button link type="primary" @click="inspect(row)">查看正文</el-button>
              <el-button v-if="row.status === 'pending'" link type="success" @click="review(row, 'approved')">通过</el-button>
              <el-button v-if="row.status === 'pending'" link type="danger" @click="review(row, 'rejected')">驳回</el-button>
            </template>
          </el-table-column>
        </el-table>
      </section>
    </template>

    <el-dialog v-model="reviewDialog.visible" :title="reviewDialog.status === 'approved' ? '通过知识贡献' : '驳回知识贡献'" width="min(560px, 92vw)">
      <p><b>{{ reviewDialog.row?.title }}</b></p>
      <el-input
        v-model="reviewDialog.notes"
        type="textarea"
        :rows="5"
        maxlength="2000"
        show-word-limit
        :placeholder="reviewDialog.status === 'approved' ? '记录核验依据、版本适用范围（建议填写）' : '说明驳回原因和修改建议（必填）'"
      />
      <template #footer>
        <el-button @click="reviewDialog.visible = false">取消</el-button>
        <el-button
          :type="reviewDialog.status === 'approved' ? 'success' : 'danger'"
          :loading="reviewing"
          @click="confirmReview"
        >
          确认{{ reviewDialog.status === 'approved' ? '通过' : '驳回' }}
        </el-button>
      </template>
    </el-dialog>

    <DetailModal v-model="detail.visible" :title="detail.title">
      <template v-if="detail.data?.content">
        <p class="document-content">{{ detail.data.content }}</p>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="版本">{{ detail.data.content_version }}</el-descriptions-item>
          <el-descriptions-item label="许可">{{ detail.data.license_type }}</el-descriptions-item>
          <el-descriptions-item label="来源">{{ detail.data.source_url }}</el-descriptions-item>
          <el-descriptions-item v-if="detail.data.review_notes" label="审核意见">{{ detail.data.review_notes }}</el-descriptions-item>
        </el-descriptions>
      </template>
      <pre v-else>{{ JSON.stringify(detail.data, null, 2) }}</pre>
    </DetailModal>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import AppShell from '@/components/layout/AppShell.vue'
import DetailModal from '@/components/common/DetailModal.vue'
import { getData, postData, putData } from '@/api'
import { useUserStore } from '@/stores/user'

const user = useUserStore()
const isAdmin = computed(() => user.current?.role === 'admin')
const health = reactive<any>({})
const tracks = ref<any[]>([])
const sessions = ref<any[]>([])
const documents = ref<any[]>([])
const evaluationSummary = reactive<any>({})
const evaluationRun = ref<any>(null)
const loading = ref(false)
const documentLoading = ref(false)
const reviewing = ref(false)
const evaluationRunning = ref(false)
const documentStatus = ref('pending')
const detail = reactive({ visible: false, title: '', data: null as any })
const reviewDialog = reactive({
  visible: false,
  row: null as any,
  status: 'approved' as 'approved' | 'rejected',
  notes: '',
})

const averageQuality = computed(() =>
  sessions.value.length
    ? Math.round(sessions.value.reduce((sum, session) => sum + Number(session.quality_metrics?.total || 0), 0) / sessions.value.length)
    : 0,
)
const metrics = computed(() => [
  { label: '正式路线', value: health.track_count || 0, note: '覆盖计算机领域主要细分方向' },
  { label: '已完成会话', value: sessions.value.filter((session) => session.status === 'completed').length, note: '来自当前治理账号可见记录' },
  { label: '平均质量', value: averageQuality.value, note: '最近会话仲裁质量总分' },
  { label: '待审核知识', value: documentStatus.value === 'pending' ? documents.value.length : '-', note: '未经审核不会进入正式生成' },
])

onMounted(async () => {
  if (isAdmin.value) await load()
})

async function load() {
  loading.value = true
  try {
    Object.assign(health, await getData('/health'))
    tracks.value = (await getData<{ items: any[] }>('/tracks')).items
    sessions.value = (await getData<{ items: any[] }>('/sessions')).items
    Object.assign(evaluationSummary, await getData('/evaluation/summary'))
    await loadDocuments()
  } finally {
    loading.value = false
  }
}

async function runEvaluation() {
  evaluationRunning.value = true
  try {
    evaluationRun.value = await postData('/evaluation/run')
    ElMessage.success('60 项冻结评测已由当前代码现场复算完成')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '冻结评测运行失败')
  } finally {
    evaluationRunning.value = false
  }
}

async function loadDocuments() {
  documentLoading.value = true
  try {
    documents.value = (await getData<{ items: any[] }>('/knowledge/documents', {
      params: { status: documentStatus.value },
    })).items
  } finally {
    documentLoading.value = false
  }
}

function review(row: any, status: 'approved' | 'rejected') {
  Object.assign(reviewDialog, { visible: true, row, status, notes: '' })
}

async function confirmReview() {
  if (reviewDialog.status === 'rejected' && !reviewDialog.notes.trim()) {
    ElMessage.warning('驳回时必须说明原因和修改建议')
    return
  }
  reviewing.value = true
  try {
    await putData(`/knowledge/documents/${reviewDialog.row.id}/review`, {
      status: reviewDialog.status,
      review_notes: reviewDialog.notes.trim(),
    })
    ElMessage.success(reviewDialog.status === 'approved' ? '知识已审核通过并进入检索库' : '知识已驳回')
    reviewDialog.visible = false
    await loadDocuments()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '审核操作失败')
  } finally {
    reviewing.value = false
  }
}

function trackName(code: string) {
  return tracks.value.find((item) => item.code === code)?.name || code
}
function healthLabel(key: string) {
  return ({ version: '应用版本', environment: '运行环境', catalog_version: '目录版本', track_count: '路线数量', llm_enabled: '平台模型状态' } as Record<string, string>)[key] || key
}
function evaluationMetricLabel(key: string) {
  return ({
    task_success_rate: '任务通过率',
    route_top3_accuracy: '路线 Top3 准确率',
    knowledge_coverage: '知识覆盖率',
    citation_coverage: '引用覆盖率',
    hallucination_risk_upper_bound: '幻觉风险上界',
    prerequisite_violation_rate: '前置依赖违反率',
    task_p95_ms: '单任务 P95',
    total_duration_ms: '总耗时',
  } as Record<string, string>)[key] || key
}
function formatEvaluationMetric(key: string, value: any) {
  if (key.endsWith('_ms')) return `${value} ms`
  if (['task_success_rate', 'route_top3_accuracy', 'knowledge_coverage', 'citation_coverage', 'hallucination_risk_upper_bound', 'prerequisite_violation_rate'].includes(key)) {
    return `${Math.round(Number(value) * 1000) / 10}%`
  }
  return value
}
function open(title: string, data: any) {
  detail.title = title
  detail.data = data
  detail.visible = true
}
function inspect(row: any) {
  open(row.title, row)
}
</script>

<style scoped>
.metric-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:15px}.metric small{display:block;color:var(--muted);margin-top:8px}.section{margin-top:18px}.evaluation-overview{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;padding:18px;background:#f7f9fd;border-radius:14px;margin-bottom:16px}.evaluation-results{margin:18px 0}.evaluation-results .metric strong{font-size:22px}.baseline-alert{margin-top:10px}pre{white-space:pre-wrap;background:#f7f9fd;padding:16px;border-radius:12px}.document-content{white-space:pre-wrap;line-height:1.8;color:#34415a}@media(max-width:900px){.metric-grid,.evaluation-overview{grid-template-columns:repeat(2,1fr)}}@media(max-width:550px){.metric-grid,.evaluation-overview{grid-template-columns:1fr}}
</style>
