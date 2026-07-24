<template>
  <AppShell>
    <section class="panel">
      <div class="panel-title"><div><h3>个性化资源库</h3><p>每一份资源都绑定路线、画像版本、会话与来源证据</p></div><el-radio-group v-model="type" @change="load"><el-radio-button value="">全部</el-radio-button><el-radio-button value="lecture">讲义</el-radio-button><el-radio-button value="practice">实操</el-radio-button><el-radio-button value="assessment">测试</el-radio-button><el-radio-button value="plan">计划</el-radio-button></el-radio-group></div>
      <div v-if="resources.length" class="resource-grid"><article v-for="item in resources" :key="item.id" class="resource clickable" @click="open(item)"><div class="icon">{{ icons[item.resource_type] }}</div><div><el-tag>{{ labels[item.resource_type] }}</el-tag><h3>{{ item.title }}</h3><p>{{ item.track_code }} · v{{ item.version }} · {{ new Date(item.created_at).toLocaleString() }}</p><span>{{ item.source_traces.length }} 条来源证据</span></div></article></div>
      <div v-else class="empty"><p>尚无此类资源</p><el-button type="primary" @click="router.push('/generate')">运行智能生成</el-button></div>
    </section>
    <DetailModal v-model="detail.visible" :title="detail.item?.title || '资源详情'"><template v-if="detail.loading"><el-skeleton :rows="8" animated /></template><template v-else><el-descriptions :column="2" border><el-descriptions-item label="资源类型">{{ labels[detail.item?.resource_type] }}</el-descriptions-item><el-descriptions-item label="路线">{{ detail.item?.track_code }}</el-descriptions-item><el-descriptions-item label="版本">v{{ detail.item?.version }}</el-descriptions-item><el-descriptions-item label="来源数">{{ detail.item?.source_traces?.length }}</el-descriptions-item></el-descriptions><section v-if="detail.item?.content?.ai_enhancement" class="ai-box"><div class="tag-row"><el-tag type="success">AI 生成段落</el-tag><el-tag type="info">{{ detail.item.content.ai_enhancement.model }}</el-tag></div><p>{{ detail.item.content.ai_enhancement.personalized_summary }}</p><small>生成时间：{{ detail.item.content.ai_enhancement.generated_at }} · 引用：{{ detail.item.content.ai_enhancement.citation_ids?.join('、') }}</small></section><h4>内容</h4><pre>{{ JSON.stringify(detail.item?.content,null,2) }}</pre><h4>来源</h4><div v-for="source in detail.item?.source_traces||[]" :key="source.chunk_id" class="source"><a :href="source.source_url" target="_blank" rel="noreferrer">{{ source.title }} · {{ source.source_title }}</a><span>{{ source.content_version }} · {{ source.source_layer || '本地知识库' }}<template v-if="source.retrieved_at"> · {{ source.retrieved_at }}</template></span></div></template></DetailModal>
  </AppShell>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue';import { useRoute,useRouter } from 'vue-router'
import AppShell from '@/components/layout/AppShell.vue';import DetailModal from '@/components/common/DetailModal.vue';import { getData } from '@/api';import type { LearningResource } from '@/types/domain'
const route=useRoute(),router=useRouter(),type=ref(String(route.query.type||'')),resources=ref<LearningResource[]>([]),detail=reactive({visible:false,loading:false,item:null as any})
const labels:any={lecture:'个性化讲义',practice:'项目实操',assessment:'分阶测试',plan:'学习计划'},icons:any={lecture:'📘',practice:'🧪',assessment:'✅',plan:'🗺️'}
onMounted(load);watch(()=>route.query.type,()=>{type.value=String(route.query.type||'');load()})
async function load(){resources.value=(await getData<{items:LearningResource[]}>('/resources',{params:{resource_type:type.value||undefined}})).items}
async function open(item:LearningResource){detail.visible=true;detail.loading=true;try{detail.item=await getData(`/resources/${item.id}`)}finally{detail.loading=false}}
</script>

<style scoped>
.resource-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}.resource{display:grid;grid-template-columns:62px 1fr;gap:16px;align-items:center;padding:18px;border:1px solid var(--line);border-radius:16px;transition:.2s}.icon{width:58px;height:58px;border-radius:18px;background:#eef3ff;display:grid;place-items:center;font-size:25px}.resource h3{margin:10px 0 6px}.resource p,.resource span{color:var(--muted);font-size:12px}.ai-box{padding:16px;margin-top:18px;border:1px solid #bfe8d8;border-radius:14px;background:#f1fbf7}.ai-box p{line-height:1.75}.ai-box small{color:var(--success)}pre{white-space:pre-wrap;word-break:break-word;background:#f7f9fd;padding:16px;border-radius:12px;line-height:1.65}.source{display:flex;justify-content:space-between;gap:15px;padding:11px;border-bottom:1px solid var(--line)}@media(max-width:800px){.resource-grid{grid-template-columns:1fr}}
</style>
