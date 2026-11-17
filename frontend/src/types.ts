export type Mode = 'random' | 'selected-nodes' | 'all-nodes'
export type TaskStatus = 'pending' | 'running' | 'finished' | 'error' | 'cancelled' | 'abnormal'
export type JsonValue = string | number | boolean | null | JsonValue[] | { [key: string]: JsonValue }
export interface Project {
  _id: string
  name: string
  description: string
  spiders: number
}
export interface RunConfig {
  cmd: string
  param: string
  mode: Mode
  node_ids: string[]
  priority: number
}
export interface Spider extends Omit<RunConfig, 'node_ids'> {
  node_ids: string[] | null
  _id: string
  name: string
  description: string
  project_id: string
  col_id: string
  col_name?: string
}
export interface TaskStat {
  create_ts: string
  start_ts: string
  end_ts: string
  runtime_duration: number
  wait_duration: number
  total_duration: number
  result_count: number
  error_log_count: number
}
export interface Task extends Omit<RunConfig, 'node_ids'> {
  node_ids: string[] | null
  _id: string
  spider_id: string
  status: TaskStatus
  node_id: string
  error: string
  schedule_id: string
  stat?: TaskStat
  spider?: Spider
}
export interface Schedule extends Omit<RunConfig, 'node_ids'> {
  node_ids: string[] | null
  _id: string
  name: string
  description: string
  spider_id: string
  cron: string
  enabled: boolean
}
export interface Node {
  _id: string
  name: string
  hostname: string
  ip: string
  is_master: boolean
  status: string
  enabled: boolean
  active: boolean
  active_ts: string
  available_runners: number
  max_runners: number
}
export interface Log {
  id: number
  msg: string
  ts: string
}
export interface Overview {
  projects: number
  spiders: number
  tasks: number
  running: number
  failed: number
  schedules: number
  nodes: number
  online_nodes: number
  recent_tasks: Task[]
}
export interface User {
  _id: string
  username: string
  role: string
  email: string
}
export interface ListResponse<T> {
  data: T[]
  total: number
}
export type PageName = 'overview' | 'spiders' | 'runs' | 'schedules' | 'nodes' | 'help'
export const statusLabels: Record<TaskStatus, string> = {
  pending: '等待执行',
  running: '运行中',
  finished: '已完成',
  error: '执行失败',
  cancelled: '已取消',
  abnormal: '异常终止',
}
export const modeLabels: Record<Mode, string> = {
  random: '随机节点',
  'selected-nodes': '指定节点',
  'all-nodes': '所有节点',
}
export const formatDate = (value?: string) =>
  !value || value.startsWith('0001-') ? '—' : new Date(value).toLocaleString('zh-CN', { hour12: false })
export const formatDuration = (value?: number) =>
  value === undefined ? '—' : value < 1000 ? `${value} ms` : `${(value / 1000).toFixed(1)} s`
