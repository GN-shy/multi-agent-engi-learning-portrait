<template>
  <AppShell>
    <section class="search-panel panel">
      <div>
        <h2>可信知识检索</h2>
        <p>检索平台审核知识库，并把有版本、有来源的内容贡献给其他学习者。</p>
      </div>
      <el-button type="primary" @click="dialogVisible = true">贡献知识</el-button>
      <div class="search-row">
        <el-input
          v-model="query"
          size="large"
          placeholder="输入概念、技能或任务，例如：状态机、工具调用、评测"
          @keyup.enter="search"
        >
          <template #prepend>
            <el-select v-model="trackCode" clearable filterable placeholder="全部路线">
              <el-option
                v-for="track in tracks"
                :key="track.code"
                :label="track.name"
                :value="track.code"
              />
            </el-select>
          </template>
        </el-input>
        <el-button type="primary" size="large" :loading="loading" @click="search">检索</el-button>
      </div>
    </section>

    <div class="result-layout">
      <section class="panel">
        <el-tabs v-model="activeTab" @tab-change="onTabChange">
          <el-tab-pane label="检索结果" name="search">
            <div class="panel-title">
              <div>
                <h3>可追溯知识片段</h3>
                <p>{{ results.length }} 条 · 目录版本 {{ catalogVersion || '等待检索' }}</p>
              </div>
            </div>
            <div v-if="results.length" class="results">
              <article
                v-for="item in results"
                :key="item.chunk_id"
                class="result clickable"
                @click="open(item)"
              >
                <div class="tag-row">
                  <el-tag>{{ trackName(item.track_code) }}</el-tag>
                  <el-tag type="info">{{ item.content_version }}</el-tag>
                  <el-tag v-if="item.source_layer === 'reviewed_contribution'" type="success">
                    社区审核
                  </el-tag>
                </div>
                <h3>{{ item.title }}</h3>
                <p>{{ item.content }}</p>
                <footer>
                  <span>来源：{{ item.source_title }}</span>
                  <b>相关度 {{ item.score }}</b>
                </footer>
              </article>
            </div>
            <div v-else class="empty">输入问题后查看可追溯知识片段</div>
          </el-tab-pane>

          <el-tab-pane label="我的贡献" name="contributions">
            <div class="panel-title">
              <div>
                <h3>知识共建记录</h3>
                <p>普通用户提交后进入审核，审核通过才会进入正式检索与生成链路。</p>
              </div>
              <el-button :loading="contributionLoading" @click="loadContributions">刷新</el-button>
            </div>
            <el-table :data="contributions" empty-text="尚未贡献知识">
              <el-table-column prop="title" label="标题" min-width="180" />
              <el-table-column label="路线" min-width="130">
                <template #default="{ row }">{{ trackName(row.track_code) }}</template>
              </el-table-column>
              <el-table-column prop="content_version" label="版本" width="110" />
              <el-table-column label="状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="statusType(row.status)">{{ statusLabel(row.status) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="review_notes" label="审核意见" min-width="180" />
              <el-table-column label="操作" width="90">
                <template #default="{ row }">
                  <el-button link type="primary" @click="openContribution(row)">详情</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>
        </el-tabs>
      </section>

      <aside class="panel">
        <div class="panel-title">
          <div><h3>可信 RAG 流程</h3><p>比赛痛点对应的知识治理闭环</p></div>
        </div>
        <ol class="rag">
          <li><b>路线约束</b><span>先限定计算机方向与技能范围</span></li>
          <li><b>知识召回</b><span>本地审核库优先，按命中度重排</span></li>
          <li><b>版本核验</b><span>保留来源、版本和可信度信息</span></li>
          <li><b>人工审核</b><span>用户贡献经治理后才能正式使用</span></li>
          <li><b>生成引用</b><span>Agent 输出绑定知识片段而非自由发挥</span></li>
        </ol>
      </aside>
    </div>

    <el-dialog v-model="dialogVisible" title="贡献可信知识" width="min(680px, 92vw)">
      <el-alert
        title="请提交可核验、允许引用的技术内容；来源地址必须使用 HTTPS。"
        type="info"
        :closable="false"
        show-icon
      />
      <el-form label-position="top" class="contribution-form">
        <el-form-item label="所属路线" required>
          <el-select v-model="form.track_code" filterable placeholder="选择计算机细分方向">
            <el-option
              v-for="track in tracks"
              :key="track.code"
              :label="track.name"
              :value="track.code"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="标题" required>
          <el-input v-model="form.title" maxlength="300" show-word-limit />
        </el-form-item>
        <el-form-item label="正文（至少 50 字）" required>
          <el-input v-model="form.content" type="textarea" :rows="7" maxlength="100000" show-word-limit />
        </el-form-item>
        <div class="grid two">
          <el-form-item label="内容版本" required>
            <el-input v-model="form.content_version" placeholder="例如：Vue 3.5 / 2026-07" />
          </el-form-item>
          <el-form-item label="许可类型" required>
            <el-select v-model="form.license_type">
              <el-option label="官方文档可引用" value="official-documentation" />
              <el-option label="CC BY 4.0" value="CC-BY-4.0" />
              <el-option label="MIT" value="MIT" />
              <el-option label="其他/待确认" value="unknown" />
            </el-select>
          </el-form-item>
        </div>
        <el-form-item label="原始来源地址" required>
          <el-input v-model="form.source_url" placeholder="https://..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitContribution">提交审核</el-button>
      </template>
    </el-dialog>

    <DetailModal v-model="detail.visible" :title="detail.item?.title || '知识详情'">
      <p class="content">{{ detail.item?.content }}</p>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="所属路线">{{ trackName(detail.item?.track_code) }}</el-descriptions-item>
        <el-descriptions-item label="技能">{{ detail.item?.skill_code || '综合知识' }}</el-descriptions-item>
        <el-descriptions-item label="来源">{{ detail.item?.source_title || detail.item?.source_url }}</el-descriptions-item>
        <el-descriptions-item label="版本">{{ detail.item?.content_version }}</el-descriptions-item>
        <el-descriptions-item v-if="detail.item?.status" label="审核状态">
          {{ statusLabel(detail.item?.status) }}
        </el-descriptions-item>
        <el-descriptions-item v-if="detail.item?.review_notes" label="审核意见">
          {{ detail.item?.review_notes }}
        </el-descriptions-item>
      </el-descriptions>
      <p v-if="detail.item?.source_url">
        <a :href="detail.item.source_url" target="_blank" rel="noreferrer">打开原始来源 →</a>
      </p>
      <template v-if="detail.item?.matched_terms?.length">
        <h4>命中词</h4>
        <div class="tag-row">
          <el-tag v-for="term in detail.item.matched_terms" :key="term">{{ term }}</el-tag>
        </div>
      </template>
    </DetailModal>
  </AppShell>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import AppShell from '@/components/layout/AppShell.vue'
import DetailModal from '@/components/common/DetailModal.vue'
import { getData, postData } from '@/api'
import type { TrackSummary } from '@/types/domain'

const route = useRoute()
const query = ref(String(route.query.q || ''))
const trackCode = ref('')
const tracks = ref<TrackSummary[]>([])
const results = ref<any[]>([])
const contributions = ref<any[]>([])
const catalogVersion = ref('')
const loading = ref(false)
const contributionLoading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const activeTab = ref('search')
const detail = reactive({ visible: false, item: null as any })
const form = reactive({
  track_code: '',
  title: '',
  content: '',
  source_url: '',
  license_type: 'official-documentation',
  content_version: '',
})

onMounted(async () => {
  tracks.value = (await getData<{ items: TrackSummary[] }>('/tracks')).items
  if (query.value) await search()
})

async function search() {
  loading.value = true
  try {
    const data = await getData<any>('/knowledge/search', {
      params: { q: query.value, track_code: trackCode.value || undefined, top_k: 20 },
    })
    results.value = data.items
    catalogVersion.value = data.filters.catalog_version
  } finally {
    loading.value = false
  }
}

async function loadContributions() {
  contributionLoading.value = true
  try {
    contributions.value = (await getData<{ items: any[] }>('/knowledge/documents')).items
  } finally {
    contributionLoading.value = false
  }
}

async function onTabChange(name: string | number) {
  if (name === 'contributions') await loadContributions()
}

async function submitContribution() {
  if (!form.track_code || !form.title.trim() || form.content.trim().length < 50) {
    ElMessage.warning('请完整填写路线、标题和至少 50 字的正文')
    return
  }
  if (!form.content_version.trim() || !form.source_url.startsWith('https://')) {
    ElMessage.warning('请填写内容版本，并使用 HTTPS 来源地址')
    return
  }
  submitting.value = true
  try {
    const item = await postData<any>('/knowledge/documents', form)
    ElMessage.success(item.status === 'approved' ? '知识已入库' : '知识已提交审核')
    Object.assign(form, {
      track_code: '',
      title: '',
      content: '',
      source_url: '',
      license_type: 'official-documentation',
      content_version: '',
    })
    dialogVisible.value = false
    activeTab.value = 'contributions'
    await loadContributions()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '提交失败，请检查内容')
  } finally {
    submitting.value = false
  }
}

function trackName(code?: string) {
  return tracks.value.find((item) => item.code === code)?.name || code || '-'
}
function statusLabel(status: string) {
  return ({ pending: '待审核', approved: '已通过', rejected: '已驳回' } as Record<string, string>)[status] || status
}
function statusType(status: string) {
  return ({ pending: 'warning', approved: 'success', rejected: 'danger' } as Record<string, any>)[status] || 'info'
}
function open(item: any) {
  detail.item = item
  detail.visible = true
}
function openContribution(item: any) {
  detail.item = { ...item, source_title: item.title }
  detail.visible = true
}
</script>

<style scoped>
.search-panel{display:flex;align-items:flex-start;justify-content:space-between;gap:18px;padding:30px}.search-panel h2{font-size:28px;margin:0 0 8px}.search-panel p{color:var(--muted);margin:0}.search-row{display:flex;gap:10px;flex:1;max-width:880px}.search-row :deep(.el-input-group__prepend){width:200px}.result-layout{display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:18px;margin-top:18px}.results{display:grid;gap:12px}.result{padding:18px;border:1px solid var(--line);border-radius:14px;transition:.2s}.result h3{margin:12px 0 7px}.result p,.result footer{color:var(--muted)}.result footer{display:flex;justify-content:space-between;border-top:1px solid var(--line);padding-top:12px;font-size:12px}.result footer b{color:#3168ee}.rag{padding-left:22px}.rag li{padding:0 0 23px 14px;border-left:2px solid #dbe5fa}.rag b,.rag span{display:block}.rag span{font-size:12px;color:var(--muted);margin-top:4px}.content{font-size:16px;line-height:1.85}.contribution-form{margin-top:20px}.contribution-form .el-select{width:100%}@media(max-width:1100px){.search-panel{flex-wrap:wrap}.search-row{order:3;min-width:100%}}@media(max-width:980px){.result-layout{grid-template-columns:1fr}.search-row{flex-direction:column}}
</style>
