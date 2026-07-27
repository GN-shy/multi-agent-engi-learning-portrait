<template>
  <AppShell>
    <section class="page-head">
      <div>
        <span class="eyebrow">多路线学习编排</span>
        <h2>把多个职业方向，合成一条学得完的路线</h2>
        <p>不是简单拼接课程：系统会去重公共技术、按前置依赖排序，并为每项学习任务给出成果证据和验收标准。</p>
      </div>
      <div class="head-stats" v-if="routePlan">
        <div><strong>{{ routePlan.pathway_count || routePlan.pathways?.length }}</strong><span>条路线</span></div>
        <div><strong>{{ routePlan.technology_count }}</strong><span>项技术</span></div>
        <div><strong>{{ routePlan.total_weeks }}</strong><span>预计周数</span></div>
      </div>
    </section>

    <div class="generate-layout">
      <section class="panel form-panel">
        <div class="panel-title">
          <div><h3>① 选择细分方向</h3><p>最多 6 条，可跨前端、后端、AI、算法、嵌入式等主方向组合</p></div>
          <el-tag>{{ form.pathway_ids.length }}/6</el-tag>
        </div>
        <el-form label-position="top">
          <el-form-item label="细分学习路线（可多选）">
            <el-select
              v-model="form.pathway_ids"
              multiple
              filterable
              collapse-tags
              collapse-tags-tooltip
              :max-collapse-tags="3"
              placeholder="输入技术或路线名称，例如 Vue、Java、Agent"
              @change="onPathwaysChanged"
            >
              <el-option
                v-for="pathway in pathways"
                :key="pathway.id"
                :label="`${pathway.track_name} · ${pathway.name}`"
                :value="pathway.id"
                :disabled="form.pathway_ids.length >= 6 && !form.pathway_ids.includes(pathway.id)"
              >
                <div class="option-row">
                  <span><b>{{ pathway.name }}</b><small>{{ pathway.track_name }}</small></span>
                  <i>{{ pathway.estimated_months }} 个月 · {{ pathway.career?.salary_range }}</i>
                </div>
              </el-option>
            </el-select>
          </el-form-item>

          <div v-if="selectedPathways.length" class="selected-route-list">
            <article v-for="pathway in selectedPathways" :key="pathway.id">
              <button class="remove" title="移除" @click="removePathway(pathway.id)">×</button>
              <span>{{ pathway.track_name }}</span>
              <b>{{ pathway.name }}</b>
              <p>{{ pathway.career?.roles.slice(0, 3).join('、') }}</p>
              <div><i>{{ pathway.career?.salary_range }}</i><i>{{ pathway.career?.education.minimum }}</i></div>
            </article>
          </div>
          <el-alert
            v-else
            title="请至少选择一条细分路线。你也可以先到“学习路线”页比较就业方向。"
            type="info"
            :closable="false"
            show-icon
          />
          <el-button link type="primary" @click="router.push('/tracks')">去比较全部 29 条路线 →</el-button>

          <div class="panel-title task-title">
            <div><h3>② 定义学习目标</h3><p>目标越具体，Agent 给出的任务和验收标准越有针对性</p></div>
          </div>
          <el-form-item label="本次目标">
            <el-input v-model="form.goal" type="textarea" :rows="3" placeholder="例如：在 6 个月内完成一个 Vue + FastAPI + Agent 的可部署作品，并用于秋招" />
          </el-form-item>
          <el-form-item label="当前最想解决的问题（可选）">
            <el-input v-model="form.topic" placeholder="例如：不知道前后端与 Agent 应按什么顺序学习" />
          </el-form-item>

          <div class="panel-title task-title">
            <div><h3>③ 选择资料来源</h3><p>所有模式都优先使用本地审核知识库，外部能力不可用时自动降级</p></div>
          </div>
          <div class="mode-grid">
            <label v-for="mode in sourceModes" :key="mode.code" :class="{ selected: form.source_mode === mode.code }">
              <input v-model="form.source_mode" type="radio" :value="mode.code" />
              <b>{{ mode.name }}</b>
              <span>{{ mode.description }}</span>
            </label>
          </div>

          <div v-if="needsExternal" class="external-config">
            <el-alert v-if="!configs.length" title="尚未配置外部服务，本次会安全降级到本地知识库。" type="warning" :closable="false" show-icon />
            <el-form-item v-if="needsSearch" label="联网搜索服务">
              <el-select v-model="form.search_config_id" clearable placeholder="不选择则自动降级">
                <el-option v-for="item in searchConfigs" :key="item.id" :label="`${item.label} · ${item.key_available ? '密钥可用' : '需装载密钥'}`" :value="item.id" :disabled="!item.enabled || !item.key_available" />
              </el-select>
            </el-form-item>
            <el-form-item v-if="needsLlm" label="AI 模型服务">
              <el-select v-model="form.llm_config_id" clearable placeholder="不选择则自动降级">
                <el-option v-for="item in llmConfigs" :key="item.id" :label="`${item.label} · ${item.model}`" :value="item.id" :disabled="!item.enabled || !item.key_available" />
              </el-select>
            </el-form-item>
            <el-button link type="primary" @click="router.push('/integrations')">管理 AI 与搜索服务 →</el-button>
          </div>

          <el-alert class="audit-alert" title="运行会保存 Agent 轨迹、候选方案、证据来源和仲裁指标；API Key 不进入轨迹、报告或导出文件。" type="info" :closable="false" show-icon />
          <el-button type="primary" class="run" :loading="running" :disabled="!form.pathway_ids.length" @click="generate">
            运行六 Agent，生成组合学习路线
          </el-button>
        </el-form>
      </section>

      <section class="preview-column">
        <div class="panel route-preview">
          <div class="panel-title">
            <div><h3>组合路线预演</h3><p>生成前先看清学习顺序、投入和就业终点</p></div>
            <el-button :loading="composing" circle @click="composeRoute">↻</el-button>
          </div>
          <template v-if="routePlan">
            <div class="summary-grid">
              <div><span>预计投入</span><b>{{ routePlan.total_weeks }} 周</b><small>约 {{ routePlan.estimated_months }} 个月</small></div>
              <div><span>技术栈</span><b>{{ routePlan.technology_count }} 项</b><small>重复项已去重</small></div>
              <div><span>学习阶段</span><b>{{ routePlan.phases.length }} 段</b><small>按依赖重排</small></div>
            </div>
            <div class="stack-cloud">
              <span v-for="topic in routeTechnologies.slice(0, 24)" :key="topic">{{ topic }}</span>
              <i v-if="routeTechnologies.length > 24">+{{ routeTechnologies.length - 24 }} 项</i>
            </div>
            <ol class="phase-list">
              <li v-for="(phase, phaseIndex) in routePlan.phases" :key="phase.id">
                <div class="phase-marker">{{ phaseIndex + 1 }}</div>
                <article>
                  <header>
                    <div><b>{{ phase.name }}</b><span>第 {{ phase.week_start }}–{{ phase.week_end }} 周</span></div>
                    <el-tag effect="plain">{{ phase.pathway_names.join(' + ') }}</el-tag>
                  </header>
                  <div class="phase-tasks">
                    <div v-for="task in phase.tasks.slice(0, 5)" :key="`${task.pathway_id}-${task.title}`">
                      <b>{{ task.title }}</b>
                      <span>{{ task.learning_action }}</span>
                      <small>验收：{{ task.acceptance }}</small>
                    </div>
                    <p v-if="phase.tasks.length > 5">另有 {{ phase.tasks.length - 5 }} 项任务，生成后在学习计划中完整显示</p>
                  </div>
                </article>
              </li>
            </ol>
            <div class="optimization">
              <b>为什么这样排序</b>
              <p v-for="note in routePlan.optimization_notes" :key="note">✓ {{ note }}</p>
            </div>
          </template>
          <el-empty v-else description="选择路线后，这里会立即生成组合顺序" />
        </div>

        <div class="panel pipeline-panel">
          <div class="panel-title"><div><h3>六 Agent 协作</h3><p>真实后端事件，不用前端动画冒充执行状态</p></div></div>
          <div class="pipeline">
            <div v-for="(agent, index) in agents" :key="agent.code" :class="['agent', statusFor(agent.code)]">
              <span>{{ index + 1 }}</span>
              <div><b>{{ agent.name }}</b><small>{{ agent.desc }}</small></div>
              <i>{{ statusText(agent.code) }}</i>
            </div>
          </div>
        </div>
      </section>
    </div>

    <section v-if="result" class="panel result">
      <div class="panel-title">
        <div><span class="eyebrow">已通过仲裁</span><h3>组合学习路线生成完成</h3><p>{{ result.goal }} · {{ selectedPathways.map((item) => item.name).join(' + ') }}</p></div>
        <el-tag type="success" size="large">可执行</el-tag>
      </div>
      <div class="metric-row">
        <button v-for="(value, key) in result.quality_metrics" :key="key" @click="openMetric(String(key), value)">
          <span>{{ metricLabel(String(key)) }}</span><strong>{{ formatMetric(String(key), value) }}</strong>
        </button>
      </div>
      <el-alert v-if="Number(result.quality_metrics.hallucination_risk) <= .05" title="未引用风险估计 ≤ 5%，达到项目质量门槛；点击指标可查看口径。" type="success" :closable="false" show-icon />
      <el-alert v-for="message in result.source_audit?.fallbacks || []" :key="message" class="fallback" :title="message" type="warning" :closable="false" show-icon />
      <div class="actions">
        <el-button type="primary" @click="router.push('/plan')">进入可勾选的学习计划</el-button>
        <el-button @click="router.push(`/session/${result.id}`)">查看 Agent 协作证据</el-button>
        <el-button @click="router.push('/resources')">查看生成资料</el-button>
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
import type { ComposedRoute, LearningSession, PathwayVariant } from '@/types/domain'

const router = useRouter()
const route = useRoute()
const pathways = ref<PathwayVariant[]>([])
const configs = ref<any[]>([])
const sourceModes = ref<any[]>([])
const running = ref(false)
const composing = ref(false)
const routePlan = ref<(ComposedRoute & {pathway_count?: number}) | null>(null)
const result = ref<(LearningSession & {source_audit?: any}) | null>(null)
const form = reactive({
  track_code: '',
  pathway_ids: [] as string[],
  pathway_id: null as string | null,
  goal: '完成一个可部署、可演示、可进入作品集的跨方向项目，并达到目标岗位的能力要求',
  topic: '',
  source_mode: 'knowledge_only',
  llm_config_id: null as string | null,
  search_config_id: null as string | null,
})
const detail = reactive({ visible: false, title: '', value: null as any, explain: '' })
const agents = [
  { code: 'lms', name: '学情建模 Agent', desc: '识别基础、时间与技能缺口' },
  { code: 'krs', name: '知识检索 Agent', desc: '跨路线检索可信证据' },
  { code: 'dgs_a', name: '严谨方案 Agent', desc: '按前置依赖构建路线' },
  { code: 'dgs_b', name: '项目方案 Agent', desc: '用作品反推能力任务' },
  { code: 'ars', name: '仲裁审核 Agent', desc: '辩论、评分、质量闸门' },
  { code: 'tis', name: '导学交互 Agent', desc: '形成下一步可执行行动' },
]
const selectedPathways = computed(() => form.pathway_ids.map((id) => pathways.value.find((item) => item.id === id)).filter(Boolean) as PathwayVariant[])
const routeTechnologies = computed(() =>
  Array.from(new Set(routePlan.value?.stack_index.flatMap((item) => item.technologies) || [])),
)
const llmConfigs = computed(() => configs.value.filter((item) => item.service_type === 'llm'))
const searchConfigs = computed(() => configs.value.filter((item) => item.service_type === 'search'))
const needsLlm = computed(() => ['knowledge_ai', 'full'].includes(form.source_mode))
const needsSearch = computed(() => ['knowledge_web', 'full'].includes(form.source_mode))
const needsExternal = computed(() => needsLlm.value || needsSearch.value)

onMounted(async () => {
  const [pathData, integrationData, catalog] = await Promise.all([
    getData<{items: PathwayVariant[]}>('/tracks/pathways/catalog'),
    getData<{items: any[]}>('/integrations/providers'),
    getData<any>('/integrations/providers/catalog'),
  ])
  pathways.value = pathData.items
  configs.value = integrationData.items
  sourceModes.value = catalog.source_modes
  const queryIds = typeof route.query.pathways === 'string'
    ? route.query.pathways.split(',').filter(Boolean)
    : typeof route.query.pathway === 'string' ? [route.query.pathway] : []
  form.pathway_ids = queryIds.filter((id) => pathways.value.some((item) => item.id === id)).slice(0, 6)
  if (!form.pathway_ids.length) form.pathway_ids = ['agent-fullstack'].filter((id) => pathways.value.some((item) => item.id === id))
  await composeRoute()
})

function removePathway(id: string) {
  form.pathway_ids = form.pathway_ids.filter((item) => item !== id)
  onPathwaysChanged()
}
function onPathwaysChanged() {
  if (form.pathway_ids.length > 6) form.pathway_ids = form.pathway_ids.slice(0, 6)
  composeRoute()
}
async function composeRoute() {
  if (!form.pathway_ids.length) {
    routePlan.value = null
    return
  }
  composing.value = true
  try {
    routePlan.value = await postData<any>('/tracks/pathways/compose', { pathway_ids: form.pathway_ids, weekly_hours: 8 })
    form.track_code = selectedPathways.value[0]?.track_code || ''
    form.pathway_id = form.pathway_ids[0] || null
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '组合路线计算失败')
  } finally { composing.value = false }
}
async function generate() {
  if (!form.pathway_ids.length) return ElMessage.warning('请至少选择一条细分路线')
  if (!form.goal.trim()) return ElMessage.warning('请填写本次目标')
  running.value = true
  result.value = null
  try {
    result.value = await postData<any>('/sessions', form)
    ElMessage.success(result.value?.source_audit?.fallback_triggered ? '生成完成，部分外部能力已安全降级' : '六 Agent 组合路线已生成')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '生成失败')
  } finally { running.value = false }
}
function eventFor(code: string) { return result.value?.events?.find((item) => item.agent_code === code) }
function statusFor(code: string) { return eventFor(code) ? 'done' : running.value ? 'queued' : 'waiting' }
function statusText(code: string) { return eventFor(code) ? '已完成' : running.value ? '后端处理中' : '等待任务' }
function metricLabel(key: string) {
  return ({ total: '质量总分', knowledge_coverage: '知识覆盖', citation_coverage: '引用覆盖', citation_integrity: '引用完整性', profile_fit: '画像适配', prerequisite_violations: '前置冲突', hallucination_risk: '未引用风险估计' } as any)[key] || key
}
function formatMetric(key: string, value: any) {
  return ['knowledge_coverage', 'citation_coverage', 'citation_integrity', 'profile_fit', 'hallucination_risk'].includes(key) ? `${Math.round(Number(value) * 100)}%` : value
}
function openMetric(key: string, value: any) {
  detail.title = metricLabel(key)
  detail.value = value
  detail.explain = ({
    knowledge_coverage: '所选路线的目标技术被生成内容实际覆盖的比例。',
    citation_coverage: '内容段落具有有效证据引用的比例。',
    citation_integrity: '引用能在本次检索证据集中被验证的比例。',
    profile_fit: '内容难度、节奏与个人画像的匹配程度。',
    prerequisite_violations: '学习顺序违反技术前置依赖的数量，应为 0。',
    hallucination_risk: '基于未引用内容比例计算的风险上界，不冒充真实世界幻觉率。',
    total: '仲裁器综合覆盖、证据、画像适配和前置依赖后的质量评分。',
  } as any)[key] || ''
  detail.visible = true
}
</script>

<style scoped>
.page-head{display:flex;justify-content:space-between;align-items:center;gap:28px;padding:8px 4px 22px}.eyebrow{color:#2f67ee;font-size:12px;font-weight:800;letter-spacing:.08em}.page-head h2{font-size:29px;margin:7px 0}.page-head p{color:var(--muted);margin:0;line-height:1.7}.head-stats{display:flex;background:white;border:1px solid var(--line);border-radius:16px;overflow:hidden}.head-stats div{padding:14px 20px;text-align:center;border-right:1px solid var(--line)}.head-stats div:last-child{border:0}.head-stats strong,.head-stats span{display:block}.head-stats strong{font-size:21px;color:#2760e8}.head-stats span{font-size:11px;color:var(--muted)}.generate-layout{display:grid;grid-template-columns:minmax(0,1fr) minmax(430px,.92fr);gap:18px;align-items:start}.el-select{width:100%}.option-row{display:flex;justify-content:space-between;align-items:center;width:100%;gap:20px}.option-row span,.option-row b,.option-row small{display:block}.option-row small{font-size:11px;color:#8a95a9}.option-row i{font-style:normal;color:#6e7d95;font-size:12px}.selected-route-list{display:grid;grid-template-columns:repeat(2,1fr);gap:9px;margin-bottom:10px}.selected-route-list article{position:relative;padding:12px;border:1px solid #d6e0f7;border-radius:13px;background:#f7faff}.selected-route-list span,.selected-route-list b{display:block}.selected-route-list span{font-size:11px;color:#7385a7}.selected-route-list b{margin:3px 22px 5px 0}.selected-route-list p{font-size:12px;color:#60708b;margin:0 0 7px;line-height:1.5}.selected-route-list div{display:flex;gap:6px;flex-wrap:wrap}.selected-route-list i{font-style:normal;font-size:10px;background:white;border-radius:6px;padding:3px 6px;color:#52627b}.remove{position:absolute;right:8px;top:7px;border:0;background:none;font-size:18px;color:#8190a8;cursor:pointer}.task-title{margin-top:24px;padding-top:19px;border-top:1px solid var(--line)}.mode-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:9px}.mode-grid label{display:block;padding:12px;border:1px solid var(--line);border-radius:12px;background:#f8fafd;cursor:pointer}.mode-grid label.selected{border-color:#3168ee;background:#eef4ff;box-shadow:0 0 0 3px rgba(49,104,238,.08)}.mode-grid input{display:none}.mode-grid b,.mode-grid span{display:block}.mode-grid span{color:var(--muted);font-size:11px;line-height:1.5;margin-top:4px}.external-config{padding:13px;border-radius:13px;background:#f7f9fd;margin-top:14px}.audit-alert{margin-top:15px}.run{width:100%;height:48px;margin-top:18px}.preview-column{display:grid;gap:18px}.route-preview{max-height:980px;overflow:auto}.summary-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.summary-grid div{background:#f4f7fd;border-radius:12px;padding:12px}.summary-grid span,.summary-grid b,.summary-grid small{display:block}.summary-grid span,.summary-grid small{font-size:11px;color:var(--muted)}.summary-grid b{font-size:20px;margin:4px 0}.stack-cloud{display:flex;gap:5px;flex-wrap:wrap;margin:14px 0}.stack-cloud span,.stack-cloud i{font-size:10px;padding:4px 7px;border-radius:6px;background:#edf3ff;color:#2b60db;font-style:normal}.stack-cloud i{background:#f1f3f7;color:#6e798c}.phase-list{list-style:none;padding:0;margin:0;display:grid;gap:10px}.phase-list>li{display:grid;grid-template-columns:30px 1fr;gap:10px}.phase-marker{width:29px;height:29px;border-radius:10px;display:grid;place-items:center;background:#2862ea;color:white;font-weight:800}.phase-list article{border:1px solid var(--line);border-radius:13px;padding:11px;background:#fbfcfe}.phase-list header{display:flex;justify-content:space-between;align-items:flex-start;gap:10px}.phase-list header>div b,.phase-list header>div span{display:block}.phase-list header span{font-size:11px;color:var(--muted);margin-top:3px}.phase-tasks{display:grid;gap:7px;margin-top:10px}.phase-tasks>div{padding:8px;background:white;border-radius:8px;border-left:3px solid #5f86ea}.phase-tasks b,.phase-tasks span,.phase-tasks small{display:block}.phase-tasks b{font-size:12px}.phase-tasks span,.phase-tasks small{font-size:10px;color:#6d7a91;line-height:1.5;margin-top:2px}.phase-tasks p{font-size:11px;color:#3168ee}.optimization{margin-top:14px;padding:13px;border-radius:12px;background:#f2faf6}.optimization p{font-size:11px;color:#506a5e;margin:6px 0}.pipeline{display:grid;gap:8px}.agent{display:grid;grid-template-columns:34px 1fr 80px;gap:10px;align-items:center;padding:11px;border-radius:12px;background:#f7f9fd;border:1px solid var(--line)}.agent>span{width:31px;height:31px;border-radius:10px;display:grid;place-items:center;background:#e7edf8;color:#6f7d94}.agent b,.agent small{display:block}.agent small{color:var(--muted);font-size:11px;margin-top:3px}.agent i{font-style:normal;font-size:11px;text-align:right}.agent.queued{border-color:#b9caee;background:#f3f7ff}.agent.done>span{background:#17a673;color:white}.agent.done i{color:#17a673}.result{margin-top:18px}.metric-row{display:grid;grid-template-columns:repeat(6,1fr);gap:9px;margin-bottom:14px}.metric-row button{border:1px solid var(--line);background:#f7f9fd;border-radius:13px;padding:13px;cursor:pointer}.metric-row span,.metric-row strong{display:block}.metric-row span{font-size:11px;color:var(--muted)}.metric-row strong{font-size:20px;margin-top:6px}.fallback{margin-top:9px}.actions{margin-top:18px}.metric-explain{font-size:15px;line-height:1.8}@media(max-width:1100px){.generate-layout{grid-template-columns:1fr}.route-preview{max-height:none}.metric-row{grid-template-columns:repeat(3,1fr)}}@media(max-width:700px){.page-head{align-items:flex-start;flex-direction:column}.head-stats{width:100%}.head-stats div{flex:1}.selected-route-list,.mode-grid,.summary-grid,.metric-row{grid-template-columns:1fr}.phase-list header{flex-direction:column}}
</style>
