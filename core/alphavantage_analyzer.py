#!/usr/bin/env python3
"""
Alpha Vantage API Integration Module
Provides access to Alpha Vantage financial data and analysis endpoints.
"""

import os
import requests
import pandas as pd
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import time

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not available, continue without it
    pass


class AlphaVantageAnalyzer:
    """
    Alpha Vantage API client for financial data and analysis.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Alpha Vantage analyzer.

        Args:
            api_key: Alpha Vantage API key. If None, will look for ALPHA_VANTAGE_API_KEY
                    in environment variables (loaded from .env file if available)
        """
        self.api_key = api_key or os.getenv('ALPHA_VANTAGE_API_KEY')
        if not self.api_key:
            raise ValueError(
                "Alpha Vantage API key is required. "
                "Set ALPHA_VANTAGE_API_KEY in your .env file or environment variables, "
                "or pass api_key parameter directly."
            )

        self.base_url = "https://www.alphavantage.co/query"
        self.rate_limit_delay = 12  # Alpha Vantage free tier allows 5 calls/minute, so 12s delay

    def _make_request(self, function: str, **params) -> Dict[str, Any]:
        """
        Make a request to Alpha Vantage API with rate limiting.

        Args:
            function: Alpha Vantage function name
            **params: Additional parameters for the API call

        Returns:
            Dict containing the API response
        """
        params.update({
            'function': function,
            'apikey': self.api_key
        })

        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()

            # Check for API errors
            data = response.json()
            if 'Error Message' in data:
                raise ValueError(f"Alpha Vantage API Error: {data['Error Message']}")
            if 'Note' in data and 'rate limit' in data['Note'].lower():
                raise ValueError(f"Alpha Vantage API Rate Limit: {data['Note']}")

            return data

        except requests.exceptions.RequestException as e:
            raise ValueError(f"Request failed: {str(e)}")

    def get_news_sentiment(self, tickers: List[str] = None, topics: List[str] = None,
                          time_from: str = None, time_to: str = None, sort: str = "LATEST",
                          limit: int = 50) -> Dict[str, Any]:
        """
        Get news sentiment data from Alpha Vantage.

        Args:
            tickers: List of stock tickers to filter news for
            topics: List of topics to filter news for
            time_from: Start date in YYYYMMDDTHHMM format
            time_to: End date in YYYYMMDDTHHMM format
            sort: Sort order ("LATEST", "EARLIEST", "RELEVANCE")
            limit: Maximum number of news items to return

        Returns:
            Dict containing news sentiment analysis
        """
        params = {
            'sort': sort,
            'limit': str(limit)
        }

        if tickers:
            params['tickers'] = ','.join(tickers)
        if topics:
            params['topics'] = ','.join(topics)
        if time_from:
            params['time_from'] = time_from
        if time_to:
            params['time_to'] = time_to

        data = self._make_request('NEWS_SENTIMENT', **params)

        # Process and structure the response
        result = {
            'metadata': {
                'total_items': len(data.get('feed', [])),
                'sort_order': sort,
                'limit': limit,
                'tickers': tickers,
                'topics': topics,
                'time_range': {'from': time_from, 'to': time_to}
            },
            'feed': []
        }

        for item in data.get('feed', []):
            processed_item = {
                'title': item.get('title', ''),
                'url': item.get('url', ''),
                'time_published': item.get('time_published', ''),
                'authors': item.get('authors', []),
                'summary': item.get('summary', ''),
                'banner_image': item.get('banner_image'),
                'source': item.get('source', ''),
                'category_within_source': item.get('category_within_source', ''),
                'source_domain': item.get('source_domain', ''),
                'topics': item.get('topics', []),
                'overall_sentiment_score': item.get('overall_sentiment_score', 0),
                'overall_sentiment_label': item.get('overall_sentiment_label', ''),
                'ticker_sentiment': []
            }

            # Process ticker-specific sentiment
            for ticker_data in item.get('ticker_sentiment', []):
                processed_item['ticker_sentiment'].append({
                    'ticker': ticker_data.get('ticker', ''),
                    'relevance_score': ticker_data.get('relevance_score', ''),
                    'ticker_sentiment_score': ticker_data.get('ticker_sentiment_score', ''),
                    'ticker_sentiment_label': ticker_data.get('ticker_sentiment_label', '')
                })

            result['feed'].append(processed_item)

        return result

    def get_company_overview(self, symbol: str) -> Dict[str, Any]:
        """
        Get company overview data.

        Args:
            symbol: Stock ticker symbol

        Returns:
            Dict containing company overview information
        """
        data = self._make_request('OVERVIEW', symbol=symbol)

        return {
            'symbol': data.get('Symbol', ''),
            'name': data.get('Name', ''),
            'description': data.get('Description', ''),
            'exchange': data.get('Exchange', ''),
            'currency': data.get('Currency', ''),
            'country': data.get('Country', ''),
            'sector': data.get('Sector', ''),
            'industry': data.get('Industry', ''),
            'address': data.get('Address', ''),
            'full_time_employees': data.get('FullTimeEmployees', ''),
            'fiscal_year_end': data.get('FiscalYearEnd', ''),
            'latest_quarter': data.get('LatestQuarter', ''),
            'market_capitalization': data.get('MarketCapitalization', ''),
            'ebitda': data.get('EBITDA', ''),
            'pe_ratio': data.get('PERatio', ''),
            'peg_ratio': data.get('PEGRatio', ''),
            'book_value': data.get('BookValue', ''),
            'dividend_per_share': data.get('DividendPerShare', ''),
            'dividend_yield': data.get('DividendYield', ''),
            'eps': data.get('EPS', ''),
            'revenue_per_share_ttm': data.get('RevenuePerShareTTM', ''),
            'profit_margin': data.get('ProfitMargin', ''),
            'operating_margin_ttm': data.get('OperatingMarginTTM', ''),
            'return_on_assets_ttm': data.get('ReturnOnAssetsTTM', ''),
            'return_on_equity_ttm': data.get('ReturnOnEquityTTM', ''),
            'revenue_ttm': data.get('RevenueTTM', ''),
            'gross_profit_ttm': data.get('GrossProfitTTM', ''),
            'diluted_eps_ttm': data.get('DilutedEPSTTM', ''),
            'quarterly_earnings_growth_yoy': data.get('QuarterlyEarningsGrowthYOY', ''),
            'quarterly_revenue_growth_yoy': data.get('QuarterlyRevenueGrowthYOY', ''),
            'analyst_target_price': data.get('AnalystTargetPrice', ''),
            'analyst_rating_strong_buy': data.get('AnalystRatingStrongBuy', ''),
            'analyst_rating_buy': data.get('AnalystRatingBuy', ''),
            'analyst_rating_hold': data.get('AnalystRatingHold', ''),
            'analyst_rating_sell': data.get('AnalystRatingSell', ''),
            'analyst_rating_strong_sell': data.get('AnalystRatingStrongSell', ''),
            'trailing_pe': data.get('TrailingPE', ''),
            'forward_pe': data.get('ForwardPE', ''),
            'price_to_sales_ratio_ttm': data.get('PriceToSalesRatioTTM', ''),
            'price_to_book_ratio': data.get('PriceToBookRatio', ''),
            'ev_to_revenue': data.get('EVToRevenue', ''),
            'ev_to_ebitda': data.get('EVToEBITDA', ''),
            'beta': data.get('Beta', ''),
            '52_week_high': data.get('52WeekHigh', ''),
            '52_week_low': data.get('52WeekLow', ''),
            '50_day_moving_average': data.get('50DayMovingAverage', ''),
            '200_day_moving_average': data.get('200DayMovingAverage', ''),
            'shares_outstanding': data.get('SharesOutstanding', ''),
            'dividend_date': data.get('DividendDate', ''),
            'ex_dividend_date': data.get('ExDividendDate', '')
        }

    def get_income_statement(self, symbol: str, annual: bool = True) -> Dict[str, Any]:
        """
        Get income statement data.

        Args:
            symbol: Stock ticker symbol
            annual: If True, get annual data; if False, get quarterly

        Returns:
            Dict containing income statement data
        """
        function = 'INCOME_STATEMENT'
        data = self._make_request(function, symbol=symbol)

        return data

    def get_balance_sheet(self, symbol: str, annual: bool = True) -> Dict[str, Any]:
        """
        Get balance sheet data.

        Args:
            symbol: Stock ticker symbol
            annual: If True, get annual data; if False, get quarterly

        Returns:
            Dict containing balance sheet data
        """
        function = 'BALANCE_SHEET'
        data = self._make_request(function, symbol=symbol)

        return data

    def get_cash_flow(self, symbol: str, annual: bool = True) -> Dict[str, Any]:
        """
        Get cash flow statement data.

        Args:
            symbol: Stock ticker symbol
            annual: If True, get annual data; if False, get quarterly

        Returns:
            Dict containing cash flow data
        """
        function = 'CASH_FLOW'
        data = self._make_request(function, symbol=symbol)

        return data

    def get_earnings(self, symbol: str) -> Dict[str, Any]:
        """
        Get earnings data.

        Args:
            symbol: Stock ticker symbol

        Returns:
            Dict containing earnings data
        """
        data = self._make_request('EARNINGS', symbol=symbol)

        return data

    def get_global_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Get global quote data for a symbol.

        Args:
            symbol: Stock ticker symbol

        Returns:
            Dict containing quote information
        """
        data = self._make_request('GLOBAL_QUOTE', symbol=symbol)

        quote = data.get('Global Quote', {})
        return {
            'symbol': quote.get('01. symbol', ''),
            'open': quote.get('02. open', ''),
            'high': quote.get('03. high', ''),
            'low': quote.get('04. low', ''),
            'price': quote.get('05. price', ''),
            'volume': quote.get('06. volume', ''),
            'latest_trading_day': quote.get('07. latest trading day', ''),
            'previous_close': quote.get('08. previous close', ''),
            'change': quote.get('09. change', ''),
            'change_percent': quote.get('10. change percent', '')
        }

    def analyze_sentiment_trends(self, news_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze sentiment trends from news data.

        Args:
            news_data: News sentiment data from get_news_sentiment()

        Returns:
            Dict containing sentiment analysis results
        """
        feed = news_data.get('feed', [])

        if not feed:
            return {'error': 'No news data available for analysis'}

        # Extract sentiment scores and labels
        sentiment_scores = []
        sentiment_labels = []
        ticker_sentiments = {}

        for item in feed:
            overall_score = item.get('overall_sentiment_score', 0)
            overall_label = item.get('overall_sentiment_label', '')

            if overall_score:
                sentiment_scores.append(float(overall_score))
            if overall_label:
                sentiment_labels.append(overall_label)

            # Process ticker-specific sentiments
            for ticker_data in item.get('ticker_sentiment', []):
                ticker = ticker_data.get('ticker', '')
                if ticker:
                    if ticker not in ticker_sentiments:
                        ticker_sentiments[ticker] = []
                    ticker_sentiments[ticker].append({
                        'score': ticker_data.get('ticker_sentiment_score', ''),
                        'label': ticker_data.get('ticker_sentiment_label', ''),
                        'relevance': ticker_data.get('relevance_score', '')
                    })

        # Calculate sentiment statistics
        analysis = {
            'total_articles': len(feed),
            'sentiment_distribution': {},
            'average_sentiment_score': 0,
            'sentiment_trend': '',
            'ticker_specific_sentiment': {},
            'top_positive_topics': [],
            'top_negative_topics': []
        }

        if sentiment_scores:
            analysis['average_sentiment_score'] = sum(sentiment_scores) / len(sentiment_scores)

            # Determine overall sentiment trend
            avg_score = analysis['average_sentiment_score']
            if avg_score > 0.1:
                analysis['sentiment_trend'] = 'POSITIVE'
            elif avg_score < -0.1:
                analysis['sentiment_trend'] = 'NEGATIVE'
            else:
                analysis['sentiment_trend'] = 'NEUTRAL'

        # Count sentiment labels
        for label in sentiment_labels:
            analysis['sentiment_distribution'][label] = analysis['sentiment_distribution'].get(label, 0) + 1

        # Analyze ticker-specific sentiments
        for ticker, sentiments in ticker_sentiments.items():
            scores = [float(s['score']) for s in sentiments if s['score']]
            if scores:
                avg_ticker_score = sum(scores) / len(scores)
                analysis['ticker_specific_sentiment'][ticker] = {
                    'average_score': avg_ticker_score,
                    'article_count': len(sentiments),
                    'sentiment_trend': 'POSITIVE' if avg_ticker_score > 0.1 else 'NEGATIVE' if avg_ticker_score < -0.1 else 'NEUTRAL'
                }

        return analysis

    def get_top_gainers_losers(self) -> Dict[str, Any]:
        """
        Get top gainers, losers, and most actively traded tickers in the US market.

        Returns:
            Dict containing top gainers, losers, and most active tickers
        """
        data = self._make_request('TOP_GAINERS_LOSERS')

        return {
            'metadata': {
                'last_updated': data.get('last_updated', ''),
                'note': 'Top 20 gainers, losers, and most actively traded tickers in the US market'
            },
            'top_gainers': data.get('top_gainers', []),
            'top_losers': data.get('top_losers', []),
            'most_actively_traded': data.get('most_actively_traded', [])
        }
