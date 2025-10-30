#!/usr/bin/env python3
"""
Recurrent Neural Network Analyzer Module
Implements LSTM and GRU networks for stock price prediction and trading recommendations.
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
import warnings
warnings.filterwarnings('ignore')

# TensorFlow/Keras imports with fallbacks
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, GRU, Dense, Dropout, Bidirectional
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
    from sklearn.preprocessing import MinMaxScaler
    from sklearn.metrics import mean_squared_error, mean_absolute_error
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False

try:
    import joblib
    JOBLIB_AVAILABLE = True
except ImportError:
    JOBLIB_AVAILABLE = False


@dataclass
class RNNModelResult:
    """Results from RNN model training and prediction."""
    model_name: str
    mse: float
    mae: float
    rmse: float
    mape: float
    predicted_returns: List[float]
    actual_returns: List[float]
    predictions: np.ndarray
    actuals: np.ndarray


@dataclass
class RNNRecommendation:
    """Trading recommendation based on RNN analysis."""
    action: str  # BUY, HOLD, SELL
    confidence: float  # 0-1
    predicted_return: float  # predicted percentage return
    risk_score: float  # 0-1 (higher = riskier)
    reasoning: str
    model_used: str


@dataclass
class RNNAnalysisResult:
    """Complete RNN analysis result."""
    ticker: str
    models_results: Dict[str, RNNModelResult]
    recommendation: RNNRecommendation
    feature_importance: Dict[str, float]
    analysis_date: datetime
    prediction_horizon: int


class RNNAnalyzer:
    """
    RNN Analyzer for stock price prediction using LSTM and GRU networks.
    """

    def __init__(self):
        """Initialize the RNN analyzer."""
        if not TENSORFLOW_AVAILABLE:
            raise ImportError("TensorFlow is required for RNN analysis. Install with: pip install tensorflow>=2.13.0")

        # Set random seeds for reproducibility
        tf.random.set_seed(42)
        np.random.seed(42)

        # Configure TensorFlow for CPU/GPU
        physical_devices = tf.config.list_physical_devices('GPU')
        if physical_devices:
            try:
                tf.config.experimental.set_memory_growth(physical_devices[0], True)
                print("GPU available and configured for RNN training")
            except:
                print("GPU available but memory growth setting failed")

        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.models = {}

    def get_available_models(self) -> List[str]:
        """Get list of available RNN models."""
        return ['lstm', 'gru', 'bidirectional_lstm', 'bidirectional_gru']

    def create_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Create technical features for RNN analysis.

        Args:
            data: Stock price data

        Returns:
            DataFrame with technical features
        """
        df = data.copy()

        # Basic price features
        df['returns'] = df['Close'].pct_change()
        df['log_returns'] = np.log(df['Close'] / df['Close'].shift(1))

        # Moving averages
        for period in [5, 10, 20, 50]:
            df[f'sma_{period}'] = df['Close'].rolling(window=period).mean()
            df[f'ema_{period}'] = df['Close'].ewm(span=period).mean()

        # Volatility measures
        df['volatility_10'] = df['returns'].rolling(window=10).std()
        df['volatility_20'] = df['returns'].rolling(window=20).std()
        df['volatility_50'] = df['returns'].rolling(window=50).std()

        # RSI
        def calculate_rsi(data, period=14):
            delta = data.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs))

        df['rsi_14'] = calculate_rsi(df['Close'], 14)

        # MACD
        ema_12 = df['Close'].ewm(span=12).mean()
        ema_26 = df['Close'].ewm(span=26).mean()
        df['macd'] = ema_12 - ema_26
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']

        # Bollinger Bands
        sma_20 = df['Close'].rolling(window=20).mean()
        std_20 = df['Close'].rolling(window=20).std()
        df['bb_upper'] = sma_20 + (std_20 * 2)
        df['bb_lower'] = sma_20 - (std_20 * 2)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / sma_20

        # Volume features
        df['volume_sma_10'] = df['Volume'].rolling(window=10).mean()
        df['volume_ratio'] = df['Volume'] / df['volume_sma_10']

        # Momentum
        for period in [5, 10, 20]:
            df[f'momentum_{period}'] = df['Close'] / df['Close'].shift(period) - 1

        # Drop NaN values
        df = df.dropna()

        # Select numeric columns only (exclude any non-numeric)
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        df = df[numeric_cols]

        return df

    def create_sequences(self, data: np.ndarray, seq_length: int = 60) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create sequences for RNN training.

        Args:
            data: Scaled feature data
            seq_length: Length of input sequences

        Returns:
            X, y arrays for training
        """
        X, y = [], []

        for i in range(len(data) - seq_length):
            X.append(data[i:(i + seq_length)])
            # Predict next day's return
            y.append(data[i + seq_length, 0])  # Close price as target

        return np.array(X), np.array(y)

    def build_lstm_model(self, input_shape: Tuple[int, int], units: int = 50) -> keras.Model:
        """Build LSTM model."""
        model = Sequential([
            LSTM(units, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            LSTM(units // 2),
            Dropout(0.2),
            Dense(1)
        ])
        model.compile(optimizer=Adam(learning_rate=0.001), loss='mse')
        return model

    def build_gru_model(self, input_shape: Tuple[int, int], units: int = 50) -> keras.Model:
        """Build GRU model."""
        model = Sequential([
            GRU(units, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            GRU(units // 2),
            Dropout(0.2),
            Dense(1)
        ])
        model.compile(optimizer=Adam(learning_rate=0.001), loss='mse')
        return model

    def build_bidirectional_lstm_model(self, input_shape: Tuple[int, int], units: int = 50) -> keras.Model:
        """Build Bidirectional LSTM model."""
        model = Sequential([
            Bidirectional(LSTM(units, return_sequences=True), input_shape=input_shape),
            Dropout(0.2),
            Bidirectional(LSTM(units // 2)),
            Dropout(0.2),
            Dense(1)
        ])
        model.compile(optimizer=Adam(learning_rate=0.001), loss='mse')
        return model

    def build_bidirectional_gru_model(self, input_shape: Tuple[int, int], units: int = 50) -> keras.Model:
        """Build Bidirectional GRU model."""
        model = Sequential([
            Bidirectional(GRU(units, return_sequences=True), input_shape=input_shape),
            Dropout(0.2),
            Bidirectional(GRU(units // 2)),
            Dropout(0.2),
            Dense(1)
        ])
        model.compile(optimizer=Adam(learning_rate=0.001), loss='mse')
        return model

    def train_model(self, model: keras.Model, X_train: np.ndarray, y_train: np.ndarray,
                   X_val: np.ndarray, y_val: np.ndarray, epochs: int = 100) -> keras.Model:
        """Train RNN model with early stopping."""
        callbacks = [
            EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True),
            ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=1e-6)
        ]

        history = model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=32,
            callbacks=callbacks,
            verbose=0
        )

        return model

    def predict_returns(self, model: keras.Model, X_test: np.ndarray,
                       last_known_price: float) -> np.ndarray:
        """Predict future returns using trained model."""
        predictions = model.predict(X_test, verbose=0)

        # Convert predictions back to price returns
        # This is a simplified approach - in practice you'd use inverse scaling
        predicted_prices = predictions.flatten()

        # Calculate returns from predicted prices
        predicted_returns = np.diff(predicted_prices) / predicted_prices[:-1]

        return predicted_returns

    def evaluate_model(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """Evaluate model performance."""
        mse = mean_squared_error(y_true, y_pred)
        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mse)
        mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100

        return {
            'mse': mse,
            'mae': mae,
            'rmse': rmse,
            'mape': mape
        }

    def generate_recommendation(self, predicted_returns: np.ndarray,
                               current_price: float, risk_tolerance: float = 0.5) -> RNNRecommendation:
        """
        Generate trading recommendation based on predicted returns.

        Args:
            predicted_returns: Array of predicted returns
            current_price: Current stock price
            risk_tolerance: Risk tolerance (0-1, higher = more risk tolerant)

        Returns:
            Trading recommendation
        """
        # Calculate average predicted return
        avg_return = np.mean(predicted_returns)

        # Calculate return volatility (risk)
        return_volatility = np.std(predicted_returns)

        # Normalize risk score (0-1)
        risk_score = min(return_volatility * 10, 1.0)  # Scale volatility to 0-1

        # Determine action based on return and risk
        if avg_return > 0.02 and risk_score < (0.3 + risk_tolerance * 0.4):  # Strong positive return, acceptable risk
            action = "BUY"
            confidence = min(avg_return * 50, 0.9)  # Scale confidence
        elif avg_return > 0.005 and risk_score < (0.5 + risk_tolerance * 0.3):  # Moderate positive return
            action = "BUY"
            confidence = min(avg_return * 30, 0.7)
        elif avg_return < -0.02:  # Strong negative return
            action = "SELL"
            confidence = min(abs(avg_return) * 50, 0.9)
        elif avg_return < -0.005:  # Moderate negative return
            action = "SELL"
            confidence = min(abs(avg_return) * 30, 0.7)
        else:  # Neutral returns
            action = "HOLD"
            confidence = 0.6

        # Create reasoning
        predicted_return_pct = avg_return * 100
        reasoning = f"RNN models predict {predicted_return_pct:.2f}% return over next period. "

        if action == "BUY":
            reasoning += f"Positive momentum suggests buying opportunity with {confidence:.1%} confidence."
        elif action == "SELL":
            reasoning += f"Negative momentum suggests selling with {confidence:.1%} confidence."
        else:
            reasoning += f"Market conditions suggest maintaining current position with {confidence:.1%} confidence."

        return RNNRecommendation(
            action=action,
            confidence=confidence,
            predicted_return=predicted_return_pct,
            risk_score=risk_score,
            reasoning=reasoning,
            model_used="ensemble_rnn"
        )

    def analyze(self, data: pd.DataFrame, ticker: str, prediction_horizon: int = 5) -> RNNAnalysisResult:
        """
        Perform complete RNN analysis for stock prediction.

        Args:
            data: Stock price data
            ticker: Stock ticker symbol
            prediction_horizon: Number of days to predict ahead

        Returns:
            Complete analysis result
        """
        print(f"   Running RNN analysis for {ticker}:")

        # Create features
        feature_data = self.create_features(data)
        if len(feature_data) < 100:
            raise ValueError(f"Insufficient data for RNN analysis. Need at least 100 data points, got {len(feature_data)}")

        # Scale features
        scaled_data = self.scaler.fit_transform(feature_data.values)

        # Create sequences
        seq_length = min(60, len(scaled_data) // 4)  # Adaptive sequence length
        X, y = self.create_sequences(scaled_data, seq_length)

        if len(X) < 50:
            raise ValueError(f"Insufficient sequences for training. Need at least 50, got {len(X)}")

        # Split data
        train_size = int(len(X) * 0.7)
        val_size = int(len(X) * 0.15)

        X_train = X[:train_size]
        y_train = y[:train_size]
        X_val = X[train_size:train_size + val_size]
        y_val = y[train_size:train_size + val_size]
        X_test = X[train_size + val_size:]
        y_test = y[train_size + val_size:]

        print(f"    Training sequences: {len(X_train)}, Validation: {len(X_val)}, Test: {len(X_test)}")

        # Train models
        models_results = {}
        available_models = self.get_available_models()

        for model_name in available_models:
            try:
                print(f"    Training {model_name.upper()} model...")

                # Build model
                input_shape = (X_train.shape[1], X_train.shape[2])

                if model_name == 'lstm':
                    model = self.build_lstm_model(input_shape)
                elif model_name == 'gru':
                    model = self.build_gru_model(input_shape)
                elif model_name == 'bidirectional_lstm':
                    model = self.build_bidirectional_lstm_model(input_shape)
                elif model_name == 'bidirectional_gru':
                    model = self.build_bidirectional_gru_model(input_shape)

                # Train model
                trained_model = self.train_model(model, X_train, y_train, X_val, y_val)

                # Make predictions
                predictions = trained_model.predict(X_test, verbose=0).flatten()

                # Evaluate
                metrics = self.evaluate_model(y_test, predictions)

                # Calculate predicted returns
                last_known_price = feature_data.iloc[-1]['Close']
                predicted_returns = self.predict_returns(trained_model, X_test[-prediction_horizon:], last_known_price)

                models_results[model_name] = RNNModelResult(
                    model_name=model_name,
                    mse=metrics['mse'],
                    mae=metrics['mae'],
                    rmse=metrics['rmse'],
                    mape=metrics['mape'],
                    predicted_returns=predicted_returns.tolist(),
                    actual_returns=[],  # Would need actual future data
                    predictions=predictions,
                    actuals=y_test
                )

                print(f"      {model_name}: MSE={metrics['mse']:.4f}, MAE={metrics['mae']:.4f}")
            except Exception as e:
                print(f"    ❌ Failed to train {model_name}: {str(e)}")
                continue

        if not models_results:
            raise ValueError("No RNN models could be trained successfully")

        # Find best model (lowest RMSE)
        best_model_name = min(models_results.keys(), key=lambda x: models_results[x].rmse)
        best_model_result = models_results[best_model_name]

        # Generate recommendation
        current_price = data['Close'].iloc[-1]
        recommendation = self.generate_recommendation(
            np.array(best_model_result.predicted_returns),
            current_price
        )

        # Feature importance (simplified - using correlation with target)
        feature_importance = {}
        for col in feature_data.columns:
            if col != 'Close':  # Don't include target
                corr = abs(feature_data[col].corr(feature_data['Close']))
                feature_importance[col] = corr

        # Sort by importance
        feature_importance = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True))

        return RNNAnalysisResult(
            ticker=ticker,
            models_results=models_results,
            recommendation=recommendation,
            feature_importance=feature_importance,
            analysis_date=datetime.now(),
            prediction_horizon=prediction_horizon
        )
