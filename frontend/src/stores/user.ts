import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { api, patchData, postData, setAccessToken } from '@/api'
import type { ApiEnvelope } from '@/api'
import type { User } from '@/types/domain'

interface AuthPayload {
  access_token: string
  token_type: string
  expires_in: number
  user: User
}

export const useUserStore = defineStore('user', () => {
  const current = ref<User | null>(null)
  const initialized = ref(false)
  const loading = ref(false)
  const error = ref('')

  const isLoggedIn = computed(() => Boolean(current.value))
  const displayName = computed(() => current.value?.username || '用户名')

  function acceptAuth(payload: AuthPayload) {
    setAccessToken(payload.access_token)
    current.value = payload.user
  }

  async function initialize() {
    if (initialized.value) return isLoggedIn.value
    try {
      const { data } = await api.post<ApiEnvelope<AuthPayload>>('/auth/refresh')
      acceptAuth(data.data)
    } catch {
      setAccessToken('')
      current.value = null
    } finally {
      initialized.value = true
    }
    return isLoggedIn.value
  }

  async function login(account: string, password: string) {
    loading.value = true
    error.value = ''
    try {
      acceptAuth(await postData<AuthPayload>('/auth/login', { account, password }))
      return true
    } catch (reason: any) {
      error.value = reason.response?.data?.detail || '登录失败，请检查账号和密码'
      return false
    } finally {
      loading.value = false
    }
  }

  async function register(info: { username: string; email: string; password: string }) {
    loading.value = true
    error.value = ''
    try {
      acceptAuth(await postData<AuthPayload>('/auth/register', info))
      return true
    } catch (reason: any) {
      error.value = reason.response?.data?.detail || '注册失败'
      return false
    } finally {
      loading.value = false
    }
  }

  async function update(body: { username?: string; avatar?: string }) {
    current.value = await patchData<User>('/auth/me', body)
  }

  async function logout() {
    try {
      await postData('/auth/logout')
    } finally {
      setAccessToken('')
      current.value = null
    }
  }

  return {
    current,
    initialized,
    loading,
    error,
    isLoggedIn,
    displayName,
    initialize,
    login,
    register,
    update,
    logout,
  }
})
