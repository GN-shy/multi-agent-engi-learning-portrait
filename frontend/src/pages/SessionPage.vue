<template>
  <AppShell>
    <div v-loading="loading">
      <section v-if="session" class="session-hero panel">
        <div>
          <div class="tag-row">
            <el-tag type="success">{{ valueLabel(session.status) }}</el-tag>
            <el-tag type="info">{{ routeLabel(session.track_code) }}</el-tag>
          </div>
          <h2>{{ session.goal }}</h2>
          <p>{{ session.topic || '综合能力提升任务' }}</p>
        </div>
        <div class="quality"><strong>{{ session.quality_metrics?.total || 0 }}</strong><span>本次生成质量</span></div>
      </section>

      <el-tabs v-if="session" v-model="active" class="tabs">
        <el-tab-pane label="协作过程" name="events">
          <section class="panel">
            <div class="panel-title">
              <div><h3>六 Agent 协作记录</h3><p>每一步都来自后端实际运行结果，不使用前端模拟数据</p></div>
              <el-tag type="success">{{ session.events?.length || 0 }} 步已完成</el-tag>
            </div>
            <div class="event-list">
              <article v-for="event in session.events" :key="event.sequence" class="event clickable" @click="openAgent(event)">
                <span>{{ event.sequence }}</span>
                <div>
                  <b>{{ agentLabel(event.agent_code) }}</b>
                  <p>{{ event.summary }}</p>
                </div>
                <div><el-tag type="success">{{ valueLabel(event.status) }}</el-tag><small>{{ event.duration_ms }} 毫秒</small></div>
              </article>
            </div>
          </section>
        </el-tab-pane>

        <el-tab-pane label="个性化讲义" name="lecture">
          <section class="panel">
            <ResourceContentRenderer type="lecture" :content="session.final_output?.lecture || {}" />
          </section>
        </el-tab-pane>

        <el-tab-pane label="项目实操" name="practice">
          <section class="panel">
            <ResourceContentRenderer type="practice" :content="session.final_output?.practice || {}" />
            <el-button class="go-action" type="primary" @click="router.push('/practice')">进入实操并提交证据</el-button>
          </section>
        </el-tab-pane>

        <el-tab-pane label="仲裁与来源" name="audit">
          <section class="panel">
            <div class="panel-title"><div><h3>双方案仲裁</h3><p>展示方案差异、交叉验证与最终选择理由</p></div></div>
            <ArbitrationPanel :data="session.arbitration || {}" />
          </section>

          <section class="panel source-panel">
            <div class="panel-title">
              <div><h3>知识依据</h3><p>点击查看来源内容、版本和原始链接</p></div>
              <el-tag>{{ session.evidence?.length || 0 }} 条</el-tag>
            </div>
            <div class="source-grid">
              <button v-for="item in session.evidence" :key="item.chunk_id" class="evidence clickable" @click="openSource(item)">
                <b>{{ item.title }}</b>
                <span>{{ item.source_title }}</span>
                <small>{{ item.content_version }} · {{ sourceLayer(item.source_layer) }}</small>
              </button>
            </div>
          </section>

          <section class="panel source-panel">
            <div class="panel-title"><div><h3>来源与生成记录</h3><p>用于解释系统实际使用了哪些能力；不包含 API Key</p></div></div>
            <div class="audit-grid">
              <div><span>请求策略</span><b>{{ sourceMode(session.source_audit?.requested_mode || session.source_mode) }}</b></div>
              <div><span>实际策略</span><b>{{ sourceMode(session.source_audit?.effective_mode) }}</b></div>
              <div><span>知识目录版本</span><b>{{ session.source_audit?.layers?.knowledge?.catalog_version || '暂无' }}</b></div>
              <div><span>联网结果</span><b>{{ session.source_audit?.layers?.web?.result_count || 0 }} 条</b></div>
              <div v-if="session.source_audit?.layers?.ai?.model"><span>生成模型</span><b>{{ session.source_audit.layers.ai.provider }} / {{ session.source_audit.layers.ai.model }}</b></div>
              <div><span>记录时间</span><b>{{ dateTime(session.source_audit?.created_at) }}</b></div>
            </div>
            <el-alert v-for="message in session.source_audit?.fallbacks || []" :key="message" class="fallback" :title="message" type="warning" :closable="false" show-icon />
          </section>
        </el-tab-pane>
      </el-tabs>

      <section v-if="session" class="panel feedback">
        <div><h3>这套内容是否适合你？</h3><p>反馈会更新画像版本，并直接调整当前学习计划。</p></div>
        <div><el-button @click="feedback('too_hard')">太难，拆分任务</el-button><el-button @click="feedback('too_easy')">太简单，提高挑战</el-button><el-button type="success" @click="feedback('helpful')">适合我</el-button></div>
      </section>
      <el-alert v-if="lastAdjustment" class="adjustment" :title="lastAdjustment.message" type="success" :closable="false" show-icon />
    </div>

    <DetailModal v-model="detail.visible" :title="detail.title">
      <AgentEvidencePanel v-if="detail.kind === 'agent'" :agent="detail.data" />
      <template v-else>
        <section class="source-detail">
          <el-tag type="success">{{ sourceLayer(detail.data?.source_layer) }}</el-tag>
          <p>{{ detail.data?.content }}</p>
          <div class="source-meta"><span>来源：{{ detail.data?.source_title }}</span><span>版本：{{ detail.data?.content_version }}</span><span v-if="detail.data?.credibility">可信度：{{ percent(detail.data.credibility) }}</span></div>
          <a v-if="detail.data?.source_url" :href="detail.data.source_url" target="_blank" rel="noreferrer">打开原始来源 ↗</a>
        </section>
      </template>
    </DetailModal>
  </AppShell>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import AppShell from '@/components/layout/AppShell.vue'
import DetailModal from '@/components/common/DetailModal.vue'
import AgentEvidencePanel from '@/components/business/AgentEvidencePanel.vue'
import ArbitrationPanel from '@/components/business/ArbitrationPanel.vue'
import ResourceContentRenderer from '@/components/business/ResourceContentRenderer.vue'
import { getData, postData } from '@/api'
import type { LearningSession } from '@/types/domain'
import { agentLabel, dateTime, percent, routeLabel, valueLabel } from '@/utils/presentation'

const route = useRoute()
const router = useRouter()
const session = ref<LearningSession | null>(null)
const loading = ref(true)
const active = ref('events')
const lastAdjustment = ref<any>(null)
const detail = reactive({ visible: false, title: '', kind: 'agent', data: null as any })

onMounted(async () => {
  try {
    session.value = await getData(`/sessions/${route.params.id}`, { params: { include_candidates: true } })
  } finally {
    loading.value = false
  }
})

function openAgent(event: any) {
  detail.title = agentLabel(event.agent_code)
  detail.kind = 'agent'
  detail.data = { ...event, code: event.agent_code }
  detail.visible = true
}
function openSource(item: any) {
  detail.title = item.title
  detail.kind = 'source'
  detail.data = item
  detail.visible = true
}
async function feedback(type: string) {
  const result = await postData<any>(`/sessions/${route.params.id}/feedback`, { feedback_type: type, content: {} })
  lastAdjustment.value = result.adjustment
  ElMessage.success(result.adjustment.message)
}
function sourceMode(code?: string) {
  return ({ knowledge_only:'仅审核知识库', knowledge_web:'知识库 + 联网检索', knowledge_ai:'知识库 + AI 创作', full:'全能力模式' } as Record<string,string>)[code || ''] || '仅审核知识库'
}
function sourceLayer(code?: string) {
  return ({ local_knowledge:'本地审核知识库', reviewed_contribution:'人工审核贡献', web_search:'联网检索' } as Record<string,string>)[code || ''] || '本地审核知识库'
}
</script>

<style scoped>
.session-hero{display:flex;justify-content:space-between;align-items:center;background:linear-gradient(120deg,#fff,#edf3ff)}.session-hero h2{margin:10px 0}.session-hero p{color:var(--muted)}.quality{text-align:center}.quality strong,.quality span{display:block}.quality strong{font-size:38px;color:#3168ee}.tabs{margin-top:18px}.event-list{display:grid;gap:10px}.event{display:grid;grid-template-columns:42px 1fr auto;gap:14px;align-items:center;padding:14px;border:1px solid var(--line);border-radius:14px;transition:.2s}.event>span{width:36px;height:36px;border-radius:12px;display:grid;place-items:center;background:#edf3ff;color:#3168ee;font-weight:700}.event p{margin:5px 0;color:var(--muted);line-height:1.6}.event small{display:block;color:var(--muted);margin-top:5px}.go-action{margin-top:20px}.source-panel{margin-top:18px}.source-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}.evidence{border:1px solid var(--line);padding:15px;background:#fbfcff;text-align:left;border-radius:14px;cursor:pointer}.evidence b,.evidence span,.evidence small{display:block}.evidence span{color:#536078;margin:6px 0}.evidence small{color:var(--muted)}.audit-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.audit-grid>div{padding:14px;background:#f6f9ff;border-radius:13px}.audit-grid span,.audit-grid b{display:block}.audit-grid span{color:var(--muted);font-size:11px;margin-bottom:5px}.fallback,.adjustment{margin-top:12px}.feedback{margin-top:18px;display:flex;justify-content:space-between;align-items:center}.feedback h3,.feedback p{margin:4px}.feedback p{color:var(--muted)}.source-detail>p{line-height:1.85;font-size:15px}.source-meta{display:flex;flex-wrap:wrap;gap:8px;margin:15px 0}.source-meta span{padding:8px 10px;background:#f4f7fc;border-radius:10px;color:#66738a;font-size:12px}.source-detail>a{text-decoration:none;color:#3168ee}@media(max-width:760px){.session-hero,.feedback{flex-direction:column;align-items:flex-start;gap:15px}.source-grid,.audit-grid{grid-template-columns:1fr}}
</style>
