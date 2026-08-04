import { createRouter, createWebHistory } from 'vue-router'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: () => import('@/pages/LoginPage.vue'), meta: { public: true } },
    { path: '/', component: () => import('@/pages/Dashboard.vue'), meta: { title: '首页总览', eyebrow: '今天从正确的路线继续成长' } },
    { path: '/tracks', component: () => import('@/pages/TrackExplorer.vue'), meta: { title: '方向探索', eyebrow: '比较之后再选择，不用靠猜' } },
    { path: '/skills', component: () => import('@/pages/SkillGraphPage.vue'), meta: { title: '技能图谱', eyebrow: '看清前置依赖和能力缺口' } },
    { path: '/profile', component: () => import('@/pages/ProfilePage.vue'), meta: { title: '能力画像', eyebrow: '用证据认识当前的自己' } },
    { path: '/knowledge', component: () => import('@/pages/KnowledgePage.vue'), meta: { title: '知识检索', eyebrow: '所有生成内容都能追溯来源' } },
    { path: '/generate', component: () => import('@/pages/GeneratePage.vue'), meta: { title: '智能生成', eyebrow: '六 Agent 协作生成个性化学习闭环' } },
    { path: '/resources', component: () => import('@/pages/ResourcePage.vue'), meta: { title: '学习资源', eyebrow: '讲义、实操、测试与计划统一管理' } },
    { path: '/practice', component: () => import('@/pages/PracticePage.vue'), meta: { title: '项目实操', eyebrow: '提交运行证据，而不只是阅读' } },
    { path: '/assessment', component: () => import('@/pages/AssessmentPage.vue'), meta: { title: '分阶测试', eyebrow: '评测结果直接回写学习画像' } },
    { path: '/report', component: () => import('@/pages/ReportPage.vue'), meta: { title: '成长报告', eyebrow: '路线、盲区、趋势和质量证据' } },
    { path: '/agents', component: () => import('@/pages/AgentsPage.vue'), meta: { title: '多智能体协作', eyebrow: '展示可审计轨迹，不展示隐藏思维链' } },
    { path: '/plan', component: () => import('@/pages/LearningPlan.vue'), meta: { title: '学习计划', eyebrow: '按反馈动态调整的阶段路径' } },
    { path: '/records', component: () => import('@/pages/RecordsPage.vue'), meta: { title: '学习记录', eyebrow: '每一次资源、测试和实践都有证据' } },
    { path: '/messages', component: () => import('@/pages/MessagesPage.vue'), meta: { title: '消息中心', eyebrow: '任务完成与路径调整及时可见' } },
    { path: '/settings', component: () => import('@/pages/SettingsPage.vue'), meta: { title: '个人设置', eyebrow: '用户名和偏好真实生效' } },
    { path: '/integrations', component: () => import('@/pages/IntegrationsPage.vue'), meta: { title: 'AI 与搜索服务', eyebrow: 'BYOK、模型可替换、成本可治理' } },
    { path: '/session/:id', component: () => import('@/pages/SessionPage.vue'), meta: { title: '会话详情', eyebrow: '完整生成、仲裁与证据链' } },
    { path: '/admin', component: () => import('@/pages/AdminPage.vue'), meta: { title: '评测与治理', eyebrow: '质量指标和系统健康状态' } },
    { path: '/:pathMatch(.*)*', component: () => import('@/pages/NotFound.vue'), meta: { title: '页面未找到', eyebrow: '请检查链接是否有效' } },
  ],
})
