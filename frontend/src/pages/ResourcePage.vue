<template>
  <AppShell>
    <section class="panel">
      <div class="panel-title">
        <div>
          <h3>个性化资源库</h3>
          <p>内容已经按学习用途排版；来源和技术审计信息与正文分开展示</p>
        </div>
        <el-radio-group v-model="type" @change="load">
          <el-radio-button value="">全部</el-radio-button>
          <el-radio-button value="lecture">讲义</el-radio-button>
          <el-radio-button value="practice">实操</el-radio-button>
          <el-radio-button value="assessment">测试</el-radio-button>
          <el-radio-button value="plan">计划</el-radio-button>
        </el-radio-group>
      </div>

      <div v-if="resources.length" class="resource-grid">
        <article v-for="item in resources" :key="item.id" class="resource clickable" @click="open(item)">
          <div class="icon">{{ icons[item.resource_type] }}</div>
          <div>
            <div class="tag-row">
              <el-tag>{{ labels[item.resource_type] }}</el-tag>
              <el-tag type="info">{{ routeLabel(item.track_code) }}</el-tag>
            </div>
            <h3>{{ cleanTitle(item.title) }}</h3>
            <p>版本 v{{ item.version }} · {{ dateTime(item.created_at) }}</p>
            <span>{{ item.source_traces.length }} 条可追溯知识依据</span>
          </div>
          <b>查看内容 →</b>
        </article>
      </div>

      <div v-else class="empty">
        <h3>还没有这类学习资源</h3>
        <p>先选择方向并运行一次学习任务，系统会生成讲义、项目、测试和计划。</p>
        <el-button type="primary" @click="router.push('/generate')">生成第一套资源</el-button>
      </div>
    </section>

    <DetailModal v-model="detail.visible" :title="cleanTitle(detail.item?.title) || '资源详情'">
      <template v-if="detail.loading"><el-skeleton :rows="9" animated /></template>
      <template v-else-if="detail.item">
        <div class="resource-meta">
          <div><span>资源类型</span><b>{{ labels[detail.item.resource_type] }}</b></div>
          <div><span>学习方向</span><b>{{ routeLabel(detail.item.track_code) }}</b></div>
          <div><span>内容版本</span><b>v{{ detail.item.version }}</b></div>
          <div><span>知识依据</span><b>{{ detail.item.source_traces?.length || 0 }} 条</b></div>
        </div>

        <ResourceContentRenderer :type="detail.item.resource_type" :content="detail.item.content || {}" />

        <el-collapse class="source-collapse">
          <el-collapse-item :title="`查看知识来源与版本（${detail.item.source_traces?.length || 0} 条）`" name="sources">
            <article v-for="source in detail.item.source_traces || []" :key="source.chunk_id" class="source">
              <div>
                <b>{{ source.title }}</b>
                <span>{{ source.source_title }} · {{ source.content_version }}</span>
              </div>
              <a :href="source.source_url" target="_blank" rel="noreferrer">查看原文 ↗</a>
            </article>
          </el-collapse-item>
        </el-collapse>
      </template>

      <template #footer>
        <el-button @click="detail.visible = false">关闭</el-button>
        <el-button
          v-if="detail.item?.session_id"
          type="primary"
          @click="router.push(`/session/${detail.item.session_id}`)"
        >查看生成依据</el-button>
      </template>
    </DetailModal>
  </AppShell>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppShell from '@/components/layout/AppShell.vue'
import DetailModal from '@/components/common/DetailModal.vue'
import ResourceContentRenderer from '@/components/business/ResourceContentRenderer.vue'
import { getData } from '@/api'
import type { LearningResource } from '@/types/domain'
import { dateTime, routeLabel } from '@/utils/presentation'

const route = useRoute()
const router = useRouter()
const type = ref(String(route.query.type || ''))
const resources = ref<LearningResource[]>([])
const detail = reactive({ visible: false, loading: false, item: null as any })
const labels: Record<string,string> = {
  lecture: '个性化讲义',
  practice: '项目实操',
  assessment: '分阶测试',
  plan: '学习计划',
}
const icons: Record<string,string> = { lecture: '读', practice: '做', assessment: '测', plan: '行' }

onMounted(load)
watch(() => route.query.type, () => {
  type.value = String(route.query.type || '')
  load()
})

async function load() {
  resources.value = (await getData<{items:LearningResource[]}>('/resources', {
    params: { resource_type: type.value || undefined },
  })).items
}
async function open(item: LearningResource) {
  detail.visible = true
  detail.loading = true
  try {
    detail.item = await getData(`/resources/${item.id}`)
  } finally {
    detail.loading = false
  }
}
function cleanTitle(title?: string) {
  return String(title || '')
    .replace(' · lecture', '')
    .replace(' · practice', '')
    .replace(' · assessment', '')
    .replace(' · plan', '')
}
</script>

<style scoped>
.resource-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.resource{display:grid;grid-template-columns:62px 1fr auto;gap:16px;align-items:center;padding:19px;border:1px solid var(--line);border-radius:17px;transition:.2s;background:linear-gradient(145deg,#fff,#fbfcff)}.resource>.icon{width:58px;height:58px;border-radius:18px;background:linear-gradient(145deg,#3168ee,#7557eb);color:white;display:grid;place-items:center;font-size:19px;font-weight:800;box-shadow:0 10px 24px rgba(49,104,238,.2)}.resource h3{margin:10px 0 6px}.resource p,.resource span{color:var(--muted);font-size:12px}.resource>b{font-size:12px;color:#3168ee}.resource-meta{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:22px}.resource-meta>div{padding:13px;border-radius:13px;background:#f5f8fd}.resource-meta span,.resource-meta b{display:block}.resource-meta span{font-size:11px;color:var(--muted);margin-bottom:5px}.source-collapse{margin-top:24px}.source{display:flex;justify-content:space-between;align-items:center;gap:15px;padding:13px 4px;border-bottom:1px solid var(--line)}.source b,.source span{display:block}.source span{color:var(--muted);font-size:12px;margin-top:5px}.source a{white-space:nowrap;text-decoration:none;color:#3168ee}.empty h3{margin-bottom:5px}.empty p{margin-bottom:18px}@media(max-width:850px){.resource-grid{grid-template-columns:1fr}.resource-meta{grid-template-columns:repeat(2,1fr)}}@media(max-width:560px){.resource{grid-template-columns:52px 1fr}.resource>b{display:none}.resource-meta{grid-template-columns:1fr}.source{align-items:flex-start;flex-direction:column}}
</style>
