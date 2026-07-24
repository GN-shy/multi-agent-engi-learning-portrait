<template>
  <AppShell>
    <section class="panel">
      <div class="panel-title"><div><h3>分阶能力测试</h3><p>不是只判选择题；要求写出可执行任务、边界与客观验收标准</p></div><el-button type="primary" @click="router.push('/generate')">生成新测试</el-button></div>
      <el-table :data="items" @row-click="open"><el-table-column prop="title" label="测试" min-width="300" /><el-table-column prop="track_code" label="路线" width="180" /><el-table-column prop="version" label="版本" width="90" /><el-table-column label="操作" width="120"><template #default><el-button text>开始测试</el-button></template></el-table-column></el-table>
      <div v-if="!items.length" class="empty">尚无测试，请先运行智能生成。</div>
    </section>
    <DetailModal v-model="detail.visible" :title="detail.item?.title || '分阶测试'">
      <template v-if="detail.loading"><el-skeleton :rows="8" animated /></template>
      <template v-else>
        <el-alert title="评分会检查答案是否包含可执行步骤、验证方式、边界和失败定位。" type="info" :closable="false" />
        <div v-for="(question,index) in detail.item?.content?.questions||[]" :key="question.id" class="question">
          <div><span>{{ index+1 }}</span><h4>{{ question.question }}</h4><el-tag>满分 {{ question.max_score }}</el-tag></div>
          <p>评分点：{{ question.rubric.join('；') }}</p>
          <el-input v-model="answers[question.id]" type="textarea" :rows="5" placeholder="请写出具体任务、步骤、验证方法和失败边界…" />
        </div>
        <div v-if="result" class="result"><strong>{{ result.score }}</strong><div><h3>{{ result.passed?'测试通过':'需要巩固' }}</h3><p>本次结果已经作为新证据回写画像。</p></div></div>
        <div v-if="result" class="details"><p v-for="row in result.details" :key="row.question_id"><b>{{ row.skill_code }} · {{ row.score }}/{{ row.max_score }}</b><span>{{ row.feedback }}</span></p></div>
      </template>
      <template #footer><el-button @click="detail.visible=false">退出</el-button><el-button type="primary" :loading="submitting" @click="submit">提交并回写画像</el-button></template>
    </DetailModal>
  </AppShell>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';import { useRouter } from 'vue-router';import { ElMessage } from 'element-plus'
import AppShell from '@/components/layout/AppShell.vue';import DetailModal from '@/components/common/DetailModal.vue';import { getData, postData } from '@/api';import type { LearningResource } from '@/types/domain'
const router=useRouter(),items=ref<LearningResource[]>([]),answers=reactive<Record<string,string>>({}),result=ref<any>(null),submitting=ref(false),detail=reactive({visible:false,loading:false,item:null as any})
onMounted(async()=>items.value=(await getData<{items:LearningResource[]}>('/resources',{params:{resource_type:'assessment'}})).items)
async function open(item:LearningResource){detail.visible=true;detail.loading=true;result.value=null;Object.keys(answers).forEach(k=>delete answers[k]);try{detail.item=await getData(`/resources/${item.id}`)}finally{detail.loading=false}}
async function submit(){if(!detail.item)return;submitting.value=true;try{result.value=await postData(`/assessments/${detail.item.id}/submit`,{answers});ElMessage.success('评分完成，画像已更新')}finally{submitting.value=false}}
</script>

<style scoped>
.question{padding:18px 0;border-bottom:1px solid var(--line)}.question>div{display:grid;grid-template-columns:34px 1fr auto;gap:10px;align-items:center}.question>div>span{width:30px;height:30px;border-radius:10px;background:#3168ee;color:white;display:grid;place-items:center}.question h4{margin:0}.question p{color:var(--muted);font-size:13px}.result{margin-top:20px;padding:18px;background:#eef8f4;border-radius:16px;display:flex;gap:18px;align-items:center}.result>strong{font-size:42px;color:#17a673}.result h3,.result p{margin:3px}.details p{display:flex;justify-content:space-between;padding:10px;border-bottom:1px solid var(--line)}.details span{color:var(--muted)}
</style>
