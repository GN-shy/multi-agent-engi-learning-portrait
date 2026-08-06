<template>
  <AppShell>
    <div class="onboarding-page">
      <header class="onboarding-head">
        <div>
          <span class="eyebrow">{{ editing ? '重新校准成长档案' : '首次使用 · 约 3 分钟' }}</span>
          <h2>先了解你，再给路线</h2>
          <p>不用写自我介绍，也不用猜一个抽象分数。只选择真实经历，后续测评和项目证据会持续修正结果。</p>
        </div>
        <div class="privacy-note"><b>你的选择用于</b><span>方向比较、学习顺序、难度和每周任务</span></div>
      </header>

      <section class="wizard panel">
        <div class="step-rail">
          <button v-for="(item,index) in steps" :key="item" :class="{active:step===index,done:step>index}" @click="jumpTo(index)">
            <i>{{ step > index ? '✓' : index + 1 }}</i><span>{{ item }}</span>
          </button>
        </div>

        <main class="wizard-content">
          <section v-if="step===0" class="step-content">
            <div class="step-title"><span>01</span><div><h3>你现在处于什么阶段？</h3><p>这会影响学习起点、解释深度和就业建议。</p></div></div>
            <div class="choice-grid stage-grid">
              <button v-for="item in stageOptions" :key="item.value" :class="{selected:form.stage===item.value}" @click="form.stage=item.value">
                <b>{{ item.label }}</b><span>{{ item.hint }}</span>
              </button>
            </div>
            <div class="form-grid">
              <label><span>当前学历/年级</span><el-select v-model="form.education" placeholder="请选择"><el-option v-for="item in educationOptions" :key="item" :label="item" :value="item" /></el-select></label>
              <label><span>就业或发展城市（可填写任意城市）</span><el-input v-model="form.city" maxlength="30" placeholder="例如：苏州、长沙、厦门；暂不确定也可以填写" /></label>
            </div>
          </section>

          <section v-else-if="step===1" class="step-content">
            <div class="step-title"><span>02</span><div><h3>你真正做过哪些事？</h3><p>选择“做到过”的程度，不考察术语记忆；没接触过可以保持默认。</p></div></div>
            <div class="experience-grid">
              <button v-for="item in experienceOptions" :key="item.value" :class="{selected:form.experiences.includes(item.value)}" @click="toggleExperience(item.value)">
                <b>{{ item.label }}</b><span>{{ item.hint }}</span>
              </button>
            </div>
            <h4>常见能力与技术</h4>
            <div class="skill-list">
              <div v-for="item in skillOptions" :key="item.code">
                <p><b>{{ item.name }}</b><span>{{ item.hint }}</span></p>
                <el-select v-model="form.skills[item.code]">
                  <el-option v-for="level in skillLevels" :key="level.value" :label="level.label" :value="level.value" />
                </el-select>
              </div>
            </div>
          </section>

          <section v-else-if="step===2" class="step-content">
            <div class="step-title"><span>03</span><div><h3>你希望这次学习解决什么？</h3><p>目标和时间必须真实，系统会据此计算路线长度和每周任务量。</p></div></div>
            <div class="choice-grid goal-grid">
              <button v-for="item in goalOptions" :key="item.value" :class="{selected:form.goals.includes(item.value)}" @click="toggleGoal(item.value)">
                <b>{{ item.label }}</b><span>{{ item.hint }}</span>
              </button>
            </div>
            <p class="selection-hint">可多选，最多 3 个目标。系统会识别主次，但不会丢掉比赛、作品或就业等并行诉求。</p>
            <div class="form-grid three-fields">
              <label><span>希望多久看到成果</span><el-select v-model="form.horizon"><el-option v-for="item in horizonOptions" :key="item.value" :label="item.label" :value="item.value" /></el-select></label>
              <label><span>每周真实可投入</span><el-input-number v-model="form.weeklyHours" :min="2" :max="60" /> <small>小时</small></label>
              <label><span>更适合你的方式</span><el-select v-model="form.learningStyle"><el-option label="边做边学" value="practice_first"/><el-option label="理论与实践均衡" value="balanced"/><el-option label="先理解原理" value="theory_first"/></el-select></label>
            </div>
          </section>

          <section v-else-if="step===3" class="step-content">
            <div class="step-title"><span>04</span><div><h3>{{ form.unsure ? '先做职业倾向量表' : '选择你想组合的方向' }}</h3><p>{{ form.unsure ? '没有标准答案，只判断你更愿意长期解决哪类问题。9 题答完后给出 3 个可解释候选。' : '可选择 1–3 个方向，系统直接合并为完整路线，不再对你主动选择的方向做伪排名。' }}</p></div></div>
            <button class="unsure" :class="{selected:form.unsure}" @click="chooseUnsure"><b>{{ form.unsure ? '✓ 我还不知道适合什么方向' : '我还不知道适合什么方向' }}</b><span>{{ form.unsure ? '正在使用职业倾向量表；再次点击可改为自主选择' : '点击后填写行为倾向题，由系统推荐候选' }}</span></button>
            <div v-if="form.unsure" class="assessment-scale">
              <article v-for="(item,index) in scaleQuestions" :key="item.code" :class="{answered:form.interestScale[item.code]>0}">
                <div><i>{{ index + 1 }}</i><p><b>{{ item.title }}</b><span>{{ item.hint }}</span></p></div>
                <el-radio-group v-model="form.interestScale[item.code]">
                  <el-radio-button v-for="level in scaleLevels" :key="level.value" :label="level.value">{{ level.label }}</el-radio-button>
                </el-radio-group>
              </article>
              <p class="scale-progress">已回答 {{ answeredScaleCount }}/{{ scaleQuestions.length }} 题。推荐会同时结合学历、城市、目标、已有基础和每周时间。</p>
            </div>
            <div v-else class="direction-grid">
              <button v-for="item in directionOptions" :key="item.value" :class="{selected:form.directions.includes(item.value)}" @click="toggleDirection(item.value)">
                <b>{{ item.label }}</b><span>{{ item.role }}</span><small>{{ item.stack }}</small>
              </button>
            </div>
          </section>

          <section v-else class="step-content confirm-step">
            <div class="step-title"><span>05</span><div><h3>这是系统理解的你</h3><p>请确认是否准确。推荐会说明依据，不把算法判断包装成事实。</p></div></div>
            <article class="learner-summary">
              <div class="summary-avatar">{{ user.displayName[0] }}</div>
              <div><span>学习者摘要</span><h3>{{ userSummary }}</h3><p>{{ evidenceSummary }}</p></div>
              <el-button @click="step=0">返回修改</el-button>
            </article>
            <div class="result-preview">
              <div><span>系统下一步会做</span><b>{{ form.unsure ? '给出 3 个方向候选' : `组合 ${form.directions.length} 个主动选择` }}</b><small>{{ form.unsure ? '逐项展示学历、城市、兴趣、目标、能力与时间依据' : '自动选择细分技术栈、合并公共基础并补齐前置依赖' }}</small></div>
              <div><span>最终会得到</span><b>完整技术栈路线</b><small>具体到技术、项目、验收标准和本周任务</small></div>
              <div><span>结果如何更新</span><b>由真实证据校准</b><small>测试、项目提交和反馈会持续修正画像</small></div>
            </div>
            <el-alert title="首次结果包含主观选择，因此会标记为“初始画像”；完成测评或项目后，系统会提高证据权重。" type="info" :closable="false" show-icon />
          </section>
        </main>

        <footer class="wizard-actions">
          <el-button v-if="step>0" size="large" @click="step--">上一步</el-button>
          <span>{{ step + 1 }} / {{ steps.length }}</span>
          <el-button v-if="step<steps.length-1" type="primary" size="large" :disabled="!canContinue" @click="step++">继续</el-button>
          <el-button v-else type="primary" size="large" :loading="saving" @click="finish">{{ form.unsure ? '确认，查看量表推荐' : '确认，生成组合学习路线' }}</el-button>
        </footer>
      </section>
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import AppShell from '@/components/layout/AppShell.vue'
import { getData, postData, putData } from '@/api'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const user = useUserStore()
const step = ref(0)
const saving = ref(false)
const editing = ref(route.query.edit === '1')
const steps = ['当前阶段','真实经历','目标与投入','方向意向','确认信息']
const stageOptions = [
  {value:'zero',label:'刚开始了解计算机',hint:'几乎没有编程经验'},
  {value:'student',label:'计算机相关专业在读',hint:'学过课程，但路线还不清晰'},
  {value:'cross',label:'非计算机专业 / 转行',hint:'需要补公共基础和作品'},
  {value:'jobseeker',label:'正在准备实习或校招',hint:'希望对齐岗位要求'},
  {value:'working',label:'已经从事技术工作',hint:'希望转方向或提升能力'},
]
const educationOptions = ['高中及以下','专科在读','专科毕业','本科大一','本科大二','本科大三','本科大四','本科毕业','硕士及以上']
const experienceOptions = [
  {value:'none',label:'还没有完整实践',hint:'只听课或刚开始'},
  {value:'course',label:'跟着课程写过代码',hint:'能完成示例和作业'},
  {value:'small_project',label:'做过小型个人项目',hint:'例如网页、脚本或管理系统'},
  {value:'independent',label:'独立完成过完整项目',hint:'能自行拆需求和排错'},
  {value:'team',label:'参与过团队协作',hint:'使用 Git、分支或评审'},
  {value:'deployed',label:'部署并维护过应用',hint:'有线上地址、日志或测试'},
]
const skillLevels = [
  {value:0,label:'没接触过'}, {value:25,label:'听说过，不会使用'}, {value:45,label:'能跟着示例完成'},
  {value:65,label:'可以独立完成任务'}, {value:85,label:'能解释原理并解决复杂问题'},
]
const skillOptions = [
  {code:'language',name:'编程语言',hint:'Python、Java、JavaScript、C/C++ 等'},
  {code:'web',name:'网页与接口',hint:'HTML/CSS、HTTP、前后端交互'},
  {code:'algorithm',name:'数据结构与算法',hint:'数组、树、复杂度和常见算法'},
  {code:'database',name:'数据库',hint:'SQL、表设计、索引和事务'},
  {code:'linux',name:'Linux 与命令行',hint:'文件、进程、服务和日志'},
  {code:'network',name:'计算机网络',hint:'TCP/IP、HTTP、DNS 和排错'},
  {code:'git',name:'Git 与协作',hint:'提交、分支、合并和代码评审'},
  {code:'engineering',name:'测试与工程交付',hint:'自动化测试、部署、文档和维护'},
]
const goalOptions = [
  {value:'internship',label:'找到一份开发实习',hint:'形成可展示作品和面试能力'},
  {value:'employment',label:'准备校招或社会招聘',hint:'对齐岗位技术栈与项目要求'},
  {value:'postgraduate',label:'考研与专业能力巩固',hint:'系统补齐计算机基础'},
  {value:'competition',label:'完成比赛或创新项目',hint:'做出可演示、可验证成果'},
  {value:'portfolio',label:'独立完成一个作品',hint:'从技术学习走到部署交付'},
  {value:'upskill',label:'提升当前岗位能力',hint:'解决真实工作中的能力缺口'},
]
const horizonOptions = [{value:'1个月',label:'1 个月：先完成最小成果'},{value:'3个月',label:'3 个月：形成项目能力'},{value:'6个月',label:'6 个月：达到实习/初级岗位要求'},{value:'1年',label:'1 年：系统构建专业能力'}]
const directionOptions = [
  {value:'web_frontend',label:'Web 前端',role:'前端工程师',stack:'HTML · CSS · JavaScript · Vue / React'},
  {value:'backend',label:'后端开发',role:'后端工程师',stack:'Java / Python · 数据库 · API · 微服务'},
  {value:'fullstack',label:'全栈开发',role:'全栈工程师',stack:'前端 · 后端 · 数据库 · 部署'},
  {value:'agent_engineering',label:'Agent 全栈',role:'智能体应用工程师',stack:'Python · LLM · RAG · Agent · Web'},
  {value:'llm_application',label:'LLM 应用',role:'LLM 应用工程师',stack:'Prompt · RAG · 评测 · 模型服务'},
  {value:'algorithms',label:'算法与竞赛',role:'算法工程师',stack:'数据结构 · 算法 · 数学 · 工程实现'},
  {value:'machine_learning',label:'机器学习',role:'机器学习工程师',stack:'Python · 数学 · 训练 · 部署'},
  {value:'embedded_iot',label:'嵌入式与物联网',role:'嵌入式工程师',stack:'C/C++ · MCU · RTOS · 硬件接口'},
  {value:'devops',label:'云原生与 DevOps',role:'DevOps / SRE',stack:'Linux · Docker · Kubernetes · CI/CD'},
  {value:'network_security',label:'网络与安全',role:'安全工程师',stack:'网络 · Linux · 攻防 · 安全工程'},
  {value:'data_engineering',label:'数据工程',role:'数据工程师',stack:'SQL · Python · 数据仓库 · 流处理'},
  {value:'mobile',label:'移动端开发',role:'移动端工程师',stack:'Android / iOS · 跨端 · 发布'},
]
const scaleQuestions = [
  {code:'visual_product',title:'看到一个不好用的页面时，我会想重新设计布局、交互和反馈。',hint:'界面体验、视觉表达与产品完成度'},
  {code:'logic_system',title:'我享受追踪数据如何流动，并找出一个系统为什么没有按预期运行。',hint:'逻辑推演、系统机制与问题定位'},
  {code:'math_model',title:'面对抽象公式、复杂度或模型原理，我愿意花较长时间推导清楚。',hint:'数学建模、算法证明与理论深度'},
  {code:'data_insight',title:'我喜欢从大量数据中整理规律，并用证据解释业务或技术问题。',hint:'数据分析、指标体系与数据管道'},
  {code:'data_ai',title:'我想让 AI 理解知识、调用工具并完成真实任务，而不只是聊天。',hint:'LLM、RAG、Agent 与智能应用'},
  {code:'hardware_device',title:'比起纯软件，我更想看到代码驱动真实设备、传感器或硬件。',hint:'嵌入式、物联网与软硬件联调'},
  {code:'security_investigation',title:'我对漏洞、异常行为和系统边界敏感，喜欢像侦探一样排查原因。',hint:'安全攻防、测试与故障分析'},
  {code:'automation_reliability',title:'我愿意把重复操作自动化，并持续提升系统稳定性和交付效率。',hint:'DevOps、质量工程与可靠性'},
  {code:'communication_product',title:'我喜欢理解用户真实需求，并把技术方案做成别人愿意使用的产品。',hint:'产品沟通、全栈交付与设计协作'},
]
const scaleLevels = [{value:1,label:'完全不像我'},{value:2,label:'不太像'},{value:3,label:'一般'},{value:4,label:'比较像'},{value:5,label:'非常像我'}]
const form = reactive({
  stage:'', education:'', city:'暂不确定', experiences:['none'] as string[],
  skills:Object.fromEntries(skillOptions.map(item=>[item.code,0])) as Record<string,number>,
  goals:[] as string[], horizon:'6个月', weeklyHours:8, learningStyle:'balanced', directions:[] as string[], unsure:true,
  interestScale:Object.fromEntries(scaleQuestions.map(item=>[item.code,0])) as Record<string,number>,
})
const labelOf = (items:any[], value:string) => items.find(item=>item.value===value)?.label || value
const selectedSkillNames = computed(() => skillOptions.filter(item=>form.skills[item.code]>=45).map(item=>item.name))
const userSummary = computed(() => {
  const stage = labelOf(stageOptions,form.stage) || '尚未选择阶段'
  const goal = form.goals.length ? form.goals.map(value=>labelOf(goalOptions,value)).join('，并且') : '尚未选择目标'
  const skills = selectedSkillNames.value.length ? `目前能够使用${selectedSkillNames.value.slice(0,3).join('、')}` : '目前尚未形成稳定技术基础'
  return `${stage}，${form.education || '学历待补充'}，${skills}；希望在${form.horizon}内${goal}，每周可投入 ${form.weeklyHours} 小时。`
})
const answeredScaleCount = computed(() => Object.values(form.interestScale).filter(value=>value>0).length)
const evidenceSummary = computed(() => form.unsure
  ? `已完成 ${answeredScaleCount.value} 项倾向证据；结果只作为探索起点，后续由测评和项目修正。`
  : `你主动选择了：${form.directions.map(code=>directionOptions.find(item=>item.value===code)?.label).join('、')}；系统将直接整合，不替你擅自删除。`)
const canContinue = computed(() => step.value===0 ? Boolean(form.stage&&form.education&&form.city.trim()) : step.value===2 ? Boolean(form.goals.length) : step.value===3 ? (form.unsure ? answeredScaleCount.value===scaleQuestions.length : Boolean(form.directions.length)) : true)

onMounted(async()=>{
  try {
    const existing=await getData<any>('/profiles/me')
    editing.value=true
    form.weeklyHours=existing.weekly_hours||8
    form.learningStyle=existing.learning_style||'balanced'
    const context=existing.decision_context||{}
    if(context.stage) form.stage=context.stage
    if(context.education) form.education=context.education
    if(context.city) form.city=context.city
    if(Array.isArray(context.experiences)) form.experiences=context.experiences
    if(Array.isArray(context.goal_codes)) form.goals=context.goal_codes
    if(context.horizon) form.horizon=context.horizon
    if(Array.isArray(context.directions)) form.directions=context.directions
    if(context.direction_mode) form.unsure=context.direction_mode==='assessment'
    if(context.interest_scale) Object.assign(form.interestScale,context.interest_scale)
  } catch (error:any) {
    if (error.response?.status !== 404) ElMessage.error(error.response?.data?.detail || '成长档案读取失败，请检查网络后重试')
  }
})
function jumpTo(index:number){ if(index<step.value) step.value=index }
function toggleExperience(value:string){
  if(value==='none'){ form.experiences=['none']; return }
  form.experiences=form.experiences.filter(item=>item!=='none')
  form.experiences=form.experiences.includes(value)?form.experiences.filter(item=>item!==value):[...form.experiences,value]
  if(!form.experiences.length) form.experiences=['none']
}
function chooseUnsure(){ form.unsure=!form.unsure; if(form.unsure) form.directions=[] }
function toggleGoal(value:string){
  if(form.goals.includes(value)) form.goals=form.goals.filter(item=>item!==value)
  else if(form.goals.length<3) form.goals.push(value)
  else ElMessage.warning('最多选择 3 个学习目标，请保留最重要的目标')
}
function toggleDirection(value:string){
  if(form.directions.includes(value)) form.directions=form.directions.filter(item=>item!==value)
  else if(form.directions.length<3) form.directions.push(value)
  else ElMessage.warning('最多选择 3 个方向进行重点比较')
}
function assessmentPayload(){
  const max=(...values:number[])=>Math.max(0,...values)
  const projectBonus=form.experiences.includes('independent')?65:form.experiences.includes('small_project')?45:form.experiences.includes('course')?30:0
  return {
    'core.programming':max(form.skills.language,form.skills.web),
    'core.data_structures':form.skills.algorithm,
    'core.database':form.skills.database,
    'core.os':Math.round((form.skills.linux+form.skills.engineering)/2),
    'core.network':form.skills.network,
    'core.linux':form.skills.linux,
    'core.git':max(form.skills.git,form.experiences.includes('team')?65:0),
    'core.software_engineering':max(form.skills.engineering,projectBonus,form.experiences.includes('deployed')?75:0),
  }
}
async function finish(){
  saving.value=true
  try{
    const directionNames=form.unsure?['职业倾向量表待推荐']:form.directions.map(code=>directionOptions.find(item=>item.value===code)?.label||code)
    const decisionContext={
      context_version:1,stage:form.stage,education:form.education,city:form.city.trim(),
      experiences:form.experiences,goal_codes:form.goals,horizon:form.horizon,
      direction_mode:form.unsure?'assessment':'chosen',directions:form.directions,
      interest_scale:form.unsure?form.interestScale:{},
    }
    await putData('/profiles/me/analyze',{
      background:`阶段：${labelOf(stageOptions,form.stage)}；学历：${form.education}；发展城市：${form.city}；实践经历：${form.experiences.map(value=>labelOf(experienceOptions,value)).join('、')}；目标周期：${form.horizon}。`,
      learning_goals:form.goals.map(value=>`${labelOf(goalOptions,value)}（${form.horizon}）`),
      preferences:[...directionNames,`@decision_context:${JSON.stringify(decisionContext)}`],
      weekly_hours:form.weeklyHours,
      learning_style:form.learningStyle,
      self_assessment:assessmentPayload(), diagnostic_results:{},
    })
    if(form.unsure){
      ElMessage.success('量表和成长档案已保存，正在计算候选方向')
      await router.replace({path:'/tracks',query:{from:'assessment'}})
    }else{
      const recommended=await postData<any>('/tracks/pathways/recommend',{track_codes:form.directions})
      if(form.directions[0]) await postData('/tracks/select',{track_code:form.directions[0]})
      ElMessage.success('已根据你的选择生成去重后的组合路线')
      await router.replace({path:'/generate',query:{pathways:recommended.pathway_ids.join(','),from:'onboarding'}})
    }
  }catch(error:any){ ElMessage.error(error.response?.data?.detail||'建档失败，请检查填写内容') }
  finally{ saving.value=false }
}
</script>

<style scoped>
.onboarding-page{max-width:1180px;margin:0 auto}.onboarding-head{display:flex;justify-content:space-between;gap:30px;align-items:center;padding:12px 4px 22px}.eyebrow{color:#2d63e2;font-size:12px;font-weight:800;letter-spacing:.08em}.onboarding-head h2{font-size:30px;margin:7px 0}.onboarding-head p{color:var(--muted);line-height:1.7;margin:0;max-width:720px}.privacy-note{min-width:250px;padding:13px 16px;border-radius:13px;background:#eef5ff}.privacy-note b,.privacy-note span{display:block}.privacy-note span{font-size:11px;color:#667792;margin-top:4px}.wizard{padding:0;overflow:hidden}.step-rail{display:grid;grid-template-columns:repeat(5,1fr);background:#f6f8fc;border-bottom:1px solid var(--line)}.step-rail button{border:0;background:transparent;padding:16px 8px;color:#77849a;display:flex;align-items:center;justify-content:center;gap:8px;cursor:pointer}.step-rail i{width:26px;height:26px;border-radius:9px;background:#e4e9f2;display:grid;place-items:center;font-style:normal;font-size:11px}.step-rail button.active{color:#245fe2;background:white}.step-rail button.active i{background:#2864e8;color:white}.step-rail button.done{color:#168463}.step-rail button.done i{background:#dff5ec;color:#168463}.wizard-content{min-height:510px;padding:32px 38px}.step-content{max-width:980px;margin:auto}.step-title{display:flex;gap:14px;align-items:center;margin-bottom:24px}.step-title>span{width:45px;height:45px;border-radius:14px;background:#2864e8;color:white;display:grid;place-items:center;font-weight:800}.step-title h3,.step-title p{margin:2px 0}.step-title h3{font-size:22px}.step-title p{color:var(--muted);font-size:13px}.choice-grid{display:grid;gap:12px}.stage-grid{grid-template-columns:repeat(5,1fr)}.goal-grid{grid-template-columns:repeat(3,1fr)}.selection-hint{font-size:11px;color:#667792;margin:10px 2px 0}.choice-grid button,.experience-grid button,.direction-grid button,.unsure{border:1px solid var(--line);background:#fbfcfe;border-radius:14px;padding:16px;text-align:left;color:inherit;cursor:pointer;transition:.16s}.choice-grid button:hover,.experience-grid button:hover,.direction-grid button:hover,.unsure:hover{border-color:#99b5f7}.choice-grid button.selected,.experience-grid button.selected,.direction-grid button.selected,.unsure.selected{border-color:#2d66eb;background:#eef4ff;box-shadow:0 0 0 3px rgba(45,102,235,.08)}.choice-grid b,.choice-grid span,.experience-grid b,.experience-grid span,.direction-grid b,.direction-grid span,.direction-grid small,.unsure b,.unsure span{display:block}.choice-grid span,.experience-grid span,.direction-grid span,.unsure span{font-size:11px;color:var(--muted);margin-top:6px;line-height:1.5}.direction-grid small{font-size:10px;color:#61718c;margin-top:8px}.form-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:16px;margin-top:24px}.three-fields{grid-template-columns:repeat(3,1fr)}.form-grid label>span{display:block;font-size:12px;font-weight:700;margin-bottom:8px}.form-grid .el-select{width:100%}.form-grid small{color:var(--muted)}.experience-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.step-content h4{margin:24px 0 10px}.skill-list{display:grid;grid-template-columns:repeat(2,1fr);gap:8px 18px}.skill-list>div{display:grid;grid-template-columns:1fr 190px;gap:12px;align-items:center;padding:9px 11px;border:1px solid var(--line);border-radius:11px}.skill-list p,.skill-list b,.skill-list span{display:block;margin:0}.skill-list span{font-size:10px;color:var(--muted);margin-top:3px}.unsure{width:100%;margin-bottom:14px}.direction-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.direction-grid button:disabled{opacity:.48;cursor:not-allowed}.learner-summary{display:grid;grid-template-columns:64px 1fr auto;gap:18px;align-items:center;padding:22px;border:1px solid #cddcff;border-radius:17px;background:linear-gradient(120deg,#f7faff,#eef4ff)}.summary-avatar{width:60px;height:60px;border-radius:18px;background:#2d65e8;color:white;display:grid;place-items:center;font-size:24px;font-weight:800}.learner-summary span{font-size:11px;color:#2d63e2;font-weight:800}.learner-summary h3{font-size:18px;line-height:1.65;margin:5px 0}.learner-summary p{font-size:12px;color:#687792;margin:0}.result-preview{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:18px 0}.result-preview>div{padding:16px;border:1px solid var(--line);border-radius:13px}.result-preview span,.result-preview b,.result-preview small{display:block}.result-preview span,.result-preview small{font-size:11px;color:var(--muted)}.result-preview b{margin:6px 0}.wizard-actions{padding:16px 38px;border-top:1px solid var(--line);display:flex;align-items:center;justify-content:flex-end;gap:12px;background:#fbfcfe}.wizard-actions>span{margin-right:auto;color:var(--muted);font-size:12px}@media(max-width:950px){.stage-grid,.direction-grid{grid-template-columns:repeat(2,1fr)}.goal-grid,.experience-grid,.three-fields{grid-template-columns:1fr}.skill-list{grid-template-columns:1fr}.onboarding-head{align-items:flex-start;flex-direction:column}.privacy-note{width:100%}}@media(max-width:650px){.step-rail span{display:none}.wizard-content{padding:24px 16px}.stage-grid,.direction-grid,.form-grid,.result-preview{grid-template-columns:1fr}.skill-list>div{grid-template-columns:1fr}.learner-summary{grid-template-columns:50px 1fr}.learner-summary .el-button{grid-column:1/-1}.wizard-actions{padding:14px 16px}}
.assessment-scale{display:grid;gap:9px}.assessment-scale article{display:grid;grid-template-columns:minmax(300px,1fr) auto;gap:16px;align-items:center;padding:12px 14px;border:1px solid var(--line);border-radius:13px;background:#fbfcfe}.assessment-scale article.answered{border-color:#bed1fb;background:#f7faff}.assessment-scale article>div{display:flex;gap:10px;align-items:flex-start}.assessment-scale i{flex:0 0 27px;width:27px;height:27px;border-radius:8px;background:#e9effc;color:#2c63e6;display:grid;place-items:center;font-style:normal;font-weight:800}.assessment-scale p,.assessment-scale b,.assessment-scale span{display:block;margin:0}.assessment-scale b{font-size:13px;line-height:1.5}.assessment-scale span{font-size:10px;color:var(--muted);margin-top:3px}.assessment-scale :deep(.el-radio-button__inner){padding:8px 10px;font-size:11px}.scale-progress{font-size:11px;color:#58709b;text-align:right}@media(max-width:950px){.assessment-scale article{grid-template-columns:1fr}}@media(max-width:650px){.assessment-scale :deep(.el-radio-group){display:grid;grid-template-columns:repeat(5,1fr)}.assessment-scale :deep(.el-radio-button__inner){width:100%;padding:8px 3px;font-size:9px}}
</style>
