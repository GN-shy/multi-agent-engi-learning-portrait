<template>
  <AppShell>
    <el-alert
      title="API Key 只提交给后端：临时模式仅驻留服务进程内存；加密模式只返回脱敏尾号。页面不会写入 localStorage、报告或 Agent 轨迹。"
      type="success"
      :closable="false"
      show-icon
    />

    <section class="panel quick-start section">
      <div class="quick-title"><div><span>3 步启用真实 AI</span><h3>加密保存后长期可用，无需每次重新连接</h3></div><el-tag effect="plain">OpenAI-compatible</el-tag></div>
      <div class="quick-steps">
        <div><i>1</i><p><b>选择厂商</b><span>DeepSeek、OpenAI 或兼容服务</span></p></div>
        <div><i>2</i><p><b>粘贴密钥并限额</b><span>密钥不进入浏览器持久存储</span></p></div>
        <div><i>3</i><p><b>连接测试</b><span>成功后在“智能生成”选择该模型</span></p></div>
      </div>
    </section>

    <div class="metric-grid section">
      <article class="metric"><span>服务配置</span><strong>{{ configs.length }}</strong><small>每个用户完全隔离</small></article>
      <article class="metric"><span>可用密钥</span><strong>{{ configs.filter(item => item.key_available).length }}</strong><small>明文永不返回前端</small></article>
      <article class="metric"><span>今日请求</span><strong>{{ totalRequests }}</strong><small>连接测试也计入限额</small></article>
      <article class="metric"><span>今日估算成本</span><strong>¥/$ {{ totalCost }}</strong><small>按用户填写的单价估算</small></article>
    </div>

    <section class="panel section">
      <div class="panel-title">
        <div><h3>AI 与搜索服务</h3><p>支持 DeepSeek、OpenAI-compatible、Tavily、Serper 及自定义搜索服务</p></div>
        <el-button type="primary" @click="openCreate">新增服务</el-button>
      </div>
      <el-table :data="configs" empty-text="尚未配置外部服务">
        <el-table-column label="服务" min-width="170">
          <template #default="{ row }">
            <b>{{ row.label }}</b>
            <div class="muted small">{{ providerLabel(row.provider) }}</div>
          </template>
        </el-table-column>
        <el-table-column label="类型" width="90">
          <template #default="{ row }"><el-tag>{{ row.service_type === 'llm' ? 'LLM' : '搜索' }}</el-tag></template>
        </el-table-column>
        <el-table-column label="模型/地址" min-width="220">
          <template #default="{ row }">
            <div>{{ row.model || '搜索 API' }}</div>
            <div class="muted small ellipsis">{{ row.base_url }}</div>
          </template>
        </el-table-column>
        <el-table-column label="密钥" width="150">
          <template #default="{ row }">
            <div>{{ row.masked_key || '未装载' }}</div>
            <el-tag size="small" :type="row.key_available ? 'success' : 'warning'">
              {{ row.storage_mode === 'temporary' ? '临时' : '加密' }} · {{ row.key_available ? '可用' : '缺失' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="今日用量" width="150">
          <template #default="{ row }">
            <div>{{ usageFor(row.id).requests || 0 }} / {{ row.daily_request_limit }} 次</div>
            <div class="muted small">{{ usageFor(row.id).estimated_cost || 0 }} / {{ row.daily_budget }} 预算</div>
          </template>
        </el-table-column>
        <el-table-column label="状态" min-width="190">
          <template #default="{ row }">
            <div class="status-line">
              <el-tag :type="testType(row.last_test_status)">{{ testLabel(row.last_test_status) }}</el-tag>
              <el-tag v-if="!row.enabled" type="info">已停用</el-tag>
            </div>
            <div v-if="row.storage_mode === 'encrypted' && row.key_available && row.last_test_status === 'success'" class="persisted-status">已持久连接，刷新或重新登录后自动恢复</div>
            <div v-else-if="row.last_test_message" class="muted small status-message">{{ row.last_test_message }}</div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="285" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" :loading="testingId === row.id" :disabled="!row.enabled || !row.key_available" @click="testConnection(row)">测试</el-button>
            <el-button link @click="openEdit(row)">编辑</el-button>
            <el-button v-if="row.storage_mode === 'temporary'" link type="warning" @click="openTemporary(row)">{{ row.key_available ? '更换密钥' : '装载密钥' }}</el-button>
            <el-button v-if="row.storage_mode === 'temporary' && row.key_available" link @click="clearTemporaryKey(row)">清除</el-button>
            <el-button link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <section class="panel section">
      <div class="panel-title"><div><h3>四种来源策略</h3><p>未配置外部服务时自动降级，核心学习闭环保持可用</p></div></div>
      <div class="mode-grid">
        <article v-for="mode in sourceModes" :key="mode.code">
          <b>{{ mode.name }}</b><p>{{ mode.description }}</p>
        </article>
      </div>
    </section>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑服务配置' : '新增服务配置'" width="min(760px, 94vw)">
      <el-form label-position="top">
        <div class="grid two">
          <el-form-item label="服务类型" required>
            <el-radio-group v-model="form.service_type" :disabled="Boolean(editingId)" @change="syncProvider">
              <el-radio-button label="llm">LLM</el-radio-button>
              <el-radio-button label="search">联网搜索</el-radio-button>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="厂商/协议" required>
            <el-select v-model="form.provider" @change="applyProviderDefault">
              <el-option v-for="item in filteredProviders" :key="item.provider" :label="providerLabel(item.provider)" :value="item.provider" />
            </el-select>
          </el-form-item>
        </div>
        <div class="grid two">
          <el-form-item label="配置名称" required><el-input v-model="form.label" placeholder="例如：我的 DeepSeek" /></el-form-item>
          <el-form-item v-if="form.service_type === 'llm'" label="模型名称" required><el-input v-model="form.model" placeholder="例如：deepseek-chat" /></el-form-item>
        </div>
        <el-form-item label="服务地址（HTTPS）" required><el-input v-model="form.base_url" placeholder="https://.../v1" /></el-form-item>
        <el-form-item :label="editingId ? 'API Key（留空则保持原密钥）' : 'API Key'" required>
          <el-input v-model="form.api_key" type="password" show-password autocomplete="new-password" />
        </el-form-item>
        <el-form-item label="保存方式">
          <el-radio-group v-model="form.storage_mode">
            <el-radio value="temporary">临时使用（服务重启/过期后清除）</el-radio>
            <el-radio value="encrypted">后端加密保存（推荐，无需重复连接）</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="服务状态">
          <el-switch v-model="form.enabled" active-text="启用" inactive-text="停用" />
        </el-form-item>
        <el-divider>限额与成本治理</el-divider>
        <div class="grid three">
          <el-form-item label="单次最大 Token"><el-input-number v-model="form.max_tokens_per_request" :min="64" :max="128000" /></el-form-item>
          <el-form-item label="每日请求上限"><el-input-number v-model="form.daily_request_limit" :min="1" :max="100000" /></el-form-item>
          <el-form-item label="超时（秒）"><el-input-number v-model="form.timeout_seconds" :min="3" :max="180" /></el-form-item>
          <el-form-item label="每日预算"><el-input-number v-model="form.daily_budget" :min="0" :precision="4" /></el-form-item>
          <el-form-item v-if="form.service_type === 'llm'" label="输入/百万 Token"><el-input-number v-model="form.input_price_per_million" :min="0" :precision="4" /></el-form-item>
          <el-form-item v-if="form.service_type === 'llm'" label="输出/百万 Token"><el-input-number v-model="form.output_price_per_million" :min="0" :precision="4" /></el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button :loading="saving" @click="save(false)">仅保存</el-button>
        <el-button type="primary" :loading="saving" @click="save(true)">保存并测试</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="temporaryDialog.visible" title="装载临时 API Key" width="min(520px, 92vw)">
      <el-alert title="密钥只驻留后端进程内存，到期、退出或显式清除后失效。" type="info" :closable="false" show-icon />
      <el-input v-model="temporaryDialog.key" class="temporary-input" type="password" show-password autocomplete="new-password" />
      <template #footer>
        <el-button @click="temporaryDialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="temporaryDialog.loading" @click="loadTemporaryKey">装载</el-button>
      </template>
    </el-dialog>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AppShell from '@/components/layout/AppShell.vue'
import { deleteData, getData, postData, putData } from '@/api'

const configs = ref<any[]>([])
const providers = ref<any[]>([])
const sourceModes = ref<any[]>([])
const sourceModeCopy: Record<string, {name: string; description: string}> = {
  knowledge_only: { name: '仅知识库', description: '只使用本地审核知识库，可靠性最高，不产生外部费用。' },
  knowledge_web: { name: '知识库 + 全网检索', description: '补充最新框架和技术资料，不调用生成模型。' },
  knowledge_ai: { name: '知识库 + AI 创作', description: '模型只能基于本地证据整合和个性化生成。' },
  full: { name: '全能力模式', description: '本地知识、联网检索、双 Agent 生成、仲裁与引用校验。' },
}
const usage = ref<any[]>([])
const dialogVisible = ref(false)
const editingId = ref('')
const saving = ref(false)
const testingId = ref('')
const temporaryDialog = reactive({ visible: false, configId: '', key: '', loading: false })
const defaults = {
  service_type: 'llm',
  provider: 'deepseek',
  label: '',
  base_url: 'https://api.deepseek.com/v1',
  model: 'deepseek-chat',
  api_key: '',
  storage_mode: 'encrypted',
  max_tokens_per_request: 2048,
  daily_budget: 2,
  timeout_seconds: 45,
  input_price_per_million: 0,
  output_price_per_million: 0,
  daily_request_limit: 100,
  enabled: true,
}
const form = reactive<any>({ ...defaults })
const filteredProviders = computed(() => providers.value.filter((item) => item.service_type === form.service_type))
const totalRequests = computed(() => usage.value.reduce((sum, item) => sum + Number(item.today.requests || 0), 0))
const totalCost = computed(() => usage.value.reduce((sum, item) => sum + Number(item.today.estimated_cost || 0), 0).toFixed(6))

onMounted(load)

async function load() {
  try {
    const [catalog, configData, usageData] = await Promise.all([
      getData<any>('/integrations/providers/catalog'),
      getData<any>('/integrations/providers'),
      getData<any>('/integrations/usage'),
    ])
    providers.value = catalog.items
    sourceModes.value = catalog.source_modes.map((item: any) => ({ ...item, ...(sourceModeCopy[item.code] || {}) }))
    configs.value = configData.items
    usage.value = usageData.items
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '外部服务配置加载失败')
  }
}
function openCreate() {
  editingId.value = ''
  Object.assign(form, defaults)
  dialogVisible.value = true
}
function openEdit(row: any) {
  editingId.value = row.id
  Object.assign(form, {
    ...row,
    api_key: '',
    input_price_per_million: row.input_price_per_million || 0,
    output_price_per_million: row.output_price_per_million || 0,
  })
  dialogVisible.value = true
}
function syncProvider() {
  const item = providers.value.find((provider) => provider.service_type === form.service_type)
  if (item) {
    form.provider = item.provider
    applyProviderDefault()
  }
}
function applyProviderDefault() {
  const item = providers.value.find((provider) => provider.provider === form.provider)
  if (item?.base_url) form.base_url = item.base_url
  if (form.provider === 'deepseek' && !form.model) form.model = 'deepseek-chat'
}
async function save(runTest: boolean) {
  if (!form.label.trim() || !form.base_url.startsWith('https://') || (!editingId.value && !form.api_key)) {
    ElMessage.warning('请填写名称、HTTPS 服务地址和 API Key')
    return
  }
  if (form.service_type === 'llm' && !form.model.trim()) {
    ElMessage.warning('LLM 配置必须填写模型名称')
    return
  }
  saving.value = true
  try {
    const saved = editingId.value
      ? await putData<any>(`/integrations/providers/${editingId.value}`, form)
      : await postData<any>('/integrations/providers', form)
    if (runTest) {
      const tested = await postData<any>(`/integrations/providers/${saved.id}/test`)
      ElMessage.success(tested.message || '配置已保存并通过连接测试')
    } else {
      ElMessage.success('服务配置已保存，明文密钥不会返回前端')
    }
    form.api_key = ''
    dialogVisible.value = false
    await load()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '配置保存失败')
  } finally {
    saving.value = false
  }
}
async function testConnection(row: any) {
  testingId.value = row.id
  try {
    const result = await postData<any>(`/integrations/providers/${row.id}/test`)
    ElMessage.success(result.message)
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '连接测试失败')
  } finally {
    testingId.value = ''
    await load()
  }
}
async function remove(row: any) {
  await ElMessageBox.confirm(`删除“${row.label}”及其用量记录？`, '删除服务配置', { type: 'warning' })
  await deleteData(`/integrations/providers/${row.id}`)
  ElMessage.success('服务配置已删除')
  await load()
}
function openTemporary(row: any) {
  Object.assign(temporaryDialog, { visible: true, configId: row.id, key: '', loading: false })
}
async function loadTemporaryKey() {
  if (temporaryDialog.key.length < 6) return ElMessage.warning('请输入有效 API Key')
  temporaryDialog.loading = true
  try {
    await postData(`/integrations/providers/${temporaryDialog.configId}/temporary-key`, { api_key: temporaryDialog.key })
    temporaryDialog.key = ''
    temporaryDialog.visible = false
    ElMessage.success('临时密钥已装载')
    await load()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '临时密钥装载失败')
  } finally {
    temporaryDialog.loading = false
  }
}
async function clearTemporaryKey(row: any) {
  await ElMessageBox.confirm(`清除“${row.label}”的临时密钥？之后可随时重新装载。`, '清除临时密钥', { type: 'warning' })
  await deleteData(`/integrations/providers/${row.id}/temporary-key`)
  ElMessage.success('临时密钥已从后端内存清除')
  await load()
}
function providerLabel(value: string) {
  return ({ deepseek: 'DeepSeek', openai: 'OpenAI', openai_compatible: 'OpenAI-compatible', tavily: 'Tavily', serper: 'Serper', custom: '自定义搜索' } as Record<string, string>)[value] || value
}
function usageFor(id: string) {
  return usage.value.find((item) => item.config.id === id)?.today || {}
}
function testLabel(value: string) {
  return ({ success: '连接成功', failed: '连接失败', untested: '未测试' } as Record<string, string>)[value] || value
}
function testType(value: string) {
  return ({ success: 'success', failed: 'danger', untested: 'info' } as Record<string, any>)[value] || 'info'
}
</script>

<style scoped>
.section{margin-top:18px}.quick-start{background:linear-gradient(120deg,#f8fbff,#eef4ff);border-color:#dbe6ff}.quick-title{display:flex;align-items:flex-start;justify-content:space-between}.quick-title span{color:#2b62df;font-size:11px;font-weight:800}.quick-title h3{margin:5px 0 0}.quick-steps{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:16px}.quick-steps>div{display:flex;gap:10px;padding:12px;border-radius:12px;background:rgba(255,255,255,.88);border:1px solid #e2eaff}.quick-steps i{width:28px;height:28px;flex:0 0 28px;display:grid;place-items:center;border-radius:9px;background:#2d65e8;color:white;font-style:normal;font-weight:800}.quick-steps p,.quick-steps b,.quick-steps span{display:block;margin:0}.quick-steps span{font-size:11px;color:var(--muted);margin-top:4px;line-height:1.45}.metric-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.metric small{display:block;color:var(--muted);margin-top:6px}.small{font-size:12px;margin-top:4px}.ellipsis{max-width:300px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.status-line{display:flex;gap:5px;align-items:center}.status-message{max-width:210px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.persisted-status{font-size:11px;color:#16835d;margin-top:4px;line-height:1.35}.mode-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.mode-grid article{padding:16px;border:1px solid var(--line);border-radius:14px;background:#f7f9fd}.mode-grid p{color:var(--muted);font-size:13px;line-height:1.6;margin-bottom:0}.el-select{width:100%}.temporary-input{margin-top:18px}@media(max-width:1000px){.metric-grid,.mode-grid{grid-template-columns:repeat(2,1fr)}.quick-steps{grid-template-columns:1fr}}@media(max-width:600px){.metric-grid,.mode-grid{grid-template-columns:1fr}}
</style>
