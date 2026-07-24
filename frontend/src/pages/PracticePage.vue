<template>
  <AppShell>
    <section class="panel">
      <div class="panel-title"><div><h3>项目实操任务</h3><p>完成步骤不等于通过：必须提交代码、截图或测试结果等运行证据</p></div><el-button type="primary" @click="router.push('/generate')">生成新任务</el-button></div>
      <div v-if="items.length" class="cards"><article v-for="item in items" :key="item.id" class="card clickable" @click="open(item)"><span>项目实操</span><h3>{{ item.title }}</h3><p>{{ item.track_code }} · {{ item.source_traces.length }} 条知识来源</p><el-button text>开始 / 继续 →</el-button></article></div>
      <div v-else class="empty">尚无实操任务，请先运行智能生成。</div>
    </section>
    <DetailModal v-model="detail.visible" :title="detail.item?.content?.title || '项目实操'">
      <template v-if="detail.loading"><el-skeleton :rows="8" animated /></template>
      <template v-else-if="detail.item">
        <el-alert :title="detail.item.content.acceptance" type="success" :closable="false"><template #title><b>最终验收：</b>{{ detail.item.content.acceptance }}</template></el-alert>
        <h4>交付物</h4><div class="tag-row"><el-tag v-for="value in detail.item.content.deliverables" :key="value">{{ value }}</el-tag></div>
        <h4>执行步骤</h4><el-checkbox-group v-model="submission.completed_step_ids" class="steps"><el-checkbox v-for="step in detail.item.content.steps" :key="step.id" :value="step.id"><b>{{ step.title }}</b><span>{{ step.proof_required }}</span></el-checkbox></el-checkbox-group>
        <h4>运行证据</h4><el-input v-model="evidenceText" type="textarea" :rows="5" placeholder="每行一条：提交哈希、测试结果、部署地址或截图说明" />
        <div v-if="result" class="score-result"><strong>{{ result.score }}</strong><div><b>{{ result.passed?'验收通过':'证据不足' }}</b><p>{{ result.next_action }}</p></div></div>
      </template>
      <template #footer><el-button @click="detail.visible=false">稍后继续</el-button><el-button type="primary" :loading="submitting" @click="submit">提交证据并评估</el-button></template>
    </DetailModal>
  </AppShell>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';import { useRouter } from 'vue-router';import { ElMessage } from 'element-plus'
import AppShell from '@/components/layout/AppShell.vue';import DetailModal from '@/components/common/DetailModal.vue';import { getData, postData } from '@/api';import type { LearningResource } from '@/types/domain'
const router=useRouter(),items=ref<LearningResource[]>([]),evidenceText=ref(''),submitting=ref(false),result=ref<any>(null)
const submission=reactive({completed_step_ids:[] as string[]})
const detail=reactive({visible:false,loading:false,item:null as any})
onMounted(async()=>items.value=(await getData<{items:LearningResource[]}>('/resources',{params:{resource_type:'practice'}})).items)
async function open(item:LearningResource){detail.visible=true;detail.loading=true;result.value=null;submission.completed_step_ids=[];evidenceText.value='';try{detail.item=await getData(`/resources/${item.id}`)}finally{detail.loading=false}}
async function submit(){if(!detail.item)return;submitting.value=true;try{result.value=await postData(`/practice/${detail.item.id}/submit`,{completed_step_ids:submission.completed_step_ids,evidence:evidenceText.value.split('\n').filter(Boolean)});ElMessage.success('实操证据已评估')}finally{submitting.value=false}}
</script>

<style scoped>
.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.card{padding:20px;border:1px solid var(--line);border-radius:17px;transition:.2s}.card>span{font-size:12px;color:#3168ee}.card p{color:var(--muted)}.steps{display:grid;gap:9px}.steps .el-checkbox{height:auto;margin:0;padding:12px;background:#f7f9fd;border-radius:11px}.steps b,.steps span{display:block}.steps span{color:var(--muted);font-size:12px;margin-top:4px}.score-result{display:flex;align-items:center;gap:18px;background:#eef8f4;border-radius:14px;padding:16px;margin-top:18px}.score-result>strong{font-size:36px;color:#17a673}.score-result p{margin:5px 0;color:#5f706a}@media(max-width:900px){.cards{grid-template-columns:1fr}}
</style>
