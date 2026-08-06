<template>
  <AppShell>
    <section class="career-hero panel">
      <div><span class="eyebrow">真实岗位反推学习</span><h2>粘贴一份真实 JD，确定学习终点</h2><p>系统只提取招聘文本中明确出现的技术、学历、经验和职责；解析结果必须由你确认后才会影响路线。</p></div>
      <div v-if="currentTarget" class="current-target"><span>当前目标</span><b>{{ currentTarget.title }}</b><small>{{ currentTarget.city || '城市未明确' }} · {{ currentTarget.company || '公司未填写' }}</small></div>
    </section>

    <div class="career-layout">
      <main>
        <section class="panel">
          <div class="panel-title"><div><h3>① 输入招聘信息</h3><p>建议保留岗位职责、任职要求、城市、学历和薪资原文</p></div></div>
          <el-input v-model="rawText" type="textarea" :rows="12" maxlength="30000" show-word-limit placeholder="粘贴完整岗位描述，例如：Java 后端开发实习生……" />
          <div class="source-row"><el-input v-model="sourceUrl" placeholder="招聘页面链接（可选，用于追溯）" /><el-button type="primary" size="large" :loading="parsing" @click="parseJob">解析岗位要求</el-button></div>
        </section>

        <section v-if="parsed" class="panel parsed-panel">
          <div class="panel-title"><div><span class="eyebrow">解析可信度 {{ Math.round(parsed.confidence*100) }}%</span><h3>② 确认提取结果</h3><p>未明确的信息保持空白或“未明确”，系统不会自行编造</p></div></div>
          <div class="form-grid">
            <label><span>岗位名称</span><el-input v-model="parsed.title" /></label>
            <label><span>公司</span><el-input v-model="parsed.company" placeholder="可选" /></label>
            <label><span>就业城市</span><el-input v-model="parsed.city" placeholder="例如：苏州" /></label>
            <label><span>学历要求</span><el-input v-model="parsed.education" /></label>
            <label><span>经验要求</span><el-input v-model="parsed.experience" /></label>
            <label><span>薪资原文</span><el-input v-model="parsed.salary" /></label>
          </div>
          <h4>岗位技术栈与当前差距</h4>
          <div class="skill-table">
            <div v-for="item in parsed.gap_analysis.items" :key="item.name">
              <p><b>{{ item.name }}</b><span>原文命中：{{ item.evidence.join('、') }}</span></p>
              <el-progress :percentage="Math.round(item.current)" :status="item.gap===0?'success':undefined" />
              <i :class="{ok:item.gap===0}">{{ item.gap===0?'已有证据':'差距 '+item.gap }}</i>
              <el-button text type="danger" @click="removeSkill(item.name)">移除误识别</el-button>
            </div>
          </div>
          <h4>岗位职责</h4>
          <div class="responsibilities"><el-input v-for="(_,index) in parsed.responsibilities" :key="index" v-model="parsed.responsibilities[index]" /><el-button @click="parsed.responsibilities.push('')">添加职责</el-button></div>
          <el-alert :title="parsed.limitations.join('；')" type="info" :closable="false" show-icon />
          <footer class="confirm"><div><b>确认后将生成路线调整建议</b><span>不会立即覆盖当前路线，你可以查看差异后接受或拒绝</span></div><el-button type="primary" size="large" :loading="saving" @click="confirmTarget">确认目标岗位</el-button></footer>
        </section>
      </main>

      <aside>
        <section class="panel target-card" v-if="currentTarget">
          <span class="eyebrow">当前目标岗位</span><h3>{{ currentTarget.title }}</h3><p>{{ currentTarget.company || '未填写公司' }} · {{ currentTarget.city || '城市未明确' }}</p>
          <div><span>学历</span><b>{{ currentTarget.education }}</b></div><div><span>经验</span><b>{{ currentTarget.experience }}</b></div><div><span>薪资</span><b>{{ currentTarget.salary }}</b></div>
          <h4>优先补齐</h4><el-tag v-for="item in currentTarget.analysis?.gap_analysis?.priority_skills?.slice(0,6)" :key="item.name" type="warning" effect="plain">{{ item.name }} · {{ item.gap }}</el-tag>
          <el-button type="primary" plain @click="router.push('/plan')">查看路线调整 →</el-button>
        </section>
        <section class="panel help"><h3>系统不会做什么</h3><ul><li>不会把未写明的薪资和学历补成事实</li><li>不会仅凭城市名称声称有多少岗位</li><li>不会在你确认前修改路线</li><li>不会用关键词命中代替真实能力证据</li></ul></section>
      </aside>
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import AppShell from '@/components/layout/AppShell.vue'
import { getData, postData } from '@/api'

const router=useRouter(),rawText=ref(''),sourceUrl=ref(''),parsing=ref(false),saving=ref(false),parsed=ref<any>(null),currentTarget=ref<any>(null)
onMounted(loadCurrent)
async function loadCurrent(){currentTarget.value=await getData('/career/targets/current').catch(()=>null)}
async function parseJob(){
  if(rawText.value.trim().length<30)return ElMessage.warning('请粘贴较完整的岗位描述，至少 30 个字符')
  parsing.value=true
  try{parsed.value=await postData('/career/jobs/parse',{raw_text:rawText.value,source_url:sourceUrl.value});if(!parsed.value.required_skills.length)ElMessage.warning('没有识别到明确技术栈，请补充任职要求或换一份完整 JD')}
  finally{parsing.value=false}
}
function removeSkill(name:string){parsed.value.required_skills=parsed.value.required_skills.filter((item:any)=>item.name!==name);parsed.value.gap_analysis.items=parsed.value.gap_analysis.items.filter((item:any)=>item.name!==name)}
async function confirmTarget(){
  if(!parsed.value.title.trim()||!parsed.value.required_skills.length)return ElMessage.warning('请确认岗位名称和至少一项明确技能')
  saving.value=true
  try{
    const result=await postData<any>('/career/targets',{...parsed.value,raw_text:rawText.value,source_url:sourceUrl.value,required_skills:parsed.value.gap_analysis.items})
    currentTarget.value=result.target
    ElMessage.success(result.revision?'目标已确认，学习中心有一条待确认的路线调整':'目标岗位已确认，请先生成学习路线')
    if(result.revision)router.push('/plan')
  }finally{saving.value=false}
}
</script>

<style scoped>
.career-hero{display:flex;justify-content:space-between;gap:30px;align-items:center;background:linear-gradient(120deg,#fff,#eef4ff)}.eyebrow{color:#2b63e5;font-size:11px;font-weight:800;letter-spacing:.08em}.career-hero h2{font-size:29px;margin:8px 0}.career-hero p{color:var(--muted);max-width:760px;line-height:1.7}.current-target{min-width:240px;padding:16px;border-radius:14px;background:white;border:1px solid #dbe5fb}.current-target span,.current-target b,.current-target small{display:block}.current-target span,.current-target small{color:var(--muted);font-size:11px}.current-target b{margin:6px 0}.career-layout{display:grid;grid-template-columns:minmax(0,1fr) 310px;gap:16px;margin-top:16px}.career-layout main,.career-layout aside{display:grid;gap:16px;align-content:start}.source-row{display:grid;grid-template-columns:1fr auto;gap:10px;margin-top:14px}.form-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.form-grid label>span{display:block;font-size:11px;font-weight:700;margin-bottom:6px}.parsed-panel h4{margin:24px 0 10px}.skill-table{display:grid;gap:8px}.skill-table>div{display:grid;grid-template-columns:1fr 220px 90px 80px;gap:12px;align-items:center;padding:10px 12px;border:1px solid var(--line);border-radius:11px}.skill-table p,.skill-table b,.skill-table span{display:block;margin:0}.skill-table span{font-size:10px;color:var(--muted);margin-top:4px}.skill-table i{font-size:11px;color:#e36b37;font-style:normal}.skill-table i.ok{color:#16a271}.responsibilities{display:grid;gap:7px;margin-bottom:14px}.confirm{display:flex;justify-content:space-between;align-items:center;gap:20px;margin-top:18px;padding-top:16px;border-top:1px solid var(--line)}.confirm b,.confirm span{display:block}.confirm span{color:var(--muted);font-size:11px;margin-top:4px}.target-card>div{display:flex;justify-content:space-between;padding:9px 0;border-bottom:1px solid var(--line);font-size:12px}.target-card .el-tag{margin:0 5px 6px 0}.target-card .el-button{width:100%;margin-top:12px}.help li{font-size:12px;color:#596981;line-height:1.8}@media(max-width:1050px){.career-layout{grid-template-columns:1fr}.career-layout aside{grid-template-columns:repeat(2,1fr)}}@media(max-width:720px){.career-hero,.confirm{align-items:flex-start;flex-direction:column}.current-target{width:100%}.form-grid,.career-layout aside{grid-template-columns:1fr}.skill-table>div{grid-template-columns:1fr}.source-row{grid-template-columns:1fr}}
</style>
