<template>
  <v-app>
    <!-- App Bar -->
    <v-app-bar app color="primary" dark elevation="4">
      <v-icon class="me-3" size="large">mdi-chart-line</v-icon>
      <v-toolbar-title class="text-h5 font-weight-bold">
        ClariFi
        <span class="text-subtitle-2 font-weight-light ms-2">Clarify your Finances</span>
      </v-toolbar-title>

      <v-spacer></v-spacer>

      <!-- Navigation Tabs -->
      <v-tabs v-model="currentTab" dark align-with-title>
        <v-tab value="dashboard">
          <v-icon start>mdi-view-dashboard</v-icon>
          Dashboard
        </v-tab>
        <v-tab value="portfolios">
          <v-icon start>mdi-briefcase</v-icon>
          Portfolios
        </v-tab>
        <v-tab value="analysis">
          <v-icon start>mdi-chart-bar</v-icon>
          Analysis
        </v-tab>
        <v-tab value="comparison">
          <v-icon start>mdi-scale-balance</v-icon>
          Comparison
        </v-tab>
        <v-tab value="screener">
          <v-icon start>mdi-filter-variant</v-icon>
          Screener
        </v-tab>
        <v-tab value="monitor">
          <v-icon start>mdi-monitor-dashboard</v-icon>
          Live Monitor
        </v-tab>
        <v-tab value="strategy">
          <v-icon start>mdi-chess-knight</v-icon>
          Strategy
        </v-tab>
        <v-tab value="history">
          <v-icon start>mdi-history</v-icon>
          History
        </v-tab>
      </v-tabs>
    </v-app-bar>

    <!-- Main Content -->
    <v-main>
      <v-container fluid class="pa-6">
        <!-- Dashboard Tab -->
        <v-window v-model="currentTab">
          <v-window-item value="dashboard">
            <DashboardTab
              :portfolios="portfolios"
              :analysis-history="analysisHistory"
              :loading="loading"
            />
          </v-window-item>

          <!-- Portfolios Tab -->
          <v-window-item value="portfolios">
            <PortfoliosTab
              :portfolios="portfolios"
              @create-portfolio="createPortfolio"
              @add-ticker="addTicker"
              @remove-ticker="removeTicker"
              @analyze-portfolio="analyzePortfolio"
              :loading="loading"
            />
          </v-window-item>

          <!-- Analysis Tab -->
          <v-window-item value="analysis">
            <AnalysisTab
              :portfolios="portfolios"
              :analysis-results="currentAnalysisResults"
              @run-analysis="runAnalysis"
              @clear-results="currentAnalysisResults = null"
              :loading="loading"
            />
          </v-window-item>

          <!-- Comparison Tab -->
          <v-window-item value="comparison">
            <ComparisonTab
              @run-comparison="runComparison"
              :loading="loading"
            />
          </v-window-item>

          <!-- Screener Tab -->
          <v-window-item value="screener">
            <ScreenerTab :loading="loading" />
          </v-window-item>

          <!-- Live Monitor Tab -->
          <v-window-item value="monitor">
            <LiveMonitorTab />
          </v-window-item>

          <!-- Strategy Tab -->
          <v-window-item value="strategy">
            <StrategyTab />
          </v-window-item>

          <!-- History Tab -->
          <v-window-item value="history">
            <HistoryTab
              :history="analysisHistory"
              @delete-analysis="deleteAnalysis"
              :loading="loading"
            />
          </v-window-item>
        </v-window>
      </v-container>
    </v-main>

    <!-- Loading Overlay -->
    <v-overlay v-model="loading" class="align-center justify-center">
      <v-progress-circular
        color="primary"
        indeterminate
        size="64"
      ></v-progress-circular>
    </v-overlay>

    <!-- Snackbar for notifications -->
    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      :timeout="snackbar.timeout"
      location="top right"
    >
      {{ snackbar.message }}
      <template v-slot:actions>
        <v-btn
          color="white"
          variant="text"
          @click="snackbar.show = false"
        >
          Close
        </v-btn>
      </template>
    </v-snackbar>
  </v-app>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import DashboardTab from './components/DashboardTab.vue'
import PortfoliosTab from './components/PortfoliosTab.vue'
import AnalysisTab from './components/AnalysisTab.vue'
import ComparisonTab from './components/ComparisonTab.vue'
import HistoryTab from './components/HistoryTab.vue'
import ScreenerTab from './components/ScreenerTab.vue'
import LiveMonitorTab from './components/LiveMonitorTab.vue'
import StrategyTab from './components/StrategyTab.vue'

export default {
  name: 'ClariFiApp',
  components: {
    DashboardTab,
    PortfoliosTab,
    AnalysisTab,
    ComparisonTab,
    HistoryTab,
    ScreenerTab,
    LiveMonitorTab,
    StrategyTab
  },
  setup() {
    const currentTab = ref('dashboard')
    const loading = ref(false)
    const portfolios = ref([])
    const analysisHistory = ref([])
    const currentAnalysisResults = ref(null)

    const snackbar = reactive({
      show: false,
      message: '',
      color: 'success',
      timeout: 3000
    })

    const baseURL = '/api'

    // API helper
    const apiCall = async (endpoint, method = 'GET', data = null) => {
      const config = {
        method,
        headers: {
          'Content-Type': 'application/json',
        }
      }

      if (data) {
        config.body = JSON.stringify(data)
      }

      try {
        const response = await fetch(`${baseURL}${endpoint}`, config)
        const result = await response.json()

        if (!response.ok) {
          throw new Error(result.detail || 'API call failed')
        }

        return result
      } catch (error) {
        console.error('API Error:', error)
        showError(error.message)
        throw error
      }
    }

    // Notification helpers
    const showSuccess = (message) => {
      snackbar.show = true
      snackbar.message = message
      snackbar.color = 'success'
    }

    const showError = (message) => {
      snackbar.show = true
      snackbar.message = message
      snackbar.color = 'error'
      snackbar.timeout = 5000
    }

    // Data loading
    const loadPortfolios = async () => {
      try {
        const response = await apiCall('/portfolios')
        portfolios.value = response.portfolios || []
      } catch (error) {
        console.error('Failed to load portfolios:', error)
      }
    }

    const loadAnalysisHistory = async () => {
      try {
        const response = await apiCall('/analysis/history?limit=50')
        analysisHistory.value = response.history || []
      } catch (error) {
        console.error('Failed to load analysis history:', error)
      }
    }

    // Portfolio management
    const createPortfolio = async (portfolioData) => {
      try {
        loading.value = true
        await apiCall('/portfolios', 'POST', portfolioData)
        showSuccess('Portfolio created successfully')
        await loadPortfolios()
      } catch (error) {
        console.error('Failed to create portfolio:', error)
      } finally {
        loading.value = false
      }
    }

    const addTicker = async (portfolioId, tickerData) => {
      try {
        loading.value = true
        await apiCall(`/portfolios/${portfolioId}/tickers`, 'POST', tickerData)
        showSuccess('Ticker added successfully')
        await loadPortfolios()
      } catch (error) {
        console.error('Failed to add ticker:', error)
      } finally {
        loading.value = false
      }
    }

    const removeTicker = async (portfolioId, ticker) => {
      try {
        loading.value = true
        await apiCall(`/portfolios/${portfolioId}/tickers/${ticker}`, 'DELETE')
        showSuccess('Ticker removed successfully')
        await loadPortfolios()
      } catch (error) {
        console.error('Failed to remove ticker:', error)
      } finally {
        loading.value = false
      }
    }

    // Analysis functions
    const runAnalysis = async (analysisData) => {
      try {
        loading.value = true
        const response = await apiCall('/analysis/comprehensive', 'POST', analysisData)
        currentAnalysisResults.value = response
        showSuccess('Analysis completed successfully')
        await loadAnalysisHistory()
        return response
      } catch (error) {
        console.error('Failed to run analysis:', error)
      } finally {
        loading.value = false
      }
    }

    const runComparison = async (comparisonData) => {
      try {
        loading.value = true
        const response = await apiCall('/analysis/compare', 'POST', comparisonData)
        showSuccess('Comparison completed successfully')
        await loadAnalysisHistory()
        return response
      } catch (error) {
        console.error('Failed to run comparison:', error)
      } finally {
        loading.value = false
      }
    }

    const analyzePortfolio = async (portfolioId) => {
      try {
        loading.value = true
        const response = await apiCall(`/analysis/portfolio/${portfolioId}`, 'POST')
        showSuccess('Portfolio analysis completed successfully')
        await loadAnalysisHistory()
        return response
      } catch (error) {
        console.error('Failed to analyze portfolio:', error)
      } finally {
        loading.value = false
      }
    }

    const deleteAnalysis = async (analysisId) => {
      try {
        loading.value = true
        // Note: Backend doesn't have delete endpoint yet
        showError('Delete analysis feature not yet implemented')
        // await apiCall(`/analysis/${analysisId}`, 'DELETE')
        // showSuccess('Analysis deleted successfully')
        // await loadAnalysisHistory()
      } catch (error) {
        console.error('Failed to delete analysis:', error)
      } finally {
        loading.value = false
      }
    }

    // Initialize data on mount
    onMounted(async () => {
      loading.value = true
      try {
        await Promise.all([
          loadPortfolios(),
          loadAnalysisHistory()
        ])
      } finally {
        loading.value = false
      }
    })

    return {
      currentTab,
      loading,
      portfolios,
      analysisHistory,
      currentAnalysisResults,
      snackbar,
      createPortfolio,
      addTicker,
      removeTicker,
      runAnalysis,
      runComparison,
      analyzePortfolio,
      deleteAnalysis
    }
  }
}
</script>

<style scoped>
.v-app-bar .v-toolbar-title {
  white-space: nowrap;
}
</style>
