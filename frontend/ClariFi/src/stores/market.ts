import { defineStore } from 'pinia'
import axios from 'axios'
import { ref } from 'vue'

export interface Stock {
  ticker: string
  name?: string
  price: number | null
  change: number | null
  change_percent: number | null
  volume: number | null
  market_cap?: number | null
  listing_date?: string
}

function apiError(error: unknown, fallback: string) {
  if (axios.isAxiosError(error)) {
    return error.response?.data?.detail || error.response?.data?.errors?.[0]?.message || error.message
  }
  return error instanceof Error ? error.message : fallback
}

export const useMarketStore = defineStore('market', () => {
  const screenerResults = ref<Stock[]>([])
  const monitoredStocks = ref<Stock[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const monitorError = ref<string | null>(null)
  const monitorState = ref<'idle' | 'connecting' | 'connected' | 'reconnecting' | 'failed'>('idle')
  const isMonitoring = ref(false)
  let ws: WebSocket | null = null
  let reconnectTimer: number | undefined

  async function fetchScreenerData(category = 'gainers', limit = 10) {
    isLoading.value = true
    error.value = null
    try {
      const response = await axios.post('/api/v1/screener', { category, limit })
      if (response.data?.status === 'error') throw new Error(response.data?.errors?.[0]?.message || 'Screener failed')
      const results = response.data?.data?.results ?? []
      screenerResults.value = Array.isArray(results)
        ? results.map((item: Record<string, unknown>) => ({
            ticker: String(item.symbol ?? ''),
            name: String(item.shortName ?? ''),
            price: numberOrNull(item.regularMarketPrice),
            change: numberOrNull(item.regularMarketChange),
            change_percent: numberOrNull(item.regularMarketChangePercent),
            volume: numberOrNull(item.regularMarketVolume),
            market_cap: numberOrNull(item.marketCap),
            listing_date: typeof item.listingDate === 'string' ? item.listingDate : undefined,
          }))
        : []
    } catch (requestError) {
      error.value = apiError(requestError, 'Failed to fetch screener data')
    } finally {
      isLoading.value = false
    }
  }

  function numberOrNull(value: unknown): number | null {
    const number = typeof value === 'number' ? value : Number(value)
    return Number.isFinite(number) ? number : null
  }

  async function startMonitoring(tickers: string[]) {
    monitorError.value = null
    const normalized = [...new Set(tickers.map((ticker) => ticker.trim().toUpperCase()).filter(Boolean))]
    if (!normalized.length) return
    try {
      await axios.post('/api/live-monitor/start', { tickers: normalized })
      isMonitoring.value = true
      connectWebSocket()
    } catch (requestError) {
      monitorState.value = 'failed'
      monitorError.value = apiError(requestError, 'Failed to start monitoring')
    }
  }

  async function stopMonitoring() {
    isMonitoring.value = false
    monitorState.value = 'idle'
    if (reconnectTimer) window.clearTimeout(reconnectTimer)
    reconnectTimer = undefined
    ws?.close()
    ws = null
    monitoredStocks.value = []
    try {
      await axios.post('/api/live-monitor/stop')
    } catch (requestError) {
      monitorError.value = apiError(requestError, 'Failed to stop monitoring')
    }
  }

  function connectWebSocket() {
    if (ws || !isMonitoring.value) return
    monitorState.value = monitorState.value === 'connected' ? 'reconnecting' : 'connecting'
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    ws = new WebSocket(`${protocol}//${window.location.host}/ws`)
    ws.onopen = () => {
      monitorState.value = 'connected'
      monitorError.value = null
    }
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'price_update' && Array.isArray(data.data)) updateMonitoredStocks(data.data)
      } catch {
        monitorError.value = 'Received an invalid market update'
      }
    }
    ws.onerror = () => {
      monitorState.value = 'failed'
      monitorError.value = 'Live market connection failed'
    }
    ws.onclose = () => {
      ws = null
      if (isMonitoring.value) {
        monitorState.value = 'reconnecting'
        reconnectTimer = window.setTimeout(connectWebSocket, 2000)
      }
    }
  }

  function updateMonitoredStocks(updates: Record<string, unknown>[]) {
    updates.forEach((update) => {
      const ticker = String(update.ticker ?? '')
      if (!ticker) return
      const stockData: Stock = {
        ticker,
        price: numberOrNull(update.current_price ?? update.price),
        change: numberOrNull(update.change),
        change_percent: numberOrNull(update.change_pct ?? update.percent_change),
        volume: numberOrNull(update.volume),
      }
      const index = monitoredStocks.value.findIndex((stock) => stock.ticker === ticker)
      if (index >= 0) monitoredStocks.value[index] = stockData
      else monitoredStocks.value.push(stockData)
    })
  }

  return {
    screenerResults, monitoredStocks, isLoading, error, monitorError, monitorState, isMonitoring,
    fetchScreenerData, startMonitoring, stopMonitoring,
  }
})
