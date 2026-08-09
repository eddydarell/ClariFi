<script setup lang="ts">
import { useThemeStore } from './stores/theme'
import AppLayout from './components/layout/AppLayout.vue'

useThemeStore()
</script>

<template>
  <AppLayout>
    <RouterView />
  </AppLayout>
</template>
