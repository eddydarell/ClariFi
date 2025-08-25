#!/usr/bin/env python3
"""
Advanced Market Visualizer
Creates sophisticated visualizations for pattern analysis, correlations, and event impacts.
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime
import os


class AdvancedVisualizer:
    def __init__(self, output_dir="graphs"):
        self.output_dir = output_dir
        self.ensure_output_directory()

        # Set advanced styling
        plt.style.use('default')
        self.colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                      '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

    def ensure_output_directory(self):
        """Create output directory if it doesn't exist."""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def plot_correlation_heatmap(self, correlation_data, save=True, show=False):
        """
        Create an advanced correlation heatmap with annotations.

        Args:
            correlation_data (dict): Correlation analysis results
            save (bool): Whether to save the plot
            show (bool): Whether to show the plot

        Returns:
            str: Filepath if saved
        """
        if not correlation_data.get('correlation_stability'):
            print("No correlation data available for heatmap")
            return None

        # Prepare correlation matrix
        pairs = list(correlation_data['correlation_stability'].keys())
        tickers = set()
        for pair in pairs:
            ticker1, ticker2 = pair.split('-')
            tickers.add(ticker1)
            tickers.add(ticker2)

        tickers = sorted(list(tickers))
        n_tickers = len(tickers)

        if n_tickers < 2:
            print("Need at least 2 tickers for correlation heatmap")
            return None

        # Create correlation matrix
        corr_matrix = np.zeros((n_tickers, n_tickers))
        stability_matrix = np.zeros((n_tickers, n_tickers))

        for i, ticker1 in enumerate(tickers):
            for j, ticker2 in enumerate(tickers):
                if i == j:
                    corr_matrix[i, j] = 1.0
                    stability_matrix[i, j] = 1.0
                elif i < j:
                    pair_key = f"{ticker1}-{ticker2}"
                    if pair_key in correlation_data['correlation_stability']:
                        corr = correlation_data['correlation_stability'][pair_key]['mean_correlation']
                        stability = correlation_data['correlation_stability'][pair_key]['stability_score']
                        corr_matrix[i, j] = corr_matrix[j, i] = corr
                        stability_matrix[i, j] = stability_matrix[j, i] = stability

        # Create subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

        # Correlation heatmap
        sns.heatmap(corr_matrix, annot=True, fmt='.3f',
                   xticklabels=tickers, yticklabels=tickers,
                   cmap='RdBu_r', center=0, vmin=-1, vmax=1,
                   square=True, ax=ax1)
        ax1.set_title('Average Correlation Matrix', fontweight='bold')

        # Stability heatmap
        sns.heatmap(stability_matrix, annot=True, fmt='.3f',
                   xticklabels=tickers, yticklabels=tickers,
                   cmap='RdYlGn', vmin=0, vmax=1,
                   square=True, ax=ax2)
        ax2.set_title('Correlation Stability Matrix', fontweight='bold')

        plt.tight_layout()

        if save:
            filename = f"correlation_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.png"
            filepath = os.path.join(self.output_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            print(f"Correlation analysis saved: {filepath}")

        if show:
            plt.show()
        else:
            plt.close()

        return filepath if save else None

    def plot_rolling_correlations(self, correlation_data, save=True, show=False):
        """Plot rolling correlations over time."""
        rolling_corrs = correlation_data.get('rolling_correlations', {})

        if not rolling_corrs:
            print("No rolling correlation data available")
            return None

        n_pairs = len(rolling_corrs)
        if n_pairs == 0:
            return None

        # Calculate subplot layout
        cols = min(3, n_pairs)
        rows = (n_pairs + cols - 1) // cols

        fig, axes = plt.subplots(rows, cols, figsize=(5*cols, 4*rows))
        if n_pairs == 1:
            axes = [axes]
        elif rows == 1:
            axes = [axes] if cols == 1 else axes
        else:
            axes = axes.flatten()

        for i, (pair, correlation_series) in enumerate(rolling_corrs.items()):
            ax = axes[i] if n_pairs > 1 else axes[0]

            # Plot rolling correlation
            ax.plot(correlation_series.index, correlation_series.values,
                   linewidth=2, color=self.colors[i % len(self.colors)])
            ax.axhline(y=0, color='black', linestyle='--', alpha=0.5)
            ax.axhline(y=0.5, color='green', linestyle=':', alpha=0.7, label='Strong +')
            ax.axhline(y=-0.5, color='red', linestyle=':', alpha=0.7, label='Strong -')

            ax.set_title(f'{pair} Rolling Correlation')
            ax.set_ylabel('Correlation')
            ax.grid(True, alpha=0.3)
            ax.legend()

            # Format x-axis
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

        # Hide extra subplots
        for i in range(n_pairs, len(axes)):
            axes[i].set_visible(False)

        plt.tight_layout()

        if save:
            filename = f"rolling_correlations_{datetime.now().strftime('%Y%m%d_%H%M')}.png"
            filepath = os.path.join(self.output_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            print(f"Rolling correlations saved: {filepath}")

        if show:
            plt.show()
        else:
            plt.close()

        return filepath if save else None

    def plot_event_impact_analysis(self, event_correlations, save=True, show=False):
        """
        Visualize the impact of events on stock prices.

        Args:
            event_correlations (dict): Event correlation results
            save (bool): Whether to save the plot
            show (bool): Whether to show the plot

        Returns:
            str: Filepath if saved
        """
        if not event_correlations:
            print("No event correlation data available")
            return None

        # Prepare data for visualization
        events_with_impact = []
        for event_date, event_data in event_correlations.items():
            if event_data['stock_impacts']:
                events_with_impact.append((event_date, event_data))

        if not events_with_impact:
            print("No events with stock impact data found")
            return None

        # Sort by date
        events_with_impact.sort(key=lambda x: x[0])

        # Limit to most recent events for readability
        max_events = 15
        if len(events_with_impact) > max_events:
            events_with_impact = events_with_impact[-max_events:]

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12))

        # Plot 1: Event day returns
        event_dates = []
        event_labels = []
        returns_by_stock = {}

        for event_date, event_data in events_with_impact:
            event_dates.append(pd.to_datetime(event_date))
            event_labels.append(f"{event_date}\n{event_data['event_info']['event'][:30]}...")

            for ticker, impact_data in event_data['stock_impacts'].items():
                if ticker not in returns_by_stock:
                    returns_by_stock[ticker] = []
                returns_by_stock[ticker].append(impact_data['event_day_return_pct'])

        # Plot event day returns
        x_pos = np.arange(len(event_dates))
        width = 0.8 / len(returns_by_stock)

        for i, (ticker, returns) in enumerate(returns_by_stock.items()):
            ax1.bar(x_pos + i * width, returns, width,
                   label=ticker, alpha=0.8, color=self.colors[i % len(self.colors)])

        ax1.set_title('Event Day Returns by Stock', fontweight='bold', fontsize=14)
        ax1.set_ylabel('Return (%)')
        ax1.set_xticks(x_pos + width * (len(returns_by_stock) - 1) / 2)
        ax1.set_xticklabels([f"{date.strftime('%Y-%m-%d')}" for date in event_dates], rotation=45)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.axhline(y=0, color='black', linestyle='-', alpha=0.5)

        # Plot 2: Volatility changes
        volatility_changes_by_stock = {}
        for event_date, event_data in events_with_impact:
            for ticker, impact_data in event_data['stock_impacts'].items():
                if ticker not in volatility_changes_by_stock:
                    volatility_changes_by_stock[ticker] = []
                volatility_changes_by_stock[ticker].append(impact_data['volatility_change'])

        for i, (ticker, vol_changes) in enumerate(volatility_changes_by_stock.items()):
            ax2.bar(x_pos + i * width, vol_changes, width,
                   label=ticker, alpha=0.8, color=self.colors[i % len(self.colors)])

        ax2.set_title('Volatility Changes Around Events', fontweight='bold', fontsize=14)
        ax2.set_ylabel('Volatility Change (%)')
        ax2.set_xticks(x_pos + width * (len(volatility_changes_by_stock) - 1) / 2)
        ax2.set_xticklabels([f"{date.strftime('%Y-%m-%d')}" for date in event_dates], rotation=45)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=0, color='black', linestyle='-', alpha=0.5)

        plt.tight_layout()

        if save:
            filename = f"event_impact_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.png"
            filepath = os.path.join(self.output_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            print(f"Event impact analysis saved: {filepath}")

        if show:
            plt.show()
        else:
            plt.close()

        return filepath if save else None

    def plot_volatility_clustering(self, volatility_analysis, save=True, show=False):
        """
        Visualize volatility clustering patterns.

        Args:
            volatility_analysis (dict): Volatility analysis results
            save (bool): Whether to save the plot
            show (bool): Whether to show the plot

        Returns:
            str: Filepath if saved
        """
        if not volatility_analysis:
            print("No volatility analysis data available")
            return None

        n_stocks = len(volatility_analysis)
        cols = min(3, n_stocks)
        rows = (n_stocks + cols - 1) // cols

        fig, axes = plt.subplots(rows, cols, figsize=(5*cols, 4*rows))
        if n_stocks == 1:
            axes = [axes]
        elif rows == 1:
            axes = [axes] if cols == 1 else axes
        else:
            axes = axes.flatten()

        for i, (ticker, vol_data) in enumerate(volatility_analysis.items()):
            ax = axes[i] if n_stocks > 1 else axes[0]

            rolling_vol = vol_data['rolling_volatility']
            high_vol_periods = vol_data['high_volatility_periods']
            low_vol_periods = vol_data['low_volatility_periods']

            # Plot rolling volatility
            ax.plot(rolling_vol.index, rolling_vol.values, linewidth=1.5,
                   color='blue', alpha=0.7, label='Rolling Volatility')

            # Highlight high and low volatility periods
            ax.scatter(high_vol_periods.index, high_vol_periods.values,
                      color='red', s=20, alpha=0.8, label='High Volatility')
            ax.scatter(low_vol_periods.index, low_vol_periods.values,
                      color='green', s=20, alpha=0.8, label='Low Volatility')

            # Add average line
            ax.axhline(y=vol_data['avg_volatility'], color='orange',
                      linestyle='--', alpha=0.7, label='Average')

            ax.set_title(f'{ticker} Volatility Clustering\n'
                        f'Clustering Score: {vol_data["volatility_clustering_score"]:.3f}')
            ax.set_ylabel('Annualized Volatility (%)')
            ax.legend()
            ax.grid(True, alpha=0.3)

            # Format x-axis
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

        # Hide extra subplots
        for i in range(n_stocks, len(axes)):
            axes[i].set_visible(False)

        plt.tight_layout()

        if save:
            filename = f"volatility_clustering_{datetime.now().strftime('%Y%m%d_%H%M')}.png"
            filepath = os.path.join(self.output_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            print(f"Volatility clustering analysis saved: {filepath}")

        if show:
            plt.show()
        else:
            plt.close()

        return filepath if save else None

    def plot_support_resistance(self, support_resistance_data, stock_data, save=True, show=False):
        """
        Plot support and resistance levels on price charts.

        Args:
            support_resistance_data (dict): Support/resistance analysis results
            stock_data (DataFrame): Stock price data
            save (bool): Whether to save the plot
            show (bool): Whether to show the plot

        Returns:
            str: Filepath if saved
        """
        ticker = support_resistance_data['ticker']

        fig, ax = plt.subplots(figsize=(15, 10))

        # Plot price data
        ax.plot(stock_data.index, stock_data['Close'], linewidth=2,
               color='blue', label='Close Price')

        # Plot support levels
        support_levels = support_resistance_data['support_levels']
        for i, (price, date_str) in enumerate(zip(support_levels['prices'], support_levels['dates'])):
            ax.axhline(y=price, color='green', linestyle='--', alpha=0.7, linewidth=1)
            # Convert date string back to datetime for plotting
            date = pd.to_datetime(date_str)
            ax.plot(date, price, 'go', markersize=8, alpha=0.8)
            # Add text label for closest levels
            if i < 3:  # Only label first 3 levels to avoid clutter
                ax.text(stock_data.index[-1], price, f'S: ${price:.2f}',
                       verticalalignment='center', color='green', fontweight='bold')

        # Plot resistance levels
        resistance_levels = support_resistance_data['resistance_levels']
        for i, (price, date_str) in enumerate(zip(resistance_levels['prices'], resistance_levels['dates'])):
            ax.axhline(y=price, color='red', linestyle='--', alpha=0.7, linewidth=1)
            # Convert date string back to datetime for plotting
            date = pd.to_datetime(date_str)
            ax.plot(date, price, 'ro', markersize=8, alpha=0.8)
            # Add text label for closest levels
            if i < 3:  # Only label first 3 levels to avoid clutter
                ax.text(stock_data.index[-1], price, f'R: ${price:.2f}',
                       verticalalignment='center', color='red', fontweight='bold')

        # Add current price line
        current_price = support_resistance_data['current_price']
        ax.axhline(y=current_price, color='orange', linestyle='-', linewidth=2,
                  alpha=0.8, label=f'Current Price: ${current_price:.2f}')

        ax.set_title(f'{ticker} Support and Resistance Levels', fontweight='bold', fontsize=16)
        ax.set_ylabel('Price ($)')
        ax.legend()
        ax.grid(True, alpha=0.3)

        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

        plt.tight_layout()

        if save:
            filename = f"support_resistance_{ticker}_{datetime.now().strftime('%Y%m%d_%H%M')}.png"
            filepath = os.path.join(self.output_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            print(f"Support/resistance analysis saved: {filepath}")

        if show:
            plt.show()
        else:
            plt.close()

        return filepath if save else None
