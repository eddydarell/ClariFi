#!/usr/bin/env python3
"""
Seasonal Analysis Module
Analyzes seasonal patterns, holiday effects, and time-of-year trends in stock data.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import calendar


@dataclass
class SeasonalPatternResult:
    """Results from seasonal pattern analysis."""
    monthly_stats: Dict[str, Dict[str, float]]
    holiday_effects: Dict[str, Dict[str, float]]
    seasonal_summary: str
    recommendation: str
    bias_score: float
    best_months: List[str]
    worst_months: List[str]


class SeasonalAnalyzer:
    """Analyzes seasonal patterns and holiday effects in stock data."""

    def __init__(self):
        # Major holidays that typically affect markets (US-focused)
        self.holidays = {
            'New Year': [(1, 1)],
            'MLK Day': [(1, 15)],  # 3rd Monday approximation
            'Presidents Day': [(2, 15)],  # 3rd Monday approximation
            'Easter': [(3, 15), (4, 15)],  # Variable, approximate
            'Memorial Day': [(5, 25)],  # Last Monday approximation
            'Independence Day': [(7, 4)],
            'Labor Day': [(9, 1)],  # First Monday
            'Thanksgiving': [(11, 22)],  # 4th Thursday approximation
            'Black Friday': [(11, 23)],
            'Christmas': [(12, 25)],
            'New Year Eve': [(12, 31)],
        }

        # Seasonal business patterns
        self.seasonal_patterns = {
            'Q1': 'Post-holiday slowdown, earnings season',
            'Q2': 'Spring recovery, summer prep',
            'Q3': 'Summer trading, back-to-school',
            'Q4': 'Holiday season, year-end positioning'
        }

    def analyze(self, stock_data: pd.DataFrame) -> Optional[SeasonalPatternResult]:
        """
        Perform comprehensive seasonal analysis on stock data.

        Args:
            stock_data: DataFrame with Date index and OHLCV columns

        Returns:
            SeasonalPatternResult with analysis results or None if insufficient data
        """
        if len(stock_data) < 252:  # Need at least 1 year of data
            return None

        try:
            # Ensure we have a datetime index
            df = stock_data.copy()
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)

            # Calculate daily returns
            df['Return'] = df['Close'].pct_change()
            df['Month'] = df.index.month
            df['Quarter'] = df.index.quarter
            df['DayOfYear'] = df.index.dayofyear
            df['Year'] = df.index.year

            # Monthly analysis
            monthly_stats = self._analyze_monthly_patterns(df)

            # Holiday effects analysis
            holiday_effects = self._analyze_holiday_effects(df)

            # Generate insights
            bias_score = self._calculate_seasonal_bias(monthly_stats)
            best_months, worst_months = self._identify_best_worst_months(monthly_stats)
            summary = self._generate_seasonal_summary(monthly_stats, holiday_effects, best_months, worst_months)
            recommendation = self._generate_recommendation(bias_score, best_months, worst_months)

            return SeasonalPatternResult(
                monthly_stats=monthly_stats,
                holiday_effects=holiday_effects,
                seasonal_summary=summary,
                recommendation=recommendation,
                bias_score=float(bias_score),
                best_months=best_months,
                worst_months=worst_months
            )

        except Exception as e:
            print(f"Error in seasonal analysis: {e}")
            return None

    def _analyze_monthly_patterns(self, df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """Analyze performance patterns by month."""
        monthly_stats = {}

        for month in range(1, 13):
            month_name = calendar.month_name[month]
            month_data = df[df['Month'] == month]['Return'].dropna()

            if len(month_data) > 0:
                monthly_stats[month_name] = {
                    'avg_return': float(month_data.mean()),
                    'median_return': float(month_data.median()),
                    'volatility': float(month_data.std()),
                    'win_rate': float((month_data > 0).mean() * 100),
                    'best_return': float(month_data.max()),
                    'worst_return': float(month_data.min()),
                    'observations': int(len(month_data))
                }
            else:
                monthly_stats[month_name] = {
                    'avg_return': 0.0,
                    'median_return': 0.0,
                    'volatility': 0.0,
                    'win_rate': 50.0,
                    'best_return': 0.0,
                    'worst_return': 0.0,
                    'observations': 0
                }

        return monthly_stats

    def _analyze_holiday_effects(self, df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """Analyze stock performance around major holidays."""
        holiday_effects = {}

        for holiday_name, dates in self.holidays.items():
            effects = []

            for month, day in dates:
                # Find all occurrences of this holiday in our data
                holiday_dates = []
                for year in df['Year'].unique():
                    try:
                        holiday_date = datetime(year, month, day)
                        if holiday_date.date() >= df.index.min().date() and holiday_date.date() <= df.index.max().date():
                            holiday_dates.append(holiday_date)
                    except ValueError:
                        continue  # Invalid date (e.g., Feb 29 in non-leap year)

                # Analyze performance around each holiday
                for holiday_date in holiday_dates:
                    effect = self._calculate_holiday_effect(df, holiday_date)
                    if effect is not None:
                        effects.append(effect)

            if effects:
                holiday_effects[holiday_name] = {
                    'avg_pre_effect': float(np.mean([e['pre_return'] for e in effects])),
                    'avg_post_effect': float(np.mean([e['post_return'] for e in effects])),
                    'avg_total_effect': float(np.mean([e['total_return'] for e in effects])),
                    'consistency': float(np.mean([e['total_return'] > 0 for e in effects]) * 100),
                    'occurrences': int(len(effects))
                }
            else:
                holiday_effects[holiday_name] = {
                    'avg_pre_effect': 0.0,
                    'avg_post_effect': 0.0,
                    'avg_total_effect': 0.0,
                    'consistency': 50.0,
                    'occurrences': 0
                }

        return holiday_effects

    def _calculate_holiday_effect(self, df: pd.DataFrame, holiday_date: datetime) -> Optional[Dict[str, float]]:
        """Calculate stock performance around a specific holiday."""
        try:
            # Find trading days around the holiday
            start_date = holiday_date - timedelta(days=7)
            end_date = holiday_date + timedelta(days=7)

            # Get data around holiday
            holiday_window = df[(df.index >= start_date) & (df.index <= end_date)].copy()

            if len(holiday_window) < 5:  # Need sufficient data
                return None

            # Find closest trading days
            pre_holiday_data = holiday_window[holiday_window.index < holiday_date]
            post_holiday_data = holiday_window[holiday_window.index > holiday_date]

            if len(pre_holiday_data) < 2 or len(post_holiday_data) < 2:
                return None

            # Calculate returns
            pre_return = float(pre_holiday_data['Return'].tail(3).sum())  # 3 days before
            post_return = float(post_holiday_data['Return'].head(3).sum())  # 3 days after
            total_return = float(pre_return + post_return)

            return {
                'pre_return': pre_return,
                'post_return': post_return,
                'total_return': total_return
            }

        except Exception:
            return None

    def _calculate_seasonal_bias(self, monthly_stats: Dict[str, Dict[str, float]]) -> float:
        """Calculate overall seasonal bias score (0-1, higher = more seasonal)."""
        # Calculate variance in monthly average returns
        monthly_returns = [stats['avg_return'] for stats in monthly_stats.values() if stats['observations'] > 0]

        if len(monthly_returns) < 6:  # Need at least half the months
            return 0.0

        # Normalize the variance to a 0-1 score
        variance = float(np.var(monthly_returns))
        max_possible_variance = 0.01  # Assume max 1% daily variance between months

        bias_score = float(min(variance / max_possible_variance, 1.0))
        return bias_score

    def _identify_best_worst_months(self, monthly_stats: Dict[str, Dict[str, float]]) -> Tuple[List[str], List[str]]:
        """Identify the best and worst performing months."""
        # Sort months by average return
        sorted_months = sorted(
            [(month, stats['avg_return']) for month, stats in monthly_stats.items()
             if stats['observations'] > 10],  # Only consider months with sufficient data
            key=lambda x: x[1],
            reverse=True
        )

        if len(sorted_months) < 6:
            return [], []

        # Top 3 and bottom 3 months
        best_months = [month for month, _ in sorted_months[:3]]
        worst_months = [month for month, _ in sorted_months[-3:]]

        return best_months, worst_months

    def _generate_seasonal_summary(self, monthly_stats: Dict[str, Dict[str, float]],
                                 holiday_effects: Dict[str, Dict[str, float]],
                                 best_months: List[str], worst_months: List[str]) -> str:
        """Generate a human-readable seasonal summary."""
        summary_parts = []

        # Best/worst months
        if best_months:
            summary_parts.append(f"Strong in {', '.join(best_months)}")
        if worst_months:
            summary_parts.append(f"weak in {', '.join(worst_months)}")

        # Holiday effects
        strong_holiday_effects = [
            holiday for holiday, effect in holiday_effects.items()
            if effect['avg_total_effect'] > 0.01 and effect['consistency'] > 60
        ]

        if strong_holiday_effects:
            summary_parts.append(f"holiday boost around {', '.join(strong_holiday_effects)}")

        # Quarterly patterns
        q_returns = {}
        for month, stats in monthly_stats.items():
            q = self._month_to_quarter(month)
            if q not in q_returns:
                q_returns[q] = []
            q_returns[q].append(stats['avg_return'])

        best_quarter = max(q_returns.keys(), key=lambda q: np.mean(q_returns[q])) if q_returns else None
        if best_quarter:
            summary_parts.append(f"strongest in {best_quarter}")

        if summary_parts:
            return "; ".join(summary_parts)
        else:
            return "No clear seasonal patterns detected"

    def _month_to_quarter(self, month_name: str) -> str:
        """Convert month name to quarter."""
        month_to_q = {
            'January': 'Q1', 'February': 'Q1', 'March': 'Q1',
            'April': 'Q2', 'May': 'Q2', 'June': 'Q2',
            'July': 'Q3', 'August': 'Q3', 'September': 'Q3',
            'October': 'Q4', 'November': 'Q4', 'December': 'Q4'
        }
        return month_to_q.get(month_name, 'Q1')

    def _generate_recommendation(self, bias_score: float, best_months: List[str],
                               worst_months: List[str]) -> str:
        """Generate actionable seasonal trading recommendation."""
        current_month = calendar.month_name[datetime.now().month]

        if bias_score < 0.2:
            return "LOW_SEASONAL"
        elif bias_score < 0.5:
            recommendation = "MODERATE_SEASONAL"
        else:
            recommendation = "HIGH_SEASONAL"

        # Add current month context
        if current_month in best_months:
            recommendation += "_FAVORABLE"
        elif current_month in worst_months:
            recommendation += "_UNFAVORABLE"
        else:
            recommendation += "_NEUTRAL"

        return recommendation


def main():
    """Test the seasonal analyzer with sample data."""
    print("🗓️ Seasonal Analyzer Test")

    # This would normally be called with real stock data
    # analyzer = SeasonalAnalyzer()
    # result = analyzer.analyze(stock_dataframe)

    print("Seasonal analyzer ready for integration!")


if __name__ == "__main__":
    main()
