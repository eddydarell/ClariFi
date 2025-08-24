<template>
  <div>
    <v-row class="mb-6">
      <v-col>
        <h2 class="text-h4 font-weight-bold text-primary">
          <v-icon class="me-2">mdi-chart-bar</v-icon>
          Stock Analysis
        </h2>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" lg="8">
        <v-card elevation="2">
          <v-card-title class="bg-primary text-white">
            <v-icon class="me-2">mdi-settings</v-icon>
            Analysis Configuration
          </v-card-title>

          <v-card-text class="pa-6">
            <v-form ref="analysisForm" v-model="formValid">
              <!-- Stock Tickers -->
              <v-text-field
                v-model="analysisData.tickers"
                label="Stock Tickers (comma-separated)"
                :rules="[v => !!v || 'At least one ticker is required']"
                required
                variant="outlined"
                placeholder="AAPL, GOOGL, MSFT"
                class="mb-4"
                hint="Enter stock symbols separated by commas"
                persistent-hint
              ></v-text-field>

              <v-row>
                <!-- Analysis Period -->
                <v-col cols="12" md="6">
                  <v-select
                    v-model="analysisData.period"
                    label="Analysis Period"
                    :items="periodOptions"
                    variant="outlined"
                    class="mb-4"
                  ></v-select>
                </v-col>

                <!-- Portfolio Selection -->
                <v-col cols="12" md="6">
                  <v-select
                    v-model="analysisData.portfolio_id"
                    label="Portfolio (Optional)"
                    :items="portfolioOptions"
                    variant="outlined"
                    class="mb-4"
                    clearable
                  ></v-select>
                </v-col>
              </v-row>

              <!-- Analysis Options -->
              <v-card variant="outlined" class="mb-4">
                <v-card-title class="text-h6">Analysis Options</v-card-title>
                <v-card-text>
                  <v-row>
                    <v-col cols="12" sm="6">
                      <v-switch
                        v-model="analysisData.include_patterns"
                        label="Pattern Analysis"
                        color="primary"
                        hide-details
                      ></v-switch>
                    </v-col>
                    <v-col cols="12" sm="6">
                      <v-switch
                        v-model="analysisData.include_events"
                        label="Event Correlation"
                        color="primary"
                        hide-details
                      ></v-switch>
                    </v-col>
                    <v-col cols="12" sm="6">
                      <v-switch
                        v-model="analysisData.include_options"
                        label="Options Analysis"
                        color="primary"
                        hide-details
                      ></v-switch>
                    </v-col>
                    <v-col cols="12" sm="6">
                      <v-switch
                        v-model="analysisData.include_seasonal"
                        label="Seasonal Analysis"
                        color="primary"
                        hide-details
                      ></v-switch>
                    </v-col>
                  </v-row>
                </v-card-text>
              </v-card>

              <!-- Run Analysis Button -->
              <v-btn
                color="primary"
                size="large"
                @click="runAnalysis"
                :disabled="!formValid"
                :loading="loading"
                prepend-icon="mdi-play"
                block
              >
                Run Analysis
              </v-btn>
            </v-form>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" lg="4">
        <v-card elevation="2">
          <v-card-title class="bg-success text-white">
            <v-icon class="me-2">mdi-information</v-icon>
            Quick Tips
          </v-card-title>
          <v-card-text>
            <v-list density="compact">
              <v-list-item>
                <template v-slot:prepend>
                  <v-icon color="primary" size="small">mdi-lightbulb</v-icon>
                </template>
                <v-list-item-title class="text-body-2">
                  Use comma-separated tickers (e.g., AAPL, GOOGL)
                </v-list-item-title>
              </v-list-item>

              <v-list-item>
                <template v-slot:prepend>
                  <v-icon color="primary" size="small">mdi-lightbulb</v-icon>
                </template>
                <v-list-item-title class="text-body-2">
                  Pattern analysis identifies trading patterns
                </v-list-item-title>
              </v-list-item>

              <v-list-item>
                <template v-slot:prepend>
                  <v-icon color="primary" size="small">mdi-lightbulb</v-icon>
                </template>
                <v-list-item-title class="text-body-2">
                  Event correlation shows market reactions
                </v-list-item-title>
              </v-list-item>

              <v-list-item>
                <template v-slot:prepend>
                  <v-icon color="primary" size="small">mdi-lightbulb</v-icon>
                </template>
                <v-list-item-title class="text-body-2">
                  Seasonal analysis reveals timing patterns
                </v-list-item-title>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>

        <!-- Recent Analysis Results -->
        <v-card elevation="2" class="mt-4">
          <v-card-title class="bg-info text-white">
            <v-icon class="me-2">mdi-chart-line</v-icon>
            Quick Actions
          </v-card-title>
          <v-card-text>
            <v-btn
              variant="outlined"
              color="primary"
              block
              class="mb-2"
              @click="loadPopularTickers"
            >
              Load Popular Tickers
            </v-btn>
            <v-btn
              variant="outlined"
              color="secondary"
              block
              @click="clearForm"
            >
              Clear Form
            </v-btn>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Analysis Results Section -->
    <v-row v-if="analysisResults" class="mt-6">
      <v-col cols="12">
        <v-card elevation="2">
          <v-card-title class="bg-success text-white">
            <v-icon class="me-2">mdi-chart-line</v-icon>
            Analysis Results
            <v-spacer></v-spacer>
            <v-btn
              icon="mdi-close"
              size="small"
              variant="text"
              @click="clearResults"
            ></v-btn>
          </v-card-title>

          <v-card-text class="pa-6">
            <!-- Summary Stats -->
            <v-row class="mb-4">
              <v-col cols="12" sm="6" md="3">
                <v-card variant="outlined" class="pa-4 text-center">
                  <div class="text-h4 text-primary font-weight-bold">{{ analysisResults.analyzed_tickers }}</div>
                  <div class="text-subtitle-2 text-medium-emphasis">Tickers Analyzed</div>
                </v-card>
              </v-col>
              <v-col cols="12" sm="6" md="3">
                <v-card variant="outlined" class="pa-4 text-center">
                  <div class="text-h4 text-success font-weight-bold">{{ (analysisResults.execution_time * 1000).toFixed(0) }}ms</div>
                  <div class="text-subtitle-2 text-medium-emphasis">Execution Time</div>
                </v-card>
              </v-col>
              <v-col cols="12" sm="6" md="3">
                <v-card variant="outlined" class="pa-4 text-center">
                  <div class="text-h4 text-info font-weight-bold">{{ formatTimestamp(analysisResults.timestamp) }}</div>
                  <div class="text-subtitle-2 text-medium-emphasis">Analysis Time</div>
                </v-card>
              </v-col>
              <v-col cols="12" sm="6" md="3">
                <v-card variant="outlined" class="pa-4 text-center">
                  <v-chip
                    :color="analysisResults.success ? 'success' : 'error'"
                    variant="flat"
                    size="large"
                  >
                    {{ analysisResults.success ? 'SUCCESS' : 'FAILED' }}
                  </v-chip>
                </v-card>
              </v-col>
            </v-row>

            <!-- Individual Stock Results -->
            <v-row>
              <v-col
                cols="12"
                md="6"
                lg="4"
                v-for="(result, ticker) in analysisResults.results"
                :key="ticker"
              >
                <v-card variant="outlined" class="mb-4">
                  <v-card-title class="bg-grey-lighten-5">
                    <v-icon class="me-2">mdi-chart-candlestick</v-icon>
                    {{ ticker }}
                  </v-card-title>

                  <v-card-text>
                    <!-- Recommendation and Risk -->
                    <div class="mb-3">
                      <v-chip
                        :color="getRecommendationColor(result.overall_recommendation)"
                        variant="flat"
                        class="me-2"
                      >
                        {{ result.overall_recommendation }}
                      </v-chip>
                      <v-chip
                        :color="getRiskColor(result.risk_level)"
                        variant="outlined"
                      >
                        {{ result.risk_level }} Risk
                      </v-chip>
                    </div>

                    <!-- Confidence Level -->
                    <div class="mb-3">
                      <v-progress-linear
                        :model-value="getConfidenceValue(result.confidence_level)"
                        :color="getConfidenceColor(result.confidence_level)"
                        height="8"
                        rounded
                      ></v-progress-linear>
                      <div class="text-caption mt-1">
                        Confidence: {{ result.confidence_level }}
                      </div>
                    </div>

                    <!-- Analysis Details -->
                    <v-list density="compact">
                      <v-list-item>
                        <template v-slot:prepend>
                          <v-icon size="small" color="primary">mdi-identifier</v-icon>
                        </template>
                        <v-list-item-title class="text-caption">
                          ID: {{ result.analysis_id.substring(0, 8) }}...
                        </v-list-item-title>
                      </v-list-item>

                      <!-- Options Analysis -->
                      <v-list-item v-if="result.options">
                        <template v-slot:prepend>
                          <v-icon
                            size="small"
                            :color="result.options.error ? 'error' : 'success'"
                          >
                            {{ result.options.error ? 'mdi-alert' : 'mdi-check' }}
                          </v-icon>
                        </template>
                        <v-list-item-title class="text-caption">
                          Options: {{ result.options.error ? 'Failed' : 'Analyzed' }}
                        </v-list-item-title>
                      </v-list-item>

                      <!-- Investment Advice -->
                      <v-list-item v-if="result.investment_advice">
                        <template v-slot:prepend>
                          <v-icon
                            size="small"
                            :color="result.investment_advice.error ? 'error' : 'success'"
                          >
                            {{ result.investment_advice.error ? 'mdi-alert' : 'mdi-lightbulb' }}
                          </v-icon>
                        </template>
                        <v-list-item-title class="text-caption">
                          Advice: {{ result.investment_advice.error ? 'Failed' : 'Available' }}
                        </v-list-item-title>
                      </v-list-item>

                      <!-- Seasonal Analysis -->
                      <v-list-item>
                        <template v-slot:prepend>
                          <v-icon
                            size="small"
                            :color="result.seasonal ? 'success' : 'warning'"
                          >
                            {{ result.seasonal ? 'mdi-calendar' : 'mdi-calendar-remove' }}
                          </v-icon>
                        </template>
                        <v-list-item-title class="text-caption">
                          Seasonal: {{ result.seasonal ? 'Available' : 'Not Available' }}
                        </v-list-item-title>
                      </v-list-item>
                    </v-list>

                    <!-- Error Messages -->
                    <v-alert
                      v-if="result.options?.error || result.investment_advice?.error"
                      type="warning"
                      variant="tonal"
                      density="compact"
                      class="mt-3"
                    >
                      <div class="text-caption">
                        <div v-if="result.options?.error">{{ result.options.error }}</div>
                        <div v-if="result.investment_advice?.error">{{ result.investment_advice.error }}</div>
                      </div>
                    </v-alert>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script>
import { ref, reactive, computed } from 'vue'

export default {
  name: 'AnalysisTab',
  props: {
    portfolios: {
      type: Array,
      default: () => []
    },
    analysisResults: {
      type: Object,
      default: null
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  emits: ['run-analysis'],
  setup(props, { emit }) {
    const formValid = ref(false)

    const analysisData = reactive({
      tickers: '',
      portfolio_id: null,
      period: '1y',
      include_patterns: true,
      include_events: true,
      include_options: true,
      include_seasonal: true
    })

    const periodOptions = [
      { title: '1 Month', value: '1mo' },
      { title: '3 Months', value: '3mo' },
      { title: '6 Months', value: '6mo' },
      { title: '1 Year', value: '1y' },
      { title: '2 Years', value: '2y' },
      { title: '5 Years', value: '5y' }
    ]

    const portfolioOptions = computed(() => {
      return props.portfolios.map(portfolio => ({
        title: portfolio.name,
        value: portfolio.id
      }))
    })

    const runAnalysis = () => {
      if (!formValid.value) return

      const data = {
        ...analysisData,
        tickers: analysisData.tickers.split(',').map(t => t.trim().toUpperCase())
      }

      emit('run-analysis', data)
    }

    const loadPopularTickers = () => {
      analysisData.tickers = 'AAPL, GOOGL, MSFT, AMZN, TSLA'
    }

    const clearForm = () => {
      analysisData.tickers = ''
      analysisData.portfolio_id = null
      analysisData.period = '1y'
      analysisData.include_patterns = true
      analysisData.include_events = true
      analysisData.include_options = true
      analysisData.include_seasonal = true
    }

    const clearResults = () => {
      emit('clear-results')
    }

    const formatTimestamp = (timestamp) => {
      const date = new Date(timestamp)
      return date.toLocaleTimeString()
    }

    const getRecommendationColor = (recommendation) => {
      switch (recommendation?.toUpperCase()) {
        case 'BUY': return 'success'
        case 'SELL': return 'error'
        case 'HOLD': return 'warning'
        default: return 'grey'
      }
    }

    const getRiskColor = (riskLevel) => {
      switch (riskLevel?.toUpperCase()) {
        case 'LOW': return 'success'
        case 'MEDIUM': return 'warning'
        case 'HIGH': return 'error'
        default: return 'grey'
      }
    }

    const getConfidenceValue = (confidenceLevel) => {
      switch (confidenceLevel?.toUpperCase()) {
        case 'HIGH': return 85
        case 'MEDIUM': return 60
        case 'LOW': return 35
        default: return 0
      }
    }

    const getConfidenceColor = (confidenceLevel) => {
      switch (confidenceLevel?.toUpperCase()) {
        case 'HIGH': return 'success'
        case 'MEDIUM': return 'warning'
        case 'LOW': return 'error'
        default: return 'grey'
      }
    }

    return {
      formValid,
      analysisData,
      periodOptions,
      portfolioOptions,
      runAnalysis,
      loadPopularTickers,
      clearForm,
      clearResults,
      formatTimestamp,
      getRecommendationColor,
      getRiskColor,
      getConfidenceValue,
      getConfidenceColor
    }
  }
}
</script>
