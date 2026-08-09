<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  status: string
  type?: 'recommendation' | 'risk' | 'confidence'
}>()

const colorClass = computed(() => {
  const status = props.status?.toLowerCase() || ''
  
  if (props.type === 'recommendation') {
    if (status.includes('buy')) return 'bg-success/20 text-success border-success/30'
    if (status.includes('sell')) return 'bg-error/20 text-error border-error/30'
    if (status.includes('hold')) return 'bg-warning/20 text-warning border-warning/30'
  }
  
  if (props.type === 'risk') {
    if (status.includes('low')) return 'bg-success/20 text-success border-success/30'
    if (status.includes('medium')) return 'bg-warning/20 text-warning border-warning/30'
    if (status.includes('high')) return 'bg-error/20 text-error border-error/30'
  }
  
  if (props.type === 'confidence') {
    if (status.includes('high')) return 'bg-success/20 text-success border-success/30'
    if (status.includes('medium')) return 'bg-warning/20 text-warning border-warning/30'
    if (status.includes('low')) return 'bg-error/20 text-error border-error/30'
  }
  
  return 'bg-secondary/20 text-secondary border-secondary/30'
})
</script>

<template>
  <span 
    class="inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-medium border"
    :class="colorClass"
  >
    {{ status }}
  </span>
</template>
