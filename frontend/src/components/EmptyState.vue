<script setup lang="ts">
import Icon from './Icon.vue'
defineProps<{ title: string; description: string; icon?: string }>()
</script>
<template>
  <div class="empty-state">
    <div class="empty-icon"><Icon :name="icon ?? 'spiders'" :size="28" /></div>
    <h3>{{ title }}</h3>
    <p>{{ description }}</p>
    <slot />
  </div>
</template>
