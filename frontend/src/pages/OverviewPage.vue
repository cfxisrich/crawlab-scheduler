<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { get, useFeedback } from '../api'
import type { Overview, PageName } from '../types'
import { formatDate, formatDuration, statusLabels } from '../types'
import Icon from '../components/Icon.vue'
import EmptyState from '../components/EmptyState.vue'
defineEmits<{ navigate: [page: PageName] }>()
const overview = ref<Overview>()
const { error, pending, run } = useFeedback()
const counts = computed(() => {
  const recent = overview.value?.recent_tasks ?? []
  return [
    recent.filter((task) => task.status === 'finished').length,
    recent.filter((task) => task.status === 'running' || task.status === 'pending').length,
    recent.filter((task) => task.status === 'error' || task.status === 'abnormal').length,
    recent.filter((task) => task.status === 'cancelled').length,
  ]
})
const refresh = () =>
  run(async () => {
    overview.value = await get<Overview>('/overview')
  })
onMounted(refresh)
</script>
<template>
  <div class="page-heading">
    <div>
      <div class="page-kicker">WORKSPACE OVERVIEW</div>
      <h1>工作台概览</h1>
      <p>每一次采集，都有迹可循。</p>
    </div>
    <div class="page-actions">
      <button class="button" :disabled="pending" @click="refresh">
        <Icon name="refresh" :size="15" />
        刷新
      </button>
      <button class="button primary" @click="$emit('navigate', 'spiders')">
        <Icon name="plus" :size="16" />
        管理任务
      </button>
    </div>
  </div>
  <div v-if="error" class="error-banner" role="alert">{{ error }}</div>
  <div v-if="pending && !overview" class="loading">
    <span class="spinner"></span>
    正在加载工作空间…
  </div>
  <template v-if="overview">
    <div class="stats">
      <div class="stat">
        <div class="stat-label">
          累计执行
          <span class="stat-icon"><Icon name="runs" :size="17" /></span>
        </div>
        <div class="stat-value">{{ overview.tasks.toLocaleString() }}</div>
        <div class="stat-note">
          来自
          <strong>{{ overview.spiders }}</strong>
          个采集任务
        </div>
      </div>
      <div class="stat">
        <div class="stat-label">
          正在运行
          <span class="stat-icon"><Icon name="bolt" :size="17" /></span>
        </div>
        <div class="stat-value">{{ overview.running }}</div>
        <div class="stat-note">当前执行中的任务实例</div>
      </div>
      <div class="stat">
        <div class="stat-label">
          异常执行
          <span class="stat-icon"><Icon name="runs" :size="17" /></span>
        </div>
        <div class="stat-value">{{ overview.failed }}</div>
        <div class="stat-note">失败与异常终止记录</div>
      </div>
      <div class="stat">
        <div class="stat-label">
          在线节点
          <span class="stat-icon"><Icon name="nodes" :size="17" /></span>
        </div>
        <div class="stat-value">
          {{ overview.online_nodes }}
          <span style="font-size: 17px; color: #a0adab; font-weight: 400">/ {{ overview.nodes }}</span>
        </div>
        <div class="stat-note">已连接的调度执行节点</div>
      </div>
    </div>
    <div class="overview-grid">
      <section class="panel">
        <div class="panel-header">
          <div>
            <h3>最近执行分布</h3>
            <p>基于最近 {{ overview.recent_tasks.length }} 条执行记录</p>
          </div>
          <span class="badge">实时查询</span>
        </div>
        <div class="panel-body">
          <div class="status-strip">
            <div v-for="(label, index) in ['执行完成', '运行 / 等待', '失败 / 异常', '已取消']" :key="label">
              <strong>{{ counts[index] }}</strong>
              <span>{{ label }}</span>
            </div>
          </div>
          <div class="status-bar" aria-label="最近执行状态分布">
            <span v-for="(count, index) in counts" :key="index" :style="{ flex: count }"></span>
          </div>
          <div
            style="
              display: flex;
              justify-content: space-between;
              margin-top: 23px;
              font-size: 11px;
              color: #86958d;
            "
          >
            <span>{{ overview.projects }} 个项目 · {{ overview.schedules }} 个定时计划</span>
            <button class="text-button" @click="$emit('navigate', 'runs')">
              查看执行记录
              <Icon name="arrow" :size="13" />
            </button>
          </div>
        </div>
      </section>
      <section class="panel flow-card" style="margin-top: 0">
        <div class="panel-body">
          <div class="eyebrow">A CLEAR WORKFLOW</div>
          <h3>从任务到结果</h3>
          <div class="flow-steps">
            <div class="flow-step">
              <span>01</span>
              <div>
                <h4>组织采集任务</h4>
                <p>上传脚本，设置运行参数</p>
              </div>
            </div>
            <div class="flow-step">
              <span>02</span>
              <div>
                <h4>安排执行时间</h4>
                <p>手动启动，或交给定时计划</p>
              </div>
            </div>
            <div class="flow-step">
              <span>03</span>
              <div>
                <h4>追踪每次执行</h4>
                <p>查看日志与采集结果</p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
    <section class="panel">
      <div class="panel-header">
        <div>
          <h3>最近执行</h3>
          <p>工作空间中最新的执行动态</p>
        </div>
        <button class="text-button" @click="$emit('navigate', 'runs')">
          全部记录
          <Icon name="arrow" :size="14" />
        </button>
      </div>
      <div v-if="overview.recent_tasks.length" class="table-scroll">
        <table>
          <thead>
            <tr>
              <th>任务</th>
              <th>执行状态</th>
              <th>创建时间</th>
              <th>耗时</th>
              <th>结果数</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="task in overview.recent_tasks" :key="task._id">
              <td>
                <div class="line">
                  <span class="row-icon"><Icon name="spiders" :size="16" /></span>
                  <div>
                    <div class="cell-title">{{ task.spider?.name || task.spider_id }}</div>
                    <div class="cell-sub mono">{{ task._id.slice(-12) }}</div>
                  </div>
                </div>
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
            </tr>
          </tbody>
        </table>
      </div>
      <EmptyState
        v-else
        title="还没有执行记录"
        description="创建第一个采集任务，然后手动运行一次。执行状态将在这里展示。"
      >
        <button class="button small primary" @click="$emit('navigate', 'spiders')">
          创建任务
          <Icon name="arrow" :size="14" />
        </button>
      </EmptyState>
    </section>
  </template>
</template>
