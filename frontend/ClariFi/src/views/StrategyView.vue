<script setup lang="ts">
import { ref } from 'vue'
import { useStrategyStore } from '@/stores/strategy'
import Card from 'primevue/card'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import StatusBadge from '@/components/common/StatusBadge.vue'
import MetricCard from '@/components/common/MetricCard.vue'

const strategyStore = useStrategyStore()
const ticker = ref('')
const period = ref('1y')

const periods = [
  { label: '1 Month', value: '1mo' },
  { label: '3 Months', value: '3mo' },
  { label: '6 Months', value: '6mo' },
  { label: '1 Year', value: '1y' },
  { label: '2 Years', value: '2y' },
  { label: '5 Years', value: '5y' }
]

async function analyze() {
  if (!ticker.value) return
  await strategyStore.analyzeStrategy(ticker.value.toUpperCase(), period.value)
}
</script>

<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-3xl font-bold text-on-surface">Strategy Analyzer</h1>
      <p class="text-on-surface-muted mt-1">Explore explainable technical and statistical scenarios</p>
    </div>

    <Card>
      <template #content>
        <div class="flex flex-col md:flex-row gap-4 items-stretch md:items-end">
          <div class="flex-1">
            <label for="strategy-ticker" class="block text-sm font-medium text-on-surface mb-2">Ticker Symbol</label>
            <InputText
              v-model="ticker"
              placeholder="e.g., AAPL"
              class="w-full"
              inputId="strategy-ticker"
              @keyup.enter="analyze"
            />
          </div>
          <div class="w-48">
            <label for="strategy-period" class="block text-sm font-medium text-on-surface mb-2">Period</label>
            <Select
              v-model="period"
              :options="periods"
              optionLabel="label"
              optionValue="value"
              class="w-full"
              inputId="strategy-period"
            />
          </div>
          <Button
            label="Analyze"
            icon="pi pi-chart-line"
            @click="analyze"
            :loading="strategyStore.isLoading"
            :disabled="!ticker"
            severity="info"
          />
        </div>
      </template>
    </Card>

    <Card v-if="strategyStore.error" class="bg-error/10 border border-error/30">
      <template #content>
        <div class="flex items-center gap-3 text-error">
          <i class="pi pi-exclamation-triangle text-xl"></i>
          <span>{{ strategyStore.error }}</span>
        </div>
      </template>
    </Card>

    <div v-if="strategyStore.result" class="space-y-6">
      <!-- Primary Recommendation Summary -->
      <Card>
        <template #header>
          <div class="p-4 border-b border-border">
            <h2 class="text-xl font-bold text-on-surface flex items-center gap-2">
              <i class="pi pi-chart-line text-primary"></i>
              Strategy Recommendation for {{ strategyStore.result.ticker }}
            </h2>
          </div>
        </template>
        <template #content>
          <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div class="space-y-2">
              <p class="text-xs text-on-surface uppercase tracking-wide">Action</p>
              <StatusBadge :status="strategyStore.result.action" type="recommendation" class="text-lg px-4 py-2" />
            </div>
            <div class="space-y-2">
              <p class="text-xs text-on-surface uppercase tracking-wide">Confidence</p>
              <StatusBadge :status="strategyStore.result.confidence" type="confidence" class="text-lg px-4 py-2" />
            </div>
            <div class="space-y-2">
              <p class="text-xs text-on-surface uppercase tracking-wide">Risk Level</p>
              <StatusBadge :status="strategyStore.result.risk_level" type="risk" class="text-lg px-4 py-2" />
            </div>
            <div class="space-y-2">
              <p class="text-xs text-on-surface uppercase tracking-wide">Timeframe</p>
              <span class="text-lg text-on-surface font-semibold">{{ strategyStore.result.timeframe }}</span>
            </div>
          </div>

          <!-- Key Metrics Row -->
          <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <MetricCard
              title="Entry Price"
              :value="`$${strategyStore.result.entry_price?.toFixed(2) || 'N/A'}`"
              icon="pi pi-dollar"
            />
            <MetricCard
              title="Expected Return"
              :value="`${strategyStore.result.expected_return_pct?.toFixed(2) || 0}%`"
              icon="pi pi-percentage"
               :trend="(strategyStore.result.expected_return_pct ?? 0) > 0 ? 'up' : (strategyStore.result.expected_return_pct ?? 0) < 0 ? 'down' : 'neutral'"
            />
            <MetricCard
              title="Overall Score"
              :value="strategyStore.result.key_metrics?.overall_score || 'N/A'"
              icon="pi pi-star"
            />
            <MetricCard
              title="Target Date"
              :value="strategyStore.result.target_date || 'N/A'"
              icon="pi pi-calendar"
            />
          </div>
        </template>
      </Card>

      <!-- Rationale -->
      <Card>
        <template #header>
          <div class="p-4 border-b border-border">
            <h3 class="text-lg font-bold text-on-surface flex items-center gap-2">
              <i class="pi pi-lightbulb text-yellow-400"></i>
              Analysis Rationale
            </h3>
          </div>
        </template>
        <template #content>
          <div class="space-y-3">
            <div
              v-for="(reason, idx) in strategyStore.result.rationale"
              :key="idx"
              class="flex items-start gap-3 p-3 bg-surface-overlay rounded-lg"
            >
              <i class="pi pi-info-circle text-blue-400 mt-0.5"></i>
              <span class="text-on-surface-muted">{{ reason }}</span>
            </div>
          </div>
        </template>
      </Card>

      <!-- Key Metrics Analysis -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Trend Analysis -->
        <Card>
          <template #header>
            <div class="p-4 border-b border-border">
              <h3 class="text-lg font-bold text-on-surface flex items-center gap-2">
                <i class="pi pi-chart-line text-green-400"></i>
                Trend Analysis
              </h3>
            </div>
          </template>
          <template #content>
            <div class="space-y-4">
              <div class="grid grid-cols-2 gap-4">
                <div class="space-y-2">
                  <p class="text-xs text-on-surface uppercase tracking-wide">Short Term</p>
                  <StatusBadge :status="strategyStore.result.key_metrics?.trend?.short_term || 'N/A'" type="recommendation" />
                </div>
                <div class="space-y-2">
                  <p class="text-xs text-on-surface uppercase tracking-wide">Medium Term</p>
                  <StatusBadge :status="strategyStore.result.key_metrics?.trend?.medium_term || 'N/A'" type="recommendation" />
                </div>
                <div class="space-y-2">
                  <p class="text-xs text-on-surface uppercase tracking-wide">Long Term</p>
                  <StatusBadge :status="strategyStore.result.key_metrics?.trend?.long_term || 'N/A'" type="recommendation" />
                </div>
                <div class="space-y-2">
                  <p class="text-xs text-on-surface uppercase tracking-wide">Trend Slope</p>
                  <span class="text-on-surface font-semibold">{{ strategyStore.result.key_metrics?.trend?.slope_pct?.toFixed(2) || 'N/A' }}%</span>
                </div>
              </div>

              <div class="grid grid-cols-2 gap-4 pt-4 border-t border-border">
                <div class="flex items-center justify-between">
                  <span class="text-sm text-on-surface-muted">Above SMA 50</span>
                  <i :class="strategyStore.result.key_metrics?.trend?.above_sma_50 ? 'pi pi-check text-success' : 'pi pi-times text-error'"></i>
                </div>
                <div class="flex items-center justify-between">
                  <span class="text-sm text-on-surface-muted">Above SMA 200</span>
                  <i :class="strategyStore.result.key_metrics?.trend?.above_sma_200 ? 'pi pi-check text-success' : 'pi pi-times text-error'"></i>
                </div>
              </div>
            </div>
          </template>
        </Card>

        <!-- Momentum Analysis -->
        <Card>
          <template #header>
            <div class="p-4 border-b border-border">
              <h3 class="text-lg font-bold text-on-surface flex items-center gap-2">
                <i class="pi pi-bolt text-orange-400"></i>
                Momentum Indicators
              </h3>
            </div>
          </template>
          <template #content>
            <div class="space-y-4">
              <div class="grid grid-cols-2 gap-4">
                <MetricCard
                  title="RSI"
                  :value="strategyStore.result.key_metrics?.momentum?.rsi?.toFixed(2) || 'N/A'"
                  icon="pi pi-gauge"
                  :subtitle="strategyStore.result.key_metrics?.momentum?.rsi_signal || ''"
                />
                <MetricCard
                  title="10-Day ROC"
                  :value="`${strategyStore.result.key_metrics?.momentum?.roc_10_day?.toFixed(2) || 'N/A'}%`"
                  icon="pi pi-percentage"
                  :trend="strategyStore.result.key_metrics?.momentum?.roc_10_day > 0 ? 'up' : strategyStore.result.key_metrics?.momentum?.roc_10_day < 0 ? 'down' : 'neutral'"
                />
              </div>

              <div class="pt-4 border-t border-border">
                <div class="flex items-center justify-between">
                  <span class="text-sm text-on-surface-muted">MACD Signal</span>
                  <span class="text-on-surface font-medium">{{ strategyStore.result.key_metrics?.momentum?.macd_signal || 'N/A' }}</span>
                </div>
              </div>
            </div>
          </template>
        </Card>

        <!-- Volatility Analysis -->
        <Card>
          <template #header>
            <div class="p-4 border-b border-border">
              <h3 class="text-lg font-bold text-on-surface flex items-center gap-2">
                <i class="pi pi-wave-pulse text-purple-400"></i>
                Volatility Analysis
              </h3>
            </div>
          </template>
          <template #content>
            <div class="space-y-4">
              <div class="grid grid-cols-2 gap-4">
                <MetricCard
                  title="20-Day Volatility"
                  :value="`${strategyStore.result.key_metrics?.volatility?.volatility_20d?.toFixed(2) || 'N/A'}%`"
                  icon="pi pi-chart-bar"
                />
                <MetricCard
                  title="60-Day Volatility"
                  :value="`${strategyStore.result.key_metrics?.volatility?.volatility_60d?.toFixed(2) || 'N/A'}%`"
                  icon="pi pi-chart-bar"
                />
              </div>

              <div class="grid grid-cols-2 gap-4 pt-4 border-t border-border">
                <div class="flex items-center justify-between">
                  <span class="text-sm text-on-surface-muted">Risk Level</span>
                  <StatusBadge :status="strategyStore.result.key_metrics?.volatility?.risk_level || 'N/A'" type="risk" />
                </div>
                <div class="flex items-center justify-between">
                  <span class="text-sm text-on-surface-muted">Volatility Increasing</span>
                  <i :class="strategyStore.result.key_metrics?.volatility?.vol_increasing ? 'pi pi-arrow-up text-error' : 'pi pi-arrow-down text-success'"></i>
                </div>
              </div>
            </div>
          </template>
        </Card>

        <!-- Risk Metrics -->
        <Card>
          <template #header>
            <div class="p-4 border-b border-border">
              <h3 class="text-lg font-bold text-on-surface flex items-center gap-2">
                <i class="pi pi-shield text-red-400"></i>
                Risk Metrics
              </h3>
            </div>
          </template>
          <template #content>
            <div class="space-y-4">
              <div class="grid grid-cols-1 gap-4">
                <MetricCard
                  title="Max Drawdown"
                  :value="`${strategyStore.result.key_metrics?.risk_metrics?.max_drawdown?.toFixed(2) || 'N/A'}%`"
                  icon="pi pi-arrow-down"
                  trend="down"
                />
                <MetricCard
                  title="Sharpe Ratio"
                  :value="strategyStore.result.key_metrics?.risk_metrics?.sharpe_ratio?.toFixed(3) || 'N/A'"
                  icon="pi pi-star"
                />
                <MetricCard
                  title="VaR (95%)"
                  :value="`${strategyStore.result.key_metrics?.risk_metrics?.var_95?.toFixed(2) || 'N/A'}%`"
                  icon="pi pi-exclamation-triangle"
                />
              </div>
            </div>
          </template>
        </Card>
      </div>

      <!-- Price Predictions -->
      <Card>
        <template #header>
          <div class="p-4 border-b border-border">
            <h3 class="text-lg font-bold text-on-surface flex items-center gap-2">
              <i class="pi pi-eye text-cyan-400"></i>
              Price Predictions
            </h3>
            <p class="text-sm text-on-surface-muted mt-1">AI-powered price forecasts for different time horizons</p>
          </div>
        </template>
        <template #content>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <!-- Short Term -->
            <div class="space-y-4">
              <div class="flex items-center gap-2">
                <h4 class="text-md font-semibold text-on-surface">Short Term (5 days)</h4>
                <StatusBadge :status="strategyStore.result.predictions?.short_term?.confidence || 'N/A'" type="confidence" />
              </div>

              <div class="space-y-3">
                <MetricCard
                  title="Predicted Price"
                  :value="`$${strategyStore.result.predictions?.short_term?.predicted_price?.toFixed(2) || 'N/A'}`"
                  icon="pi pi-dollar"
                />
                <MetricCard
                  title="Expected Change"
                  :value="`${strategyStore.result.predictions?.short_term?.predicted_change_pct?.toFixed(2) || 'N/A'}%`"
                  icon="pi pi-percentage"
                  :trend="strategyStore.result.predictions?.short_term?.predicted_change_pct > 0 ? 'up' : strategyStore.result.predictions?.short_term?.predicted_change_pct < 0 ? 'down' : 'neutral'"
                />
                <div class="text-xs text-on-surface-muted">
                  <p class="font-medium text-on-surface mb-1">Target Date:</p>
                  <p>{{ strategyStore.result.predictions?.short_term?.target_date || 'N/A' }}</p>
                </div>
              </div>

              <div v-if="strategyStore.result.predictions?.short_term?.reasoning" class="space-y-2">
                <p class="text-xs text-on-surface uppercase tracking-wide">Reasoning</p>
                <ul class="space-y-1">
                  <li
                    v-for="(reason, idx) in strategyStore.result.predictions.short_term.reasoning"
                    :key="idx"
                    class="text-xs text-on-surface-muted flex items-start gap-2"
                  >
                    <i class="pi pi-circle-fill text-on-surface-faint mt-0.5"></i>
                    <span>{{ reason }}</span>
                  </li>
                </ul>
              </div>
            </div>

            <!-- Mid Term -->
            <div class="space-y-4">
              <div class="flex items-center gap-2">
                <h4 class="text-md font-semibold text-on-surface">Mid Term (30 days)</h4>
                <StatusBadge :status="strategyStore.result.predictions?.mid_term?.confidence || 'N/A'" type="confidence" />
              </div>

              <div class="space-y-3">
                <MetricCard
                  title="Predicted Price"
                  :value="`$${strategyStore.result.predictions?.mid_term?.predicted_price?.toFixed(2) || 'N/A'}`"
                  icon="pi pi-dollar"
                />
                <MetricCard
                  title="Expected Change"
                  :value="`${strategyStore.result.predictions?.mid_term?.predicted_change_pct?.toFixed(2) || 'N/A'}%`"
                  icon="pi pi-percentage"
                  :trend="strategyStore.result.predictions?.mid_term?.predicted_change_pct > 0 ? 'up' : strategyStore.result.predictions?.mid_term?.predicted_change_pct < 0 ? 'down' : 'neutral'"
                />
                <div class="text-xs text-on-surface-muted">
                  <p class="font-medium text-on-surface mb-1">Target Date:</p>
                  <p>{{ strategyStore.result.predictions?.mid_term?.target_date || 'N/A' }}</p>
                </div>
              </div>

              <div v-if="strategyStore.result.predictions?.mid_term?.reasoning" class="space-y-2">
                <p class="text-xs text-on-surface uppercase tracking-wide">Reasoning</p>
                <ul class="space-y-1">
                  <li
                    v-for="(reason, idx) in strategyStore.result.predictions.mid_term.reasoning"
                    :key="idx"
                    class="text-xs text-on-surface-muted flex items-start gap-2"
                  >
                    <i class="pi pi-circle-fill text-on-surface-faint mt-0.5"></i>
                    <span>{{ reason }}</span>
                  </li>
                </ul>
              </div>
            </div>

            <!-- Long Term -->
            <div class="space-y-4">
              <div class="flex items-center gap-2">
                <h4 class="text-md font-semibold text-on-surface">Long Term (90 days)</h4>
                <StatusBadge :status="strategyStore.result.predictions?.long_term?.confidence || 'N/A'" type="confidence" />
              </div>

              <div class="space-y-3">
                <MetricCard
                  title="Predicted Price"
                  :value="`$${strategyStore.result.predictions?.long_term?.predicted_price?.toFixed(2) || 'N/A'}`"
                  icon="pi pi-dollar"
                />
                <MetricCard
                  title="Expected Change"
                  :value="`${strategyStore.result.predictions?.long_term?.predicted_change_pct?.toFixed(2) || 'N/A'}%`"
                  icon="pi pi-percentage"
                  :trend="strategyStore.result.predictions?.long_term?.predicted_change_pct > 0 ? 'up' : strategyStore.result.predictions?.long_term?.predicted_change_pct < 0 ? 'down' : 'neutral'"
                />
                <div class="text-xs text-on-surface-muted">
                  <p class="font-medium text-on-surface mb-1">Target Date:</p>
                  <p>{{ strategyStore.result.predictions?.long_term?.target_date || 'N/A' }}</p>
                </div>
              </div>

              <div v-if="strategyStore.result.predictions?.long_term?.reasoning" class="space-y-2">
                <p class="text-xs text-on-surface uppercase tracking-wide">Reasoning</p>
                <ul class="space-y-1">
                  <li
                    v-for="(reason, idx) in strategyStore.result.predictions.long_term.reasoning"
                    :key="idx"
                    class="text-xs text-on-surface-muted flex items-start gap-2"
                  >
                    <i class="pi pi-circle-fill text-on-surface-faint mt-0.5"></i>
                    <span>{{ reason }}</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </template>
      </Card>

      <!-- Optimal Entry Moment -->
      <Card v-if="strategyStore.result.optimal_moment" class="bg-gradient-to-r from-primary/10 to-secondary/10 border border-primary/30">
        <template #header>
          <div class="p-4 border-b border-border">
            <h3 class="text-lg font-bold text-on-surface flex items-center gap-2">
              <i class="pi pi-clock text-primary"></i>
              Optimal Entry Moment
            </h3>
             <p class="text-sm text-on-surface-muted mt-1">Heuristic timing context, not a guaranteed entry signal</p>
          </div>
        </template>
        <template #content>
          <div class="space-y-6">
            <!-- Optimal Action Summary -->
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div class="space-y-2">
                <p class="text-xs text-on-surface uppercase tracking-wide">Recommended Action</p>
                <StatusBadge :status="strategyStore.result.optimal_moment?.action || 'N/A'" type="recommendation" class="text-lg px-4 py-2" />
              </div>
              <MetricCard
                title="Expected Price"
                :value="`$${strategyStore.result.optimal_moment?.expected_price?.toFixed(2) || 'N/A'}`"
                icon="pi pi-dollar"
              />
              <MetricCard
                title="Expected Return"
                :value="`${strategyStore.result.optimal_moment?.expected_return_pct?.toFixed(2) || 'N/A'}%`"
                icon="pi pi-percentage"
                 :trend="(strategyStore.result.optimal_moment?.expected_return_pct ?? 0) > 0 ? 'up' : (strategyStore.result.optimal_moment?.expected_return_pct ?? 0) < 0 ? 'down' : 'neutral'"
              />
              <div class="space-y-2">
                <p class="text-xs text-on-surface uppercase tracking-wide">Confidence</p>
                <StatusBadge :status="strategyStore.result.optimal_moment?.confidence || 'N/A'" type="confidence" class="text-lg px-4 py-2" />
              </div>
            </div>

            <!-- Timing Details -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-surface-overlay rounded-lg">
              <div class="text-center">
                <p class="text-xs text-on-surface uppercase tracking-wide mb-1">Optimal Date</p>
                <p class="text-lg font-bold text-on-surface">{{ strategyStore.result.optimal_moment?.optimal_date || 'N/A' }}</p>
              </div>
              <div class="text-center">
                <p class="text-xs text-on-surface uppercase tracking-wide mb-1">Days from Now</p>
                <p class="text-lg font-bold text-on-surface">{{ strategyStore.result.optimal_moment?.days_from_now || 'N/A' }}</p>
              </div>
              <div class="text-center">
                <p class="text-xs text-on-surface uppercase tracking-wide mb-1">Risk/Reward Ratio</p>
                <p class="text-lg font-bold text-on-surface">{{ strategyStore.result.optimal_moment?.risk_reward_ratio?.toFixed(2) || 'N/A' }}</p>
              </div>
            </div>

            <!-- Supporting Signals -->
            <div v-if="strategyStore.result.optimal_moment?.supporting_signals" class="space-y-4">
              <h4 class="text-md font-semibold text-on-surface flex items-center gap-2">
                <i class="pi pi-check-circle text-success"></i>
                Supporting Signals
              </h4>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="space-y-3">
                  <div class="flex justify-between items-center">
                    <span class="text-sm text-on-surface-muted">Signal Type</span>
                    <span class="text-on-surface font-medium">{{ strategyStore.result.optimal_moment.supporting_signals.candidate_type || 'N/A' }}</span>
                  </div>
                  <div class="flex justify-between items-center">
                    <span class="text-sm text-on-surface-muted">Win Rate</span>
                    <span class="text-on-surface font-medium">{{ strategyStore.result.optimal_moment.supporting_signals.win_rate?.toFixed(1) || 'N/A' }}%</span>
                  </div>
                  <div class="flex justify-between items-center">
                    <span class="text-sm text-on-surface-muted">Signal Score</span>
                    <span class="text-on-surface font-medium">{{ strategyStore.result.optimal_moment.supporting_signals.score?.toFixed(2) || 'N/A' }}</span>
                  </div>
                </div>

                <div class="space-y-3">
                  <div class="flex justify-between items-center">
                    <span class="text-sm text-on-surface-muted">Total Candidates</span>
                    <span class="text-on-surface font-medium">{{ strategyStore.result.optimal_moment.supporting_signals.all_candidates_count || 'N/A' }}</span>
                  </div>
                  <div class="flex justify-between items-center">
                    <span class="text-sm text-on-surface-muted">Hold Period</span>
                    <span class="text-on-surface font-medium">{{ strategyStore.result.optimal_moment.supporting_signals.optimal_hold_period || 'N/A' }} days</span>
                  </div>
                  <div class="flex justify-between items-center">
                    <span class="text-sm text-on-surface-muted">Trend Alignment</span>
                    <i :class="strategyStore.result.optimal_moment.supporting_signals.trend_alignment ? 'pi pi-check text-success' : 'pi pi-times text-error'"></i>
                  </div>
                </div>
              </div>
            </div>

            <!-- Reasoning -->
            <div v-if="strategyStore.result.optimal_moment?.reasoning" class="space-y-3">
              <h4 class="text-md font-semibold text-on-surface">Strategic Reasoning</h4>
              <div class="space-y-2">
                <div
                  v-for="(reason, idx) in strategyStore.result.optimal_moment.reasoning"
                  :key="idx"
                  class="flex items-start gap-3 p-3 bg-surface-overlay rounded-lg"
                >
                  <i class="pi pi-info-circle text-primary mt-0.5"></i>
                  <span class="text-on-surface-muted">{{ reason }}</span>
                </div>
              </div>
            </div>
          </div>
        </template>
      </Card>
    </div>
  </div>
</template>
