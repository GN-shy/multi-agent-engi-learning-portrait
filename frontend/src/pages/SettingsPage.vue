<template>
  <AppShell>
    <div class="grid two settings">
      <section class="panel">
        <div class="panel-title">
          <div><h3>个人资料</h3><p>首页、报告和 Agent 交互都会动态读取用户名</p></div>
        </div>
        <el-form label-position="top">
          <el-form-item label="用户名">
            <el-input v-model="username" maxlength="40" show-word-limit />
          </el-form-item>
          <el-form-item label="邮箱">
            <el-input :model-value="user.current?.email" disabled />
          </el-form-item>
          <el-form-item label="身份">
            <el-input :model-value="roleLabel" disabled />
          </el-form-item>
          <el-button type="primary" :loading="saving" @click="save">保存用户名</el-button>
        </el-form>
      </section>

      <section class="panel">
        <div class="panel-title">
          <div><h3>账户安全</h3><p>修改密码后会撤销已有刷新令牌，需要重新登录</p></div>
        </div>
        <el-form label-position="top">
          <el-form-item label="当前密码">
            <el-input v-model="password.current_password" type="password" show-password />
          </el-form-item>
          <el-form-item label="新密码（至少 8 位）">
            <el-input v-model="password.new_password" type="password" show-password />
          </el-form-item>
          <el-form-item label="确认新密码">
            <el-input v-model="password.confirm" type="password" show-password />
          </el-form-item>
          <el-button type="warning" :loading="changingPassword" @click="changePassword">
            修改密码并重新登录
          </el-button>
        </el-form>
      </section>

      <section class="panel">
        <div class="panel-title">
          <div><h3>数据权利</h3><p>导出平台保存的画像、路线、学习、评测和反馈数据</p></div>
        </div>
        <el-alert
          title="导出文件不包含密码、令牌、密钥或隐藏推理过程。"
          type="success"
          :closable="false"
          show-icon
        />
        <el-button class="export-button" :loading="exporting" @click="exportData">
          导出我的数据（JSON）
        </el-button>
      </section>

      <section class="panel">
        <div class="panel-title">
          <div><h3>隐私与可信设置</h3><p>平台默认执行的不可关闭安全基线</p></div>
        </div>
        <div class="setting-row">
          <div><b>隐藏模型思维链</b><span>仅展示执行摘要、证据、评分和裁定</span></div>
          <el-switch :model-value="true" disabled />
        </div>
        <div class="setting-row">
          <div><b>来源可追溯</b><span>正式生成章节要求绑定有效知识引用</span></div>
          <el-switch :model-value="true" disabled />
        </div>
        <div class="setting-row">
          <div><b>刷新令牌保护</b><span>使用 HttpOnly Cookie，前端脚本无法读取</span></div>
          <el-switch :model-value="true" disabled />
        </div>
        <div class="setting-row">
          <div><b>画像证据更新</b><span>测试和实践提交会产生新画像版本</span></div>
          <el-switch :model-value="true" disabled />
        </div>
      </section>

      <section class="panel danger-zone">
        <div class="panel-title">
          <div><h3>注销账户</h3><p>永久删除账号、画像、路线、会话、资源、评测与反馈记录</p></div>
        </div>
        <el-alert
          title="此操作不可恢复。建议先在“数据权利”中导出个人数据。"
          type="error"
          :closable="false"
          show-icon
        />
        <el-form label-position="top" class="delete-form">
          <el-form-item label="当前密码">
            <el-input v-model="accountDelete.current_password" type="password" show-password />
          </el-form-item>
          <el-form-item label="输入 DELETE 确认">
            <el-input v-model="accountDelete.confirmation" />
          </el-form-item>
          <el-button type="danger" :loading="deleting" @click="deleteAccount">
            永久删除我的账户
          </el-button>
        </el-form>
      </section>
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import AppShell from '@/components/layout/AppShell.vue'
import { deleteData, getData, putData } from '@/api'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const user = useUserStore()
const username = ref(user.displayName)
const saving = ref(false)
const changingPassword = ref(false)
const exporting = ref(false)
const deleting = ref(false)
const password = reactive({ current_password: '', new_password: '', confirm: '' })
const accountDelete = reactive({ current_password: '', confirmation: '' })
const roleLabel = computed(() => user.current?.role === 'admin' ? '治理管理员' : '学习者')

async function save() {
  if (username.value.trim().length < 2) {
    ElMessage.warning('用户名至少需要 2 个字符')
    return
  }
  saving.value = true
  try {
    await user.update({ username: username.value.trim() })
    ElMessage.success('用户名已更新，所有页面立即生效')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '用户名更新失败')
  } finally {
    saving.value = false
  }
}

async function changePassword() {
  if (password.current_password.length < 8 || password.new_password.length < 8) {
    ElMessage.warning('当前密码和新密码都至少需要 8 位')
    return
  }
  if (password.new_password !== password.confirm) {
    ElMessage.warning('两次输入的新密码不一致')
    return
  }
  await ElMessageBox.confirm('修改后需要使用新密码重新登录，是否继续？', '确认修改密码', {
    type: 'warning',
  })
  changingPassword.value = true
  try {
    await putData('/auth/password', {
      current_password: password.current_password,
      new_password: password.new_password,
    })
    ElMessage.success('密码已修改，请重新登录')
    await user.logout()
    await router.replace('/login')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '密码修改失败')
  } finally {
    changingPassword.value = false
  }
}

async function exportData() {
  exporting.value = true
  try {
    const data = await getData<any>('/auth/data-export')
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `工学智链_个人数据_${new Date().toISOString().slice(0, 10)}.json`
    link.click()
    URL.revokeObjectURL(url)
    ElMessage.success('个人数据已导出')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '数据导出失败')
  } finally {
    exporting.value = false
  }
}

async function deleteAccount() {
  if (accountDelete.current_password.length < 8 || accountDelete.confirmation !== 'DELETE') {
    ElMessage.warning('请输入当前密码，并准确输入 DELETE')
    return
  }
  await ElMessageBox.confirm(
    '将永久删除全部个人学习数据，且无法恢复。是否确认？',
    '最后确认',
    { type: 'error', confirmButtonText: '确认永久删除', cancelButtonText: '取消' },
  )
  deleting.value = true
  try {
    await deleteData('/auth/me', accountDelete)
    await user.logout()
    ElMessage.success('账户与关联数据已删除')
    await router.replace('/login')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '账户删除失败')
  } finally {
    deleting.value = false
  }
}
</script>

<style scoped>
.settings{align-items:start}.setting-row{display:flex;justify-content:space-between;align-items:center;padding:16px 0;border-bottom:1px solid var(--line)}.setting-row b,.setting-row span{display:block}.setting-row span{color:var(--muted);font-size:12px;margin-top:5px}.export-button{margin-top:22px;width:100%}.danger-zone{border-color:#f2c9cf}.danger-zone h3{color:var(--danger)}.delete-form{margin-top:18px}
</style>
