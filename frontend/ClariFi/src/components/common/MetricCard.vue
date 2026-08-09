<script setup lang="ts">
defineProps<{
  title: string
  value: string | number
  icon?: string
  trend?: 'up' | 'down' | 'neutral'
  subtitle?: string
}>()
</script>

<template>
  <div class="bg-surface border border-border rounded-lg p-4 hover:border-border-strong transition-colors">
    <div class="flex items-start justify-between">
      <div class="flex-1">
        <p class="text-xs text-on-surface-muted uppercase tracking-wide mb-1">{{ title }}</p>
        <p class="text-2xl font-bold text-on-surface">{{ value }}</p>
        <p v-if="subtitle" class="text-xs text-on-surface-muted mt-1">{{ subtitle }}</p>
      </div>
      <div v-if="icon" class="ml-3">
        <i :class="icon" class="text-primary text-xl"></i>
      </div>
    </div>
    <div v-if="trend" class="mt-2 flex items-center gap-1">
      <i
        :class="trend === 'up' ? 'pi pi-arrow-up text-success' : trend === 'down' ? 'pi pi-arrow-down text-error' : 'pi pi-minus text-secondary'"
        class="text-xs"
      ></i>
    </div>
  </div>
</template>
