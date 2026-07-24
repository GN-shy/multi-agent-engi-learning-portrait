const labels: Record<string, string> = {
  programming_and_algorithms: '编程与算法',
  systems_foundation: '系统基础',
  software_engineering: '软件工程',
  architecture_and_security: '架构与安全',
  engineering_delivery: '工程交付',
  route_specific: '方向专项',
  track_name: '学习方向',
  track_code: '方向',
  role: '目标岗位',
  score: '匹配分',
  readiness: '基础准备度',
  interest_fit: '兴趣匹配',
  feasibility: '时间可行性',
  estimated_weeks: '预计周期',
  matched_keywords: '匹配关键词',
  skill_gaps: '待补技能',
  project: '代表项目',
  why: '推荐依据',
  counterfactual: '投入变化分析',
  if_weekly_hours_plus_4: '每周多投入 4 小时后的周期',
  highest_cost_skill: '学习成本最高的技能',
  switch_cost: '转向成本',
  skill_code: '技能',
  current: '当前水平',
  target: '目标水平',
  gap: '能力差距',
  difficulty: '难度',
  profile_score: '画像综合分',
  evidence_count: '有效画像证据',
  top_gaps: '首要技能缺口',
  query: '检索主题',
  retrieved: '检索证据数',
  source_ids: '采用的来源',
  sections: '生成章节数',
  strategy: '生成策略',
  candidate_scores: '候选方案评分',
  debate_triggered: '是否触发交叉验证',
  debate_rounds: '交叉验证轮次',
  debate: '交叉验证记录',
  winner: '主方案',
  decision_summary: '仲裁结论',
  total: '质量总分',
  knowledge_coverage: '知识覆盖率',
  citation_coverage: '引用覆盖率',
  citation_integrity: '引用完整性',
  profile_fit: '画像适配度',
  prerequisite_violations: '前置依赖冲突',
  hallucination_risk: '未引用风险估计',
  round: '轮次',
  topic: '争议主题',
  dgs_a: '严谨方案观点',
  dgs_b: '项目方案观点',
  ars_decision: '审核裁定',
  evidence_ids: '裁定证据',
  title: '名称',
  description: '说明',
  objective: '学习目标',
  explanation: '核心讲解',
  checkpoint: '掌握检查',
  citation_ids: '知识引用',
  source_title: '来源',
  source_url: '原始链接',
  content_version: '内容版本',
  source_layer: '资料层',
  credibility: '可信度',
  retrieved_at: '检索时间',
  duration_ms: '处理耗时',
  status: '状态',
  event_type: '处理阶段',
  summary: '处理结果',
  agent_code: '执行角色',
  sequence: '执行顺序',
  weekly_hours: '每周投入',
  learning_style: '学习方式',
  objectives: '本次学习目标',
  deliverables: '项目交付物',
  acceptance: '验收标准',
  proof_required: '所需证据',
  pass_score: '通过分数',
  max_score: '本题满分',
  rubric: '评分要点',
  week_start: '开始周',
  week_end: '结束周',
  hours_per_week: '每周投入',
  milestone: '阶段里程碑',
  effective_mode: '实际来源策略',
  requested_mode: '请求来源策略',
  fallbacks: '安全降级记录',
}

const routes: Record<string, string> = {
  web_frontend: 'Web 前端开发',
  backend: '后端开发',
  fullstack: '全栈开发',
  mobile: '移动端开发',
  quality_engineering: '测试与质量工程',
  devops: '云原生与 DevOps',
  algorithms: '算法与竞赛',
  machine_learning: '机器学习与深度学习',
  llm_application: 'LLM 应用开发',
  agent_engineering: 'Agent 全栈开发',
  embedded_iot: '嵌入式与物联网',
  operating_systems: '操作系统与系统编程',
  network_security: '网络与安全',
  database_systems: '数据库系统与内核',
  data_engineering: '数据工程',
}

const values: Record<string, string> = {
  completed: '已完成',
  running: '执行中',
  pending: '待开始',
  failed: '执行失败',
  active: '进行中',
  rigorous: '先修依赖优先',
  project_first: '项目实践优先',
  specification_first: '规范与原理优先',
  challenge_first: '挑战任务优先',
  theory_first: '理论先行',
  practice_first: '实操先行',
  balanced: '理论与实践均衡',
  knowledge_only: '仅审核知识库',
  knowledge_web: '知识库 + 联网检索',
  knowledge_ai: '知识库 + AI 创作',
  full: '全能力模式',
  local_knowledge: '本地审核知识库',
  reviewed_contribution: '人工审核贡献',
  web_search: '联网检索',
  dgs_a: '严谨生成方案',
  dgs_b: '项目生成方案',
  true: '是',
  false: '否',
}

export function fieldLabel(key: string): string {
  return labels[key] || key.replace(/_/g, ' ')
}

export function routeLabel(code?: string): string {
  return code ? routes[code] || code : '未选择方向'
}

export function valueLabel(value: unknown): string {
  if (typeof value === 'boolean') return value ? '是' : '否'
  if (value === null || value === undefined || value === '') return '暂无'
  if (typeof value === 'string') return values[value] || routes[value] || value
  return String(value)
}

export function percent(value: unknown): string {
  const number = Number(value || 0)
  return `${Math.round(number <= 1 ? number * 100 : number)}%`
}

export function dateTime(value?: string): string {
  if (!value) return '暂无'
  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString('zh-CN')
}

export function agentLabel(code?: string): string {
  return ({
    lms: '学情建模 Agent',
    krs: '知识检索 Agent',
    dgs_a: '严谨生成 Agent',
    dgs_b: '项目生成 Agent',
    ars: '仲裁审核 Agent',
    tis: '导学交互 Agent',
  } as Record<string, string>)[code || ''] || code || '未知 Agent'
}
