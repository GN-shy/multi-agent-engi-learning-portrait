<template>
  <AppShell>
    <section class="intro panel">
      <div><h2>计算机不是一条路</h2><p>系统会同时比较基础准备度、兴趣证据、时间可行性和补齐成本。</p></div>
      <el-button type="primary" :loading="comparing" @click="compareSelected">比较所选方向（{{ selected.length }}）</el-button>
    </section>
    <el-tabs v-model="activeCluster" class="cluster-tabs">
      <el-tab-pane v-for="cluster in clusters" :key="cluster.code" :name="cluster.code" :label="cluster.name">
        <p class="cluster-copy">{{ cluster.description }}</p>
        <div class="track-grid">
          <article v-for="track in cluster.tracks" :key="track.code" class="track-card clickable" :class="{chosen:selected.includes(track.code)}" @click="openTrack(track)">
            <div class="track-top"><el-checkbox :model-value="selected.includes(track.code)" @click.stop @change="toggle(track.code)" /><el-tag>{{ track.skill_count }} 个专项技能</el-tag></div>
            <h3>{{ track.name }}</h3><p>{{ track.description }}</p>
            <div class="tag-row"><el-tag v-for="tag in track.keywords.slice(0,4)" :key="tag" type="info" effect="plain">{{ tag }}</el-tag></div>
            <footer><span>{{ track.role }}</span><b>查看详情 →</b></footer>
          </article>
        </div>
      </el-tab-pane>
    </el-tabs>

    <section v-if="comparisons.length" class="panel comparison">
      <div class="panel-title"><div><h3>路线比较结果</h3><p>点击任意结果查看缺口与反事实投入</p></div></div>
      <div class="compare-grid">
        <article v-for="item in comparisons" :key="item.track_code" class="compare-card clickable" @click="openComparison(item)">
          <div class="score">{{ item.score }}</div><h3>{{ item.track_name }}</h3>
          <p>{{ item.role }} · 预计 {{ item.estimated_weeks }} 周</p>
          <el-progress :percentage="item.score" :stroke-width="8" />
          <div class="triple"><span>基础 {{ item.readiness }}</span><span>兴趣 {{ item.interest_fit }}</span><span>可行 {{ item.feasibility }}</span></div>
          <el-button type="primary" plain @click.stop="selectTrack(item)">选择这条路线</el-button>
        </article>
      </div>
    </section>

    <DetailModal v-model="detail.visible" :title="detail.title">
      <template v-if="detail.track">
        <p class="detail-description">{{ detail.track.description }}</p>
        <h4>代表项目</h4><p>{{ detail.track.project?.title || detail.track.project }}</p>
        <ul v-if="detail.track.project?.deliverables"><li v-for="item in detail.track.project.deliverables" :key="item">{{ item }}</li></ul>
        <h4 v-if="detail.track.skills">专项技能</h4>
        <div class="skill-list"><div v-for="skill in detail.track.skills" :key="skill.code"><b>{{ skill.name }}</b><span>{{ skill.description }}</span></div></div>
        <template v-if="detail.track.why"><h4>推荐依据</h4><p v-for="reason in detail.track.why" :key="reason">✓ {{ reason }}</p><h4>反事实比较</h4><p>每周多投入 4 小时，预计可从 {{ detail.track.estimated_weeks }} 周缩短到 {{ detail.track.counterfactual.if_weekly_hours_plus_4 }} 周。</p></template>
      </template>
      <template #footer><el-button @click="detail.visible=false">关闭</el-button><el-button v-if="detail.track?.track_code" type="primary" @click="selectTrack(detail.track)">选择路线</el-button></template>
    </DetailModal>
  </AppShell>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import AppShell from '@/components/layout/AppShell.vue'
import DetailModal from '@/components/common/DetailModal.vue'
import { getData, postData } from '@/api'
import type { RouteMatch, TrackCluster, TrackSummary } from '@/types/domain'

const clusters=ref<TrackCluster[]>([]),activeCluster=ref('software'),selected=ref<string[]>(['web_frontend','backend','agent_engineering'])
const comparisons=ref<RouteMatch[]>([]),comparing=ref(false)
const detail=reactive({visible:false,title:'',track:null as any})
onMounted(async()=>{clusters.value=(await getData<{clusters:TrackCluster[]}>('/tracks/tree')).clusters})
function toggle(code:string){selected.value=selected.value.includes(code)?selected.value.filter(item=>item!==code):selected.value.length<6?[...selected.value,code]:selected.value}
async function openTrack(track:TrackSummary){const full=await getData<any>(`/tracks/${track.code}`);detail.title=full.name;detail.track=full;detail.visible=true}
async function compareSelected(){if(!selected.value.length)return ElMessage.warning('请至少选择一个方向');comparing.value=true;try{comparisons.value=(await postData<{items:RouteMatch[]}>('/tracks/compare',{track_codes:selected.value})).items}catch{ElMessage.error('比较失败，请先完成能力画像')}finally{comparing.value=false}}
function openComparison(item:RouteMatch){detail.title=`${item.track_name} · 匹配依据`;detail.track=item;detail.visible=true}
async function selectTrack(item:RouteMatch){await postData('/tracks/select',{track_code:item.track_code});ElMessage.success(`已选择 ${item.track_name}`);detail.visible=false}
</script>

<style scoped>
.intro{display:flex;align-items:center;justify-content:space-between}.intro h2{font-size:28px;margin:0 0 8px}.intro p,.cluster-copy{color:var(--muted)}.cluster-tabs{margin-top:20px}.track-grid,.compare-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}.track-card,.compare-card{background:white;border:1px solid var(--line);border-radius:18px;padding:20px;transition:.2s ease}.track-card.chosen{border-color:#3168ee;box-shadow:0 0 0 3px rgba(49,104,238,.1)}.track-top,.track-card footer{display:flex;justify-content:space-between;align-items:center}.track-card h3{font-size:20px;margin:18px 0 8px}.track-card p{color:var(--muted);min-height:48px}.track-card footer{border-top:1px solid var(--line);margin-top:18px;padding-top:14px}.track-card footer b{color:#3168ee;font-size:13px}.comparison{margin-top:24px}.compare-card{text-align:center}.score{width:64px;height:64px;border-radius:20px;margin:0 auto;display:grid;place-items:center;background:#edf3ff;color:#2f64e5;font-size:26px;font-weight:800}.triple{display:flex;justify-content:space-between;font-size:12px;color:#758197;margin:13px 0 18px}.skill-list{display:grid;gap:10px}.skill-list div{padding:13px;background:#f6f8fc;border-radius:12px}.skill-list b,.skill-list span{display:block}.skill-list span{color:var(--muted);margin-top:5px}.detail-description{font-size:16px;line-height:1.7}@media(max-width:1100px){.track-grid,.compare-grid{grid-template-columns:repeat(2,1fr)}}@media(max-width:700px){.track-grid,.compare-grid{grid-template-columns:1fr}.intro{align-items:flex-start;gap:16px;flex-direction:column}}
</style>
