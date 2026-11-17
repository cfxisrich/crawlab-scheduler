<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { all, useFeedback } from '../api'
import type { Node } from '../types'
import { formatDate } from '../types'
import Icon from '../components/Icon.vue'
import EmptyState from '../components/EmptyState.vue'
const nodes = ref<Node[]>([])
const loaded = ref(false)
const { pending, error, run } = useFeedback()
const refresh = () =>
  run(async () => {
    nodes.value = await all<Node>('/nodes')
    loaded.value = true
  })
onMounted(refresh)
</script>
<template>
  <div class="page-heading">
    <div>
      <div class="page-kicker">DISTRIBUTED WORKERS</div>
      <h1>执行节点</h1>
      <p>查看节点连接状态与可用执行容量。</p>
    </div>
    <button class="button" :disabled="pending" @click="refresh">
      <Icon name="refresh" :size="15" />
      刷新节点
    </button>
  </div>
  <div v-if="error" class="error-banner" role="alert">{{ error }}</div>
  <div v-if="pending && !loaded" class="loading">
    <span class="spinner"></span>
    正在获取节点…
  </div>
  <div class="node-grid">
    <section v-for="node in nodes" :key="node._id" class="panel node-card" style="margin-top: 0">
      <div style="display: flex; align-items: center; justify-content: space-between">
        <span class="row-icon"><Icon name="nodes" :size="20" /></span>
        <span class="badge" :class="node.active ? 'online' : 'offline'">
          <span class="dot"></span>
          {{ node.active ? '在线' : '离线' }}
        </span>
      </div>
      <h3>{{ node.name || node.hostname }}</h3>
      <div class="cell-sub">{{ node.is_master ? 'MASTER · 主节点' : 'WORKER · 执行节点' }}</div>
      <div class="node-meta">
        <div>
          <span>主机名</span>
          <strong>{{ node.hostname }}</strong>
        </div>
        <div>
          <span>IP 地址</span>
          <code>{{ node.ip }}</code>
        </div>
        <div>
          <span>执行槽位</span>
          <strong>{{ node.available_runners }} 可用 / {{ node.max_runners }} 总计</strong>
        </div>
        <div>
          <span>任务分配</span>
          <strong>{{ node.enabled ? '已启用' : '已禁用' }}</strong>
        </div>
        <div>
          <span>最近活跃</span>
          <strong>{{ formatDate(node.active_ts) }}</strong>
        </div>
      </div>
    </section>
  </div>
  <section v-if="loaded && !nodes.length" class="panel">
    <EmptyState
      icon="nodes"
      title="尚未连接执行节点"
      description="启动 Docker Compose 中的 Master 与 Worker 服务，然后刷新查看节点。"
    />
  </section>
  <p class="selection-note">节点信息来自 Crawlab。节点配置与运行环境通过部署文件管理。</p>
</template>
