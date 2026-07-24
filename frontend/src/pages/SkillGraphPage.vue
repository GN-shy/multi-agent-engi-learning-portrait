<template>
  <AppShell>
    <section class="toolbar panel">
      <div><h2>技能依赖不是清单，而是一张图</h2><p>蓝色是通用底座，紫色是方向专项；点击节点查看学习与验收细节。</p></div>
      <el-select v-model="trackCode" filterable @change="loadGraph"><el-option v-for="track in tracks" :key="track.code" :label="track.name" :value="track.code" /></el-select>
    </section>
    <div class="grid graph-layout">
      <section class="panel graph-panel"><EChart v-if="graph.nodes?.length" :option="graphOption" height="650px" @click="onNodeClick" /></section>
      <aside class="panel">
        <div class="panel-title"><div><h3>学习顺序</h3><p>按难度与前置关系排序</p></div></div>
        <div v-for="(node,index) in orderedNodes" :key="node.id" class="order-item clickable" @click="showNode(node)">
          <span>{{ index+1 }}</span><div><b>{{ node.name }}</b><small>{{ node.kind==='core'?'通用底座':'方向专项' }} · 难度 {{ node.difficulty }}</small></div>
        </div>
      </aside>
    </div>
    <DetailModal v-model="detail.visible" :title="detail.node?.name || '技能详情'">
      <p class="description">{{ detail.node?.description }}</p><el-descriptions :column="2" border><el-descriptions-item label="技能编码">{{ detail.node?.id }}</el-descriptions-item><el-descriptions-item label="难度">{{ detail.node?.difficulty }}/5</el-descriptions-item><el-descriptions-item label="类型">{{ detail.node?.kind==='core'?'计算机通用底座':'路线专项能力' }}</el-descriptions-item><el-descriptions-item label="后续节点">{{ successors.join('、') || '路线终点' }}</el-descriptions-item></el-descriptions>
      <h4>前置技能</h4><div class="tag-row"><el-tag v-for="name in prerequisites" :key="name">{{ name }}</el-tag><span v-if="!prerequisites.length" class="muted">无硬性前置，可直接开始</span></div>
    </DetailModal>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import AppShell from '@/components/layout/AppShell.vue';import DetailModal from '@/components/common/DetailModal.vue';import EChart from '@/components/common/EChart.vue'
import { getData } from '@/api';import type { SkillEdge,SkillNode,TrackSummary } from '@/types/domain'
const tracks=ref<TrackSummary[]>([]),trackCode=ref('agent_engineering')
const graph=reactive<{nodes:SkillNode[];edges:SkillEdge[];track?:TrackSummary}>({nodes:[],edges:[]})
const detail=reactive({visible:false,node:null as SkillNode|null})
const orderedNodes=computed(()=>[...graph.nodes].sort((a,b)=>a.difficulty-b.difficulty))
const graphOption=computed(()=>({tooltip:{formatter:(p:any)=>p.data?.description||p.name},series:[{type:'graph',layout:'force',roam:true,draggable:true,label:{show:true,position:'right'},force:{repulsion:260,edgeLength:[90,180]},data:graph.nodes.map(n=>({...n,symbolSize:38+n.difficulty*6,itemStyle:{color:n.kind==='core'?'#3674ed':'#7656e8'}})),edges:graph.edges.map(e=>({source:e.source,target:e.target,lineStyle:{color:'#aab8d2'},symbol:['none','arrow']})),emphasis:{focus:'adjacency',lineStyle:{width:3}}}]}))
const prerequisites=computed(()=>graph.edges.filter(e=>e.target===detail.node?.id).map(e=>graph.nodes.find(n=>n.id===e.source)?.name||e.source))
const successors=computed(()=>graph.edges.filter(e=>e.source===detail.node?.id).map(e=>graph.nodes.find(n=>n.id===e.target)?.name||e.target))
onMounted(async()=>{tracks.value=(await getData<{items:TrackSummary[]}>('/tracks')).items;await loadGraph()})
async function loadGraph(){const result=await getData<any>(`/tracks/${trackCode.value}/skill-graph`);Object.assign(graph,result)}
function onNodeClick(params:any){const node=graph.nodes.find(item=>item.id===params.data?.id);if(node)showNode(node)}
function showNode(node:SkillNode){detail.node=node;detail.visible=true}
</script>

<style scoped>
.toolbar{display:flex;justify-content:space-between;align-items:center}.toolbar h2{margin:0 0 8px}.toolbar p{margin:0;color:var(--muted)}.toolbar .el-select{width:260px}.graph-layout{grid-template-columns:minmax(0,1fr) 320px;margin-top:18px}.graph-panel{padding:5px}.order-item{display:flex;gap:12px;align-items:center;padding:12px;border-radius:12px;transition:.2s}.order-item>span{width:30px;height:30px;border-radius:10px;background:#edf3ff;color:#3168ee;display:grid;place-items:center;font-weight:700}.order-item b,.order-item small{display:block}.order-item small{color:var(--muted);margin-top:3px}.description{font-size:16px;line-height:1.8}@media(max-width:950px){.graph-layout{grid-template-columns:1fr}.toolbar{flex-direction:column;align-items:flex-start;gap:14px}}
</style>
