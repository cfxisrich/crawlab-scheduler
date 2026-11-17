<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { all, get, list, useFeedback, write } from '../api'
import type { Node, PageName, Project, RunConfig, Spider } from '../types'
import { modeLabels } from '../types'
import Icon from '../components/Icon.vue'
import Modal from '../components/Modal.vue'
import EmptyState from '../components/EmptyState.vue'
import Pagination from '../components/Pagination.vue'
import RunFields from '../components/RunFields.vue'
const emit = defineEmits<{ notify: [message: string]; navigate: [page: PageName] }>()
const projects = ref<Project[]>([])
const nodes = ref<Node[]>([])
const spiders = ref<Spider[]>([])
const total = ref(0)
const page = ref(1)
const keyword = ref('')
const projectId = ref('')
const loaded = ref(false)
const dialog = ref<'spider' | 'project' | 'run' | 'code' | 'delete' | null>(null)
const editingId = ref('')
const selectedName = ref('')
const deleteType = ref<'spiders' | 'projects'>('spiders')
const spiderForm = ref({ name: '', description: '', project_id: '', col_name: '' })
const projectForm = ref({ name: '', description: '' })
const runConfig = ref<RunConfig>({
  cmd: 'python main.py',
  param: '',
  mode: 'random',
  node_ids: [],
  priority: 0,
})
const filePath = ref('main.py')
const fileContent = ref('')
const fileNames = ref<{ name: string; path: string; is_dir: boolean }[]>([])
const { pending, error, run } = useFeedback()
const action = useFeedback()
const fetchSpiders = async () => {
  const params = new URLSearchParams({ page: String(page.value), size: '20', keyword: keyword.value })
  if (projectId.value) params.set('project_id', projectId.value)
  const result = await list<Spider>('/spiders?' + params)
  spiders.value = result.data
  total.value = result.total
  loaded.value = true
}
const refresh = () =>
  run(async () => {
    await fetchSpiders()
    projects.value = await all<Project>('/projects')
    nodes.value = await all<Node>('/nodes')
  })
const filter = (id = projectId.value) => {
  projectId.value = id
  page.value = 1
  void run(fetchSpiders)
}
const changePage = (value: number) => {
  page.value = value
  void run(fetchSpiders)
}
function openSpider(spider?: Spider) {
  action.error.value = ''
  editingId.value = spider?._id ?? ''
  spiderForm.value = {
    name: spider?.name ?? '',
    description: spider?.description ?? '',
    project_id: spider?.project_id ?? (projectId.value || '000000000000000000000000'),
    col_name: spider?.col_name ?? '',
  }
  runConfig.value = {
    cmd: spider?.cmd ?? 'python main.py',
    param: spider?.param ?? '',
    mode: spider?.mode ?? 'random',
    node_ids: [...(spider?.node_ids ?? [])],
    priority: spider?.priority ?? 0,
  }
  dialog.value = 'spider'
}
function openProject(project?: Project) {
  action.error.value = ''
  editingId.value = project?._id ?? ''
  projectForm.value = { name: project?.name ?? '', description: project?.description ?? '' }
  dialog.value = 'project'
}
function openRun(spider: Spider) {
  action.error.value = ''
  editingId.value = spider._id
  selectedName.value = spider.name
  runConfig.value = {
    cmd: spider.cmd,
    param: spider.param,
    mode: spider.mode,
    node_ids: [...(spider.node_ids ?? [])],
    priority: spider.priority,
  }
  dialog.value = 'run'
}
async function saveSpider() {
  await action.run(async () => {
    await write(
      editingId.value ? '/spiders/' + editingId.value : '/spiders',
      editingId.value ? 'PUT' : 'POST',
      { ...spiderForm.value, ...runConfig.value },
    )
    dialog.value = null
    emit('notify', '任务配置已保存')
    await refresh()
  })
}
async function saveProject() {
  await action.run(async () => {
    await write(
      editingId.value ? '/projects/' + editingId.value : '/projects',
      editingId.value ? 'PUT' : 'POST',
      projectForm.value,
    )
    dialog.value = null
    emit('notify', '项目已保存')
    await refresh()
  })
}
async function runSpider() {
  await action.run(async () => {
    const ids = await write<string[]>('/spiders/' + editingId.value + '/run', 'POST', runConfig.value)
    dialog.value = null
    emit('notify', '已提交 ' + ids.length + ' 个执行实例')
    emit('navigate', 'runs')
  })
}
async function openCode(spider: Spider) {
  action.error.value = ''
  editingId.value = spider._id
  selectedName.value = spider.name
  filePath.value = 'main.py'
  fileContent.value = ''
  fileNames.value = []
  dialog.value = 'code'
  await action.run(async () => {
    fileNames.value = await get<typeof fileNames.value>('/spiders/' + editingId.value + '/files?path=/')
  })
}
async function readLocal(event: Event) {
  const files = (event.target as HTMLInputElement).files!
  if (!files.length) return
  await action.run(async () => {
    if (files[0].size > 1024 * 1024) throw new Error('单个脚本文件不能超过 1 MiB。')
    filePath.value = files[0].name
    fileContent.value = await files[0].text()
  })
}
async function loadCode(path: string) {
  await action.run(async () => {
    filePath.value = path.replace(/^\//, '')
    fileContent.value = await get<string>(
      '/spiders/' + editingId.value + '/file?' + new URLSearchParams({ path: filePath.value }),
    )
  })
}
async function saveCode() {
  await action.run(async () => {
    await write('/spiders/' + editingId.value + '/files', 'POST', {
      path: filePath.value,
      content: fileContent.value,
    })
    dialog.value = null
    emit('notify', '脚本已保存到任务代码目录')
  })
}
function askDelete(type: 'spiders' | 'projects', id: string, name: string) {
  deleteType.value = type
  editingId.value = id
  selectedName.value = name
  action.error.value = ''
  dialog.value = 'delete'
}
async function remove() {
  await action.run(async () => {
    await write('/' + deleteType.value + '/' + editingId.value, 'DELETE')
    if (deleteType.value === 'projects' && projectId.value === editingId.value) projectId.value = ''
    dialog.value = null
    emit('notify', '已删除')
    page.value = 1
    await refresh()
  })
}
onMounted(refresh)
</script>
<template>
  <div class="page-heading">
    <div>
      <div class="page-kicker">PROJECTS & SPIDERS</div>
      <h1>项目与任务</h1>
      <p>让每个采集脚本，都有自己的工作空间。</p>
    </div>
    <div class="page-actions">
      <button class="button" @click="openProject()">
        <Icon name="plus" :size="15" />
        新建项目
      </button>
      <button class="button primary" @click="openSpider()">
        <Icon name="plus" :size="16" />
        新建任务
      </button>
    </div>
  </div>
  <div v-if="error" class="error-banner" role="alert">{{ error }}</div>
  <div class="project-chips">
    <button class="project-chip" :class="{ active: !projectId }" @click="filter('')">全部项目</button>
    <div
      v-for="project in projects"
      :key="project._id"
      class="project-chip"
      :class="{ active: projectId === project._id }"
    >
      <button @click="filter(project._id)">{{ project.name }}</button>
      <button class="chip-edit" :aria-label="'编辑项目 ' + project.name" @click="openProject(project)">
        <Icon name="edit" :size="12" />
      </button>
    </div>
  </div>
  <form class="toolbar" @submit.prevent="filter()">
    <div class="toolbar-filters">
      <div class="search-input">
        <Icon name="search" />
        <input v-model="keyword" placeholder="搜索任务名称…" aria-label="搜索任务名称" />
      </div>
      <button class="button" :disabled="pending">搜索</button>
    </div>
    <button class="button" type="button" :disabled="pending" @click="refresh">
      <Icon name="refresh" :size="14" />
      刷新
    </button>
  </form>
  <section class="panel">
    <div class="panel-header">
      <h3>采集任务</h3>
      <span class="count-label">{{ total }} 个任务</span>
    </div>
    <div v-if="pending && !loaded" class="loading">
      <span class="spinner"></span>
      正在加载任务…
    </div>
    <div v-if="spiders.length" class="table-scroll">
      <table>
        <thead>
          <tr>
            <th>任务名称</th>
            <th>运行命令</th>
            <th>执行方式</th>
            <th>优先级</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="spider in spiders" :key="spider._id">
            <td>
              <div class="line">
                <span class="row-icon"><Icon name="spiders" :size="16" /></span>
                <div>
                  <div class="cell-title">{{ spider.name }}</div>
                  <div class="cell-sub">{{ spider.description || '未填写描述' }}</div>
                </div>
              </div>
            </td>
            <td>
              <code>{{ spider.cmd }}</code>
              <div class="cell-sub mono">{{ spider.param }}</div>
            </td>
            <td>
              <span class="badge">{{ modeLabels[spider.mode] }}</span>
            </td>
            <td class="mono">{{ spider.priority }}</td>
            <td>
              <div class="line">
                <button class="text-button" @click="openRun(spider)">
                  <Icon name="play" :size="12" />
                  运行
                </button>
                <button class="text-button" @click="openCode(spider)">代码</button>
                <button
                  class="icon-button"
                  :aria-label="'编辑任务 ' + spider.name"
                  @click="openSpider(spider)"
                >
                  <Icon name="edit" :size="14" />
                </button>
                <button
                  class="icon-button"
                  :aria-label="'删除任务 ' + spider.name"
                  @click="askDelete('spiders', spider._id, spider.name)"
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
      v-if="loaded && !spiders.length"
      title="这里还没有采集任务"
      description="新建一个任务，上传 Python 脚本，再设置它的运行方式。搜索时可尝试清空筛选条件。"
    >
      <button class="button small primary" @click="openSpider()">新建任务</button>
    </EmptyState>
    <Pagination :page="page" :total="total" :size="20" :disabled="pending" @change="changePage" />
  </section>
  <Modal
    v-if="dialog === 'spider'"
    :title="editingId ? '编辑采集任务' : '新建采集任务'"
    @close="dialog = null"
  >
    <form class="form-grid" @submit.prevent="saveSpider">
      <div v-if="action.error.value" class="error-banner" role="alert">{{ action.error.value }}</div>
      <label>
        任务名称
        <input v-model="spiderForm.name" required maxlength="120" placeholder="例如：每日商品采集" />
      </label>
      <label>
        所属项目
        <select v-model="spiderForm.project_id">
          <option value="000000000000000000000000">未分组</option>
          <option v-for="project in projects" :key="project._id" :value="project._id">
            {{ project.name }}
          </option>
        </select>
      </label>
      <label>
        描述
        <input v-model="spiderForm.description" maxlength="1000" placeholder="这个任务采集什么数据？" />
      </label>
      <RunFields v-model="runConfig" :nodes="nodes" />
      <label>
        结果集合名称
        <input
          v-model="spiderForm.col_name"
          :disabled="Boolean(editingId)"
          placeholder="留空由 Crawlab 自动分配"
        />
        <span class="form-hint">
          结果集合仅在创建时设置。脚本需调用 Crawlab SDK 保存数据，才会显示在执行结果中。
        </span>
      </label>
      <div class="form-actions">
        <button class="button" type="button" @click="dialog = null">取消</button>
        <button class="button primary" :disabled="action.pending.value">保存任务</button>
      </div>
    </form>
  </Modal>
  <Modal v-if="dialog === 'project'" :title="editingId ? '编辑项目' : '新建项目'" @close="dialog = null">
    <form class="form-grid" @submit.prevent="saveProject">
      <div v-if="action.error.value" class="error-banner" role="alert">{{ action.error.value }}</div>
      <label>
        项目名称
        <input v-model="projectForm.name" required maxlength="120" placeholder="例如：电商数据采集" />
      </label>
      <label>
        项目描述
        <textarea v-model="projectForm.description" maxlength="1000"></textarea>
      </label>
      <div class="form-actions">
        <button
          v-if="editingId"
          type="button"
          class="button danger"
          style="margin-right: auto"
          @click="askDelete('projects', editingId, projectForm.name)"
        >
          删除项目
        </button>
        <button class="button" type="button" @click="dialog = null">取消</button>
        <button class="button primary" :disabled="action.pending.value">保存项目</button>
      </div>
    </form>
  </Modal>
  <Modal v-if="dialog === 'run'" title="运行采集任务" @close="dialog = null">
    <form class="form-grid" @submit.prevent="runSpider">
      <p class="schedule-summary">即将运行：{{ selectedName }}。本次调整仅应用于此次执行。</p>
      <div v-if="action.error.value" class="error-banner" role="alert">{{ action.error.value }}</div>
      <RunFields v-model="runConfig" :nodes="nodes" />
      <div class="form-actions">
        <button class="button" type="button" @click="dialog = null">取消</button>
        <button class="button primary" :disabled="action.pending.value">
          <Icon name="play" :size="14" />
          开始运行
        </button>
      </div>
    </form>
  </Modal>
  <Modal v-if="dialog === 'code'" :title="selectedName + ' · 任务代码'" wide @close="dialog = null">
    <form class="form-grid" @submit.prevent="saveCode">
      <div v-if="action.error.value" class="error-banner" role="alert">{{ action.error.value }}</div>
      <div v-if="fileNames.length" class="project-chips">
        <button
          v-for="file in fileNames.filter((item) => !item.is_dir)"
          :key="file.path"
          class="project-chip"
          type="button"
          @click="loadCode(file.path)"
        >
          {{ file.name }}
        </button>
      </div>
      <label>
        选择本地脚本
        <input type="file" accept=".py,.txt,.json,.csv,.yaml,.yml" @change="readLocal" />
        <span class="form-hint">UTF-8 文本文件，单个文件最多 1 MiB。可分次上传脚本和配置文件。</span>
      </label>
      <label>
        任务内文件路径
        <input v-model="filePath" required placeholder="main.py" />
        <span class="form-hint">相同路径会覆盖原文件。可输入相对路径，例如 config/settings.json。</span>
      </label>
      <label>
        文件内容
        <textarea
          v-model="fileContent"
          class="mono"
          rows="16"
          spellcheck="false"
          placeholder="选择本地文件或直接编辑代码"
        ></textarea>
      </label>
      <div class="form-actions">
        <button type="button" class="button" @click="loadCode(filePath)" :disabled="action.pending.value">
          读取此路径
        </button>
        <button type="button" class="button" @click="dialog = null">取消</button>
        <button class="button primary" :disabled="action.pending.value">保存文件</button>
      </div>
    </form>
  </Modal>
  <Modal v-if="dialog === 'delete'" title="确认删除" @close="dialog = null">
    <div class="form-grid">
      <div v-if="action.error.value" class="error-banner" role="alert">{{ action.error.value }}</div>
      <p style="font-size: 13px">
        确认删除{{ deleteType === 'projects' ? '项目' : '任务' }}「{{ selectedName }}」？此操作无法撤销。
      </p>
      <div class="form-actions">
        <button class="button" @click="dialog = null">保留</button>
        <button class="button danger" :disabled="action.pending.value" @click="remove">确认删除</button>
      </div>
    </div>
  </Modal>
</template>
