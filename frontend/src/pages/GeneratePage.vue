<template>
  <AppShell>
    <div class="generate-layout">
      <section class="panel form-panel">
        <div class="panel-title">
          <div><h3>发起学习任务</h3><p>绑定正式路线与来源策略，输出完整学习闭环</p></div>
        </div>
        <el-form label-position="top">
          <el-form-item label="目标路线">
            <el-select v-model="form.track_code" filterable @change="loadPathways">
              <el-option v-for="track in tracks" :key="track.code" :label="`${track.name} · ${track.role}`" :value="track.code" />
            </el-select>
          </el-form-item>
          <el-form-item label="细分学习路线">
            <el-select v-model="form.pathway_id" filterable placeholder="请选择具体技术路线">
              <el-option
                v-for="pathway in pathways"
                :key="pathway.id"
                :label="`${pathway.name} · ${pathway.estimated_months} 个月`"
                :value="pathway.id"
              />
            </el-select>
          </el-form-item>
          <div v-if="selectedPathway" class="pathway-preview">
            <div><b>{{ selectedPathway.name }}</b><span>{{ selectedPathway.stages.length }} 个阶段 · 难度 {{ selectedPathway.difficulty }}/5</span></div>
            <p>{{ selectedPathway.suitable_for }}</p>
            <small>最终里程碑：{{ selectedPathway.milestone }}</small>
          </div>
          <el-form-item label="本次目标">
            <el-input v-model="form.goal" type="textarea" :rows="3" placeholder="例如：完成一个可评测、可观测的多智能体项目" />
          </el-form-item>
          <el-form-item label="聚焦主题（可选）">
            <el-input v-model="form.topic" placeholder="例如：状态图、工具调用和轨迹评测" />
          </el-form-item>

          <el-form-item label="资料来源策略">
            <div class="mode-grid">
              <label v-for="mode in sourceModes" :key="mode.code" :class="{ selected: form.source_mode === mode.code }">
                <input v-model="form.source_mode" type="radio" :value="mode.code" />
                <b>{{ mode.name }}</b>
                <span>{{ mode.description }}</span>
              </label>
            </div>
          </el-form-item>

          <div v-if="needsExternal" class="external-config">
            <el-alert
              v-if="!configs.length"
              title="尚未配置外部服务；本次仍可运行，缺失能力会自动降级到本地审核知识库。"
              type="warning"
              :closable="false"
              show-icon
            />
            <el-form-item v-if="needsSearch" label="联网搜索服务">
              <el-select v-model="form.search_config_id" clearable placeholder="未选择时自动降级">
                <el-option
                  v-for="item in searchConfigs"
                  :key="item.id"
                  :label="`${item.label} · ${item.key_available ? '密钥可用' : '需装载密钥'}`"
                  :value="item.id"
                  :disabled="!item.enabled || !item.key_available"
                />
              </el-select>
            </el-form-item>
            <el-form-item v-if="needsLlm" label="AI 模型服务">
              <el-select v-model="form.llm_config_id" clearable placeholder="未选择时自动降级">
                <el-option
                  v-for="item in llmConfigs"
                  :key="item.id"
                  :label="`${item.label} · ${item.model} · ${item.key_available ? '密钥可用' : '需装载密钥'}`"
                  :value="item.id"
                  :disabled="!item.enabled || !item.key_available"
                />
              </el-select>
            </el-form-item>
            <el-button link type="primary" @click="router.push('/integrations')">管理 AI 与搜索服务 →</el-button>
          </div>

          <el-alert
            class="audit-alert"
            title="运行会保存结构化 Agent 轨迹、候选方案、来源版本、仲裁结果与质量指标；API Key 永不进入这些记录。"
            type="info"
            :closable="false"
            show-icon
          />
          <el-button type="primary" class="run" :loading="running" @click="generate">
            运行六 Agent 闭环
          </el-button>
        </el-form>
      </section>

      <section class="panel pipeline-panel">
        <div class="panel-title"><div><h3>协作流程</h3><p>完成后展示后端真实 Agent 事件；不使用前端计时动画冒充执行进度</p></div></div>
        <el-alert v-if="running" class="running-alert" title="后端正在执行画像、检索、双方案生成和仲裁，请保持页面打开。" type="info" :closable="false" show-icon />
        <div class="pipeline">
          <div v-for="(agent,index) in agents" :key="agent.code" :class="['agent',statusFor(agent.code)]">
            <span>{{ index+1 }}</span>
            <div><b>{{ agent.name }}</b><small>{{ agent.desc }}</small></div>
            <i>{{ statusText(agent.code) }}</i>
          </div>
        </div>
      </section>
    </div>

    <section v-if="result" class="panel result">
      <div class="panel-title">
        <div><h3>生成完成</h3><p>{{ result.goal }} · {{ result.route_match.track_name }}</p></div>
        <el-tag type="success">已完成</el-tag>
      </div>
      <div class="metric-row">
        <button v-for="(value,key) in result.quality_metrics" :key="key" @click="openMetric(String(key),value)">
          <span>{{ metricLabel(String(key)) }}</span><strong>{{ formatMetric(String(key),value) }}</strong>
        </button>
      </div>
      <div v-if="result.source_audit" class="source-audit">
        <div>
          <span>请求策略</span><b>{{ modeName(result.source_audit.requested_mode) }}</b>
        </div>
        <div>
          <span>实际策略</span><b>{{ modeName(result.source_audit.effective_mode) }}</b>
        </div>
        <div>
          <span>本地目录</span><b>{{ result.source_audit.layers?.knowledge?.catalog_version }}</b>
        </div>
        <div>
          <span>联网结果</span><b>{{ result.source_audit.layers?.web?.result_count || 0 }} 条</b>
        </div>
        <div v-if="result.source_audit.layers?.ai?.model">
          <span>生成模型</span><b>{{ result.source_audit.layers.ai.model }}</b>
        </div>
      </div>
      <el-alert
        v-for="message in result.source_audit?.fallbacks || []"
        :key="message"
        class="fallback"
        :title="message"
        type="warning"
        :closable="false"
        show-icon
      />
      <div class="actions">
        <el-button type="primary" @click="router.push(`/session/${result.id}`)">查看完整会话</el-button>
        <el-button @click="router.push('/resources')">查看生成资源</el-button>
        <el-button @click="router.push('/plan')">进入学习计划</el-button>
      </div>
    </section>

    <DetailModal v-model="detail.visible" :title="detail.title">
      <p class="metric-explain">{{ detail.explain }}</p>
      <HumanDetail :value="detail.value" :hint="detail.explain" />
    </DetailModal>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import AppShell from '@/components/layout/AppShell.vue'
import DetailModal from '@/components/common/DetailModal.vue'
import HumanDetail from '@/components/common/HumanDetail.vue'
import { getData, postData } from '@/api'
import type { LearningSession, PathwayVariant, TrackSummary } from '@/types/domain'

const router = useRouter()
const route = useRoute()
const tracks = ref<TrackSummary[]>([])
const pathways = ref<PathwayVariant[]>([])
const configs = ref<any[]>([])
const sourceModes = ref<any[]>([])
const running = ref(false)
const result = ref<(LearningSession & { source_audit?: any }) | null>(null)
const form = reactive({
  track_code: 'agent_engineering',
  pathway_id: null as string | null,
  goal: '完成一个可评测、可观测的多智能体项目',
  topic: '状态图、工具调用与轨迹评测',
  source_mode: 'knowledge_only',
  llm_config_id: null as string | null,
  search_config_id: null as string | null,
})
const detail = reactive({ visible: false, title: '', value: null as any, explain: '' })
const agents = [
  { code:'lms', name:'学情建模 Agent', desc:'画像与技能缺口' },
  { code:'krs', name:'知识检索 Agent', desc:'路线、来源与证据重排' },
  { code:'dgs_a', name:'严谨生成 Agent', desc:'前置依赖优先' },
  { code:'dgs_b', name:'项目生成 Agent', desc:'项目挑战优先' },
  { code:'ars', name:'仲裁审核 Agent', desc:'评分、辩论与融合' },
  { code:'tis', name:'导学交互 Agent', desc:'追问与下一行动' },
]
const llmConfigs = computed(() => configs.value.filter((item) => item.service_type === 'llm'))
const searchConfigs = computed(() => configs.value.filter((item) => item.service_type === 'search'))
const needsLlm = computed(() => ['knowledge_ai', 'full'].includes(form.source_mode))
const needsSearch = computed(() => ['knowledge_web', 'full'].includes(form.source_mode))
const needsExternal = computed(() => needsLlm.value || needsSearch.value)
const selectedPathway = computed(() => pathways.value.find((item) => item.id === form.pathway_id))

onMounted(async () => {
  const [trackData, integrationData, catalog] = await Promise.all([
    getData<{items: TrackSummary[]}>('/tracks'),
    getData<{items: any[]}>('/integrations/providers'),
    getData<any>('/integrations/providers/catalog'),
  ])
  tracks.value = trackData.items
  configs.value = integrationData.items
  sourceModes.value = catalog.source_modes
  if (typeof route.query.track === 'string' && tracks.value.some((item) => item.code === route.query.track)) {
    form.track_code = route.query.track
  }
  await loadPathways()
  if (typeof route.query.pathway === 'string' && pathways.value.some((item) => item.id === route.query.pathway)) {
    form.pathway_id = route.query.pathway
  }
})

async function loadPathways() {
  const data = await getData<{items: PathwayVariant[]}>(`/tracks/${form.track_code}/pathways`)
  pathways.value = data.items
  if (!pathways.value.some((item) => item.id === form.pathway_id)) {
    form.pathway_id = pathways.value[0]?.id || null
  }
}

async function generate() {
  if (!form.goal.trim()) return ElMessage.warning('请填写本次目标')
  running.value = true
  result.value = null
  try {
    result.value = await postData<any>('/sessions', form)
    ElMessage.success(result.value?.source_audit?.fallback_triggered ? '生成完成，部分外部能力已安全降级' : '六 Agent 闭环已完成')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '生成失败')
  } finally {
    running.value = false
  }
}
function eventFor(code: string) { return result.value?.events?.find((item) => item.agent_code === code) }
function statusFor(code: string) { return eventFor(code) ? 'done' : running.value ? 'queued' : 'waiting' }
function statusText(code: string) { return eventFor(code) ? '已完成' : running.value ? '后端处理中' : '等待任务' }
function metricLabel(key: string) { return ({ total:'质量总分', knowledge_coverage:'知识覆盖', citation_coverage:'引用覆盖', citation_integrity:'引用完整性', profile_fit:'画像适配', prerequisite_violations:'前置冲突', hallucination_risk:'未引用风险估计' } as any)[key] || key }
function formatMetric(key: string, value: any) { return ['knowledge_coverage','citation_coverage','citation_integrity','profile_fit','hallucination_risk'].includes(key) ? `${Math.round(Number(value) * 100)}%` : value }
function modeName(code: string) { return sourceModes.value.find((item) => item.code === code)?.name || code }
function openMetric(key: string, value: any) {
  detail.title = metricLabel(key)
  detail.value = value
  detail.explain = ({ knowledge_coverage:'正式路线专项技能被内容覆盖的比例。', citation_coverage:'讲义章节具有有效知识片段引用的比例。', citation_integrity:'所有章节引用均能在本次检索证据集中找到的比例。', profile_fit:'内容难度与当前画像深度的匹配程度。', prerequisite_violations:'学习顺序违反技能 DAG 前置关系的数量。', hallucination_risk:'基于缺失引用估算的风险上界，不冒充真实幻视率测试。', total:'仲裁器对覆盖、引用、适配和前置关系的加权结果。' } as any)[key] || ''
  detail.visible = true
}
</script>

<style scoped>
.generate-layout{display:grid;grid-template-columns:1fr 1fr;gap:18px}.el-select{width:100%}.pathway-preview{padding:14px;border:1px solid #cddcff;border-radius:14px;background:#f3f7ff;margin:-4px 0 18px}.pathway-preview>div{display:flex;justify-content:space-between;gap:12px}.pathway-preview span,.pathway-preview p,.pathway-preview small{color:var(--muted)}.pathway-preview p{margin:8px 0;line-height:1.6}.pathway-preview small{display:block}.mode-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;width:100%}.mode-grid label{display:block;padding:13px;border:1px solid var(--line);border-radius:13px;background:#f8fafd;cursor:pointer;transition:.2s}.mode-grid label.selected{border-color:#3168ee;background:#eef4ff;box-shadow:0 0 0 3px rgba(49,104,238,.08)}.mode-grid input{display:none}.mode-grid b,.mode-grid span{display:block}.mode-grid span{color:var(--muted);font-size:12px;line-height:1.5;margin-top:4px}.external-config{padding:14px;border-radius:14px;background:#f7f9fd;margin-bottom:15px}.audit-alert,.running-alert{margin-top:14px}.run{width:100%;height:46px;margin-top:20px}.pipeline{display:grid;gap:10px}.agent{display:grid;grid-template-columns:38px 1fr 92px;gap:12px;align-items:center;padding:14px;border-radius:14px;background:#f7f9fd;border:1px solid var(--line);transition:.3s}.agent>span{width:34px;height:34px;border-radius:11px;display:grid;place-items:center;background:#e7edf8;color:#6f7d94}.agent b,.agent small{display:block}.agent small{color:var(--muted);margin-top:4px}.agent i{font-style:normal;font-size:12px;text-align:right}.agent.queued{border-color:#b9caee;background:#f3f7ff}.agent.queued>span{background:#dce7ff;color:#3168ee}.agent.done>span{background:#17a673;color:white}.agent.done i{color:#17a673}.result{margin-top:18px}.metric-row{display:grid;grid-template-columns:repeat(6,1fr);gap:10px}.metric-row button{border:1px solid var(--line);background:#f7f9fd;border-radius:14px;padding:14px;cursor:pointer}.metric-row span,.metric-row strong{display:block}.metric-row span{font-size:12px;color:var(--muted)}.metric-row strong{font-size:22px;margin-top:7px}.source-audit{display:flex;flex-wrap:wrap;gap:10px;margin-top:18px}.source-audit div{padding:12px 16px;border-radius:12px;background:#eef4ff}.source-audit span,.source-audit b{display:block}.source-audit span{font-size:11px;color:var(--muted);margin-bottom:4px}.fallback{margin-top:10px}.actions{margin-top:20px}.metric-explain{font-size:16px;line-height:1.8}@media(max-width:1000px){.generate-layout{grid-template-columns:1fr}.metric-row{grid-template-columns:repeat(3,1fr)}}@media(max-width:600px){.mode-grid,.metric-row{grid-template-columns:1fr 1fr}}
</style>
