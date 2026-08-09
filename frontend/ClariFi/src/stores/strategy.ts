import { defineStore } from 'pinia'
import axios from 'axios'
import { ref } from 'vue'

export interface StrategyResult {
    ticker: string
    action: string
    timeframe: string
    target_date: string
    confidence: string
    rationale: string[]
    entry_price: number
    expected_return_pct: number | null
    risk_level: string
    key_metrics: {
        overall_score: number
        trend: {
            short_term: string
            medium_term: string
            long_term: string | null
            slope_pct: number
            above_sma_50: boolean
            above_sma_200: boolean | null
        }
        momentum: {
            rsi: number
            rsi_signal: string
            macd_signal?: string
            roc_10_day: number
        }
        volatility: {
            volatility_20d: number
            volatility_60d: number
            vol_increasing: boolean
            risk_level: string
        }
        risk_metrics: {
            max_drawdown: number
            sharpe_ratio: number
            var_95: number
        }
    }
    predictions: {
        short_term: {
            timeframe: string
            horizon_days: number
            target_date: string
            predicted_price: number
            predicted_change_pct: number
            confidence: string
            reasoning: string[]
        }
        mid_term: {
            timeframe: string
            horizon_days: number
            target_date: string
            predicted_price: number
            predicted_change_pct: number
            confidence: string
            reasoning: string[]
        }
        long_term: {
            timeframe: string
            horizon_days: number
            target_date: string
            predicted_price: number
            predicted_change_pct: number
            confidence: string
            reasoning: string[]
        }
    }
    optimal_moment: {
        action: string
        optimal_date: string
        days_from_now: number
        expected_price: number
        expected_return_pct: number
        confidence: string
        reasoning: string[]
        supporting_signals: {
            reason?: string
            candidate_type?: string
            all_candidates_count?: number
            score?: number
            win_rate?: number
            trend_alignment?: boolean
            volatility?: number
            max_drawdown?: number
            optimal_hold_period?: number
        }
        risk_reward_ratio: number
    } | null
}

export const useStrategyStore = defineStore('strategy', () => {
    const result = ref<StrategyResult | null>(null)
    const isLoading = ref(false)
    const error = ref<string | null>(null)

    async function analyzeStrategy(ticker: string, period: string = '1y') {
        isLoading.value = true
        error.value = null
        result.value = null

        try {
            const response = await axios.post('/api/v1/strategy', { ticker, period })
            const data = response.data

            if (data?.status === 'error' || data?.status === 'partial') {
                throw new Error(data?.detail || data?.errors?.[0]?.message || 'Strategy analysis failed')
            }

            const strategy = data.data?.strategy || data.strategy || data

            result.value = strategy as StrategyResult
        } catch (e: unknown) {
            error.value = axios.isAxiosError(e)
                ? e.response?.data?.detail || e.message
                : e instanceof Error ? e.message : 'Failed to analyze strategy'
        } finally {
            isLoading.value = false
        }
    }

    return {
        result,
        isLoading,
        error,
        analyzeStrategy
    }
})
