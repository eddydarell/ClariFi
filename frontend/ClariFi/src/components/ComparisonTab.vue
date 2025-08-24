<template>
  <div>
    <v-row class="mb-6">
      <v-col>
        <h2 class="text-h4 font-weight-bold text-primary">
          <v-icon class="me-2">mdi-scale-balance</v-icon>
          Stock Comparison
        </h2>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" lg="8">
        <v-card elevation="2">
          <v-card-title class="bg-primary text-white">
            <v-icon class="me-2">mdi-compare</v-icon>
            Comparison Configuration
          </v-card-title>

          <v-card-text class="pa-6">
            <v-form ref="comparisonForm" v-model="formValid">
              <!-- Base Ticker -->
              <v-text-field
                v-model="comparisonData.base_ticker"
                label="Base Ticker"
                :rules="[v => !!v || 'Base ticker is required']"
                required
                variant="outlined"
                placeholder="AAPL"
                class="mb-4"
                hint="The stock to compare others against"
                persistent-hint
              ></v-text-field>

              <!-- Compare Tickers -->
              <v-text-field
                v-model="comparisonData.compare_tickers"
                label="Compare Tickers (comma-separated)"
                :rules="[v => !!v || 'At least one ticker to compare is required']"
                required
                variant="outlined"
                placeholder="GOOGL, MSFT, AMZN"
                class="mb-4"
                hint="Enter stock symbols to compare against the base ticker"
                persistent-hint
              ></v-text-field>

              <v-row>
                <!-- Time Period -->
                <v-col cols="12" md="6">
                  <v-select
                    v-model="comparisonData.period"
                    label="Time Period"
                    :items="periodOptions"
                    variant="outlined"
                    class="mb-4"
                  ></v-select>
                </v-col>

                <!-- Comparison Type -->
                <v-col cols="12" md="6">
                  <v-select
                    v-model="comparisonData.comparison_type"
                    label="Comparison Type"
                    :items="comparisonTypes"
                    variant="outlined"
                    class="mb-4"
                  ></v-select>
                </v-col>
              </v-row>

              <!-- Comparison Metrics -->
              <v-card variant="outlined" class="mb-4">
                <v-card-title class="text-h6">Comparison Metrics</v-card-title>
                <v-card-text>
                  <v-row>
                    <v-col cols="12" sm="6">
                      <v-switch
                        v-model="comparisonData.include_returns"
                        label="Returns Analysis"
                        color="primary"
                        hide-details
                      ></v-switch>
                    </v-col>
                    <v-col cols="12" sm="6">
                      <v-switch
                        v-model="comparisonData.include_volatility"
                        label="Volatility Analysis"
                        color="primary"
                        hide-details
                      ></v-switch>
                    </v-col>
                    <v-col cols="12" sm="6">
                      <v-switch
                        v-model="comparisonData.include_correlation"
                        label="Correlation Analysis"
                        color="primary"
                        hide-details
                      ></v-switch>
                    </v-col>
                    <v-col cols="12" sm="6">
                      <v-switch
                        v-model="comparisonData.include_beta"
                        label="Beta Analysis"
                        color="primary"
                        hide-details
                      ></v-switch>
                    </v-col>
                  </v-row>
                </v-card-text>
              </v-card>

              <!-- Advanced Options -->
              <v-expansion-panels variant="accordion" class="mb-4">
                <v-expansion-panel>
                  <v-expansion-panel-title>
                    <v-icon class="me-2">mdi-cog</v-icon>
                    Advanced Options
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                    <v-row>
                      <v-col cols="12" md="6">
                        <v-switch
                          v-model="comparisonData.normalize_prices"
                          label="Normalize Prices"
                          color="primary"
                          hide-details
                        ></v-switch>
                      </v-col>
                      <v-col cols="12" md="6">
                        <v-switch
                          v-model="comparisonData.include_dividends"
                          label="Include Dividends"
                          color="primary"
                          hide-details
                        ></v-switch>
                      </v-col>
                      <v-col cols="12" md="6">
                        <v-switch
                          v-model="comparisonData.risk_adjusted"
                          label="Risk-Adjusted Returns"
                          color="primary"
                          hide-details
                        ></v-switch>
                      </v-col>
                      <v-col cols="12" md="6">
                        <v-switch
                          v-model="comparisonData.sector_analysis"
                          label="Sector Analysis"
                          color="primary"
                          hide-details
                        ></v-switch>
                      </v-col>
                    </v-row>
                  </v-expansion-panel-text>
                </v-expansion-panel>
              </v-expansion-panels>

              <!-- Run Comparison Button -->
              <v-btn
                color="primary"
                size="large"
                @click="runComparison"
                :disabled="!formValid"
                :loading="loading"
                prepend-icon="mdi-play"
                block
              >
                Run Comparison
              </v-btn>
            </v-form>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" lg="4">
        <v-card elevation="2">
          <v-card-title class="bg-success text-white">
            <v-icon class="me-2">mdi-information</v-icon>
            Comparison Guide
          </v-card-title>
          <v-card-text>
            <v-list density="compact">
              <v-list-item>
                <template v-slot:prepend>
                  <v-icon color="primary" size="small">mdi-target</v-icon>
                </template>
                <v-list-item-title class="text-body-2">
                  Choose a base ticker to compare against
                </v-list-item-title>
              </v-list-item>

              <v-list-item>
                <template v-slot:prepend>
                  <v-icon color="primary" size="small">mdi-chart-line</v-icon>
                </template>
                <v-list-item-title class="text-body-2">
                  Relative comparison shows percentage performance
                </v-list-item-title>
              </v-list-item>

              <v-list-item>
                <template v-slot:prepend>
                  <v-icon color="primary" size="small">mdi-sigma</v-icon>
                </template>
                <v-list-item-title class="text-body-2">
                  Correlation shows how stocks move together
                </v-list-item-title>
              </v-list-item>

              <v-list-item>
                <template v-slot:prepend>
                  <v-icon color="primary" size="small">mdi-trending-up</v-icon>
                </template>
                <v-list-item-title class="text-body-2">
                  Beta measures sensitivity to market moves
                </v-list-item-title>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>

        <!-- Preset Comparisons -->
        <v-card elevation="2" class="mt-4">
          <v-card-title class="bg-info text-white">
            <v-icon class="me-2">mdi-star</v-icon>
            Preset Comparisons
          </v-card-title>
          <v-card-text>
            <v-btn
              variant="outlined"
              color="primary"
              block
              class="mb-2"
              @click="loadTechGiants"
            >
              Tech Giants vs AAPL
            </v-btn>
            <v-btn
              variant="outlined"
              color="primary"
              block
              class="mb-2"
              @click="loadBankStocks"
            >
              Bank Stocks vs JPM
            </v-btn>
            <v-btn
              variant="outlined"
              color="primary"
              block
              class="mb-2"
              @click="loadEVStocks"
            >
              EV Stocks vs TSLA
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
  </div>
</template>

<script>
import { ref, reactive } from 'vue'

export default {
  name: 'ComparisonTab',
  props: {
    loading: {
      type: Boolean,
      default: false
    }
  },
  emits: ['run-comparison'],
  setup(props, { emit }) {
    const formValid = ref(false)

    const comparisonData = reactive({
      base_ticker: '',
      compare_tickers: '',
      period: '1y',
      comparison_type: 'relative',
      include_returns: true,
      include_volatility: true,
      include_correlation: true,
      include_beta: true,
      normalize_prices: true,
      include_dividends: false,
      risk_adjusted: false,
      sector_analysis: false
    })

    const periodOptions = [
      { title: '1 Month', value: '1mo' },
      { title: '3 Months', value: '3mo' },
      { title: '6 Months', value: '6mo' },
      { title: '1 Year', value: '1y' },
      { title: '2 Years', value: '2y' },
      { title: '5 Years', value: '5y' }
    ]

    const comparisonTypes = [
      { title: 'Relative Performance', value: 'relative' },
      { title: 'Absolute Values', value: 'absolute' },
      { title: 'Statistical Analysis', value: 'statistical' },
      { title: 'Risk Analysis', value: 'risk' }
    ]

    const runComparison = () => {
      if (!formValid.value) return

      const data = {
        ...comparisonData,
        base_ticker: comparisonData.base_ticker.trim().toUpperCase(),
        compare_tickers: comparisonData.compare_tickers.split(',').map(t => t.trim().toUpperCase())
      }

      emit('run-comparison', data)
    }

    const loadTechGiants = () => {
      comparisonData.base_ticker = 'AAPL'
      comparisonData.compare_tickers = 'GOOGL, MSFT, AMZN, META'
    }

    const loadBankStocks = () => {
      comparisonData.base_ticker = 'JPM'
      comparisonData.compare_tickers = 'BAC, WFC, C, GS'
    }

    const loadEVStocks = () => {
      comparisonData.base_ticker = 'TSLA'
      comparisonData.compare_tickers = 'NIO, XPEV, LI, RIVN'
    }

    const clearForm = () => {
      comparisonData.base_ticker = ''
      comparisonData.compare_tickers = ''
      comparisonData.period = '1y'
      comparisonData.comparison_type = 'relative'
      comparisonData.include_returns = true
      comparisonData.include_volatility = true
      comparisonData.include_correlation = true
      comparisonData.include_beta = true
      comparisonData.normalize_prices = true
      comparisonData.include_dividends = false
      comparisonData.risk_adjusted = false
      comparisonData.sector_analysis = false
    }

    return {
      formValid,
      comparisonData,
      periodOptions,
      comparisonTypes,
      runComparison,
      loadTechGiants,
      loadBankStocks,
      loadEVStocks,
      clearForm
    }
  }
}
</script>
