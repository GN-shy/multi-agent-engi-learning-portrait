<template>
  <AppShell>
    <section class="panel">
      <div class="panel-title"><div><h3>学习证据时间线</h3><p>资源生成、测试提交和项目实践都进入同一记录</p></div><el-input v-model="keyword" placeholder="筛选标题或路线" clearable /></div>
      <el-timeline v-if="filtered.length">
        <el-timeline-item v-for="item in filtered" :key="item.id" :timestamp="new Date(item.created_at).toLocaleString()" placement="top" :type="item.type==='assessment'?'success':'primary'">
          <article class="record clickable" @click="open(item)"><el-tag>{{ typeLabel(item.type) }}</el-tag><h3>{{ item.title }}</h3><p>{{ item.track_code }}</p></article>
        </el-timeline-item>
      </el-timeline>
      <div v-else class="empty">尚无匹配记录</div>
    </section>
    <DetailModal v-model="detail.visible" :title="detail.item?.title || '记录详情'"><el-descriptions :column="1" border><el-descriptions-item label="记录 ID">{{ detail.item?.id }}</el-descriptions-item><el-descriptions-item label="类型">{{ typeLabel(detail.item?.type) }}</el-descriptions-item><el-descriptions-item label="路线">{{ detail.item?.track_code }}</el-descriptions-item><el-descriptions-item label="时间">{{ detail.item?.created_at }}</el-descriptions-item></el-descriptions></DetailModal>
  </AppShell>
</template>

<script setup lang="ts">
import { computed,onMounted,reactive,ref } from 'vue';import AppShell from '@/components/layout/AppShell.vue';import DetailModal from '@/components/common/DetailModal.vue';import { getData } from '@/api'
const items=ref<any[]>([]),keyword=ref(''),detail=reactive({visible:false,item:null as any})
const filtered=computed(()=>items.value.filter(item=>`${item.title}${item.track_code}`.toLowerCase().includes(keyword.value.toLowerCase())))
onMounted(async()=>items.value=(await getData<{items:any[]}>('/records')).items)
function open(item:any){detail.item=item;detail.visible=true}
function typeLabel(type:string){return type==='assessment'?'分阶测试':type?.replace('resource:lecture','个性化讲义').replace('resource:practice','项目实操').replace('resource:assessment','测试资源').replace('resource:plan','学习计划')}
</script>

<style scoped>
.panel-title .el-input{width:260px}.record{border:1px solid var(--line);border-radius:15px;padding:17px;transition:.2s}.record h3{margin:10px 0 6px}.record p{margin:0;color:var(--muted)}
</style>
