#!/usr/bin/env python3
"""
Transformer-based Analyzer Module
Implements Temporal Fusion Transformer (TFT) and other transformer architectures
for stock price prediction and trading recommendations.
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
    # Suppress TensorFlow warnings and info messages
    tf.get_logger().setLevel('ERROR')
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
    from tensorflow import keras
    from tensorflow.keras.models import Model
    from tensorflow.keras.layers import (
        Dense, Dropout, LayerNormalization, MultiHeadAttention,
        GlobalAveragePooling1D, Input, Concatenate, Flatten,
        Conv1D, MaxPooling1D, LSTM, GRU
    )
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
    from sklearn.preprocessing import MinMaxScaler, StandardScaler
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
class TransformerModelResult:
    """Results from Transformer model training and prediction."""
    model_name: str
    mse: float
    mae: float
    rmse: float
    mape: float
    predicted_returns: List[float]
    actual_returns: List[float]
    predictions: np.ndarray
    actuals: np.ndarray
    attention_weights: Optional[np.ndarray] = None


@dataclass
class TransformerRecommendation:
    """Transformer-based trading recommendation."""
    ticker: str
    action: str  # BUY, SELL, HOLD
    confidence: float
    predicted_return_pct: float
    risk_score: float
    reasoning: str
    model_used: str
    attention_focus: Dict[str, float]  # Which features were most attended to


@dataclass
class TransformerAnalysisResult:
    """Complete Transformer analysis results."""
    ticker: str
    models_trained: List[TransformerModelResult]
    best_model: str
    recommendation: TransformerRecommendation
    feature_analysis: Dict[str, Any]
    prediction_horizon: int
    training_period: str


class TemporalFusionTransformer:
    """
    Temporal Fusion Transformer (TFT) implementation for multivariate time series forecasting.

    Based on the paper: "Temporal Fusion Transformers for Interpretable Multi-horizon Time Series Forecasting"
    by Bryan Lim et al.
    """

    def __init__(self, input_shape: Tuple[int, int], output_dim: int = 1,
                 num_heads: int = 4, ff_dim: int = 64, num_blocks: int = 2):
        self.input_shape = input_shape
        self.output_dim = output_dim
        self.num_heads = num_heads
        self.ff_dim = ff_dim
        self.num_blocks = num_blocks
        self.model = None

    def build_model(self):
        """Build the TFT model architecture."""
        inputs = Input(shape=self.input_shape)

        # Variable selection network
        var_selection = Dense(self.input_shape[-1] // 2, activation='relu')(inputs)
        var_selection = Dense(1, activation='sigmoid')(var_selection)

        # Gating mechanism
        gated_inputs = inputs * var_selection

        # Multi-head attention blocks
        x = gated_inputs
        for _ in range(self.num_blocks):
            # Self-attention
            attn_output = MultiHeadAttention(
                num_heads=self.num_heads,
                key_dim=self.input_shape[-1] // self.num_heads
            )(x, x)
            attn_output = Dropout(0.1)(attn_output)
            x = LayerNormalization(epsilon=1e-6)(x + attn_output)

            # Feed-forward
            ff_output = Dense(self.ff_dim, activation='relu')(x)
            ff_output = Dense(self.input_shape[-1])(ff_output)
            ff_output = Dropout(0.1)(ff_output)
            x = LayerNormalization(epsilon=1e-6)(x + ff_output)

        # Global pooling and output
        x = GlobalAveragePooling1D()(x)
        x = Dense(64, activation='relu')(x)
        x = Dropout(0.2)(x)
        outputs = Dense(self.output_dim)(x)

        self.model = Model(inputs=inputs, outputs=outputs)
        self.model.compile(optimizer=Adam(learning_rate=0.001),
                          loss='mse', metrics=['mae'])

        return self.model


class TransformerAnalyzer:
    """
    Transformer-based Analyzer for stock price prediction.

    Implements Temporal Fusion Transformer (TFT) and other transformer architectures
    for advanced time series forecasting with attention mechanisms.
    """

    def __init__(self, models_dir: str = "models"):
        self.models_dir = models_dir
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.models = {}

        # Create models directory if it doesn't exist
        if not os.path.exists(models_dir):
            os.makedirs(models_dir)

    def get_available_models(self) -> List[str]:
        """Get list of available Transformer models."""
        return ['tft', 'transformer_encoder', 'conv_transformer']

    def create_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Create comprehensive technical features for Transformer analysis.

        Args:
            data: Stock price data

        Returns:
            DataFrame with engineered features
        """
        df = data.copy()

        # Basic price features
        df['returns'] = df['Close'].pct_change()
        df['log_returns'] = np.log(df['Close'] / df['Close'].shift(1))

        # Moving averages
        for period in [5, 10, 20, 50]:
            df[f'SMA_{period}'] = df['Close'].rolling(window=period).mean()
            df[f'EMA_{period}'] = df['Close'].ewm(span=period).mean()

        # Volatility measures
        df['volatility_20'] = df['returns'].rolling(window=20).std()
        df['volatility_50'] = df['returns'].rolling(window=50).std()

        # RSI
        def calculate_rsi(data, period=14):
            delta = data.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs))

        df['RSI'] = calculate_rsi(df['Close'])

        # MACD
        ema_12 = df['Close'].ewm(span=12).mean()
        ema_26 = df['Close'].ewm(span=26).mean()
        df['MACD'] = ema_12 - ema_26
        df['MACD_signal'] = df['MACD'].ewm(span=9).mean()
        df['MACD_hist'] = df['MACD'] - df['MACD_signal']

        # Bollinger Bands
        sma_20 = df['Close'].rolling(window=20).mean()
        std_20 = df['Close'].rolling(window=20).std()
        df['BB_upper'] = sma_20 + (std_20 * 2)
        df['BB_lower'] = sma_20 - (std_20 * 2)
        df['BB_middle'] = sma_20

        # Volume features
        df['volume_sma_20'] = df['Volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['Volume'] / df['volume_sma_20']

        # Momentum indicators
        for period in [5, 10, 14]:
            df[f'momentum_{period}'] = df['Close'] / df['Close'].shift(period) - 1

        # Drop NaN values
        df = df.dropna()

        return df

    def prepare_sequences(self, data: pd.DataFrame, sequence_length: int = 60,
                         prediction_horizon: int = 1) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare sequences for Transformer training.

        Args:
            data: Feature-engineered data
            sequence_length: Length of input sequences
            prediction_horizon: Days to predict ahead

        Returns:
            Tuple of (X, y) arrays
        """
        # Select only numeric columns for features
        feature_cols = [col for col in data.columns if col not in ['Close', 'Date'] and data[col].dtype in ['float64', 'int64', 'float32', 'int32']]

        X, y = [], []

        for i in range(sequence_length, len(data) - prediction_horizon + 1):
            X.append(data[feature_cols].iloc[i-sequence_length:i].values)
            y.append(data['Close'].iloc[i + prediction_horizon - 1])

        return np.array(X), np.array(y)

    def build_temporal_fusion_transformer(self, input_shape: Tuple[int, int]) -> Model:
        """Build Temporal Fusion Transformer model."""
        tft = TemporalFusionTransformer(input_shape=input_shape)
        return tft.build_model()

    def build_transformer_encoder(self, input_shape: Tuple[int, int]) -> Model:
        """Build a simpler transformer encoder model."""
        inputs = Input(shape=input_shape)

        # Positional encoding (simplified)
        positions = tf.range(start=0, limit=input_shape[0], delta=1)
        position_embeddings = tf.keras.layers.Embedding(
            input_dim=input_shape[0], output_dim=input_shape[1]
        )(positions)

        # Add positional encoding to inputs
        x = inputs + position_embeddings

        # Multi-head attention
        attn_output = MultiHeadAttention(num_heads=4, key_dim=input_shape[1] // 4)(x, x)
        x = LayerNormalization(epsilon=1e-6)(x + attn_output)

        # Feed-forward
        ff_output = Dense(64, activation='relu')(x)
        ff_output = Dense(input_shape[1])(ff_output)
        x = LayerNormalization(epsilon=1e-6)(x + ff_output)

        # Global pooling and output
        x = GlobalAveragePooling1D()(x)
        x = Dense(32, activation='relu')(x)
        x = Dropout(0.2)(x)
        outputs = Dense(1)(x)

        model = Model(inputs=inputs, outputs=outputs)
        model.compile(optimizer=Adam(learning_rate=0.001), loss='mse', metrics=['mae'])

        return model

    def build_conv_transformer(self, input_shape: Tuple[int, int]) -> Model:
        """Build a convolutional transformer hybrid model."""
        inputs = Input(shape=input_shape)

        # Convolutional feature extraction
        x = Conv1D(filters=64, kernel_size=3, activation='relu')(inputs)
        x = MaxPooling1D(pool_size=2)(x)
        x = Conv1D(filters=128, kernel_size=3, activation='relu')(x)
        x = MaxPooling1D(pool_size=2)(x)

        # Transformer layers
        attn_output = MultiHeadAttention(num_heads=4, key_dim=128 // 4)(x, x)
        x = LayerNormalization(epsilon=1e-6)(x + attn_output)

        # Global pooling and output
        x = GlobalAveragePooling1D()(x)
        x = Dense(64, activation='relu')(x)
        x = Dropout(0.3)(x)
        outputs = Dense(1)(x)

        model = Model(inputs=inputs, outputs=outputs)
        model.compile(optimizer=Adam(learning_rate=0.001), loss='mse', metrics=['mae'])

        return model

    def train_model(self, model_name: str, X_train: np.ndarray, y_train: np.ndarray,
                   X_val: np.ndarray, y_val: np.ndarray, epochs: int = 50) -> Model:
        """
        Train a Transformer model.

        Args:
            model_name: Name of the model to train
            X_train: Training features
            y_train: Training targets
            X_val: Validation features
            y_val: Validation targets
            epochs: Number of training epochs

        Returns:
            Trained model
        """
        if not TENSORFLOW_AVAILABLE:
            raise ImportError("TensorFlow is required for Transformer models")

        # Build model
        if model_name == 'tft':
            model = self.build_temporal_fusion_transformer(X_train.shape[1:])
        elif model_name == 'transformer_encoder':
            model = self.build_transformer_encoder(X_train.shape[1:])
        elif model_name == 'conv_transformer':
            model = self.build_conv_transformer(X_train.shape[1:])
        else:
            raise ValueError(f"Unknown model: {model_name}")

        # Callbacks
        early_stopping = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
        reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=1e-6)

        # Train model
        history = model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=32,
            callbacks=[early_stopping, reduce_lr],
            verbose=0
        )

        # Save model
        model_path = os.path.join(self.models_dir, f'{model_name}_transformer.keras')
        model.save(model_path)

        self.models[model_name] = model
        return model

    def predict(self, model_name: str, X: np.ndarray) -> np.ndarray:
        """Make predictions with a trained model."""
        if model_name not in self.models:
            model_path = os.path.join(self.models_dir, f'{model_name}_transformer.keras')
            if os.path.exists(model_path):
                self.models[model_name] = tf.keras.models.load_model(model_path)
            else:
                raise ValueError(f"Model {model_name} not found")

        return self.models[model_name].predict(X, verbose=0)

    def evaluate_model(self, model_name: str, X_test: np.ndarray, y_test: np.ndarray,
                      predictions: np.ndarray) -> TransformerModelResult:
        """Evaluate model performance."""
        mse = mean_squared_error(y_test, predictions)
        mae = mean_absolute_error(y_test, predictions)
        rmse = np.sqrt(mse)
        mape = np.mean(np.abs((y_test - predictions) / y_test)) * 100

        # Calculate returns
        actual_returns = np.diff(y_test) / y_test[:-1]
        predicted_returns = np.diff(predictions.flatten()) / predictions[:-1].flatten()

        return TransformerModelResult(
            model_name=model_name,
            mse=mse,
            mae=mae,
            rmse=rmse,
            mape=mape,
            predicted_returns=predicted_returns.tolist(),
            actual_returns=actual_returns.tolist(),
            predictions=predictions,
            actuals=y_test
        )

    def generate_recommendation(self, ticker: str, model_results: List[TransformerModelResult],
                               current_price: float, predictions: np.ndarray) -> TransformerRecommendation:
        """Generate trading recommendation based on model results."""
        # Find best model
        best_result = min(model_results, key=lambda x: x.mse)
        best_model = best_result.model_name

        # Calculate predicted return
        last_actual = best_result.actuals[-1]
        last_predicted = best_result.predictions[-1][0] if len(best_result.predictions.shape) > 1 else best_result.predictions[-1]
        predicted_return_pct = ((last_predicted - last_actual) / last_actual) * 100

        # Determine action based on prediction confidence
        confidence = 1 - (best_result.mape / 100)  # Higher confidence for lower MAPE

        if predicted_return_pct > 2 and confidence > 0.6:
            action = "BUY"
            reasoning = f"Strong upward trend predicted with {predicted_return_pct:.2f}% return"
        elif predicted_return_pct < -2 and confidence > 0.6:
            action = "SELL"
            reasoning = f"Downward trend predicted with {predicted_return_pct:.2f}% return"
        else:
            action = "HOLD"
            reasoning = f"Neutral signal with {predicted_return_pct:.2f}% predicted return"

        # Calculate risk score (simplified)
        risk_score = best_result.rmse / current_price

        # Mock attention focus (would need actual attention weights from TFT)
        attention_focus = {
            'price_trends': 0.4,
            'volume': 0.3,
            'technical_indicators': 0.2,
            'momentum': 0.1
        }

        return TransformerRecommendation(
            ticker=ticker,
            action=action,
            confidence=confidence,
            predicted_return_pct=predicted_return_pct,
            risk_score=risk_score,
            reasoning=reasoning,
            model_used=best_model,
            attention_focus=attention_focus
        )

    def analyze(self, ticker: str, data: pd.DataFrame, models: List[str] = None,
               sequence_length: int = 60, prediction_horizon: int = 1) -> TransformerAnalysisResult:
        """
        Perform complete Transformer analysis.

        Args:
            ticker: Stock ticker symbol
            data: Historical price data
            models: List of models to train (default: all available)
            sequence_length: Length of input sequences
            prediction_horizon: Days to predict ahead

        Returns:
            Complete analysis results
        """
        if models is None:
            models = self.get_available_models()

        # Create features
        feature_data = self.create_features(data)

        # Prepare sequences
        X, y = self.prepare_sequences(feature_data, sequence_length, prediction_horizon)

        # Scale data
        X_reshaped = X.reshape(X.shape[0], -1)
        X_scaled = self.scaler.fit_transform(X_reshaped)
        X_scaled = X_scaled.reshape(X.shape)

        # Split data
        train_size = int(len(X) * 0.7)
        val_size = int(len(X) * 0.2)

        X_train = X_scaled[:train_size]
        y_train = y[:train_size]
        X_val = X_scaled[train_size:train_size + val_size]
        y_val = y[train_size:train_size + val_size]
        X_test = X_scaled[train_size + val_size:]
        y_test = y[train_size + val_size:]

        # Train and evaluate models
        model_results = []
        for model_name in models:
            try:
                print(f"Training {model_name}...")
                model = self.train_model(model_name, X_train, y_train, X_val, y_val)

                # Make predictions
                predictions = self.predict(model_name, X_test)

                # Evaluate
                result = self.evaluate_model(model_name, X_test, y_test, predictions)
                model_results.append(result)

                print(f"{model_name} - MSE: {result.mse:.4f}, MAE: {result.mae:.4f}, MAPE: {result.mape:.2f}%")

            except Exception as e:
                print(f"Error training {model_name}: {str(e)}")
                continue

        if not model_results:
            raise ValueError("No models were successfully trained")

        # Generate recommendation
        current_price = data['Close'].iloc[-1]
        recommendation = self.generate_recommendation(ticker, model_results, current_price, predictions)

        # Feature analysis
        feature_analysis = {
            'total_features': len(feature_data.columns) - 2,  # Exclude Date and Close
            'sequence_length': sequence_length,
            'prediction_horizon': prediction_horizon,
            'training_samples': len(X_train),
            'validation_samples': len(X_val),
            'test_samples': len(X_test)
        }

        return TransformerAnalysisResult(
            ticker=ticker,
            models_trained=model_results,
            best_model=min(model_results, key=lambda x: x.mse).model_name,
            recommendation=recommendation,
            feature_analysis=feature_analysis,
            prediction_horizon=prediction_horizon,
            training_period=f"{len(feature_data)} days"
        )
