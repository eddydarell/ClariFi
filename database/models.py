#!/usr/bin/env python3
"""
Database models for ClariFi application
"""

import sqlite3
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

DATABASE_PATH = "clarifi.db"


class DatabaseManager:

    def insert_event(self, event_date: str, event: str, category: str, impact: str, summary: str = "", link: str = "", event_id: Optional[str] = None):
        """Insert a new event into the events table."""
        if event_id is None:
            event_id = str(uuid.uuid4())
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO events (id, event_date, event, category, impact, summary, link)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (event_id, event_date, event, category, impact, summary, link))
            conn.commit()

    def get_all_events(self) -> List[Dict[str, Any]]:
        """Fetch all events from the events table."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, event_date, event, category, impact, summary, link, created_at FROM events ORDER BY event_date ASC')
            return [dict(row) for row in cursor.fetchall()]

    def upsert_ticker_price_rows(self, ticker: str, rows: List[Dict[str, Any]]) -> int:
        """Insert or update ticker OHLCV rows."""
        if not rows:
            return 0
        normalized_ticker = ticker.upper()
        inserted = 0
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for row in rows:
                cursor.execute('''
                    INSERT INTO ticker_prices (
                        id, ticker, price_date, open, high, low, close, adj_close, volume
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(ticker, price_date) DO UPDATE SET
                        open=excluded.open,
                        high=excluded.high,
                        low=excluded.low,
                        close=excluded.close,
                        adj_close=excluded.adj_close,
                        volume=excluded.volume
                ''', (
                    str(uuid.uuid4()),
                    normalized_ticker,
                    row.get('price_date'),
                    row.get('open'),
                    row.get('high'),
                    row.get('low'),
                    row.get('close'),
                    row.get('adj_close'),
                    row.get('volume'),
                ))
                inserted += 1
            conn.commit()
        return inserted

    def get_ticker_prices(self, ticker: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch OHLCV rows for ticker ordered by date ascending."""
        query = '''
            SELECT ticker, price_date, open, high, low, close, adj_close, volume
            FROM ticker_prices
            WHERE ticker = ?
            ORDER BY price_date ASC
        '''
        params: List[Any] = [ticker.upper()]
        if limit is not None:
            query += ' LIMIT ?'
            params.append(limit)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_tickers_with_price_data(self) -> List[str]:
        """Get all tickers that have persisted price data."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT DISTINCT ticker FROM ticker_prices ORDER BY ticker ASC')
            return [row['ticker'] for row in cursor.fetchall()]
    """Manages SQLite database operations for ClariFi"""

    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.init_database()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA synchronous=NORMAL')  # safe pairing with WAL
        conn.execute('PRAGMA foreign_keys=ON')
        try:
            yield conn
        finally:
            conn.close()

    def init_database(self):
        """Initialize database with all required tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Portfolio table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS portfolios (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Portfolio tickers table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS portfolio_tickers (
                    id TEXT PRIMARY KEY,
                    portfolio_id TEXT NOT NULL,
                    ticker TEXT NOT NULL,
                    quantity REAL DEFAULT 0.0,
                    avg_cost REAL DEFAULT 0.0,
                    current_price REAL DEFAULT 0.0,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (portfolio_id) REFERENCES portfolios (id) ON DELETE CASCADE,
                    UNIQUE(portfolio_id, ticker)
                )
            ''')

            # Event table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY,
                    event_date TEXT NOT NULL,
                    event TEXT NOT NULL,
                    category TEXT NOT NULL,
                    impact TEXT NOT NULL,
                    summary TEXT,
                    link TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Ticker OHLCV table (source of truth for historical market data)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ticker_prices (
                    id TEXT PRIMARY KEY,
                    ticker TEXT NOT NULL,
                    price_date TEXT NOT NULL,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    adj_close REAL,
                    volume REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(ticker, price_date)
                )
            ''')

            # events.event_date lookups drive correlation range queries
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_date ON events(event_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_category ON events(category)')

            # Add current_price and updated_at columns if they don't exist (for existing databases)
            try:
                cursor.execute('ALTER TABLE portfolio_tickers ADD COLUMN current_price REAL DEFAULT 0.0')
            except sqlite3.OperationalError:
                pass  # Column already exists

            try:
                cursor.execute('ALTER TABLE portfolio_tickers ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
            except sqlite3.OperationalError:
                pass  # Column already exists

            # Add summary and link columns to events table if they don't exist
            try:
                cursor.execute('ALTER TABLE events ADD COLUMN summary TEXT DEFAULT ""')
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute('ALTER TABLE events ADD COLUMN link TEXT DEFAULT ""')
            except sqlite3.OperationalError:
                pass

            # Analysis results table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id TEXT PRIMARY KEY,
                    portfolio_id TEXT,
                    ticker TEXT NOT NULL,
                    analysis_type TEXT NOT NULL,
                    analysis_data TEXT NOT NULL,  -- JSON data
                    recommendation TEXT,
                    confidence_level TEXT,
                    risk_level TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (portfolio_id) REFERENCES portfolios (id) ON DELETE SET NULL
                )
            ''')

            # Analysis history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analysis_history (
                    id TEXT PRIMARY KEY,
                    analysis_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    analysis_data TEXT NOT NULL,  -- JSON data
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (analysis_id) REFERENCES analysis_results (id) ON DELETE CASCADE
                )
            ''')

            # Command history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS command_history (
                    id TEXT PRIMARY KEY,
                    command TEXT NOT NULL,
                    parameters TEXT,  -- JSON data
                    execution_time REAL,
                    status TEXT NOT NULL,  -- SUCCESS, ERROR, CANCELLED
                    output TEXT,
                    error_message TEXT,
                    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Comparison results table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS comparison_results (
                    id TEXT PRIMARY KEY,
                    portfolio_id TEXT,
                    ticker TEXT,
                    predicted_data TEXT NOT NULL,  -- JSON data
                    actual_data TEXT NOT NULL,  -- JSON data
                    comparison_metrics TEXT NOT NULL,  -- JSON data
                    accuracy_score REAL,
                    prediction_date TIMESTAMP NOT NULL,
                    actual_date TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (portfolio_id) REFERENCES portfolios (id) ON DELETE SET NULL
                )
            ''')

            # Portfolio transactions/changes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS portfolio_transactions (
                    id TEXT PRIMARY KEY,
                    portfolio_id TEXT NOT NULL,
                    ticker TEXT NOT NULL,
                    transaction_type TEXT NOT NULL,  -- ADD, REMOVE, UPDATE_QUANTITY, UPDATE_PRICE
                    old_value TEXT,  -- JSON with old values
                    new_value TEXT,  -- JSON with new values
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (portfolio_id) REFERENCES portfolios (id) ON DELETE CASCADE
                )
            ''')

            # Ticker predictions table - per-horizon price/trend forecasts scored against
            # realized prices once each horizon's target date has passed.
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ticker_predictions (
                    id TEXT PRIMARY KEY,
                    ticker TEXT NOT NULL,
                    horizon TEXT NOT NULL,  -- 1_week, 1_month, 3_month, 6_month, 1_year
                    run_id TEXT,
                    entry_price REAL NOT NULL,
                    predicted_price REAL NOT NULL,
                    predicted_change_pct REAL NOT NULL,
                    predicted_trend TEXT NOT NULL,  -- UP, DOWN, FLAT
                    confidence TEXT NOT NULL,
                    target_date TEXT NOT NULL,
                    decision_status TEXT,
                    evidence_tags TEXT,
                    data_quality TEXT,
                    empirical_validation TEXT,
                    trade_plan_validation TEXT,
                    policy_version TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved INTEGER NOT NULL DEFAULT 0,
                    actual_price REAL,
                    actual_change_pct REAL,
                    actual_trend TEXT,
                    accuracy_score INTEGER,  -- +1 accurate, -1 inaccurate
                    resolved_at TIMESTAMP
                )
            ''')

            for column_name, column_type in (
                ('decision_status', 'TEXT'),
                ('evidence_tags', 'TEXT'),
                ('data_quality', 'TEXT'),
                ('empirical_validation', 'TEXT'),
                ('trade_plan_validation', 'TEXT'),
                ('policy_version', 'TEXT'),
            ):
                try:
                    cursor.execute(f'ALTER TABLE ticker_predictions ADD COLUMN {column_name} {column_type}')
                except sqlite3.OperationalError:
                    pass

            # Suggestion cache table - short-term ticker suggestions are cached for a
            # rolling TTL (default 24h) so the same ticker isn't re-suggested until it expires.
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS suggestion_cache (
                    id TEXT PRIMARY KEY,
                    ticker TEXT NOT NULL,
                    score REAL NOT NULL,
                    expected_7d_return REAL,
                    momentum REAL,
                    volume_signal REAL,
                    analyst_bias REAL,
                    risk_flag TEXT,
                    reason TEXT,
                    cached_at TIMESTAMP NOT NULL,
                    expires_at TIMESTAMP NOT NULL
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS shadow_trades (
                    id TEXT PRIMARY KEY,
                    ticker TEXT NOT NULL,
                    entry_date TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    stop_price REAL NOT NULL,
                    target_price REAL NOT NULL,
                    time_stop_days INTEGER NOT NULL,
                    estimated_round_trip_cost_pct REAL NOT NULL,
                    policy_version TEXT,
                    provenance TEXT,
                    status TEXT NOT NULL DEFAULT 'OPEN',
                    exit_date TEXT,
                    exit_price REAL,
                    exit_reason TEXT,
                    realized_return_pct REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    closed_at TIMESTAMP
                )
            ''')

            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_portfolio_tickers_portfolio ON portfolio_tickers(portfolio_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_analysis_results_ticker ON analysis_results(ticker)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ticker_prices_lookup ON ticker_prices(ticker, price_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_analysis_results_portfolio ON analysis_results(portfolio_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_command_history_executed ON command_history(executed_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_comparison_results_ticker ON comparison_results(ticker)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_portfolio_transactions_portfolio ON portfolio_transactions(portfolio_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_portfolio_transactions_ticker ON portfolio_transactions(ticker)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ticker_predictions_ticker ON ticker_predictions(ticker)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ticker_predictions_due ON ticker_predictions(ticker, resolved, target_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_shadow_trades_open ON shadow_trades(ticker, status, entry_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_suggestion_cache_ticker ON suggestion_cache(ticker)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_suggestion_cache_expires ON suggestion_cache(expires_at)')

            conn.commit()


class Portfolio:
    """Portfolio model for managing collections of tickers"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create(self, name: str, description: str = "") -> str:
        """Create a new portfolio"""
        portfolio_id = str(uuid.uuid4())
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO portfolios (id, name, description)
                VALUES (?, ?, ?)
            ''', (portfolio_id, name, description))
            conn.commit()
        return portfolio_id

    def get_all(self) -> List[Dict[str, Any]]:
        """Get all portfolios"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM portfolios ORDER BY created_at DESC')
            return [dict(row) for row in cursor.fetchall()]

    def get_by_id(self, portfolio_id: str) -> Optional[Dict[str, Any]]:
        """Get portfolio by ID"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM portfolios WHERE id = ?', (portfolio_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get portfolio by name"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM portfolios WHERE name = ?', (name,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def add_ticker(self, portfolio_id: str, ticker: str, quantity: float = 0.0, avg_cost: float = 0.0) -> str:
        """Add a ticker to portfolio"""
        ticker_id = str(uuid.uuid4())
        existing = None
        is_update = False

        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # Check if ticker already exists
            cursor.execute('''
                SELECT id, quantity, avg_cost FROM portfolio_tickers
                WHERE portfolio_id = ? AND ticker = ?
            ''', (portfolio_id, ticker.upper()))
            existing = cursor.fetchone()

            if existing:
                # Update existing ticker
                cursor.execute('''
                    UPDATE portfolio_tickers
                    SET quantity = ?, avg_cost = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE portfolio_id = ? AND ticker = ?
                ''', (quantity, avg_cost, portfolio_id, ticker.upper()))
                ticker_id = existing["id"]
                is_update = True
            else:
                # Insert new ticker
                cursor.execute('''
                    INSERT INTO portfolio_tickers (id, portfolio_id, ticker, quantity, avg_cost)
                    VALUES (?, ?, ?, ?, ?)
                ''', (ticker_id, portfolio_id, ticker.upper(), quantity, avg_cost))

            conn.commit()

        # Log transaction after commit to avoid database lock
        if is_update:
            self._log_transaction(portfolio_id, ticker.upper(), "UPDATE_QUANTITY",
                                {"quantity": existing["quantity"], "avg_cost": existing["avg_cost"]},
                                {"quantity": quantity, "avg_cost": avg_cost})
        else:
            self._log_transaction(portfolio_id, ticker.upper(), "ADD",
                                None, {"quantity": quantity, "avg_cost": avg_cost})

        return ticker_id

    def remove_ticker(self, portfolio_id: str, ticker: str) -> bool:
        """Remove a ticker from portfolio"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # Get current ticker data before deletion
            cursor.execute('''
                SELECT quantity, avg_cost, current_price FROM portfolio_tickers
                WHERE portfolio_id = ? AND ticker = ?
            ''', (portfolio_id, ticker.upper()))
            ticker_data = cursor.fetchone()

            if ticker_data:
                # Delete the ticker
                cursor.execute('''
                    DELETE FROM portfolio_tickers
                    WHERE portfolio_id = ? AND ticker = ?
                ''', (portfolio_id, ticker.upper()))

                # Log transaction
                self._log_transaction(portfolio_id, ticker.upper(), "REMOVE",
                                    dict(ticker_data), None)

                conn.commit()
                return cursor.rowcount > 0
            return False

    def update_ticker_price(self, portfolio_id: str, ticker: str, current_price: float) -> bool:
        """Update the current price for a ticker in portfolio"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # Get old price for transaction log
            cursor.execute('''
                SELECT current_price FROM portfolio_tickers
                WHERE portfolio_id = ? AND ticker = ?
            ''', (portfolio_id, ticker.upper()))
            old_data = cursor.fetchone()
            old_price = old_data["current_price"] if old_data else None

            cursor.execute('''
                UPDATE portfolio_tickers
                SET current_price = ?, updated_at = CURRENT_TIMESTAMP
                WHERE portfolio_id = ? AND ticker = ?
            ''', (current_price, portfolio_id, ticker.upper()))

            if cursor.rowcount > 0:
                # Log price update
                self._log_transaction(portfolio_id, ticker.upper(), "UPDATE_PRICE",
                                    {"current_price": old_price},
                                    {"current_price": current_price})

            conn.commit()
            return cursor.rowcount > 0

    def _log_transaction(self, portfolio_id: str, ticker: str, transaction_type: str,
                        old_value: dict = None, new_value: dict = None, notes: str = ""):
        """Log a portfolio transaction"""
        transaction_id = str(uuid.uuid4())
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO portfolio_transactions
                (id, portfolio_id, ticker, transaction_type, old_value, new_value, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (transaction_id, portfolio_id, ticker, transaction_type,
                  json.dumps(old_value) if old_value else None,
                  json.dumps(new_value) if new_value else None,
                  notes))
            conn.commit()

    def get_tickers(self, portfolio_id: str) -> List[Dict[str, Any]]:
        """Get all tickers in a portfolio"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM portfolio_tickers
                WHERE portfolio_id = ?
                ORDER BY ticker
            ''', (portfolio_id,))
            return [dict(row) for row in cursor.fetchall()]

    def update(self, portfolio_id: str, name: str = None, description: str = None) -> bool:
        """Update portfolio name and/or description"""
        if name is None and description is None:
            return False

        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # Build dynamic update query
            updates = []
            params = []

            if name is not None:
                updates.append("name = ?")
                params.append(name)

            if description is not None:
                updates.append("description = ?")
                params.append(description)

            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(portfolio_id)

            query = f"UPDATE portfolios SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount > 0

    def delete(self, portfolio_id: str) -> bool:
        """Delete portfolio and all associated tickers"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # First delete all tickers in the portfolio
            cursor.execute('DELETE FROM portfolio_tickers WHERE portfolio_id = ?', (portfolio_id,))

            # Then delete the portfolio itself
            cursor.execute('DELETE FROM portfolios WHERE id = ?', (portfolio_id,))
            conn.commit()
            return cursor.rowcount > 0

    def update_ticker_price(self, portfolio_id: str, ticker: str, current_price: float) -> bool:
        """Update the current price for a ticker in portfolio"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE portfolio_tickers
                SET current_price = ?, updated_at = CURRENT_TIMESTAMP
                WHERE portfolio_id = ? AND ticker = ?
            ''', (current_price, portfolio_id, ticker.upper()))
            conn.commit()
            return cursor.rowcount > 0

    def update_ticker(self, portfolio_id: str, ticker: str, quantity: float = None, avg_cost: float = None) -> bool:
        """Update ticker quantity and/or average cost"""
        if quantity is None and avg_cost is None:
            return False

        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # Build dynamic update query
            updates = []
            params = []

            if quantity is not None:
                updates.append("quantity = ?")
                params.append(quantity)

            if avg_cost is not None:
                updates.append("avg_cost = ?")
                params.append(avg_cost)

            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.extend([portfolio_id, ticker.upper()])

            query = f"UPDATE portfolio_tickers SET {', '.join(updates)} WHERE portfolio_id = ? AND ticker = ?"
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount > 0

    def get_portfolio_info(self, portfolio_id: str) -> Dict[str, Any]:
        """Get comprehensive portfolio information"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # Get basic portfolio info
            cursor.execute('SELECT * FROM portfolios WHERE id = ?', (portfolio_id,))
            portfolio = cursor.fetchone()

            if not portfolio:
                return {"error": "Portfolio not found"}

            portfolio = dict(portfolio)

            # Get tickers with latest prices and analysis
            cursor.execute('''
                SELECT
                    pt.ticker,
                    pt.quantity,
                    pt.avg_cost,
                    pt.current_price,
                    pt.updated_at as price_updated_at,
                    (pt.current_price * pt.quantity) as current_value,
                    (pt.avg_cost * pt.quantity) as total_cost,
                    ((pt.current_price - pt.avg_cost) * pt.quantity) as unrealized_pnl,
                    (((pt.current_price - pt.avg_cost) / NULLIF(pt.avg_cost, 0)) * 100) as percentage_change
                FROM portfolio_tickers pt
                WHERE pt.portfolio_id = ?
                ORDER BY pt.ticker
            ''', (portfolio_id,))

            tickers_data = []
            total_current_value = 0
            total_cost = 0
            total_unrealized_pnl = 0

            for row in cursor.fetchall():
                ticker_info = dict(row)
                tickers_data.append(ticker_info)

                if ticker_info['current_value']:
                    total_current_value += ticker_info['current_value']
                if ticker_info['total_cost']:
                    total_cost += ticker_info['total_cost']
                if ticker_info['unrealized_pnl']:
                    total_unrealized_pnl += ticker_info['unrealized_pnl']

            # Get latest analysis for each ticker
            for ticker_info in tickers_data:
                ticker = ticker_info['ticker']
                cursor.execute('''
                    SELECT recommendation, confidence_level, risk_level, created_at
                    FROM analysis_results
                    WHERE ticker = ? AND (portfolio_id = ? OR portfolio_id IS NULL)
                    ORDER BY created_at DESC
                    LIMIT 1
                ''', (ticker, portfolio_id))

                analysis = cursor.fetchone()
                if analysis:
                    ticker_info['analysis'] = dict(analysis)
                else:
                    ticker_info['analysis'] = None

            # Calculate portfolio-level metrics
            portfolio_percentage_change = 0
            if total_cost > 0:
                portfolio_percentage_change = ((total_current_value - total_cost) / total_cost) * 100

            # Get portfolio changes (recently added/removed tickers)
            cursor.execute('''
                SELECT
                    ticker,
                    transaction_type,
                    old_value,
                    new_value,
                    created_at as change_date,
                    notes
                FROM portfolio_transactions
                WHERE portfolio_id = ?
                AND created_at >= datetime('now', '-30 days')
                ORDER BY created_at DESC
                LIMIT 20
            ''', (portfolio_id,))

            recent_changes = []
            for row in cursor.fetchall():
                change = dict(row)
                # Parse JSON values
                if change['old_value']:
                    change['old_value'] = json.loads(change['old_value'])
                if change['new_value']:
                    change['new_value'] = json.loads(change['new_value'])
                recent_changes.append(change)

            # Get accuracy metrics for the portfolio
            cursor.execute('''
                SELECT
                    AVG(accuracy_score) as avg_accuracy,
                    COUNT(*) as total_predictions,
                    MIN(accuracy_score) as min_accuracy,
                    MAX(accuracy_score) as max_accuracy
                FROM comparison_results
                WHERE portfolio_id = ?
            ''', (portfolio_id,))

            accuracy_row = cursor.fetchone()
            accuracy_metrics = dict(accuracy_row) if accuracy_row and accuracy_row['total_predictions'] > 0 else {
                'avg_accuracy': None,
                'total_predictions': 0,
                'min_accuracy': None,
                'max_accuracy': None
            }

            return {
                'portfolio': portfolio,
                'tickers': tickers_data,
                'summary': {
                    'total_tickers': len(tickers_data),
                    'total_current_value': round(total_current_value, 2),
                    'total_cost': round(total_cost, 2),
                    'total_unrealized_pnl': round(total_unrealized_pnl, 2),
                    'portfolio_percentage_change': round(portfolio_percentage_change, 2)
                },
                'accuracy_metrics': accuracy_metrics,
                'recent_changes': recent_changes
            }

    def get_portfolio_analytics(self, portfolio_id: str) -> Dict[str, Any]:
        """Get advanced portfolio analytics and insights"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # Get portfolio basic information
            cursor.execute('SELECT * FROM portfolios WHERE id = ?', (portfolio_id,))
            portfolio = cursor.fetchone()
            if not portfolio:
                return {"error": "Portfolio not found"}

            portfolio = dict(portfolio)

            # Get portfolio tickers with their values
            cursor.execute('''
                SELECT
                    ticker,
                    quantity,
                    avg_cost,
                    current_price,
                    (current_price * quantity) as current_value,
                    (avg_cost * quantity) as cost_basis,
                    ((current_price - avg_cost) * quantity) as unrealized_pnl
                FROM portfolio_tickers
                WHERE portfolio_id = ?
                AND quantity > 0
            ''', (portfolio_id,))

            holdings = [dict(row) for row in cursor.fetchall()]

            # Calculate basic portfolio metrics
            total_current_value = sum(h.get('current_value', 0) or 0 for h in holdings)
            total_cost_basis = sum(h.get('cost_basis', 0) or 0 for h in holdings)
            total_unrealized_pnl = sum(h.get('unrealized_pnl', 0) or 0 for h in holdings)

            # Portfolio composition analysis
            composition = []
            if total_current_value > 0:
                for holding in holdings:
                    current_value = holding.get('current_value', 0) or 0
                    if current_value > 0:
                        composition.append({
                            'ticker': holding['ticker'],
                            'weight': (current_value / total_current_value) * 100,
                            'value': current_value,
                            'quantity': holding.get('quantity', 0)
                        })

                # Sort by weight descending
                composition.sort(key=lambda x: x['weight'], reverse=True)

            # Risk distribution analysis (try to get from analysis results, fall back to basic metrics)
            cursor.execute('''
                SELECT
                    ar.risk_level,
                    COUNT(*) as count,
                    AVG(pt.current_price * pt.quantity) as avg_value
                FROM portfolio_tickers pt
                LEFT JOIN analysis_results ar ON pt.ticker = ar.ticker
                WHERE pt.portfolio_id = ?
                AND ar.id IN (
                    SELECT id FROM analysis_results ar2
                    WHERE ar2.ticker = ar.ticker
                    ORDER BY ar2.created_at DESC LIMIT 1
                )
                GROUP BY ar.risk_level
            ''', (portfolio_id,))

            risk_distribution = [dict(row) for row in cursor.fetchall()]

            # Recommendation distribution
            cursor.execute('''
                SELECT
                    ar.recommendation,
                    COUNT(*) as count,
                    AVG(pt.current_price * pt.quantity) as avg_value
                FROM portfolio_tickers pt
                LEFT JOIN analysis_results ar ON pt.ticker = ar.ticker
                WHERE pt.portfolio_id = ?
                AND ar.id IN (
                    SELECT id FROM analysis_results ar2
                    WHERE ar2.ticker = ar.ticker
                    ORDER BY ar2.created_at DESC LIMIT 1
                )
                GROUP BY ar.recommendation
            ''', (portfolio_id,))

            recommendation_distribution = [dict(row) for row in cursor.fetchall()]

            # Performance trends over time
            cursor.execute('''
                SELECT
                    DATE(ch.executed_at) as date,
                    COUNT(*) as analysis_count,
                    AVG(cr.accuracy_score) as avg_accuracy
                FROM command_history ch
                LEFT JOIN comparison_results cr ON DATE(ch.executed_at) = DATE(cr.created_at)
                WHERE ch.parameters LIKE '%' || ? || '%'
                AND ch.executed_at >= datetime('now', '-90 days')
                GROUP BY DATE(ch.executed_at)
                ORDER BY date DESC
                LIMIT 30
            ''', (portfolio_id,))

            performance_trends = [dict(row) for row in cursor.fetchall()]

            # Calculate diversification metrics
            diversification_metrics = {
                'total_holdings': len(holdings),
                'concentration_risk': 'High' if composition and composition[0]['weight'] > 50 else 'Medium' if composition and composition[0]['weight'] > 30 else 'Low',
                'top_3_concentration': sum(h['weight'] for h in composition[:3]) if len(composition) >= 3 else (sum(h['weight'] for h in composition) if composition else 0)
            }

            # Performance metrics
            portfolio_return = ((total_current_value - total_cost_basis) / total_cost_basis * 100) if total_cost_basis > 0 else 0
            performance_metrics = {
                'total_return_pct': round(portfolio_return, 2),
                'total_value': round(total_current_value, 2),
                'total_cost_basis': round(total_cost_basis, 2),
                'unrealized_pnl': round(total_unrealized_pnl, 2),
                'largest_position': composition[0] if composition else None,
                'smallest_position': composition[-1] if composition else None
            }

            # Basic risk assessment based on portfolio characteristics
            risk_assessment = 'Low'
            if diversification_metrics['concentration_risk'] == 'High':
                risk_assessment = 'High'
            elif len(holdings) < 5:
                risk_assessment = 'Medium-High'
            elif diversification_metrics['top_3_concentration'] > 70:
                risk_assessment = 'Medium'

            return {
                'portfolio_summary': {
                    'name': portfolio['name'],
                    'total_holdings': len(holdings),
                    'total_value': round(total_current_value, 2),
                    'total_return_pct': round(portfolio_return, 2)
                },
                'composition': composition[:10],  # Top 10 holdings
                'diversification_metrics': diversification_metrics,
                'performance_metrics': performance_metrics,
                'risk_assessment': {
                    'overall_risk': risk_assessment,
                    'concentration_risk': diversification_metrics['concentration_risk'],
                    'diversification_score': max(0, min(100, (100 - diversification_metrics['top_3_concentration']) if diversification_metrics['top_3_concentration'] > 0 else 50))
                },
                'analysis_based_metrics': {
                    'risk_distribution': risk_distribution,
                    'recommendation_distribution': recommendation_distribution,
                    'performance_trends': performance_trends,
                    'has_analysis_data': len(risk_distribution) > 0 or len(recommendation_distribution) > 0
                }
            }


class AnalysisResult:
    """Analysis results model"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def save(self, portfolio_id: Optional[str], ticker: str, analysis_type: str,
             analysis_data: Dict[str, Any], recommendation: str = "",
             confidence_level: str = "", risk_level: str = "") -> str:
        """Save analysis results"""
        result_id = str(uuid.uuid4())
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO analysis_results
                (id, portfolio_id, ticker, analysis_type, analysis_data,
                 recommendation, confidence_level, risk_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (result_id, portfolio_id, ticker.upper(), analysis_type,
                  json.dumps(analysis_data), recommendation, confidence_level, risk_level))
            conn.commit()
        return result_id

    def get_by_ticker(self, ticker: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get analysis results for a ticker"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM analysis_results
                WHERE ticker = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (ticker.upper(), limit))
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                result['analysis_data'] = json.loads(result['analysis_data'])
                results.append(result)
            return results

    def get_by_portfolio(self, portfolio_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get analysis results for a portfolio"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM analysis_results
                WHERE portfolio_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (portfolio_id, limit))
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                result['analysis_data'] = json.loads(result['analysis_data'])
                results.append(result)
            return results

    def get_all(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all analysis results"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM analysis_results
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                result['analysis_data'] = json.loads(result['analysis_data'])
                results.append(result)
            return results

    def update_status(self, analysis_id: str, status: str, notes: str = "") -> bool:
        """Update analysis status and add to history"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # Get current analysis data
            cursor.execute('SELECT * FROM analysis_results WHERE id = ?', (analysis_id,))
            current = cursor.fetchone()

            if not current:
                return False

            # Add to history
            history_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO analysis_history (id, analysis_id, version, analysis_data, notes)
                VALUES (?, ?, 1, ?, ?)
            ''', (history_id, analysis_id, current['analysis_data'], notes))

            conn.commit()
            return True


class CommandHistory:
    """Command history model"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def log_command(self, command: str, parameters: Dict[str, Any] = None,
                   execution_time: float = 0.0, status: str = "SUCCESS",
                   output: str = "", error_message: str = "") -> str:
        """Log a command execution"""
        command_id = str(uuid.uuid4())
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO command_history
                (id, command, parameters, execution_time, status, output, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (command_id, command, json.dumps(parameters) if parameters else None,
                  execution_time, status, output, error_message))
            conn.commit()
        return command_id

    def get_recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent command history"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM command_history
                ORDER BY executed_at DESC
                LIMIT ?
            ''', (limit,))
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                if result['parameters']:
                    result['parameters'] = json.loads(result['parameters'])
                results.append(result)
            return results

    def update_status(self, command_id: str, status: str, execution_time: float = 0.0,
                     output: str = "", error_message: str = "") -> bool:
        """Update command execution status"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE command_history
                SET status = ?, execution_time = ?, output = ?, error_message = ?
                WHERE id = ?
            ''', (status, execution_time, output, error_message, command_id))
            conn.commit()
            return cursor.rowcount > 0


class ComparisonResult:
    """Comparison results model"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def save_comparison(self, portfolio_id: Optional[str], ticker: str,
                       predicted_data: Dict[str, Any], actual_data: Dict[str, Any],
                       comparison_metrics: Dict[str, Any], accuracy_score: float,
                       prediction_date: datetime, actual_date: datetime) -> str:
        """Save comparison results"""
        comparison_id = str(uuid.uuid4())
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO comparison_results
                (id, portfolio_id, ticker, predicted_data, actual_data,
                 comparison_metrics, accuracy_score, prediction_date, actual_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (comparison_id, portfolio_id, ticker.upper(),
                  json.dumps(predicted_data), json.dumps(actual_data),
                  json.dumps(comparison_metrics), accuracy_score,
                  prediction_date, actual_date))
            conn.commit()
        return comparison_id

    def get_by_ticker(self, ticker: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get comparison results for a ticker"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM comparison_results
                WHERE ticker = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (ticker.upper(), limit))
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                result['predicted_data'] = json.loads(result['predicted_data'])
                result['actual_data'] = json.loads(result['actual_data'])
                result['comparison_metrics'] = json.loads(result['comparison_metrics'])
                results.append(result)
            return results

    def get_accuracy_trends(self, ticker: str = None, portfolio_id: str = None) -> Dict[str, Any]:
        """Get accuracy trends for analysis refinement"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            where_clause = "WHERE 1=1"
            params = []

            if ticker:
                where_clause += " AND ticker = ?"
                params.append(ticker.upper())

            if portfolio_id:
                where_clause += " AND portfolio_id = ?"
                params.append(portfolio_id)

            cursor.execute(f'''
                SELECT
                    AVG(accuracy_score) as avg_accuracy,
                    COUNT(*) as total_comparisons,
                    MIN(accuracy_score) as min_accuracy,
                    MAX(accuracy_score) as max_accuracy,
                    ticker
                FROM comparison_results
                {where_clause}
                GROUP BY ticker
                ORDER BY avg_accuracy DESC
            ''', params)

            return [dict(row) for row in cursor.fetchall()]


class TickerPrediction:
    """Tracks per-horizon price/trend predictions and scores them once realized.

    Each ticker run stores a forecast for 1 week, 1 month, 3 months, 6 months and
    1 year ahead. On later runs, any prediction whose target date has passed is
    resolved against the observed price and awarded a +1 (accurate) or -1
    (inaccurate) score, which rolls up into a per-ticker confidence indicator.
    """

    HORIZONS = ("1_week", "1_month", "3_month", "6_month", "1_year")
    TREND_FLAT_THRESHOLD_PCT = 1.0  # |change%| below this is considered FLAT
    TOLERANCE_BY_HORIZON = {
        "1_week": 5.0,
        "1_month": 8.0,
        "3_month": 12.0,
        "6_month": 18.0,
        "1_year": 25.0,
    }

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    @classmethod
    def classify_trend(cls, change_pct: float) -> str:
        """Classify a percentage price change into UP/DOWN/FLAT."""
        if change_pct > cls.TREND_FLAT_THRESHOLD_PCT:
            return "UP"
        if change_pct < -cls.TREND_FLAT_THRESHOLD_PCT:
            return "DOWN"
        return "FLAT"

    def save_predictions(self, ticker: str, entry_price: float,
                        predictions: Dict[str, Dict[str, Any]],
                        run_id: Optional[str] = None,
                        provenance: Optional[Dict[str, Any]] = None) -> List[str]:
        """Persist one row per tracked horizon for this analysis run."""
        ticker = ticker.upper()
        provenance = provenance or {}
        ids: List[str] = []
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            for horizon in self.HORIZONS:
                pred = predictions.get(horizon)
                if not pred:
                    continue
                prediction_id = str(uuid.uuid4())
                predicted_change_pct = pred["predicted_change_pct"]
                cursor.execute('''
                    INSERT INTO ticker_predictions
                    (id, ticker, horizon, run_id, entry_price, predicted_price,
                     predicted_change_pct, predicted_trend, confidence, target_date,
                     decision_status, evidence_tags, data_quality, empirical_validation,
                     trade_plan_validation, policy_version)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    prediction_id, ticker, horizon, run_id, entry_price,
                    pred["predicted_price"], predicted_change_pct,
                    self.classify_trend(predicted_change_pct), pred["confidence"],
                    pred["target_date"],
                    provenance.get('decision_status'),
                    json.dumps(provenance.get('evidence_tags', [])),
                    json.dumps(provenance.get('data_quality', {})),
                    json.dumps(provenance.get('empirical_validation', {})),
                    json.dumps(provenance.get('trade_plan_validation', {})),
                    provenance.get('policy_version'),
                ))
                ids.append(prediction_id)
            conn.commit()
        return ids

    def get_due_predictions(self, ticker: str, as_of: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch unresolved predictions whose target date has already passed."""
        as_of = as_of or datetime.now().strftime('%Y-%m-%d')
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM ticker_predictions
                WHERE ticker = ? AND resolved = 0 AND target_date <= ?
                ORDER BY target_date ASC
            ''', (ticker.upper(), as_of))
            return [dict(row) for row in cursor.fetchall()]

    def resolve_prediction(self, prediction_id: str, actual_price: float, entry_price: float,
                          predicted_trend: str, horizon: str) -> Dict[str, Any]:
        """Score a due prediction against the observed actual price."""
        actual_change_pct = ((actual_price - entry_price) / entry_price) * 100 if entry_price else 0.0
        actual_trend = self.classify_trend(actual_change_pct)

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT predicted_change_pct FROM ticker_predictions WHERE id = ?', (prediction_id,))
            row = cursor.fetchone()
            predicted_change_pct = row['predicted_change_pct'] if row else 0.0

            tolerance = self.TOLERANCE_BY_HORIZON.get(horizon, 10.0)
            price_error_pct = abs(actual_change_pct - predicted_change_pct)
            accurate = (actual_trend == predicted_trend) and (price_error_pct <= tolerance)
            accuracy_score = 1 if accurate else -1

            cursor.execute('''
                UPDATE ticker_predictions
                SET resolved = 1, actual_price = ?, actual_change_pct = ?, actual_trend = ?,
                    accuracy_score = ?, resolved_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (actual_price, actual_change_pct, actual_trend, accuracy_score, prediction_id))
            conn.commit()

        return {
            "id": prediction_id,
            "actual_price": actual_price,
            "actual_change_pct": actual_change_pct,
            "actual_trend": actual_trend,
            "price_error_pct": price_error_pct,
            "accurate": accurate,
            "accuracy_score": accuracy_score,
        }

    def get_recent(self, ticker: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Fetch recent predictions (resolved or pending) for a ticker."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM ticker_predictions WHERE ticker = ?
                ORDER BY created_at DESC LIMIT ?
            ''', (ticker.upper(), limit))
            return [dict(row) for row in cursor.fetchall()]

    def get_confidence_summary(self, ticker: str) -> Dict[str, Any]:
        """Aggregate resolved prediction scores into a confidence indicator per horizon."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT horizon,
                       COUNT(*) as resolved_count,
                       SUM(CASE WHEN accuracy_score = 1 THEN 1 ELSE 0 END) as correct_count,
                       SUM(accuracy_score) as score_sum
                FROM ticker_predictions
                WHERE ticker = ? AND resolved = 1
                GROUP BY horizon
            ''', (ticker.upper(),))

            by_horizon: Dict[str, Any] = {}
            total_score = 0
            total_resolved = 0
            total_correct = 0
            for row in cursor.fetchall():
                r = dict(row)
                accuracy_rate = (r['correct_count'] / r['resolved_count']) if r['resolved_count'] else None
                by_horizon[r['horizon']] = {
                    "resolved_count": r['resolved_count'],
                    "correct_count": r['correct_count'],
                    "score": r['score_sum'],
                    "accuracy_rate": accuracy_rate,
                }
                total_score += r['score_sum'] or 0
                total_resolved += r['resolved_count']
                total_correct += r['correct_count']

            cursor.execute('''
                SELECT COUNT(*) as pending FROM ticker_predictions WHERE ticker = ? AND resolved = 0
            ''', (ticker.upper(),))
            pending = cursor.fetchone()['pending']

        return {
            "ticker": ticker.upper(),
            "confidence_score": total_score,
            "resolved_count": total_resolved,
            "correct_count": total_correct,
            "overall_accuracy_rate": (total_correct / total_resolved) if total_resolved else None,
            "pending_count": pending,
            "by_horizon": by_horizon,
        }


class SuggestionCache:
    """Caches `suggest` command results for a rolling TTL (default 24h).

    Once a ticker is suggested it is cached and excluded from being suggested
    again until its cache entry expires, at which point it becomes eligible
    again. Active cache entries are surfaced back to callers so they can be
    appended to subsequent `suggest` results with a freshness indicator.
    """

    DEFAULT_TTL_HOURS = 24.0
    TIMESTAMP_FORMAT = '%Y-%m-%d %H:%M:%S'

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def purge_expired(self, as_of: Optional[datetime] = None) -> int:
        """Delete cache entries whose TTL has elapsed, freeing their tickers for re-suggestion."""
        as_of = as_of or datetime.utcnow()
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'DELETE FROM suggestion_cache WHERE expires_at <= ?',
                (as_of.strftime(self.TIMESTAMP_FORMAT),)
            )
            deleted = cursor.rowcount
            conn.commit()
        return deleted

    def get_active(self, as_of: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Fetch all cache entries that have not yet expired."""
        as_of = as_of or datetime.utcnow()
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM suggestion_cache
                WHERE expires_at > ?
                ORDER BY cached_at DESC
            ''', (as_of.strftime(self.TIMESTAMP_FORMAT),))
            return [dict(row) for row in cursor.fetchall()]

    def get_active_tickers(self, as_of: Optional[datetime] = None) -> set:
        """Set of tickers currently within their 24h suggestion cooldown."""
        return {row['ticker'] for row in self.get_active(as_of=as_of)}

    def add_suggestions(self, suggestions: List[Any], ttl_hours: float = DEFAULT_TTL_HOURS) -> int:
        """Cache newly-suggested tickers, skipping any already actively cached."""
        if not suggestions:
            return 0
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=ttl_hours)
        active_tickers = self.get_active_tickers(as_of=now)
        inserted = 0
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            for item in suggestions:
                ticker = item.symbol.upper()
                if ticker in active_tickers:
                    continue
                cursor.execute('''
                    INSERT INTO suggestion_cache
                    (id, ticker, score, expected_7d_return, momentum, volume_signal,
                     analyst_bias, risk_flag, reason, cached_at, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    str(uuid.uuid4()), ticker, item.score, item.expected_7d_return,
                    item.momentum, item.volume_signal, item.analyst_bias,
                    item.risk_flag, item.reason,
                    now.strftime(self.TIMESTAMP_FORMAT), expires_at.strftime(self.TIMESTAMP_FORMAT),
                ))
                active_tickers.add(ticker)
                inserted += 1
            conn.commit()
        return inserted
