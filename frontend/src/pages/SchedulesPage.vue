<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { all, list, useFeedback, write } from '../api'
import type { Node, RunConfig, Schedule, Spider } from '../types'
import { modeLabels } from '../types'
import Icon from '../components/Icon.vue'
import Modal from '../components/Modal.vue'
import EmptyState from '../components/EmptyState.vue'
import Pagination from '../components/Pagination.vue'
import RunFields from '../components/RunFields.vue'
const emit = defineEmits<{ notify: [message: string] }>()
const schedules = ref<Schedule[]>([])
const spiders = ref<Spider[]>([])
const nodes = ref<Node[]>([])
const page = ref(1)
const total = ref(0)
const keyword = ref('')
const loaded = ref(false)
const dialog = ref<'edit' | 'delete' | null>(null)
const editingId = ref('')
const form = ref({ name: '', description: '', spider_id: '', cron: '*/5 * * * *', enabled: false })
const config = ref<RunConfig>({ cmd: 'python main.py', param: '', mode: 'random', node_ids: [], priority: 0 })
const { pending, error, run } = useFeedback()
const action = useFeedback()
const fetchSchedules = async () => {
  const response = await list<Schedule>(
    '/schedules?' + new URLSearchParams({ page: String(page.value), size: '20', keyword: keyword.value }),
  )
  schedules.value = response.data
  total.value = response.total
  loaded.value = true
}
const refresh = () =>
  run(async () => {
    await fetchSchedules()
    spiders.value = await all<Spider>('/spiders')
    nodes.value = await all<Node>('/nodes')
  })
function changePage(value: number) {
  page.value = value
  void run(fetchSchedules)
}
function useSpider() {
  const spider = spiders.value.find((item) => item._id === form.value.spider_id)!
  config.value = {
    cmd: spider.cmd,
    param: spider.param,
    mode: spider.mode,
    node_ids: [...(spider.node_ids ?? [])],
    priority: spider.priority,
  }
}
function open(schedule?: Schedule) {
  editingId.value = schedule?._id ?? ''
  action.error.value = ''
  form.value = {
    name: schedule?.name ?? '',
    description: schedule?.description ?? '',
    spider_id: schedule?.spider_id ?? '',
    cron: schedule?.cron ?? '*/5 * * * *',
    enabled: schedule?.enabled ?? false,
  }
  config.value = {
    cmd: schedule?.cmd ?? 'python main.py',
    param: schedule?.param ?? '',
    mode: schedule?.mode ?? 'random',
    node_ids: [...(schedule?.node_ids ?? [])],
    priority: schedule?.priority ?? 0,
  }
  dialog.value = 'edit'
}
async function save() {
  await action.run(async () => {
    await write(
      editingId.value ? '/schedules/' + editingId.value : '/schedules',
      editingId.value ? 'PUT' : 'POST',
      { ...form.value, ...config.value },
    )
    dialog.value = null
    emit('notify', '定时计划已保存')
    await refresh()
  })
}
async function toggle(schedule: Schedule) {
  await run(async () => {
    await write('/schedules/' + schedule._id + (schedule.enabled ? '/disable' : '/enable'), 'POST')
    emit('notify', schedule.enabled ? '定时计划已停用' : '定时计划已启用')
    await fetchSchedules()
  })
}
function askDelete(schedule: Schedule) {
  editingId.value = schedule._id
  form.value.name = schedule.name
  action.error.value = ''
  dialog.value = 'delete'
}
async function remove() {
  await action.run(async () => {
    await write('/schedules/' + editingId.value, 'DELETE')
    dialog.value = null
    emit('notify', '定时计划已删除')
    page.value = 1
    await refresh()
  })
}
onMounted(refresh)
</script>
<template>
  <div class="page-heading">
    <div>
      <div class="page-kicker">SCHEDULED OPERATIONS</div>
      <h1>定时计划</h1>
      <p>设定节奏，让重复的采集工作自动发生。</p>
    </div>
    <button class="button primary" @click="open()">
      <Icon name="plus" :size="16" />
      新建计划
    </button>
  </div>
  <div v-if="error" class="error-banner" role="alert">{{ error }}</div>
  <form class="toolbar" @submit.prevent="changePage(1)">
    <div class="toolbar-filters">
      <div class="search-input">
        <Icon name="search" />
        <input v-model="keyword" placeholder="搜索计划名称…" aria-label="搜索计划名称" />
      </div>
      <button class="button" :disabled="pending">搜索</button>
    </div>
    <button type="button" class="button" :disabled="pending" @click="refresh">
      <Icon name="refresh" :size="15" />
      刷新
    </button>
  </form>
  <section class="panel">
    <div class="panel-header">
      <h3>调度计划</h3>
      <span class="count-label">{{ total }} 个计划</span>
    </div>
    <div v-if="pending && !loaded" class="loading">
      <span class="spinner"></span>
      正在加载计划…
    </div>
    <div v-if="schedules.length" class="table-scroll">
      <table>
        <thead>
          <tr>
            <th>计划名称</th>
            <th>采集任务</th>
            <th>CRON 表达式</th>
            <th>执行方式</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="schedule in schedules" :key="schedule._id">
            <td>
              <div class="cell-title">{{ schedule.name }}</div>
              <div class="cell-sub">{{ schedule.description || '未填写描述' }}</div>
            </td>
            <td>{{ spiders.find((item) => item._id === schedule.spider_id)?.name || schedule.spider_id }}</td>
            <td>
              <code>{{ schedule.cron }}</code>
            </td>
            <td>
              <span class="badge">{{ modeLabels[schedule.mode] }}</span>
            </td>
            <td>
              <span class="badge" :class="schedule.enabled ? 'enabled' : 'offline'">
                <span class="dot"></span>
                {{ schedule.enabled ? '已启用' : '已停用' }}
              </span>
            </td>
            <td>
              <div class="line">
                <button class="text-button" :disabled="pending" @click="toggle(schedule)">
                  <Icon :name="schedule.enabled ? 'pause' : 'play'" :size="12" />
                  {{ schedule.enabled ? '停用' : '启用' }}
                </button>
                <button class="icon-button" :aria-label="'编辑计划 ' + schedule.name" @click="open(schedule)">
                  <Icon name="edit" :size="14" />
                </button>
                <button
                  class="icon-button"
                  :aria-label="'删除计划 ' + schedule.name"
                  @click="askDelete(schedule)"
                >
                  <Icon name="trash" :size="14" />
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <EmptyState
      v-if="loaded && !schedules.length"
      icon="schedules"
      title="还没有定时计划"
      description="为已有采集任务设置 Cron 表达式，就能按时自动运行。"
    >
      <button class="button small primary" @click="open()">新建计划</button>
    </EmptyState>
    <Pagination :page="page" :total="total" :size="20" :disabled="pending" @change="changePage" />
  </section>
  <p class="selection-note">
    Cron 使用五位格式：分 · 时 · 日 · 月 · 周。调度时间以部署时配置的服务时区为准。
  </p>
  <Modal v-if="dialog === 'edit'" :title="editingId ? '编辑定时计划' : '新建定时计划'" @close="dialog = null">
    <form class="form-grid" @submit.prevent="save">
      <div v-if="action.error.value" class="error-banner" role="alert">{{ action.error.value }}</div>
      <label>
        计划名称
        <input v-model="form.name" required maxlength="120" placeholder="例如：每日 09:00 采集" />
      </label>
      <label>
        采集任务
        <select v-model="form.spider_id" required @change="useSpider">
          <option value="" disabled>选择一个任务</option>
          <option v-for="spider in spiders" :key="spider._id" :value="spider._id">{{ spider.name }}</option>
        </select>
      </label>
      <label>
        Cron 表达式
        <input v-model="form.cron" class="mono" required placeholder="*/5 * * * *" />
        <span class="form-hint">每 5 分钟：*/5 * * * *　每天 09:00：0 9 * * *</span>
      </label>
      <label>
        计划描述
        <input v-model="form.description" maxlength="1000" placeholder="可选描述" />
      </label>
      <RunFields v-model="config" :nodes="nodes" />
      <label class="check-label">
        <input v-model="form.enabled" type="checkbox" />
        保存后启用此计划
      </label>
      <div class="form-actions">
        <button class="button" type="button" @click="dialog = null">取消</button>
        <button class="button primary" :disabled="action.pending.value">保存计划</button>
      </div>
    </form>
  </Modal>
  <Modal v-if="dialog === 'delete'" title="删除定时计划" @close="dialog = null">
    <div class="form-grid">
      <div v-if="action.error.value" class="error-banner" role="alert">{{ action.error.value }}</div>
      <p style="font-size: 13px">确认删除「{{ form.name }}」？删除后该计划不再触发执行。</p>
      <div class="form-actions">
        <button class="button" @click="dialog = null">保留</button>
        <button class="button danger" :disabled="action.pending.value" @click="remove">确认删除</button>
      </div>
    </div>
  </Modal>
</template>
