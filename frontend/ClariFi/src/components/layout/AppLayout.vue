<script setup lang="ts">
import NavBar from './NavBar.vue';
</script>

<template>
    <div class="min-h-screen bg-background flex flex-col">
        <NavBar />
        <main class="flex-1 container mx-auto py-6 px-4">
            <slot></slot>
        </main>
    </div>
</template>
