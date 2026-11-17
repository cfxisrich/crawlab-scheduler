<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import Icon from './components/Icon.vue'
import OverviewPage from './pages/OverviewPage.vue'
import SpidersPage from './pages/SpidersPage.vue'
import RunsPage from './pages/RunsPage.vue'
import SchedulesPage from './pages/SchedulesPage.vue'
import NodesPage from './pages/NodesPage.vue'
import HelpPage from './pages/HelpPage.vue'
import { ApiError, get, useFeedback, write } from './api'
import type { PageName, User } from './types'

const user = ref<User | null>(null)
const checking = ref(true)
const username = ref('')
const password = ref('')
const mobileOpen = ref(false)
const toast = ref('')
const { error, pending, run } = useFeedback()
const nav = [
  { key: 'overview', label: '工作台概览', subtitle: '总览采集任务与执行状态' },
  { key: 'spiders', label: '项目与任务', subtitle: '组织采集项目，配置每一次执行' },
  { key: 'runs', label: '执行记录', subtitle: '追踪运行状态、日志与采集结果' },
  { key: 'schedules', label: '定时计划', subtitle: '让重复的工作按时发生' },
  { key: 'nodes', label: '执行节点', subtitle: '查看分布式执行节点的连接状态' },
  { key: 'help', label: '使用指南', subtitle: '从第一个任务，到稳定运行' },
] as const
const initialPage = window.location.hash.slice(1)
const page = ref<PageName>(
  nav.some((item) => item.key === initialPage) ? (initialPage as PageName) : 'overview',
)
const current = computed(() => nav.find((item) => item.key === page.value)!)
const components = {
  overview: OverviewPage,
  spiders: SpidersPage,
  runs: RunsPage,
  schedules: SchedulesPage,
  nodes: NodesPage,
  help: HelpPage,
}
const toastTimer = ref<ReturnType<typeof setTimeout>>()
function navigate(value: PageName) {
  page.value = value
  window.location.hash = value
  mobileOpen.value = false
}
function syncHash() {
  const value = window.location.hash.slice(1)
  if (nav.some((item) => item.key === value)) page.value = value as PageName
}
function notify(message: string) {
  toast.value = message
  clearTimeout(toastTimer.value)
  toastTimer.value = setTimeout(() => {
    toast.value = ''
  }, 4500)
}
function sessionExpired() {
  user.value = null
  error.value = '登录状态已失效，请重新登录。'
}
async function login() {
  await run(async () => {
    await write('/login', 'POST', { username: username.value, password: password.value })
    user.value = await get<User>('/session')
    password.value = ''
  })
}
async function logout() {
  await run(async () => {
    await write('/logout', 'POST')
    user.value = null
  })
}
onMounted(async () => {
  window.addEventListener('session-expired', sessionExpired)
  window.addEventListener('hashchange', syncHash)
  try {
    user.value = await get<User>('/session')
  } catch (failure) {
    if (!(failure instanceof ApiError && failure.status === 401))
      error.value = failure instanceof Error ? failure.message : '服务暂不可用'
  } finally {
    checking.value = false
  }
})
onUnmounted(() => {
  clearTimeout(toastTimer.value)
  window.removeEventListener('session-expired', sessionExpired)
  window.removeEventListener('hashchange', syncHash)
})
</script>

<template>
  <div v-if="checking" class="loading">
    <span class="spinner"></span>
    正在连接工作台…
  </div>
  <div v-else-if="!user" class="login-page">
    <section class="login-art">
      <div class="brand">
        <div class="brand-mark">
          <i></i>
          <i></i>
          <i></i>
        </div>
        <div>
          <div class="brand-name">FlowHarbor</div>
          <div class="brand-sub">流 港 调 度</div>
        </div>
      </div>
      <div class="hero-text">
        <div class="eyebrow">YOUR DATA, IN MOTION.</div>
        <h1>
          让采集有序发生，
          <br />
          让数据
          <em>如期抵达。</em>
        </h1>
        <p>
          为你的采集工作搭建一个可靠的港口。
          <br />
          统一任务、调度与执行，一切尽在掌握。
        </p>
        <div class="architecture-visual" aria-hidden="true">
          <div class="arch-box">
            <Icon name="schedules" :size="24" />
            任务计划
            <small>Schedule</small>
          </div>
          <div class="arch-connector"></div>
          <div class="arch-box">
            <Icon name="bolt" :size="24" />
            调度中心
            <small>Master</small>
          </div>
          <div class="arch-connector"></div>
          <div class="arch-workers">
            <div class="arch-box">Worker 01</div>
            <div class="arch-box">Worker 02</div>
          </div>
        </div>
      </div>
      <div class="login-art-footer">
        <span>PRIVATE DEPLOYMENT · POWERED BY CRAWLAB</span>
        <span>v0.1</span>
      </div>
    </section>
    <section class="login-form-side">
      <div class="login-form">
        <div class="page-kicker">WELCOME TO YOUR WORKSPACE</div>
        <h2>登录工作台</h2>
        <p>使用你的 Crawlab 账户，继续今天的工作。</p>
        <div v-if="error" role="alert" class="error-banner">{{ error }}</div>
        <form @submit.prevent="login">
          <label>
            用户名
            <input v-model="username" autocomplete="username" required placeholder="输入用户名" />
          </label>
          <label>
            密码
            <input
              v-model="password"
              type="password"
              autocomplete="current-password"
              required
              placeholder="输入密码"
            />
          </label>
          <button class="button primary" :disabled="pending" type="submit">
            <span v-if="pending" class="spinner"></span>
            {{ pending ? '正在连接…' : '进入工作台' }}
            <Icon name="arrow" :size="17" />
          </button>
        </form>
        <div class="login-note">
          <Icon name="lock" :size="14" />
          <span>连接你的私有调度服务。首次使用请先按照部署手册初始化 Crawlab，并设置管理员密码。</span>
        </div>
      </div>
    </section>
  </div>
  <div v-else class="app-layout">
    <aside class="sidebar" :class="{ open: mobileOpen }">
      <div class="brand">
        <div class="brand-mark">
          <i></i>
          <i></i>
          <i></i>
        </div>
        <div>
          <div class="brand-name">FlowHarbor</div>
          <div class="brand-sub">流 港 调 度</div>
        </div>
      </div>
      <div class="workspace-label">
        <span class="dot"></span>
        私有调度工作空间
        <Icon name="lock" :size="13" />
      </div>
      <div class="nav-label">WORKSPACE / 工作空间</div>
      <nav aria-label="主导航">
        <button
          v-for="item in nav.slice(0, 5)"
          :key="item.key"
          class="nav-item"
          :class="{ active: page === item.key }"
          :aria-current="page === item.key ? 'page' : undefined"
          @click="navigate(item.key)"
        >
          <Icon :name="item.key" :size="18" />
          {{ item.label }}
        </button>
      </nav>
      <div class="nav-label" style="margin-top: 30px">RESOURCES / 资源</div>
      <nav>
        <button class="nav-item" :class="{ active: page === 'help' }" @click="navigate('help')">
          <Icon name="help" :size="18" />
          使用指南
        </button>
      </nav>
      <div class="sidebar-bottom">
        <div class="engine-card">
          <div class="line">
            <Icon name="nodes" :size="15" />
            <span>Crawlab 调度引擎</span>
          </div>
          <p>
            任务各就其位
            <br />
            数据如期抵达
          </p>
        </div>
        <div class="sidebar-user">
          <span class="avatar">{{ user.username.slice(0, 1).toUpperCase() }}</span>
          <div>
            {{ user.username }}
            <small>{{ user.role || '工作空间账户' }}</small>
          </div>
          <button class="icon-button" aria-label="退出登录" :disabled="pending" @click="logout">
            <Icon name="logout" :size="17" />
          </button>
        </div>
      </div>
    </aside>
    <main class="main">
      <header class="topbar">
        <div class="line">
          <button class="icon-button mobile-menu" aria-label="切换菜单" @click="mobileOpen = !mobileOpen">
            <Icon name="menu" />
          </button>
          <div class="breadcrumb">
            <span>工作空间</span>
            <span>/</span>
            <strong>{{ current.label }}</strong>
          </div>
        </div>
        <div class="topbar-right">
          <span class="line">
            <Icon name="lock" :size="13" />
            私有部署
          </span>
          <span class="version-tag">v0.1.0</span>
        </div>
      </header>
      <div class="page">
        <div v-if="error" class="error-banner" role="alert">
          {{ error }}
          <button aria-label="关闭提示" @click="error = ''"><Icon name="close" :size="15" /></button>
        </div>
        <component :is="components[page]" @navigate="navigate" @notify="notify" />
        <footer class="footer">
          <span>
            <strong>FlowHarbor</strong>
            · 流港调度
          </span>
          <span>基于 Crawlab · 为有序的数据工作而构建</span>
        </footer>
      </div>
    </main>
    <div v-if="toast" role="status" class="toast">
      <Icon name="check" :size="17" />
      {{ toast }}
    </div>
  </div>
</template>
