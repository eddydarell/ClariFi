#!/usr/bin/env python3
"""
Event Correlation Module
Correlates market movements with news events and external factors.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import json
import re
from typing import Dict, List, Optional


class EventCorrelator:
    def __init__(self):
        self.major_events = self._load_major_events()
        self.news_cache = {}

    def _load_major_events(self):
        """
        Load major historical events that typically affect markets.
        This is a starter dataset - can be expanded.
        """
        return {
            '2020-03-11': {'event': 'WHO declares COVID-19 pandemic', 'category': 'health', 'impact': 'negative'},
            '2020-03-15': {'event': 'Federal Reserve cuts rates to near zero', 'category': 'monetary_policy', 'impact': 'positive'},
            '2020-03-27': {'event': 'CARES Act signed ($2 trillion stimulus)', 'category': 'fiscal_policy', 'impact': 'positive'},
            '2021-01-06': {'event': 'Capitol riots', 'category': 'political', 'impact': 'negative'},
            '2021-03-11': {'event': 'American Rescue Plan Act signed', 'category': 'fiscal_policy', 'impact': 'positive'},
            '2022-02-24': {'event': 'Russia invades Ukraine', 'category': 'geopolitical', 'impact': 'negative'},
            '2022-03-16': {'event': 'Federal Reserve raises rates 0.25%', 'category': 'monetary_policy', 'impact': 'negative'},
            '2023-03-10': {'event': 'Silicon Valley Bank collapse', 'category': 'financial', 'impact': 'negative'},
            '2023-05-03': {'event': 'Federal Reserve raises rates to 5.25%', 'category': 'monetary_policy', 'impact': 'negative'},
            '2024-01-01': {'event': 'AI boom continues - ChatGPT anniversary', 'category': 'technology', 'impact': 'positive'},
            '2024-03-20': {'event': 'Federal Reserve maintains rates', 'category': 'monetary_policy', 'impact': 'neutral'},
            '2024-11-05': {'event': 'US Presidential Election 2024', 'category': 'political', 'impact': 'volatile'},
            '2025-01-20': {'event': 'Presidential Inauguration 2025', 'category': 'political', 'impact': 'neutral'},
        }

    def correlate_events_with_movements(self, stock_data_dict, lookback_days=5, lookahead_days=5):
        """
        Correlate major events with stock movements.

        Args:
            stock_data_dict (dict): Dictionary of ticker -> DataFrame
            lookback_days (int): Days before event to analyze
            lookahead_days (int): Days after event to analyze

        Returns:
            dict: Event correlation analysis
        """
        correlations = {}

        for event_date, event_info in self.major_events.items():
            event_dt = pd.to_datetime(event_date)

            correlations[event_date] = {
                'event_info': event_info,
                'stock_impacts': {}
            }

            for ticker, data in stock_data_dict.items():
                impact = self._analyze_event_impact(data, event_dt, lookback_days, lookahead_days)
                if impact:
                    correlations[event_date]['stock_impacts'][ticker] = impact

        return correlations

    def _analyze_event_impact(self, stock_data, event_date, lookback_days, lookahead_days):
        """Analyze the impact of a specific event on a stock."""
        try:
            # Find the closest trading day to the event
            available_dates = stock_data.index
            event_idx = available_dates.get_indexer([event_date], method='nearest')[0]

            if event_idx == -1:
                return None

            actual_event_date = available_dates[event_idx]

            # Get before and after periods
            start_idx = max(0, event_idx - lookback_days)
            end_idx = min(len(available_dates) - 1, event_idx + lookahead_days)

            if start_idx >= end_idx or event_idx <= start_idx or event_idx >= end_idx:
                return None

            before_data = stock_data.iloc[start_idx:event_idx]
            after_data = stock_data.iloc[event_idx:end_idx + 1]

            if len(before_data) == 0 or len(after_data) == 0:
                return None

            # Calculate returns - ensure all values are native Python types
            before_return = float((before_data['Close'].iloc[-1] / before_data['Close'].iloc[0] - 1) * 100)
            after_return = float((after_data['Close'].iloc[-1] / after_data['Close'].iloc[0] - 1) * 100)
            event_day_return = float((stock_data['Close'].iloc[event_idx] / stock_data['Close'].iloc[event_idx - 1] - 1) * 100) if event_idx > 0 else 0.0

            # Calculate volatility - ensure all values are native Python types
            before_volatility = float(before_data['Close'].pct_change().std() * np.sqrt(252) * 100)
            after_volatility = float(after_data['Close'].pct_change().std() * np.sqrt(252) * 100)

            return {
                'actual_event_date': str(actual_event_date.strftime('%Y-%m-%d')),
                'before_return_pct': before_return,
                'after_return_pct': after_return,
                'event_day_return_pct': event_day_return,
                'before_volatility': before_volatility,
                'after_volatility': after_volatility,
                'volatility_change': float(after_volatility - before_volatility),
                'price_at_event': float(stock_data['Close'].iloc[event_idx])
            }

        except Exception as e:
            return None

    def identify_unusual_movements(self, stock_data_dict, threshold_std=2.0):
        """
        Identify unusual price movements that might correlate with events.

        Args:
            stock_data_dict (dict): Dictionary of ticker -> DataFrame
            threshold_std (float): Standard deviation threshold for unusual movements

        Returns:
            dict: Unusual movements for each ticker
        """
        unusual_movements = {}

        for ticker, data in stock_data_dict.items():
            returns = data['Close'].pct_change()
            mean_return = float(returns.mean())
            std_return = float(returns.std())

            # Find unusual movements
            unusual_dates = returns[
                (returns > mean_return + threshold_std * std_return) |
                (returns < mean_return - threshold_std * std_return)
            ]

            unusual_movements[ticker] = []

            for date, return_pct in unusual_dates.items():
                movement_info = {
                    'date': date.strftime('%Y-%m-%d'),
                    'return_pct': float(return_pct * 100),
                    'magnitude': 'Large Up' if return_pct > 0 else 'Large Down',
                    'z_score': float((return_pct - mean_return) / std_return),
                    'price': float(data.loc[date, 'Close']),
                    'volume': float(data.loc[date, 'Volume']) if 'Volume' in data.columns else None
                }

                # Check if this date is close to any known events
                movement_info['nearby_events'] = self._find_nearby_events(date)

                unusual_movements[ticker].append(movement_info)

        return unusual_movements

    def _find_nearby_events(self, target_date, window_days=7):
        """Find events within a window of the target date."""
        nearby_events = []
        target_dt = pd.to_datetime(target_date)

        for event_date, event_info in self.major_events.items():
            event_dt = pd.to_datetime(event_date)
            days_diff = abs((target_dt - event_dt).days)

            if days_diff <= window_days:
                nearby_events.append({
                    'event_date': event_date,
                    'days_diff': days_diff,
                    'event': event_info['event'],
                    'category': event_info['category'],
                    'expected_impact': event_info['impact']
                })

        return sorted(nearby_events, key=lambda x: x['days_diff'])

    def generate_event_summary(self, correlations, unusual_movements):
        """
        Generate a comprehensive summary of event-market correlations.

        Args:
            correlations (dict): Event correlation results
            unusual_movements (dict): Unusual movement results

        Returns:
            dict: Summary of findings
        """
        summary = {
            'most_impactful_events': [],
            'most_volatile_stocks': [],
            'consistent_patterns': [],
            'unexplained_movements': []
        }

        # Analyze most impactful events
        event_impacts = []
        for event_date, event_data in correlations.items():
            if not event_data['stock_impacts']:
                continue

            total_impact = 0
            impact_count = 0

            for ticker, impact_data in event_data['stock_impacts'].items():
                total_impact += abs(impact_data['after_return_pct'])
                impact_count += 1

            if impact_count > 0:
                avg_impact = float(total_impact / impact_count)
                event_impacts.append({
                    'event_date': event_date,
                    'event': event_data['event_info']['event'],
                    'category': event_data['event_info']['category'],
                    'avg_impact': avg_impact,
                    'affected_stocks': impact_count
                })

        summary['most_impactful_events'] = sorted(event_impacts, key=lambda x: x['avg_impact'], reverse=True)[:10]

        # Analyze most volatile stocks during events
        stock_volatilities = {}
        for event_date, event_data in correlations.items():
            for ticker, impact_data in event_data['stock_impacts'].items():
                if ticker not in stock_volatilities:
                    stock_volatilities[ticker] = []
                stock_volatilities[ticker].append(impact_data['volatility_change'])

        for ticker, volatility_changes in stock_volatilities.items():
            avg_volatility_change = float(np.mean(volatility_changes))
            summary['most_volatile_stocks'].append({
                'ticker': ticker,
                'avg_volatility_change': avg_volatility_change,
                'event_count': len(volatility_changes)
            })

        summary['most_volatile_stocks'] = sorted(summary['most_volatile_stocks'],
                                               key=lambda x: x['avg_volatility_change'], reverse=True)[:10]

        # Find unexplained movements (large movements without nearby events)
        for ticker, movements in unusual_movements.items():
            for movement in movements:
                if not movement['nearby_events']:  # No nearby events
                    summary['unexplained_movements'].append({
                        'ticker': ticker,
                        'date': movement['date'],
                        'return_pct': float(movement['return_pct']),
                        'magnitude': movement['magnitude']
                    })

        return summary

    def add_custom_event(self, date, event_description, category, expected_impact):
        """
        Add a custom event to the events database.

        Args:
            date (str): Event date in YYYY-MM-DD format
            event_description (str): Description of the event
            category (str): Category of the event
            expected_impact (str): Expected impact (positive/negative/neutral/volatile)
        """
        self.major_events[date] = {
            'event': event_description,
            'category': category,
            'impact': expected_impact
        }

        print(f"Added custom event: {date} - {event_description}")

    def get_events_by_category(self, category):
        """Get all events of a specific category."""
        return {date: info for date, info in self.major_events.items()
                if info['category'] == category}

    def get_events_in_period(self, start_date, end_date):
        """Get all events within a specific period."""
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)

        return {date: info for date, info in self.major_events.items()
                if start_dt <= pd.to_datetime(date) <= end_dt}
