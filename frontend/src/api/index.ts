import axios, { AxiosError, type AxiosRequestConfig } from 'axios'

export interface ApiEnvelope<T> {
  code: number
  message: string
  data: T
  request_id: string
}

let accessToken = ''
let refreshPromise: Promise<string> | null = null

export function setAccessToken(token: string) {
  accessToken = token
}

export function hasAccessToken() {
  return Boolean(accessToken)
}

export const api = axios.create({
  baseURL: '/api/v1',
  timeout: 90_000,
  withCredentials: true,
})

api.interceptors.request.use((config) => {
  if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as (AxiosRequestConfig & { _retried?: boolean }) | undefined
    if (
      error.response?.status === 401 &&
      original &&
      !original._retried &&
      !String(original.url).includes('/auth/')
    ) {
      original._retried = true
      refreshPromise ??= api
        .post<ApiEnvelope<{ access_token: string }>>('/auth/refresh')
        .then(({ data }) => {
          setAccessToken(data.data.access_token)
          return data.data.access_token
        })
        .finally(() => {
          refreshPromise = null
        })
      const token = await refreshPromise
      original.headers = { ...original.headers, Authorization: `Bearer ${token}` }
      return api.request(original)
    }
    return Promise.reject(error)
  },
)

export async function getData<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  const { data } = await api.get<ApiEnvelope<T>>(url, config)
  return data.data
}

export async function postData<T>(
  url: string,
  body?: unknown,
  config?: AxiosRequestConfig,
): Promise<T> {
  const { data } = await api.post<ApiEnvelope<T>>(url, body, config)
  return data.data
}

export async function putData<T>(url: string, body?: unknown): Promise<T> {
  const { data } = await api.put<ApiEnvelope<T>>(url, body)
  return data.data
}

export async function patchData<T>(url: string, body?: unknown): Promise<T> {
  const { data } = await api.patch<ApiEnvelope<T>>(url, body)
  return data.data
}

export async function deleteData<T>(url: string, body?: unknown): Promise<T> {
  const { data } = await api.delete<ApiEnvelope<T>>(url, { data: body })
  return data.data
}

export function websocketUrl(path: string) {
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${location.host}${path}`
}

// 过渡兼容：会话详情页在全部替换完成前仍使用这些具名函数。
export type SessionResult = import('@/types/domain').LearningSession
export async function createSession(input: {
  track_code: string
  goal: string
  topic?: string
}): Promise<SessionResult> {
  return postData<SessionResult>('/sessions', input)
}
export async function getSession(sessionId: string): Promise<SessionResult> {
  return getData<SessionResult>(`/sessions/${sessionId}`)
}
export async function getReport(): Promise<any> {
  return getData('/reports/latest')
}
export async function searchKnowledge(q: string, trackCode?: string): Promise<any[]> {
  return (await getData<{ items: any[] }>('/knowledge/search', { params: { q, track_code: trackCode } })).items
}
export async function sessionInteract(
  sessionId: string,
  interaction: { feedback_type?: string; [key: string]: any },
): Promise<any> {
  return postData(`/sessions/${sessionId}/feedback`, {
    feedback_type: interaction.feedback_type || 'question',
    content: interaction,
  })
}
export function createWsConnection(sessionId: string): WebSocket {
  return new WebSocket(websocketUrl(`/api/v1/sessions/ws/${sessionId}`))
}
