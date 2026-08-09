<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router';
import { useThemeStore } from '../../stores/theme'

const route = useRoute()
const themeStore = useThemeStore()

const items = ref([
    { label: 'Screener', icon: 'pi pi-filter', to: '/screener' },
    { label: 'Live Monitor', icon: 'pi pi-chart-line', to: '/monitor' },
    { label: 'Strategy', icon: 'pi pi-compass', to: '/strategy' }
])
</script>

<template>
    <nav class="bg-surface border-b border-border px-4 md:px-6 py-4 flex flex-wrap gap-3 items-center justify-between">
        <div class="flex items-center gap-3">
            <i class="pi pi-chart-bar text-primary text-2xl"></i>
            <router-link to="/screener" class="text-xl font-bold tracking-tight text-on-surface">ClariFi</router-link>
        </div>

        <div class="order-3 md:order-none w-full md:w-auto flex items-center justify-center gap-1 bg-surface-overlay p-1 rounded-lg">
            <router-link
                v-for="item in items"
                :key="item.to"
                :to="item.to"
                class="px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 flex items-center gap-2"
                :class="route.path === item.to ? 'bg-primary/10 text-primary' : 'text-on-surface-muted hover:text-on-surface hover:bg-surface-hover'"
            >
                <i :class="item.icon" aria-hidden="true"></i>
                {{ item.label }}
            </router-link>
        </div>

        <div class="flex items-center gap-4">
            <div class="text-xs text-on-surface-faint">
                <span class="w-2 h-2 rounded-full bg-success inline-block mr-1"></span>
                System Online
            </div>
            <button
                @click="themeStore.toggle()"
                class="p-2 rounded-lg hover:bg-surface-hover transition-colors text-on-surface-muted hover:text-on-surface"
                :aria-label="themeStore.resolved === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'"
            >
                <i :class="themeStore.resolved === 'dark' ? 'pi pi-sun' : 'pi pi-moon'" class="text-lg"></i>
            </button>
        </div>
    </nav>
</template>
