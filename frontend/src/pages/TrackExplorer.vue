<template>
  <AppShell>
    <section class="hero panel">
      <div>
        <span class="eyebrow">29 条细分路线 · 可自由组合</span>
        <h2>先看清职业终点，再决定学什么</h2>
        <p>比较岗位、薪资参考、学历要求和技术栈；最多选择 6 条路线，系统会去重公共基础并生成一条可执行的组合路线。</p>
      </div>
      <div class="hero-actions">
        <el-input v-model="keyword" clearable placeholder="搜索方向、岗位或技术，例如 Vue、算法、嵌入式" />
        <el-button @click="router.push('/career-target')">粘贴真实 JD</el-button>
        <el-button type="primary" :loading="comparing" @click="compareSelected">
          智能比较主方向（{{ selectedTracks.length }}）
        </el-button>
      </div>
    </section>

    <section v-if="!profileReady" class="profile-required panel">
      <div><span class="eyebrow">先建立真实输入</span><h3>浏览方向不受限制，但个性化比较需要先了解你的情况</h3><p>系统不会用演示画像或默认分数给你推荐。完成 3 分钟引导后，才计算匹配度、能力缺口和预计周期。</p></div>
      <el-button type="primary" size="large" @click="router.push('/onboarding')">建立成长档案 →</el-button>
    </section>

    <div v-else-if="route.query.from === 'onboarding' || route.query.from === 'assessment'" class="onboarding-result">
      <el-alert :title="route.query.from === 'assessment' ? '量表已完成：以下是综合学历、城市、目标、能力、兴趣和时间后的 3 个探索候选；城市项是产业生态启发式，不是实时岗位数量。' : '以下比较基于你刚刚确认的阶段、经历、目标和每周投入；它是可修改的决策建议，不是职业定论。'" type="success" :closable="false" show-icon />
      <el-button @click="router.push('/onboarding?edit=1')">修改我的情况</el-button>
    </div>

    <section v-if="selectedPathways.length" class="route-cart panel">
      <div class="cart-title">
        <div>
          <span class="eyebrow">我的组合路线</span>
          <h3>已选择 {{ selectedPathways.length }}/6 个细分方向</h3>
        </div>
        <el-button link @click="clearPathways">清空选择</el-button>
      </div>
      <div class="selected-chips">
        <button v-for="pathway in selectedPathways" :key="pathway.id" @click="openPathway(pathway)">
          <span>{{ pathway.track_name }}</span>
          <b>{{ pathway.name }}</b>
          <i @click.stop="togglePathway(pathway)">×</i>
        </button>
      </div>
      <div class="cart-footer">
        <p>生成时会自动合并 HTML/CSS、Git、数据库等重复基础，并按依赖关系重排学习顺序。</p>
        <el-button type="primary" size="large" @click="goGenerateSelected">生成最佳组合路线 →</el-button>
      </div>
    </section>

    <el-tabs v-model="activeCluster" class="cluster-tabs">
      <el-tab-pane
        v-for="cluster in visibleClusters"
        :key="cluster.code"
        :name="cluster.code"
        :label="`${cluster.name} ${cluster.tracks.length}`"
      >
        <p class="cluster-copy">{{ cluster.description }}</p>
        <div class="track-grid">
          <article
            v-for="track in cluster.tracks"
            :key="track.code"
            class="track-card"
            :class="{ chosen: selectedTracks.includes(track.code) }"
          >
            <div class="track-top">
              <el-checkbox
                :model-value="selectedTracks.includes(track.code)"
                @change="toggleTrack(track.code)"
              >
                加入主方向比较
              </el-checkbox>
              <el-tag effect="plain">{{ track.pathway_count }} 条细分路线</el-tag>
            </div>
            <button class="track-body" @click="openTrack(track)">
              <h3>{{ track.name }}</h3>
              <p>{{ track.description }}</p>
              <div class="tag-row">
                <el-tag v-for="tag in track.keywords.slice(0, 5)" :key="tag" type="info" effect="plain">{{ tag }}</el-tag>
              </div>
            </button>
            <footer>
              <span>{{ track.skill_count }} 项核心能力 · {{ track.estimated_months.join(' / ') }} 个月</span>
              <el-button type="primary" link @click="openTrack(track)">查看技术栈与就业 →</el-button>
            </footer>
          </article>
        </div>
      </el-tab-pane>
    </el-tabs>

    <section v-if="comparisons.length" class="panel comparison">
      <div class="section-title">
        <div><span class="eyebrow">{{ assessmentMode ? '职业倾向量表结果' : '基于你的画像' }}</span><h3>{{ assessmentMode ? '建议优先体验的 3 个候选方向' : '主方向比较结果' }}</h3></div>
        <span>六个维度分别计算，推荐只用于缩小探索范围，不是职业定论</span>
      </div>
      <div class="compare-grid">
        <article v-for="(item, index) in comparisons" :key="item.track_code" class="compare-card" :class="{confirmed:selectedTrackCode===item.track_code}">
          <div class="rank" :class="{ first: index === 0 }">{{ index === 0 ? (assessmentMode ? '优先体验' : '最佳匹配') : `候选 ${index + 1}` }}</div>
          <div class="score">{{ item.score }}</div>
          <h3>{{ item.track_name }}</h3>
          <p>{{ item.role }} · 预计补齐 {{ item.estimated_weeks }} 周</p>
          <el-progress :percentage="item.score" :stroke-width="8" />
          <div class="dimension-grid">
            <span>能力基础 <b>{{ item.dimension_scores?.ability ?? item.readiness }}</b></span>
            <span>兴趣倾向 <b>{{ item.dimension_scores?.interest ?? item.interest_fit }}</b></span>
            <span>目标一致 <b>{{ item.dimension_scores?.goal ?? '-' }}</b></span>
            <span>学历适配 <b>{{ item.dimension_scores?.education ?? '-' }}</b></span>
            <span>城市生态 <b>{{ item.dimension_scores?.city ?? '-' }}</b></span>
            <span>时间可行 <b>{{ item.dimension_scores?.time ?? item.feasibility }}</b></span>
          </div>
          <div class="career-mini" v-if="item.career_summary">
            <span>可就业：{{ item.career_summary.roles.slice(0, 3).join('、') }}</span>
            <span>薪资参考：{{ item.career_summary.salary_ranges.slice(0, 2).join(' / ') }}</span>
          </div>
          <div class="compare-actions">
            <el-button @click="openComparison(item)">查看依据</el-button>
            <el-button type="primary" @click="openComparedTrack(item)">选择细分路线</el-button>
          </div>
          <el-button class="confirm-track" :type="selectedTrackCode===item.track_code?'success':'primary'" plain @click="confirmTrack(item)">{{ selectedTrackCode===item.track_code?'已确认为主方向':'确认这个主方向' }}</el-button>
        </article>
      </div>
    </section>

    <DetailModal v-model="detail.visible" :title="detail.title">
      <template v-if="detail.kind === 'track' && detail.track">
        <p class="detail-description">{{ detail.track.description }}</p>
        <div class="track-summary">
          <div><span>培养岗位</span><b>{{ detail.track.role }}</b></div>
          <div><span>细分路线</span><b>{{ detail.track.pathway_variants?.length }} 条</b></div>
          <div><span>代表项目</span><b>{{ detail.track.project?.title || detail.track.project }}</b></div>
        </div>
        <h4>选择你真正想学的技术路线</h4>
        <el-collapse v-model="openPathways" class="pathway-list">
          <el-collapse-item
            v-for="pathway in detail.track.pathway_variants"
            :key="pathway.id"
            :name="pathway.id"
          >
            <template #title>
              <div class="pathway-title">
                <div>
                  <b>{{ pathway.name }}</b>
                  <span>{{ pathway.estimated_months }} 个月 · {{ pathway.stages.length }} 个阶段 · {{ countTopics(pathway) }} 项技术</span>
                </div>
                <el-tag :type="isPathwaySelected(pathway.id) ? 'success' : 'info'">
                  {{ isPathwaySelected(pathway.id) ? '已加入组合' : '展开查看' }}
                </el-tag>
              </div>
            </template>
            <p class="pathway-fit">适合：{{ pathway.suitable_for }}</p>
            <section v-if="pathway.career" class="career-panel">
              <div>
                <span>就业岗位</span>
                <b>{{ pathway.career.roles.join('、') }}</b>
              </div>
              <div>
                <span>市场薪资参考</span>
                <b>{{ pathway.career.salary_range }}</b>
              </div>
              <div>
                <span>学历要求</span>
                <b>{{ pathway.career.education.minimum }}；竞争力：{{ pathway.career.education.competitive }}</b>
              </div>
              <div>
                <span>市场判断</span>
                <b>{{ pathway.career.market_outlook }}</b>
              </div>
              <small>{{ pathway.salary_scope }}</small>
            </section>
            <ol class="stage-list">
              <li v-for="(stage, index) in pathway.stages" :key="stage.title">
                <span class="stage-number">{{ index + 1 }}</span>
                <div>
                  <header><b>{{ stage.title }}</b><span>{{ stage.duration }}</span></header>
                  <div class="topic-list"><i v-for="topic in stage.topics" :key="topic">{{ topic }}</i></div>
                </div>
              </li>
            </ol>
            <section v-if="pathway.career" class="portfolio">
              <b>求职作品集必须证明</b>
              <ul><li v-for="item in pathway.career.portfolio" :key="item">{{ item }}</li></ul>
            </section>
            <p class="milestone"><b>最终里程碑：</b>{{ pathway.milestone }}</p>
            <el-button
              :type="isPathwaySelected(pathway.id) ? 'success' : 'primary'"
              @click="togglePathway(pathway)"
            >
              {{ isPathwaySelected(pathway.id) ? '已加入，点击移除' : '加入组合路线' }}
            </el-button>
            <el-button @click="generateSingle(pathway)">只生成这一条路线</el-button>
          </el-collapse-item>
        </el-collapse>
      </template>

      <template v-else-if="detail.kind === 'pathway' && detail.pathway">
        <p class="detail-description">{{ detail.pathway.suitable_for }}</p>
        <section v-if="detail.pathway.career" class="career-panel">
          <div><span>就业岗位</span><b>{{ detail.pathway.career.roles.join('、') }}</b></div>
          <div><span>薪资参考</span><b>{{ detail.pathway.career.salary_range }}</b></div>
          <div><span>学历要求</span><b>{{ detail.pathway.career.education.competitive }}</b></div>
        </section>
        <ol class="stage-list">
          <li v-for="(stage, index) in detail.pathway.stages" :key="stage.title">
            <span class="stage-number">{{ index + 1 }}</span>
            <div><header><b>{{ stage.title }}</b><span>{{ stage.duration }}</span></header><div class="topic-list"><i v-for="topic in stage.topics" :key="topic">{{ topic }}</i></div></div>
          </li>
        </ol>
      </template>

      <template v-else-if="detail.kind === 'comparison' && detail.comparison">
        <div class="track-summary">
          <div><span>综合匹配</span><b>{{ detail.comparison.score }} 分</b></div>
          <div><span>预计周期</span><b>{{ detail.comparison.estimated_weeks }} 周</b></div>
          <div><span>优先补齐</span><b>{{ detail.comparison.skill_gaps.slice(0, 2).map((x:any) => x.name).join('、') }}</b></div>
        </div>
        <h4>为什么推荐</h4>
        <ul class="reason-list"><li v-for="reason in detail.comparison.why" :key="reason">{{ reason }}</li></ul>
        <el-alert v-if="detail.comparison.decision_basis" :title="`可信度：${detail.comparison.confidence?.level || '初始'} · ${detail.comparison.decision_basis.city_data_type}`" type="info" :closable="false" show-icon />
        <h4>投入变化会怎样</h4>
        <p class="detail-description">每周多投入 4 小时，预计可从 {{ detail.comparison.estimated_weeks }} 周缩短到 {{ detail.comparison.counterfactual.if_weekly_hours_plus_4 }} 周。成本最高的能力是“{{ detail.comparison.counterfactual.highest_cost_skill }}”。</p>
      </template>
      <template #footer>
        <el-button @click="detail.visible = false">关闭</el-button>
        <el-button v-if="selectedPathways.length" type="primary" @click="goGenerateSelected">生成已选组合（{{ selectedPathways.length }}）</el-button>
      </template>
    </DetailModal>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import AppShell from '@/components/layout/AppShell.vue'
import DetailModal from '@/components/common/DetailModal.vue'
import { getData, postData } from '@/api'
import type { PathwayVariant, RouteMatch, TrackCluster, TrackSummary } from '@/types/domain'

const router = useRouter()
const route = useRoute()
const clusters = ref<TrackCluster[]>([])
const allPathways = ref<PathwayVariant[]>([])
const activeCluster = ref('software')
const keyword = ref('')
const selectedTracks = ref<string[]>([])
const selectedPathwayIds = ref<string[]>([])
const selectedTrackCode = ref('')
const profileReady = ref(false)
const comparisons = ref<RouteMatch[]>([])
const comparing = ref(false)
const openPathways = ref<string[]>([])
const detail = reactive({
  visible: false,
  title: '',
  kind: '' as 'track' | 'comparison' | 'pathway',
  track: null as any,
  comparison: null as any,
  pathway: null as PathwayVariant | null,
})
const assessmentMode = computed(() => route.query.from === 'assessment')

const selectedPathways = computed(() =>
  selectedPathwayIds.value
    .map((id) => allPathways.value.find((item) => item.id === id))
    .filter(Boolean) as PathwayVariant[],
)
const visibleClusters = computed(() => {
  const value = keyword.value.trim().toLowerCase()
  if (!value) return clusters.value
  return clusters.value
    .map((cluster) => ({
      ...cluster,
      tracks: cluster.tracks.filter((track) => {
        const paths = allPathways.value.filter((item) => item.track_code === track.code)
        return [track.name, track.role, track.description, ...track.keywords,
          ...paths.flatMap((item) => [item.name, ...(item.career?.roles || []), ...item.stages.flatMap((stage) => stage.topics)])]
          .join(' ').toLowerCase().includes(value)
      }),
    }))
    .filter((cluster) => cluster.tracks.length)
})

onMounted(async () => {
  const [tree, pathData, profileResult] = await Promise.all([
    getData<{clusters: TrackCluster[]}>('/tracks/tree'),
    getData<{items: PathwayVariant[]}>('/tracks/pathways/catalog'),
    getData<any>('/profiles/me').then(value=>({ok:true,value})).catch(()=>({ok:false,value:null})),
  ])
  clusters.value = tree.clusters
  allPathways.value = pathData.items
  profileReady.value = profileResult.ok
  const recommended = typeof route.query.recommend === 'string' ? route.query.recommend.split(',').filter(Boolean) : []
  if (recommended.length > 6) ElMessage.info('候选方向超过 6 个，系统已保留前 6 个最相关方向进行比较')
  selectedTracks.value = recommended.filter(code=>clusters.value.some(cluster=>cluster.tracks.some(track=>track.code===code))).slice(0,6)
  if (profileReady.value && assessmentMode.value) await runAssessment()
  else if (profileReady.value && selectedTracks.value.length) await compareSelected()
})

async function runAssessment() {
  comparing.value = true
  try {
    const result = await postData<{items: RouteMatch[]}>('/tracks/compare', {track_codes: []})
    comparisons.value = result.items.slice(0, 3)
    selectedTracks.value = comparisons.value.map(item=>item.track_code)
    ElMessage.success('已完成综合计算，请先体验候选方向再做最终选择')
  } catch (error:any) {
    ElMessage.error(error.response?.data?.detail || '量表结果计算失败')
  } finally { comparing.value=false }
}

function toggleTrack(code: string) {
  if (selectedTracks.value.includes(code)) selectedTracks.value = selectedTracks.value.filter((item) => item !== code)
  else if (selectedTracks.value.length < 6) selectedTracks.value.push(code)
  else ElMessage.warning('主方向最多比较 6 个')
}
function isPathwaySelected(id: string) { return selectedPathwayIds.value.includes(id) }
function togglePathway(pathway: PathwayVariant) {
  if (isPathwaySelected(pathway.id)) {
    selectedPathwayIds.value = selectedPathwayIds.value.filter((id) => id !== pathway.id)
  } else if (selectedPathwayIds.value.length < 6) {
    selectedPathwayIds.value.push(pathway.id)
    ElMessage.success(`已加入：${pathway.name}`)
  } else ElMessage.warning('组合路线最多选择 6 个细分方向')
}
function clearPathways() { selectedPathwayIds.value = [] }
function countTopics(pathway: PathwayVariant) { return new Set(pathway.stages.flatMap((stage) => stage.topics)).size }
async function openTrack(track: TrackSummary) {
  const full = await getData<any>(`/tracks/${track.code}`)
  detail.title = `${full.name}：技术路线与就业`
  detail.kind = 'track'
  detail.track = full
  detail.visible = true
  openPathways.value = full.pathway_variants?.length ? [full.pathway_variants[0].id] : []
}
function openPathway(pathway: PathwayVariant) {
  detail.title = pathway.name
  detail.kind = 'pathway'
  detail.pathway = pathway
  detail.visible = true
}
async function compareSelected() {
  if (!profileReady.value) {
    ElMessage.info('先完成成长档案，系统不会使用默认画像给出个性化结论')
    return router.push('/onboarding')
  }
  if (!selectedTracks.value.length) return ElMessage.warning('请至少选择一个主方向')
  comparing.value = true
  try {
    comparisons.value = (await postData<{items: RouteMatch[]}>('/tracks/compare', { track_codes: selectedTracks.value })).items
    comparisons.value[0] && ElMessage.success(`当前最佳匹配：${comparisons.value[0].track_name}`)
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '比较失败，请先完成学情画像')
  } finally { comparing.value = false }
}
async function confirmTrack(item: RouteMatch) {
  await postData('/tracks/select', { track_code: item.track_code })
  selectedTrackCode.value = item.track_code
  ElMessage.success(`已确认“${item.track_name}”为当前主方向，后续仍可修改`)
}
function openComparison(item: RouteMatch) {
  detail.title = `${item.track_name}：推荐依据`
  detail.kind = 'comparison'
  detail.comparison = item
  detail.visible = true
}
async function openComparedTrack(item: RouteMatch) {
  const track = clusters.value.flatMap((cluster) => cluster.tracks).find((row) => row.code === item.track_code)
  if (track) await openTrack(track)
}
async function generateSingle(pathway: PathwayVariant) {
  await postData('/tracks/select', { track_code: pathway.track_code })
  selectedTrackCode.value = pathway.track_code
  detail.visible = false
  router.push({ path: '/generate', query: { pathways: pathway.id } })
}
async function goGenerateSelected() {
  if (!selectedPathwayIds.value.length) return ElMessage.warning('请先选择至少一条细分路线')
  await postData('/tracks/select', { track_code: selectedPathways.value[0].track_code })
  selectedTrackCode.value = selectedPathways.value[0].track_code
  detail.visible = false
  router.push({ path: '/generate', query: { pathways: selectedPathwayIds.value.join(',') } })
}
</script>

<style scoped>
.hero{display:grid;grid-template-columns:1fr 420px;gap:36px;align-items:center;background:linear-gradient(125deg,#fff 0%,#f3f7ff 72%,#e9f1ff 100%)}.eyebrow{color:#2f67ee;font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase}.hero h2{font-size:30px;margin:8px 0}.hero p,.cluster-copy,.section-title>span{color:var(--muted);line-height:1.7}.hero-actions{display:grid;grid-template-columns:1fr auto;gap:10px}.route-cart{margin-top:18px;border-color:#bdd0ff;background:linear-gradient(120deg,#fff,#f5f8ff)}.cart-title,.cart-footer,.section-title{display:flex;align-items:center;justify-content:space-between;gap:20px}.cart-title h3{margin:4px 0}.selected-chips{display:flex;gap:10px;flex-wrap:wrap;margin:16px 0}.selected-chips button{display:grid;grid-template-columns:1fr auto;border:1px solid #cbd9fb;background:white;border-radius:12px;padding:9px 10px;text-align:left;color:inherit;cursor:pointer;min-width:170px}.selected-chips span{font-size:11px;color:#72809a}.selected-chips b{font-size:13px;margin-top:3px}.selected-chips i{grid-column:2;grid-row:1/3;align-self:center;font-style:normal;font-size:20px;color:#8190aa;padding-left:10px}.cart-footer p{margin:0;color:var(--muted);font-size:13px}.cluster-tabs{margin-top:22px}.track-grid,.compare-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}.track-card,.compare-card{background:white;border:1px solid var(--line);border-radius:18px;padding:18px;transition:.2s}.track-card:hover,.compare-card:hover{transform:translateY(-2px);box-shadow:0 14px 34px rgba(31,61,123,.09)}.track-card.chosen{border-color:#3168ee;box-shadow:0 0 0 3px rgba(49,104,238,.09)}.track-top,.track-card footer{display:flex;justify-content:space-between;align-items:center;gap:10px}.track-body{width:100%;border:0;background:none;text-align:left;color:inherit;padding:0;cursor:pointer}.track-body h3{font-size:20px;margin:17px 0 8px}.track-body p{color:var(--muted);min-height:50px;line-height:1.6}.tag-row{display:flex;gap:6px;flex-wrap:wrap}.track-card footer{border-top:1px solid var(--line);margin-top:17px;padding-top:13px;font-size:12px;color:var(--muted)}.comparison{margin-top:24px}.section-title h3{margin:4px 0 14px;font-size:22px}.compare-card{text-align:center;position:relative}.rank{position:absolute;top:15px;left:15px;border-radius:8px;padding:4px 8px;background:#f1f3f7;color:#7c879b;font-size:11px}.rank.first{background:#fff0d9;color:#d27900}.score{width:64px;height:64px;border-radius:20px;margin:8px auto;display:grid;place-items:center;background:#edf3ff;color:#2f64e5;font-size:26px;font-weight:800}.compare-card>p{color:var(--muted)}.triple{display:flex;justify-content:space-between;font-size:12px;color:#758197;margin:13px 0}.triple b{color:#16213a}.career-mini{display:grid;gap:6px;background:#f7f9fc;border-radius:10px;padding:10px;text-align:left;font-size:12px;color:#5f6e86}.compare-actions{display:flex;justify-content:center;margin-top:14px}.detail-description{font-size:15px;line-height:1.75;color:#56647c}.track-summary{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:14px 0 22px}.track-summary>div{padding:12px;border-radius:12px;background:#f6f8fc}.track-summary span,.track-summary b{display:block}.track-summary span{font-size:11px;color:var(--muted);margin-bottom:5px}.pathway-title{width:100%;display:flex;justify-content:space-between;align-items:center;padding-right:12px}.pathway-title>div{display:flex;flex-direction:column;align-items:flex-start}.pathway-title span,.pathway-fit{font-size:12px;color:var(--muted)}.career-panel{display:grid;grid-template-columns:1fr 1fr;gap:9px;padding:14px;border:1px solid #cfe3db;background:#f4fbf8;border-radius:14px}.career-panel>div{display:grid;gap:4px}.career-panel span{font-size:11px;color:#628074}.career-panel b{font-size:13px;line-height:1.5}.career-panel small{grid-column:1/-1;color:#74827e;line-height:1.5}.stage-list{list-style:none;padding:0;display:grid;gap:10px}.stage-list li{display:grid;grid-template-columns:30px 1fr;gap:10px;padding:12px;border:1px solid var(--line);border-radius:12px;background:#fafbfe}.stage-number{width:28px;height:28px;border-radius:9px;background:#e8efff;color:#2862e9;display:grid;place-items:center;font-weight:800}.stage-list header{display:flex;justify-content:space-between;gap:12px}.stage-list header span{color:#3168ee;font-size:12px}.topic-list{display:flex;gap:6px;flex-wrap:wrap;margin-top:9px}.topic-list i{font-style:normal;font-size:12px;padding:5px 8px;background:white;border:1px solid #e1e7f1;border-radius:7px;color:#536179}.portfolio,.milestone{padding:12px 14px;border-radius:12px;line-height:1.7}.portfolio{background:#fff8eb;margin:12px 0}.portfolio ul{margin:5px 0 0;padding-left:20px}.milestone{background:#eef5ff}.reason-list{line-height:1.9}@media(max-width:1100px){.hero{grid-template-columns:1fr}.track-grid,.compare-grid{grid-template-columns:repeat(2,1fr)}}@media(max-width:700px){.track-grid,.compare-grid,.track-summary,.career-panel{grid-template-columns:1fr}.hero-actions{grid-template-columns:1fr}.cart-footer,.section-title{align-items:flex-start;flex-direction:column}.pathway-title{align-items:flex-start;gap:8px;flex-direction:column}}
.profile-required{margin-top:18px;display:flex;justify-content:space-between;align-items:center;gap:24px;border-color:#cbdafa;background:linear-gradient(120deg,#fff,#f1f6ff)}.profile-required h3{margin:5px 0}.profile-required p{margin:0;color:var(--muted);font-size:12px;line-height:1.7}.onboarding-result{display:grid;grid-template-columns:1fr auto;gap:10px;align-items:center;margin-top:18px}.compare-card.confirmed{border-color:#29a77b;box-shadow:0 0 0 3px rgba(41,167,123,.1)}.confirm-track{width:100%;margin-top:10px}@media(max-width:700px){.profile-required{align-items:flex-start;flex-direction:column}.onboarding-result{grid-template-columns:1fr}}
.dimension-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin:13px 0}.dimension-grid span{padding:7px 3px;border-radius:8px;background:#f6f8fc;font-size:10px;color:#758197}.dimension-grid b{display:block;color:#16213a;font-size:13px;margin-top:2px}
.hero-actions{grid-template-columns:minmax(180px,1fr) auto auto}.hero{grid-template-columns:1fr 500px}@media(max-width:700px){.hero-actions{grid-template-columns:1fr}.hero{grid-template-columns:1fr}}
</style>
