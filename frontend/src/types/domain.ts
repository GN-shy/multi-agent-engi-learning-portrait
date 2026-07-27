export interface User {
  id: string
  username: string
  email: string
  avatar: string
  role: string
  created_at: string
}

export interface TrackSummary {
  code: string
  cluster: string
  name: string
  role: string
  description: string
  keywords: string[]
  skill_count: number
  project: string
  pathway_count: number
  pathway_names: string[]
  estimated_months: string[]
}

export interface PathwayStage {
  title: string
  duration: string
  topics: string[]
}

export interface CareerProfile {
  roles: string[]
  work_content: string[]
  salary_range: string
  education: {
    minimum: string
    competitive: string
    note: string
  }
  market_outlook: string
  portfolio: string[]
}

export interface PathwayVariant {
  id: string
  track_code: string
  track_name?: string
  track_role?: string
  name: string
  estimated_months: string
  difficulty: number
  demand: number
  suitable_for: string
  milestone: string
  stages: PathwayStage[]
  stage_count?: number
  technology_count?: number
  career?: CareerProfile
  salary_scope?: string
}

export interface ComposedRouteTask {
  title: string
  pathway_id: string
  pathway_name: string
  stage_title: string
  skill_code: string
  learning_action: string
  evidence_required: string
  acceptance: string
}

export interface ComposedRoutePhase {
  id: string
  name: string
  week_start: number
  week_end: number
  pathway_names: string[]
  tasks: ComposedRouteTask[]
  milestone: string
}

export interface ComposedRoute {
  pathway_ids: string[]
  pathways: PathwayVariant[]
  strategy: string
  weekly_hours: number
  total_weeks: number
  estimated_months: number
  technology_count: number
  stack_index: Array<{
    pathway_id: string
    pathway_name: string
    track_code: string
    track_name: string
    estimated_months: string
    technologies: string[]
  }>
  phases: ComposedRoutePhase[]
  final_milestones: Array<{pathway_id?: string; pathway_name: string; milestone: string}>
  optimization_notes?: string[]
}

export interface TrackCluster {
  code: string
  name: string
  description: string
  tracks: TrackSummary[]
}

export interface SkillNode {
  id: string
  name: string
  description: string
  difficulty: number
  kind: 'core' | 'route'
}

export interface SkillEdge {
  source: string
  target: string
  relation: 'prerequisite'
}

export interface RouteMatch {
  track_code: string
  track_name: string
  role: string
  score: number
  readiness: number
  interest_fit: number
  feasibility: number
  estimated_weeks: number
  matched_keywords: string[]
  skill_gaps: Array<{
    skill_code: string
    name: string
    current: number
    target: number
    gap: number
    difficulty: number
  }>
  project: {
    title: string
    deliverables: string[]
    acceptance: string
  }
  why: string[]
  counterfactual: {
    if_weekly_hours_plus_4: number
    highest_cost_skill: string
    switch_cost: number
  }
  pathway_variants: Array<{
    id: string
    name: string
    estimated_months: string
    difficulty: number
    milestone: string
    stage_count: number
    technology_count?: number
    career?: CareerProfile
    salary_scope?: string
  }>
  career_summary?: {
    roles: string[]
    salary_ranges: string[]
    education: string[]
    salary_scope: string
  }
}

export interface Profile {
  id: string
  version: number
  background: string
  learning_goals: string[]
  preferences: string[]
  weekly_hours: number
  learning_style: string
  knowledge_breadth: number
  knowledge_depth: number
  engineering_maturity: number
  cognitive_load: number
  dimension_scores: Record<string, number>
  skill_scores: Record<string, number>
  blind_spots: Array<{ skill_code: string; name: string; score: number }>
  strengths: Array<{ skill_code: string; name: string; score: number }>
  comprehensive_score: number
  updated_at: string
}

export interface AgentEvent {
  sequence: number
  agent_code: string
  event_type: string
  status: string
  summary: string
  evidence: Record<string, unknown>
  duration_ms: number
  created_at?: string
}

export interface LearningSession {
  id: string
  session_id: string
  track_code: string
  goal: string
  topic: string
  source_mode?: 'knowledge_only' | 'knowledge_web' | 'knowledge_ai' | 'full'
  llm_config_id?: string | null
  search_config_id?: string | null
  source_audit?: Record<string, any>
  status: string
  profile: Record<string, unknown>
  route_match: RouteMatch
  evidence: Array<Record<string, any>>
  arbitration: Record<string, any>
  final_output: Record<string, any>
  quality_metrics: Record<string, number>
  events: AgentEvent[]
  created_at: string
}

export interface LearningResource {
  id: string
  session_id: string
  track_code: string
  resource_type: 'lecture' | 'practice' | 'assessment' | 'plan'
  title: string
  version: number
  source_traces: Array<Record<string, any>>
  content?: Record<string, any>
  created_at: string
}
