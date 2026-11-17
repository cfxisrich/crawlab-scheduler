<script setup lang="ts">
defineProps<{ page: number; total: number; size: number; disabled?: boolean }>()
defineEmits<{ change: [page: number] }>()
</script>
<template>
  <div class="pagination">
    <span>共 {{ total }} 条 · 第 {{ page }} / {{ Math.max(1, Math.ceil(total / size)) }} 页</span>
    <div>
      <button class="button small" :disabled="disabled || page === 1" @click="$emit('change', page - 1)">
        上一页
      </button>
      <button
        class="button small"
        :disabled="disabled || page * size >= total"
        @click="$emit('change', page + 1)"
      >
        下一页
      </button>
    </div>
  </div>
</template>
