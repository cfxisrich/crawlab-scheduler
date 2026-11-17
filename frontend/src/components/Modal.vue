<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import Icon from './Icon.vue'
defineProps<{ title: string; wide?: boolean }>()
const emit = defineEmits<{ close: [] }>()
const panel = ref<HTMLDialogElement>()
const previousFocus = document.activeElement
onMounted(() => panel.value!.showModal())
onUnmounted(() => {
  if (previousFocus instanceof HTMLElement) previousFocus.focus()
})
</script>

<template>
  <Teleport to="body">
    <dialog
      ref="panel"
      class="modal"
      :class="{ wide }"
      aria-labelledby="dialog-title"
      @cancel.prevent="emit('close')"
    >
      <header class="modal-header">
        <div>
          <span class="eyebrow">FLOWHARBOR WORKSPACE</span>
          <h2 id="dialog-title">{{ title }}</h2>
        </div>
        <button class="icon-button" aria-label="关闭对话框" @click="emit('close')">
          <Icon name="close" />
        </button>
      </header>
      <div class="modal-body"><slot /></div>
    </dialog>
  </Teleport>
</template>
