<script setup lang="ts">
defineProps<{ name: string; size?: number }>()
const paths: Record<string, string> = {
  overview: 'M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z',
  spiders: 'M3 7h7l2-3h9v16H3z M7 12h10 M7 16h6',
  runs: 'M8 3H4v18h16V3h-4 M8 2h8v4H8z M8 11h8 M8 15h5',
  schedules: 'M8 2v4 M16 2v4 M3 10h18 M3 4h18v17H3z M8 14h2 M14 14h2 M8 18h2',
  nodes: 'M8 3h8v5H8z M2 16h8v5H2z M14 16h8v5h-8z M12 8v4 M6 16v-4h12v4',
  help: 'M9 9a3 3 0 116 0c0 2-3 2-3 4 M12 17h.01 M22 12a10 10 0 11-20 0 10 10 0 0120 0',
  arrow: 'M5 12h14 M13 6l6 6-6 6',
  plus: 'M12 5v14 M5 12h14',
  refresh: 'M20 7v5h-5 M4 17v-5h5 M6 7a7 7 0 0112-2l2 3 M4 16l2 3a7 7 0 0012-2',
  play: 'M7 4l14 8-14 8z',
  pause: 'M8 5v14 M16 5v14',
  close: 'M6 6l12 12 M18 6L6 18',
  check: 'M5 12l4 4L19 6',
  search: 'M21 21l-5-5 M18 10a8 8 0 11-16 0 8 8 0 0116 0',
  logout: 'M9 4H4v16h5 M10 12h11 M17 8l4 4-4 4',
  upload: 'M12 16V3 M7 8l5-5 5 5 M4 14v7h16v-7',
  download: 'M12 3v13 M7 11l5 5 5-5 M4 16v5h16v-5',
  edit: 'M14 5l5 5 M4 20l5-1L21 7l-5-5L4 14z',
  trash: 'M3 6h18 M9 6V3h6v3 M5 6l1 15h12l1-15 M10 10v7 M14 10v7',
  time: 'M12 7v5l3 2 M22 12a10 10 0 11-20 0 10 10 0 0120 0',
  menu: 'M4 6h16 M4 12h16 M4 18h16',
  lock: 'M7 10V7a5 5 0 0110 0v3 M5 10h14v11H5z M12 14v3',
  bolt: 'M13 2L4 14h7l-1 8 10-13h-8z',
}
</script>

<template>
  <svg
    :width="size ?? 20"
    :height="size ?? 20"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.7"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <path :d="paths[name]" />
  </svg>
</template>
