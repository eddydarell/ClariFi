<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12" md="4">
        <v-card class="mb-4" elevation="2">
          <v-card-title class="text-primary">
            <v-icon start color="primary">mdi-monitor-dashboard</v-icon>
            Live Monitor
          </v-card-title>
          <v-card-text>
            <v-text-field
              v-model="newTicker"
              label="Add Ticker"
              variant="outlined"
              append-inner-icon="mdi-plus"
              @click:append-inner="addTicker"
              @keyup.enter="addTicker"
              hint="Enter symbol (e.g., AAPL, BTC-USD)"
              persistent-hint
            ></v-text-field>
            
            <v-list class="bg-transparent">
              <v-list-item v-for="ticker in tickers" :key="ticker" :title="ticker">
                <template v-slot:append>
                  <v-btn icon="mdi-delete" size="small" color="error" variant="text" @click="removeTicker(ticker)"></v-btn>
                </template>
              </v-list-item>
            </v-list>
            
            <v-divider class="my-4"></v-divider>
            
            <v-btn
              block
              :color="monitoring ? 'error' : 'success'"
              size="large"
              @click="toggleMonitoring"
              :loading="loading"
              elevation="4"
            >
              <v-icon start>{{ monitoring ? 'mdi-stop' : 'mdi-play' }}</v-icon>
              {{ monitoring ? 'Stop Monitoring' : 'Start Monitoring' }}
            </v-btn>
            
            <div class="mt-4 text-caption text-center" v-if="monitoring">
              <v-progress-circular indeterminate size="20" color="primary" class="me-2"></v-progress-circular>
              Live updates active
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" md="8">
        <v-row>
          <v-col v-for="(data, ticker) in tickerData" :key="ticker" cols="12" sm="6" lg="4">
            <v-card :color="getCardColor(data.change)" elevation="3" class="transition-swing">
              <v-card-title class="d-flex justify-space-between">
                {{ ticker }}
                <span class="text-h6">{{ formatPrice(data.price) }}</span>
              </v-card-title>
              <v-card-text>
                <div class="d-flex align-center">
                  <v-icon :color="getIconColor(data.change)" size="large" class="me-2">
                    {{ getIcon(data.change) }}
                  </v-icon>
                  <span :class="getTextColor(data.change) + ' text-h5 font-weight-bold'">
                    {{ formatChange(data.change) }}
                  </span>
                  <span :class="getTextColor(data.change) + ' ms-2 text-subtitle-1'">
                    ({{ formatPercent(data.change_pct) }})
                  </span>
                </div>
                <div class="text-caption text-medium-emphasis mt-2">
                  Last update: {{ formatTime(data.timestamp) }}
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
        
        <v-alert v-if="!monitoring && Object.keys(tickerData).length === 0" type="info" variant="tonal" class="mt-4">
          Add tickers and click Start Monitoring to see real-time data.
        </v-alert>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import { ref, onUnmounted } from 'vue'

export default {
  name: 'LiveMonitorTab',
  setup() {
    const newTicker = ref('')
    const tickers = ref(['AAPL', 'BTC-USD', 'NVDA'])
    const monitoring = ref(false)
    const loading = ref(false)
    const tickerData = ref({})
    let socket = null

    const addTicker = () => {
      if (newTicker.value && !tickers.value.includes(newTicker.value.toUpperCase())) {
        tickers.value.push(newTicker.value.toUpperCase())
        newTicker.value = ''
        if (monitoring.value) {
            updateMonitoringConfig()
        }
      }
    }

    const removeTicker = (t) => {
      tickers.value = tickers.value.filter(item => item !== t)
      delete tickerData.value[t]
      if (monitoring.value) {
          updateMonitoringConfig()
      }
    }

    const updateMonitoringConfig = async () => {
        try {
            await fetch('/api/live-monitor/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ tickers: tickers.value })
            })
        } catch (e) {
            console.error("Failed to update config", e)
        }
    }

    const toggleMonitoring = async () => {
      loading.value = true
      try {
        if (monitoring.value) {
          // Stop
          await fetch('/api/live-monitor/stop', { method: 'POST' })
          monitoring.value = false
          if (socket) {
            socket.close()
            socket = null
          }
        } else {
          // Start
          await updateMonitoringConfig()
          monitoring.value = true
          connectWebSocket()
        }
      } catch (e) {
        console.error(e)
      } finally {
        loading.value = false
      }
    }

    const connectWebSocket = () => {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
        const wsUrl = `${protocol}//${window.location.host}/ws`
        
        socket = new WebSocket(wsUrl)
        
        socket.onopen = () => {
            console.log("WebSocket connected")
        }
        
        socket.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data)
                if (message.type === 'price_update') {
                    message.data.forEach(update => {
                        tickerData.value[update.ticker] = update
                    })
                }
            } catch (e) {
                console.error("Error parsing WS message", e)
            }
        }
        
        socket.onclose = () => {
            console.log("WebSocket disconnected")
            if (monitoring.value) {
                // Auto reconnect if supposed to be running
                setTimeout(connectWebSocket, 3000)
            }
        }
    }

    onUnmounted(() => {
      if (socket) socket.close()
    })

    // Formatters
    const formatPrice = (val) => val ? '$' + val.toFixed(2) : '$0.00'
    const formatChange = (val) => val ? (val > 0 ? '+' : '') + val.toFixed(2) : '0.00'
    const formatPercent = (val) => val ? (val > 0 ? '+' : '') + val.toFixed(2) + '%' : '0.00%'
    const formatTime = (iso) => iso ? new Date(iso).toLocaleTimeString() : ''
    
    const getIcon = (change) => change > 0 ? 'mdi-arrow-up-bold' : (change < 0 ? 'mdi-arrow-down-bold' : 'mdi-minus')
    const getIconColor = (change) => change > 0 ? 'success' : (change < 0 ? 'error' : 'grey')
    const getTextColor = (change) => change > 0 ? 'text-success' : (change < 0 ? 'text-error' : 'text-grey')
    const getCardColor = (change) => {
        // Optional: subtle background tint
        return undefined 
    }

    return {
      newTicker,
      tickers,
      monitoring,
      loading,
      tickerData,
      addTicker,
      removeTicker,
      toggleMonitoring,
      formatPrice,
      formatChange,
      formatPercent,
      formatTime,
      getIcon,
      getIconColor,
      getTextColor,
      getCardColor
    }
  }
}
</script>

<style scoped>
.transition-swing {
  transition: 0.3s cubic-bezier(0.25, 0.8, 0.5, 1);
}
</style>
