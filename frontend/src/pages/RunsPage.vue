<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { all, get, list, useFeedback, write } from '../api'
import type { JsonValue, Log, Spider, Task, TaskStatus } from '../types'
import { formatDate, formatDuration, statusLabels } from '../types'
import Icon from '../components/Icon.vue'
import Modal from '../components/Modal.vue'
import EmptyState from '../components/EmptyState.vue'
import Pagination from '../components/Pagination.vue'
const emit = defineEmits<{ notify: [message: string] }>()
const tasks = ref<Task[]>([])
const spiders = ref<Spider[]>([])
const page = ref(1)
const total = ref(0)
const loaded = ref(false)
const status = ref<TaskStatus | ''>('')
const spiderId = ref('')
const detail = ref<Task | null>(null)
const tab = ref<'logs' | 'results'>('logs')
const logs = ref<Log[]>([])
const results = ref<Record<string, JsonValue>[]>([])
const detailTotal = ref(0)
const detailPage = ref(1)
const confirmingCancel = ref(false)
const { pending, error, run } = useFeedback()
const action = useFeedback()
const fetchTasks = async () => {
  const params = new URLSearchParams({ page: String(page.value), size: '20' })
  if (status.value) params.set('status', status.value)
  if (spiderId.value) params.set('spider_id', spiderId.value)
  const response = await list<Task>('/tasks?' + params)
  tasks.value = response.data
  total.value = response.total
  loaded.value = true
}
const refresh = () => run(fetchTasks)
const changePage = (value: number) => {
  page.value = value
  void refresh()
}
const filter = () => changePage(1)
async function loadDetail() {
  detail.value = await get<Task>('/tasks/' + detail.value!._id)
  if (tab.value === 'logs') {
    const response = await list<Log>(
      '/tasks/' + detail.value._id + '/logs?page=' + detailPage.value + '&size=100',
    )
    logs.value = response.data
    detailTotal.value = response.total
    return
  }
  const response = await list<Record<string, JsonValue>>(
    '/tasks/' + detail.value._id + '/results?page=' + detailPage.value + '&size=20',
  )
  results.value = response.data
  detailTotal.value = response.total
}
async function openDetail(task: Task) {
  detail.value = task
  tab.value = 'logs'
  detailPage.value = 1
  logs.value = []
  results.value = []
  detailTotal.value = 0
  confirmingCancel.value = false
  await action.run(loadDetail)
}
function switchTab(value: 'logs' | 'results') {
  tab.value = value
  detailPage.value = 1
  detailTotal.value = 0
  void action.run(loadDetail)
}
function detailChangePage(value: number) {
  detailPage.value = value
  void action.run(loadDetail)
}
async function execute(operation: 'cancel' | 'restart') {
  await action.run(async () => {
    await write('/tasks/' + detail.value!._id + '/' + operation, 'POST')
    confirmingCancel.value = false
    emit('notify', operation === 'cancel' ? '已提交取消请求，请刷新查看状态' : '已提交重新执行请求')
    await loadDetail()
    await refresh()
  })
}
function downloadResults() {
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(results.value, null, 2)], { type: 'application/json;charset=utf-8' }),
  )
  const link = document.createElement('a')
  link.href = url
  link.download = detail.value!._id + '-page-' + detailPage.value + '.json'
  link.click()
  URL.revokeObjectURL(url)
}
onMounted(() =>
  run(async () => {
    await fetchTasks()
    spiders.value = await all<Spider>('/spiders')
  }),
)
</script>
<template>
  <div class="page-heading">
    <div>
      <div class="page-kicker">EXECUTION HISTORY</div>
      <h1>执行记录</h1>
      <p>从启动到完成，追踪每一次执行。</p>
    </div>
    <button class="button" :disabled="pending" @click="refresh">
      <Icon name="refresh" :size="15" />
      刷新记录
    </button>
  </div>
  <div v-if="error" class="error-banner" role="alert">{{ error }}</div>
  <div class="toolbar">
    <div class="toolbar-filters">
      <select v-model="status" aria-label="按状态筛选" @change="filter">
        <option value="">全部状态</option>
        <option v-for="(label, value) in statusLabels" :key="value" :value="value">
          {{ label }}
        </option>
      </select>
      <select v-model="spiderId" aria-label="按任务筛选" @change="filter">
        <option value="">全部采集任务</option>
        <option v-for="spider in spiders" :key="spider._id" :value="spider._id">{{ spider.name }}</option>
      </select>
    </div>
    <span class="count-label">共 {{ total }} 条执行记录</span>
  </div>
  <section class="panel">
    <div v-if="pending && !loaded" class="loading">
      <span class="spinner"></span>
      正在加载执行记录…
    </div>
    <div v-if="tasks.length" class="table-scroll">
      <table>
        <thead>
          <tr>
            <th>采集任务 / 执行 ID</th>
            <th>执行状态</th>
            <th>创建时间</th>
            <th>运行耗时</th>
            <th>采集结果</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="task in tasks" :key="task._id">
            <td>
              <div class="cell-title">{{ task.spider?.name || task.spider_id }}</div>
              <div class="cell-sub mono">{{ task._id }}</div>
            </td>
            <td>
              <span class="badge" :class="task.status">
                <span class="dot"></span>
                {{ statusLabels[task.status] }}
              </span>
            </td>
            <td class="muted">{{ formatDate(task.stat?.create_ts) }}</td>
            <td class="mono">{{ formatDuration(task.stat?.runtime_duration) }}</td>
            <td>{{ task.stat?.result_count ?? '—' }}</td>
            <td>
              <button class="text-button" @click="openDetail(task)">
                查看详情
                <Icon name="arrow" :size="13" />
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <EmptyState
      v-if="loaded && !tasks.length"
      icon="runs"
      title="没有匹配的执行记录"
      description="启动一个采集任务，或调整上方筛选条件。"
    />
    <Pagination :page="page" :total="total" :size="20" :disabled="pending" @change="changePage" />
  </section>
  <Modal v-if="detail" title="执行详情" wide @close="detail = null">
    <div v-if="action.error.value" class="error-banner" role="alert">{{ action.error.value }}</div>
    <div
      style="
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 15px;
        margin-bottom: 20px;
      "
    >
      <div>
        <h3>{{ detail.spider?.name || detail.spider_id }}</h3>
        <div class="cell-sub mono">{{ detail._id }}</div>
      </div>
      <span class="badge" :class="detail.status">{{ statusLabels[detail.status] }}</span>
    </div>
    <dl class="detail-grid">
      <div>
        <dt>创建时间</dt>
        <dd>{{ formatDate(detail.stat?.create_ts) }}</dd>
      </div>
      <div>
        <dt>启动时间</dt>
        <dd>{{ formatDate(detail.stat?.start_ts) }}</dd>
      </div>
      <div>
        <dt>完成时间</dt>
        <dd>{{ formatDate(detail.stat?.end_ts) }}</dd>
      </div>
      <div>
        <dt>运行耗时</dt>
        <dd>{{ formatDuration(detail.stat?.runtime_duration) }}</dd>
      </div>
      <div>
        <dt>执行节点</dt>
        <dd class="mono">{{ detail.node_id }}</dd>
      </div>
      <div>
        <dt>运行命令</dt>
        <dd class="mono">{{ detail.cmd }} {{ detail.param }}</dd>
      </div>
    </dl>
    <div v-if="detail.error" class="error-banner">失败原因：{{ detail.error }}</div>
    <div class="tabs">
      <button :class="{ active: tab === 'logs' }" @click="switchTab('logs')">执行日志</button>
      <button :class="{ active: tab === 'results' }" @click="switchTab('results')">采集结果</button>
      <button style="margin-left: auto" :disabled="action.pending.value" @click="action.run(loadDetail)">
        <Icon name="refresh" :size="14" />
        刷新详情
      </button>
    </div>
    <template v-if="tab === 'logs'">
      <pre class="log-panel">{{
        logs.length
          ? logs.map((line) => '[' + line.ts + '] ' + line.msg).join('\n')
          : action.pending.value
            ? '正在读取日志…'
            : '暂无日志。任务开始执行后，脚本输出会显示在这里。'
      }}</pre>
      <Pagination
        :page="detailPage"
        :total="detailTotal"
        :size="100"
        :disabled="action.pending.value"
        @change="detailChangePage"
      />
    </template>
    <template v-if="tab === 'results'">
      <div v-if="results.length">
        <div style="text-align: right; margin-bottom: 10px">
          <button class="button small" @click="downloadResults">
            <Icon name="download" :size="14" />
            下载本页 JSON
          </button>
        </div>
        <pre class="log-panel">{{ JSON.stringify(results, null, 2) }}</pre>
      </div>
      <EmptyState v-else title="暂无采集结果" description="脚本通过 Crawlab SDK 保存的数据会显示在这里。" />
      <Pagination
        :page="detailPage"
        :total="detailTotal"
        :size="20"
        :disabled="action.pending.value"
        @change="detailChangePage"
      />
    </template>
    <div v-if="confirmingCancel" class="error-banner">
      <span>确认取消此次执行？</span>
      <button class="text-button danger" :disabled="action.pending.value" @click="execute('cancel')">
        确认取消
      </button>
      <button class="text-button" @click="confirmingCancel = false">继续运行</button>
    </div>
    <div class="form-actions">
      <button
        v-if="detail.status === 'running' || detail.status === 'pending'"
        class="button danger"
        :disabled="action.pending.value"
        @click="confirmingCancel = true"
      >
        取消执行
      </button>
      <button v-else class="button primary" :disabled="action.pending.value" @click="execute('restart')">
        <Icon name="play" :size="13" />
        重新执行
      </button>
      <button class="button" @click="detail = null">关闭</button>
    </div>
  </Modal>
</template>
