<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12" md="4">
        <v-card class="mb-4" elevation="2">
          <v-card-title class="text-primary">
            <v-icon start color="primary">mdi-chess-knight</v-icon>
            Strategy Analyzer
          </v-card-title>
          <v-card-text>
            <v-text-field
              v-model="ticker"
              label="Ticker Symbol"
              variant="outlined"
              prepend-inner-icon="mdi-finance"
              @keyup.enter="generateStrategy"
              hint="e.g., AAPL, MSFT, TSLA"
              persistent-hint
            ></v-text-field>
            
            <v-select
              v-model="period"
              :items="periods"
              label="Analysis Period"
              variant="outlined"
              class="mt-2"
            ></v-select>
            
            <v-btn
              block
              color="primary"
              size="large"
              class="mt-4"
              @click="generateStrategy"
              :loading="loading"
              elevation="4"
            >
              <v-icon start>mdi-robot</v-icon>
              Generate Strategy
            </v-btn>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" md="8">
        <v-fade-transition>
          <v-card v-if="strategy" elevation="3" class="border-primary">
            <v-card-title class="d-flex justify-space-between align-center bg-surface-light pa-4">
              <div class="d-flex align-center">
                <span class="text-h5 font-weight-bold me-3">{{ strategy.ticker }}</span>
                <v-chip :color="getActionColor(strategy.action)" label class="font-weight-bold px-4">
                  {{ strategy.action }}
                </v-chip>
              </div>
              <div class="text-caption text-medium-emphasis">
                Target: {{ strategy.target_date }} ({{ strategy.timeframe }})
              </div>
            </v-card-title>
            
            <v-divider></v-divider>
            
            <v-card-text class="pa-4">
              <v-row>
                <v-col cols="12" sm="4">
                  <div class="text-subtitle-2 text-medium-emphasis">Confidence</div>
                  <div class="text-h6" :class="getConfidenceColor(strategy.confidence)">
                    {{ strategy.confidence }}
                  </div>
                </v-col>
                <v-col cols="12" sm="4">
                  <div class="text-subtitle-2 text-medium-emphasis">Risk Level</div>
                  <div class="text-h6" :class="getRiskColor(strategy.risk_level)">
                    {{ strategy.risk_level }}
                  </div>
                </v-col>
                <v-col cols="12" sm="4">
                  <div class="text-subtitle-2 text-medium-emphasis">Expected Return</div>
                  <div class="text-h6 text-success">
                    {{ formatPercent(strategy.expected_return_pct) }}
                  </div>
                </v-col>
              </v-row>
              
              <v-divider class="my-4"></v-divider>
              
              <div class="text-h6 mb-2">Rationale</div>
              <v-list density="compact" class="bg-transparent">
                <v-list-item v-for="(reason, i) in strategy.rationale" :key="i">
                  <template v-slot:prepend>
                    <v-icon color="primary" size="small">mdi-check-circle-outline</v-icon>
                  </template>
                  <v-list-item-title class="text-wrap">{{ reason }}</v-list-item-title>
                </v-list-item>
              </v-list>
              
              <v-divider class="my-4"></v-divider>
              
              <div class="text-h6 mb-2">Predictions</div>
              <v-row>
                <v-col v-for="(pred, key) in strategy.predictions" :key="key" cols="12" sm="4">
                  <v-card variant="outlined" class="pa-2 text-center">
                    <div class="text-caption text-uppercase">{{ key.replace('_', ' ') }}</div>
                    <div class="text-body-1 font-weight-bold" :class="pred.predicted_change_pct > 0 ? 'text-success' : 'text-error'">
                      {{ formatPercent(pred.predicted_change_pct) }}
                    </div>
                    <div class="text-caption text-medium-emphasis">{{ pred.target_date }}</div>
                  </v-card>
                </v-col>
              </v-row>
              
            </v-card-text>
          </v-card>
          
          <v-alert v-else-if="!loading && !strategy" type="info" variant="tonal" class="mt-4">
            Enter a ticker symbol to generate an AI-driven investment strategy.
          </v-alert>
        </v-fade-transition>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import { ref } from 'vue'

export default {
  name: 'StrategyTab',
  setup() {
    const ticker = ref('')
    const period = ref('1y')
    const loading = ref(false)
    const strategy = ref(null)
    
    const periods = ['1mo', '3mo', '6mo', '1y', '2y', '5y']

    const generateStrategy = async () => {
      if (!ticker.value) return
      
      loading.value = true
      strategy.value = null
      
      try {
        const response = await fetch('/api/strategy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                ticker: ticker.value.toUpperCase(), 
                period: period.value 
            })
        })
        const data = await response.json()
        if (data.success) {
            strategy.value = data.strategy
        } else {
            // Handle error (could emit or show snackbar if we had access)
            console.error(data.detail)
        }
      } catch (e) {
        console.error(e)
      } finally {
        loading.value = false
      }
    }

    // Helpers
    const getActionColor = (action) => {
        switch(action) {
            case 'BUY': return 'success'
            case 'SELL': return 'error'
            default: return 'warning'
        }
    }
    
    const getConfidenceColor = (conf) => {
        switch(conf) {
            case 'HIGH': return 'text-success'
            case 'LOW': return 'text-error'
            default: return 'text-warning'
        }
    }
    
    const getRiskColor = (risk) => {
        switch(risk) {
            case 'LOW': return 'text-success'
            case 'HIGH': return 'text-error'
            default: return 'text-warning'
        }
    }
    
    const formatPercent = (val) => val ? (val > 0 ? '+' : '') + val.toFixed(2) + '%' : '0.00%'

    return {
      ticker,
      period,
      periods,
      loading,
      strategy,
      generateStrategy,
      getActionColor,
      getConfidenceColor,
      getRiskColor,
      formatPercent
    }
  }
}
</script>

<style scoped>
.border-primary {
    border: 1px solid rgb(var(--v-theme-primary));
}
</style>
