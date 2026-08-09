<script setup lang="ts">
import { ref } from 'vue'
import { useMarketStore } from '@/stores/market'
import Card from 'primevue/card'
import Button from 'primevue/button'
import Chip from 'primevue/chip'
import InputChips from 'primevue/inputchips'

const marketStore = useMarketStore()
const tickersInput = ref<string[]>([])

async function startMonitoring() {
  if (tickersInput.value.length === 0 || marketStore.monitorState === 'connecting') return
  await marketStore.startMonitoring(tickersInput.value)
}

async function stopMonitoring() {
  await marketStore.stopMonitoring()
  tickersInput.value = []
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold text-on-surface">Live Monitor</h1>
        <p class="text-on-surface-muted mt-1">Real-time stock price monitoring</p>
      </div>
      <div class="flex items-center gap-2">
        <span
          class="flex items-center gap-2 text-xs px-3 py-1.5 rounded-full"
          :class="marketStore.isMonitoring ? 'bg-success/20 text-success' : 'bg-surface-overlay text-on-surface-muted'"
        >
          <span class="w-2 h-2 rounded-full" :class="marketStore.isMonitoring ? 'bg-success animate-pulse' : 'bg-on-surface-faint'"></span>
               {{ marketStore.monitorState === 'connecting' ? 'Connecting' : marketStore.monitorState === 'reconnecting' ? 'Reconnecting' : marketStore.isMonitoring ? 'Monitoring Active' : 'Inactive' }}
        </span>
      </div>
    </div>

    <Card>
      <template #content>
        <div class="space-y-4">
          <div>
            <label for="monitor-tickers" class="block text-sm font-medium text-on-surface mb-2">
              Enter Tickers (press Enter after each)
            </label>
            <InputChips
              v-model="tickersInput"
              placeholder="e.g., AAPL, MSFT, GOOGL"
              class="w-full"
              :disabled="marketStore.isMonitoring"
              inputId="monitor-tickers"
            />
          </div>
          <p v-if="marketStore.monitorError" role="alert" class="text-sm text-error">{{ marketStore.monitorError }}</p>
          <div class="flex gap-3">
            <Button
              v-if="!marketStore.isMonitoring"
              label="Start Monitoring"
              icon="pi pi-play"
              @click="startMonitoring"
              :disabled="tickersInput.length === 0"
              severity="success"
            />
            <Button
              v-else
              label="Stop Monitoring"
              icon="pi pi-stop"
              @click="stopMonitoring"
              severity="danger"
            />
          </div>
        </div>
      </template>
    </Card>

    <div v-if="marketStore.monitoredStocks.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <Card
        v-for="stock in marketStore.monitoredStocks"
        :key="stock.ticker"
        class="hover:border-primary/50 transition-all"
      >
        <template #content>
          <div class="space-y-3">
            <div class="flex items-center justify-between">
              <h3 class="text-xl font-bold text-primary">{{ stock.ticker }}</h3>
              <Chip
                 :label="(stock.change_percent ?? 0) >= 0 ? '↑' : '↓'"
                 :class="(stock.change_percent ?? 0) >= 0 ? 'bg-success/20 text-success' : 'bg-error/20 text-error'"
              />
            </div>

            <div class="space-y-2">
              <div class="flex justify-between items-baseline">
                <span class="text-sm text-on-surface-muted">Price</span>
                <span class="text-2xl font-bold text-on-surface">${{ stock.price?.toFixed(2) }}</span>
              </div>

              <div class="flex justify-between items-baseline">
                <span class="text-sm text-on-surface-muted">Change</span>
                <span
                  class="text-lg font-semibold"
                   :class="(stock.change ?? 0) >= 0 ? 'text-success' : 'text-error'"
                >
                   {{ (stock.change ?? 0) >= 0 ? '+' : '' }}${{ stock.change == null ? 'N/A' : stock.change.toFixed(2) }}
                </span>
              </div>

              <div class="flex justify-between items-baseline">
                <span class="text-sm text-on-surface-muted">% Change</span>
                <span
                  class="text-lg font-semibold"
                   :class="(stock.change_percent ?? 0) >= 0 ? 'text-success' : 'text-error'"
                >
                   {{ (stock.change_percent ?? 0) >= 0 ? '+' : '' }}{{ stock.change_percent == null ? 'N/A' : stock.change_percent.toFixed(2) }}%
                </span>
              </div>
            </div>
          </div>
        </template>
      </Card>
    </div>

     <Card v-else-if="marketStore.isMonitoring">
      <template #content>
        <div class="text-center py-12 text-on-surface-muted">
          <i class="pi pi-spin pi-spinner text-4xl mb-4"></i>
           <p>{{ marketStore.monitorState === 'reconnecting' ? 'Reconnecting to market updates...' : 'Waiting for price updates...' }}</p>
        </div>
      </template>
    </Card>
  </div>
</template>
