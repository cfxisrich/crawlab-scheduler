<script setup lang="ts">
import type { Node, RunConfig } from '../types'
defineProps<{ nodes: Node[] }>()
const config = defineModel<RunConfig>({ required: true })
</script>
<template>
  <label>
    运行命令
    <input v-model="config.cmd" required placeholder="python main.py" />
    <span class="form-hint">在任务代码目录执行。所需依赖须预先安装到 Worker 镜像。</span>
  </label>
  <label>
    命令参数
    <input v-model="config.param" placeholder="例如：--limit 10" />
  </label>
  <div class="form-row">
    <label>
      执行方式
      <select v-model="config.mode">
        <option value="random">随机节点</option>
        <option value="selected-nodes">指定节点</option>
        <option value="all-nodes">所有节点</option>
      </select>
    </label>
    <label>
      优先级
      <input v-model.number="config.priority" type="number" step="1" min="-100" max="100" required />
      <span class="form-hint">数值越高，调度优先级越高。</span>
    </label>
  </div>
  <label v-if="config.mode === 'selected-nodes'">
    选择节点
    <select v-model="config.node_ids" multiple required size="4">
      <option v-for="node in nodes" :key="node._id" :value="node._id">
        {{ node.name || node.hostname }} · {{ node.active ? '在线' : '离线' }}
      </option>
    </select>
    <span class="form-hint">可按住 Ctrl / Command 选择多个节点。</span>
  </label>
</template>
