<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useMarketStore } from '@/stores/market'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Select from 'primevue/select'
import Card from 'primevue/card'

const marketStore = useMarketStore()

const category = ref('gainers')
const limit = ref(10)

const categories = [
  { label: 'Top Gainers', value: 'gainers' },
  { label: 'Top Losers', value: 'losers' },
  { label: 'Most Active', value: 'actives' },
  { label: 'New Listings', value: 'new' }
]

const limits = [
  { label: '10', value: 10 },
  { label: '25', value: 25 },
  { label: '50', value: 50 }
]

async function runScreener() {
  await marketStore.fetchScreenerData(category.value, limit.value)
}

onMounted(() => {
  runScreener()
})

function formatNumber(value: number) {
  return Number.isFinite(value) ? value.toLocaleString() : 'N/A'
}

function formatPercent(value: number) {
  if (!Number.isFinite(value)) return 'N/A'
  return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold text-on-surface">Market Screener</h1>
        <p class="text-on-surface-muted mt-1">Discover top performing stocks</p>
      </div>
    </div>

    <Card>
      <template #content>
         <div class="flex flex-col md:flex-row gap-4 items-stretch md:items-end">
          <div class="flex-1">
            <label for="screener-category" class="block text-sm font-medium text-on-surface mb-2">Category</label>
            <Select
              v-model="category"
              :options="categories"
              optionLabel="label"
              optionValue="value"
              class="w-full"
              inputId="screener-category"
            />
          </div>
          <div class="w-32">
            <label for="screener-limit" class="block text-sm font-medium text-on-surface mb-2">Limit</label>
            <Select
              v-model="limit"
              :options="limits"
              optionLabel="label"
              optionValue="value"
              class="w-full"
              inputId="screener-limit"
            />
          </div>
          <Button
            label="Run Screener"
            icon="pi pi-search"
            @click="runScreener"
            :loading="marketStore.isLoading"
            severity="info"
          />
        </div>
      </template>
    </Card>

    <Card v-if="marketStore.error" class="bg-error/10 border border-error/30">
      <template #content>
        <div class="flex items-center gap-3 text-error">
          <i class="pi pi-exclamation-triangle text-xl"></i>
          <span>{{ marketStore.error }}</span>
        </div>
      </template>
    </Card>

    <Card>
      <template #content>
        <div v-if="!marketStore.isLoading && marketStore.screenerResults.length === 0" class="py-12 text-center text-on-surface-muted">
          No stocks matched this screen.
        </div>
        <DataTable
          :value="marketStore.screenerResults"
          :loading="marketStore.isLoading"
          stripedRows
          class="text-sm"
        >
          <Column field="ticker" header="Ticker" class="font-semibold text-primary"></Column>
          <Column field="price" header="Price">
            <template #body="{ data }">
              {{ data.price == null ? 'N/A' : `$${data.price.toFixed(2)}` }}
            </template>
          </Column>
          <Column field="change" header="Change">
            <template #body="{ data }">
              <span :class="data.change >= 0 ? 'text-success' : 'text-error'">
                {{ data.change == null ? 'N/A' : `${data.change >= 0 ? '+' : ''}$${data.change.toFixed(2)}` }}
              </span>
            </template>
          </Column>
          <Column field="change_percent" header="% Change">
            <template #body="{ data }">
              <span :class="data.change_percent >= 0 ? 'text-success' : 'text-error'">
                {{ formatPercent(data.change_percent) }}
              </span>
            </template>
          </Column>
          <Column field="volume" header="Volume">
            <template #body="{ data }">
              {{ formatNumber(data.volume) }}
            </template>
          </Column>
          <Column field="market_cap" header="Market Cap">
            <template #body="{ data }">
              {{ data.market_cap == null ? 'N/A' : formatNumber(data.market_cap) }}
            </template>
          </Column>
        </DataTable>
      </template>
    </Card>
  </div>
</template>
