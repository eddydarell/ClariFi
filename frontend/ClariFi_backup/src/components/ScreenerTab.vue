<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12" md="4">
        <v-card class="mb-4" elevation="2">
          <v-card-title class="text-primary">
            <v-icon start color="primary">mdi-filter-variant</v-icon>
            Market Screener
          </v-card-title>
          <v-card-text>
            <v-select
              v-model="category"
              :items="categories"
              label="Category"
              variant="outlined"
              prepend-inner-icon="mdi-shape"
            ></v-select>
            
            <v-slider
              v-model="limit"
              label="Limit Results"
              min="5"
              max="50"
              step="5"
              thumb-label
              color="primary"
            ></v-slider>
            
            <v-btn
              block
              color="primary"
              size="large"
              @click="screenMarket"
              :loading="loading"
              elevation="4"
            >
              <v-icon start>mdi-magnify</v-icon>
              Screen Market
            </v-btn>
          </v-card-text>
        </v-card>
        
        <!-- Insights Card -->
        <v-card v-if="results.length > 0" class="mt-4" variant="outlined" color="info">
          <v-card-title class="text-subtitle-1">
            <v-icon start size="small">mdi-lightbulb-on</v-icon>
            Insights
          </v-card-title>
          <v-card-text class="text-body-2">
             <div v-if="category === 'gainers'">
               Consider these stocks for momentum trading. Check news for catalysts.
             </div>
             <div v-else-if="category === 'losers'">
               Potential value opportunities or falling knives. Research fundamentals.
             </div>
             <div v-else-if="category === 'actives'">
               High volume indicates significant interest. Check for breakouts.
             </div>
             <div v-else>
               Recently public companies. Expect high volatility.
             </div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" md="8">
        <v-card elevation="2">
          <v-card-title class="d-flex align-center">
            Results
            <v-spacer></v-spacer>
            <v-chip v-if="results.length" color="primary" variant="outlined">
              {{ results.length }} Found
            </v-chip>
          </v-card-title>
          
          <v-data-table
            :headers="headers"
            :items="results"
            :loading="loading"
            hover
          >
            <template v-slot:item.symbol="{ item }">
              <span class="font-weight-bold text-primary">{{ item.raw.symbol }}</span>
            </template>
            
            <template v-slot:item.regularMarketPrice="{ item }">
              ${{ formatNumber(item.raw.regularMarketPrice) }}
            </template>
            
            <template v-slot:item.regularMarketChange="{ item }">
              <span :class="getColor(item.raw.regularMarketChange)">
                {{ formatChange(item.raw.regularMarketChange) }}
              </span>
            </template>
            
            <template v-slot:item.regularMarketChangePercent="{ item }">
              <v-chip :color="getColor(item.raw.regularMarketChangePercent)" size="small" variant="tonal">
                {{ formatPercent(item.raw.regularMarketChangePercent) }}
              </v-chip>
            </template>
            
            <template v-slot:item.regularMarketVolume="{ item }">
              {{ formatVolume(item.raw.regularMarketVolume) }}
            </template>
          </v-data-table>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import { ref, computed } from 'vue'

export default {
  name: 'ScreenerTab',
  props: {
    loading: Boolean
  },
  emits: ['screen-market'],
  setup(props, { emit }) {
    const category = ref('gainers')
    const limit = ref(20)
    const results = ref([])
    
    const categories = [
      { title: 'Top Gainers', value: 'gainers' },
      { title: 'Top Losers', value: 'losers' },
      { title: 'Most Active', value: 'actives' },
      { title: 'New Listings', value: 'new' }
    ]
    
    const headers = computed(() => {
      if (category.value === 'new') {
        return [
          { title: 'Symbol', key: 'symbol', align: 'start' },
          { title: 'Name', key: 'shortName', align: 'start' },
          { title: 'Price', key: 'regularMarketPrice', align: 'end' },
          { title: 'Volume', key: 'regularMarketVolume', align: 'end' },
          { title: 'Listing Date', key: 'listingDate', align: 'end' },
        ]
      }
      return [
        { title: 'Symbol', key: 'symbol', align: 'start' },
        { title: 'Name', key: 'shortName', align: 'start' },
        { title: 'Price', key: 'regularMarketPrice', align: 'end' },
        { title: 'Change', key: 'regularMarketChange', align: 'end' },
        { title: '% Change', key: 'regularMarketChangePercent', align: 'end' },
        { title: 'Volume', key: 'regularMarketVolume', align: 'end' },
      ]
    })

    const screenMarket = async () => {
      try {
        // We emit the event but also handle the API call here if passed as prop, 
        // or we can just make the call here if we inject the API client.
        // For consistency with App.vue pattern, we'll emit.
        // But wait, App.vue handles logic. Let's assume App.vue passes a function or we emit.
        // Actually, to keep components clean, let's emit and let parent handle data fetching
        // BUT, for the results to show up here, we need to receive them back.
        // Better pattern: Parent passes 'results' prop? Or this component handles its own data?
        // Given App.vue structure, it seems to handle data.
        // However, Screener data is specific to this tab.
        // Let's make this component handle its own API call for simplicity if possible, 
        // OR emit and wait for update.
        // Let's emit and expect the parent to return the data via a promise or update a prop.
        // Let's use a direct fetch here for simplicity as it's a self-contained feature.
        
        // Actually, let's stick to the pattern: Emit event, parent calls API, parent updates prop?
        // No, that's complex. Let's just fetch here.
        
        const response = await fetch('/api/screener', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ category: category.value, limit: limit.value })
        })
        const data = await response.json()
        if (data.success) {
            results.value = data.data
        }
      } catch (e) {
        console.error(e)
      }
    }

    // Formatters
    const formatNumber = (num) => num ? num.toFixed(2) : '0.00'
    const formatChange = (num) => num ? (num > 0 ? '+' : '') + num.toFixed(2) : '0.00'
    const formatPercent = (num) => num ? (num > 0 ? '+' : '') + num.toFixed(2) + '%' : '0.00%'
    const formatVolume = (num) => {
        if (!num) return '0'
        if (num >= 1e6) return (num / 1e6).toFixed(1) + 'M'
        if (num >= 1e3) return (num / 1e3).toFixed(1) + 'K'
        return num.toString()
    }
    
    const getColor = (val) => {
        if (!val) return ''
        return val > 0 ? 'text-success' : (val < 0 ? 'text-error' : '')
    }

    return {
      category,
      limit,
      categories,
      results,
      headers,
      screenMarket,
      formatNumber,
      formatChange,
      formatPercent,
      formatVolume,
      getColor
    }
  }
}
</script>
