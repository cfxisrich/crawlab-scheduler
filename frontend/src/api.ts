import { ref } from 'vue'
import type { ListResponse } from './types'

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message)
  }
}

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, {
    ...init,
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json', 'X-FlowHarbor-Request': '1', ...init?.headers },
  })
  if (!response.ok) {
    if (!response.headers.get('content-type')?.includes('application/json'))
      throw new ApiError(
        '服务暂不可用（HTTP ' + response.status + '），请检查接入服务是否已启动。',
        response.status,
      )
    const body = (await response.json()) as { detail: string | { loc: (string | number)[]; msg: string }[] }
    const message =
      typeof body.detail === 'string'
        ? body.detail
        : body.detail.map((item) => `${item.loc.join('.')}: ${item.msg}`).join('；')
    if (response.status === 401 && path !== '/login' && path !== '/session')
      window.dispatchEvent(new Event('session-expired'))
    throw new ApiError(message, response.status)
  }
  return response.json() as Promise<T>
}

export const get = <T>(path: string) => request<{ data: T }>(path).then((body) => body.data)
export const list = <T>(path: string) => request<ListResponse<T>>(path)
export const write = <T = null>(path: string, method: 'POST' | 'PUT' | 'DELETE', body?: object) =>
  request<{ data: T }>(path, { method, body: body === undefined ? undefined : JSON.stringify(body) }).then(
    (result) => result.data,
  )

export async function all<T>(path: string): Promise<T[]> {
  const first = await list<T>(`${path}?page=1&size=100`)
  const remaining = await Promise.all(
    Array.from({ length: Math.ceil(first.total / 100) - 1 }, (_, index) =>
      list<T>(`${path}?page=${index + 2}&size=100`),
    ),
  )
  return first.data.concat(...remaining.map((page) => page.data))
}

export function useFeedback() {
  const pending = ref(false)
  const error = ref('')
  const run = async (action: () => Promise<void>) => {
    pending.value = true
    error.value = ''
    try {
      await action()
      return true
    } catch (failure) {
      error.value = failure instanceof Error ? failure.message : '请求未完成'
      return false
    } finally {
      pending.value = false
    }
  }
  return { pending, error, run }
}
