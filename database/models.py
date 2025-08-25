#!/usr/bin/env python3
"""
Database models for ClariFi application
"""

import sqlite3
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

DATABASE_PATH = "clarifi.db"


class DatabaseManager:
    """Manages SQLite database operations for ClariFi"""

    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.init_database()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
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

            # Add current_price and updated_at columns if they don't exist (for existing databases)
            try:
                cursor.execute('ALTER TABLE portfolio_tickers ADD COLUMN current_price REAL DEFAULT 0.0')
            except sqlite3.OperationalError:
                pass  # Column already exists

            try:
                cursor.execute('ALTER TABLE portfolio_tickers ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
            except sqlite3.OperationalError:
                pass  # Column already exists

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

            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_portfolio_tickers_portfolio ON portfolio_tickers(portfolio_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_analysis_results_ticker ON analysis_results(ticker)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_analysis_results_portfolio ON analysis_results(portfolio_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_command_history_executed ON command_history(executed_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_comparison_results_ticker ON comparison_results(ticker)')

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
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO portfolio_tickers (id, portfolio_id, ticker, quantity, avg_cost)
                VALUES (?, ?, ?, ?, ?)
            ''', (ticker_id, portfolio_id, ticker.upper(), quantity, avg_cost))
            conn.commit()
        return ticker_id

    def remove_ticker(self, portfolio_id: str, ticker: str) -> bool:
        """Remove a ticker from portfolio"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM portfolio_tickers
                WHERE portfolio_id = ? AND ticker = ?
            ''', (portfolio_id, ticker.upper()))
            conn.commit()
            return cursor.rowcount > 0

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
