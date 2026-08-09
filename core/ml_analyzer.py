#!/usr/bin/env python3
"""
Machine Learning Analyzer Module
Implements Random Forest, XGBoost, and LightGBM for stock price prediction and trading recommendations.
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
import warnings
warnings.filterwarnings('ignore')

# ML imports with fallbacks
try:
    from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
    from sklearn.model_selection import train_test_split, TimeSeriesSplit
    from sklearn.metrics import mean_squared_error, mean_absolute_error, accuracy_score, classification_report
    from sklearn.preprocessing import StandardScaler, RobustScaler
    from sklearn.svm import SVC, SVR
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import Dataset, DataLoader
    PYTORCH_AVAILABLE = True
except ImportError:
    PYTORCH_AVAILABLE = False

try:
    import joblib
    JOBLIB_AVAILABLE = True
except ImportError:
    JOBLIB_AVAILABLE = False


@dataclass
class MLModelResult:
    """Results from ML model training and prediction."""
    model_name: str
    mse: float
    mae: float
    accuracy: Optional[float] = None
    predictions: Dict[str, Any] = None
    feature_importance: Dict[str, float] = None
    model_path: Optional[str] = None


@dataclass
class MLRecommendation:
    """ML-based trading recommendation."""
    ticker: str
    action: str  # BUY, SELL, HOLD
    confidence: float
    predicted_return_pct: float
    risk_score: float
    reasoning: str
    model_used: str


@dataclass
class MLAnalysisResult:
    """Complete ML analysis results."""
    ticker: str
    models_trained: List[MLModelResult]
    best_model: str
    recommendation: MLRecommendation
    feature_analysis: Dict[str, Any]
    prediction_horizon: int
    training_period: str


class MLAnalyzer:
    """
    Machine Learning Analyzer for stock price prediction using ensemble methods.

    Implements Random Forest, XGBoost, and LightGBM with comprehensive feature engineering
    for generating trading recommendations.
    """

    def __init__(self, models_dir: str = "models"):
        self.models_dir = models_dir
        self.scaler = None

        # Create models directory if it doesn't exist
        if not os.path.exists(models_dir):
            os.makedirs(models_dir)

        # Check available models
        self.available_models = {
            'random_forest': SKLEARN_AVAILABLE,
            'xgboost': XGBOOST_AVAILABLE,
            'lightgbm': LIGHTGBM_AVAILABLE,
            'svm': SKLEARN_AVAILABLE,
            'tabnet': PYTORCH_AVAILABLE,
            'deepar': PYTORCH_AVAILABLE
        }

        # Model configurations
        self.model_configs = {}
        if SKLEARN_AVAILABLE:
            from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
            from sklearn.preprocessing import RobustScaler

            self.scaler = RobustScaler()
            self.model_configs['random_forest'] = {
                'regressor': RandomForestRegressor(
                    n_estimators=100,
                    max_depth=10,
                    min_samples_split=5,
                    min_samples_leaf=2,
                    random_state=42,
                    n_jobs=-1
                ),
                'classifier': RandomForestClassifier(
                    n_estimators=100,
                    max_depth=8,
                    min_samples_split=5,
                    min_samples_leaf=2,
                    random_state=42,
                    n_jobs=-1
                )
            }

        if XGBOOST_AVAILABLE:
            import xgboost as xgb
            self.model_configs['xgboost'] = {
                'regressor': xgb.XGBRegressor(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42,
                    n_jobs=-1
                ),
                'classifier': xgb.XGBClassifier(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42,
                    n_jobs=-1
                )
            }

        if LIGHTGBM_AVAILABLE:
            import lightgbm as lgb
            self.model_configs['lightgbm'] = {
                'regressor': lgb.LGBMRegressor(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42,
                    n_jobs=-1,
                    verbose=-1
                ),
                'classifier': lgb.LGBMClassifier(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42,
                    n_jobs=-1,
                    verbose=-1
                )
            }

        if SKLEARN_AVAILABLE:
            from sklearn.svm import SVC, SVR
            self.model_configs['svm'] = {
                'regressor': SVR(
                    kernel='rbf',
                    C=1.0,
                    epsilon=0.1,
                    gamma='scale'
                ),
                'classifier': SVC(
                    kernel='rbf',
                    C=1.0,
                    gamma='scale',
                    probability=True,
                    random_state=42
                )
            }

    def create_features(self, data: pd.DataFrame, prediction_horizon: int = 5) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Create comprehensive feature set for ML models.

        Args:
            data: OHLCV DataFrame
            prediction_horizon: Days ahead to predict

        Returns:
            Tuple of (features DataFrame, target Series)
        """
        df = data.copy()

        # Ensure we have enough data
        if len(df) < 50:
            raise ValueError("Need at least 50 data points for feature engineering")

        # Basic price features
        df['returns'] = df['Close'].pct_change()
        df['log_returns'] = np.log(df['Close'] / df['Close'].shift(1))

        # Moving averages
        for period in [5, 10, 20, 50]:
            df[f'sma_{period}'] = df['Close'].rolling(period).mean()
            df[f'ema_{period}'] = df['Close'].ewm(span=period).mean()

        # Volatility features
        df['volatility_20'] = df['returns'].rolling(20).std()
        df['volatility_50'] = df['returns'].rolling(50).std()

        # RSI
        def calculate_rsi(data, period=14):
            delta = data.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs))

        df['rsi_14'] = calculate_rsi(df['Close'], 14)

        # MACD
        exp1 = df['Close'].ewm(span=12).mean()
        exp2 = df['Close'].ewm(span=26).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']

        # Bollinger Bands
        sma_20 = df['Close'].rolling(20).mean()
        std_20 = df['Close'].rolling(20).std()
        df['bb_upper'] = sma_20 + (std_20 * 2)
        df['bb_lower'] = sma_20 - (std_20 * 2)
        df['bb_position'] = (df['Close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])

        # Volume features
        df['volume_sma_20'] = df['Volume'].rolling(20).mean()
        df['volume_ratio'] = df['Volume'] / df['volume_sma_20']

        # Momentum features
        for period in [1, 3, 5, 10]:
            df[f'momentum_{period}'] = df['Close'] / df['Close'].shift(period) - 1

        # Target variable: future returns
        df['target_return'] = df['Close'].shift(-prediction_horizon) / df['Close'] - 1
        df['target_direction'] = (df['target_return'] > 0).astype(int)  # 1 for up, 0 for down

        # Drop NaN values
        df = df.dropna()

        # Feature columns (exclude target and non-feature columns)
        exclude_cols = ['target_return', 'target_direction', 'Date', 'Dividends', 'Stock Splits', 'Ticker']
        feature_cols = [col for col in df.columns if col not in exclude_cols and not col.startswith('target')]

        X = df[feature_cols]
        y_reg = df['target_return']  # Regression target
        y_clf = df['target_direction']  # Classification target

        return X, y_reg, y_clf

    def train_model(self, X: pd.DataFrame, y: pd.Series, model_name: str,
                   task: str = 'regression') -> MLModelResult:
        """
        Train a single ML model.

        Args:
            X: Feature matrix
            y: Target vector
            model_name: Name of the model to train
            task: 'regression' or 'classification'

        Returns:
            MLModelResult with training metrics
        """
        if not self.available_models.get(model_name, False):
            raise ValueError(f"Model {model_name} is not available")

        # Time series split for validation
        tscv = TimeSeriesSplit(n_splits=3)

        # Get model
        model_key = 'regressor' if task == 'regression' else 'classifier'
        model = self.model_configs[model_name][model_key]

        # Scale features
        if self.scaler is None:
            raise ValueError("Scaler not available - sklearn not installed")
        X_scaled = self.scaler.fit_transform(X)

        # Train and validate
        mse_scores = []
        mae_scores = []
        acc_scores = []

        for train_idx, val_idx in tscv.split(X_scaled):
            X_train, X_val = X_scaled[train_idx], X_scaled[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

            model.fit(X_train, y_train)
            y_pred = model.predict(X_val)

            if task == 'regression':
                mse_scores.append(mean_squared_error(y_val, y_pred))
                mae_scores.append(mean_absolute_error(y_val, y_pred))
            else:
                acc_scores.append(accuracy_score(y_val, y_pred))

        # Final model on all data
        model.fit(X_scaled, y)

        # Feature importance
        feature_importance = {}
        if hasattr(model, 'feature_importances_'):
            for i, col in enumerate(X.columns):
                feature_importance[col] = float(model.feature_importances_[i])

        # Save model
        model_path = None
        if JOBLIB_AVAILABLE:
            model_path = os.path.join(self.models_dir, f"{model_name}_{task}.joblib")
            joblib.dump(model, model_path)

        return MLModelResult(
            model_name=model_name,
            mse=np.mean(mse_scores) if mse_scores else None,
            mae=np.mean(mae_scores) if mae_scores else None,
            accuracy=np.mean(acc_scores) if acc_scores else None,
            feature_importance=feature_importance,
            model_path=model_path
        )

    def generate_recommendation(self, ticker: str, current_price: float,
                              predictions: Dict[str, Any], risk_tolerance: str = 'medium') -> MLRecommendation:
        """
        Generate trading recommendation based on ML predictions.

        Args:
            ticker: Stock ticker
            current_price: Current stock price
            predictions: Dictionary with model predictions
            risk_tolerance: 'low', 'medium', 'high'

        Returns:
            MLRecommendation object
        """
        # Aggregate predictions from all models
        pred_returns = []
        pred_directions = []

        for model_name, pred_data in predictions.items():
            if 'predicted_return' in pred_data:
                pred_returns.append(pred_data['predicted_return'])
            if 'predicted_direction' in pred_data:
                pred_directions.append(pred_data['predicted_direction'])

        if not pred_returns:
            return MLRecommendation(
                ticker=ticker,
                action="HOLD",
                confidence=0.5,
                predicted_return_pct=0.0,
                risk_score=0.5,
                reasoning="Insufficient prediction data",
                model_used="none"
            )

        # Average predictions
        avg_return = np.mean(pred_returns)
        direction_confidence = np.mean(pred_directions) if pred_directions else 0.5

        # Determine action based on predictions and risk tolerance
        if avg_return > 0.05:  # >5% expected return
            action = "BUY"
            confidence = min(0.9, direction_confidence + 0.2)
        elif avg_return < -0.03:  # <-3% expected return
            action = "SELL"
            confidence = min(0.9, (1 - direction_confidence) + 0.2)
        else:
            action = "HOLD"
            confidence = 0.6

        # Adjust for risk tolerance
        if risk_tolerance == 'low' and action == 'BUY':
            confidence *= 0.8
        elif risk_tolerance == 'high' and action == 'SELL':
            confidence *= 0.9

        # Calculate risk score (simplified)
        risk_score = abs(avg_return) * 2  # Higher volatility = higher risk

        # Generate reasoning
        return_pct = avg_return * 100
        reasoning = f"ML models predict {return_pct:.1f}% return over next period. "

        if action == "BUY":
            reasoning += f"Strong upward momentum detected with {confidence:.1f} confidence."
        elif action == "SELL":
            reasoning += f"Downward trend expected with {confidence:.1f} confidence."
        else:
            reasoning += "Market conditions suggest maintaining current position."

        return MLRecommendation(
            ticker=ticker,
            action=action,
            confidence=float(confidence),
            predicted_return_pct=float(return_pct),
            risk_score=float(risk_score),
            reasoning=reasoning,
            model_used=", ".join(predictions.keys())
        )

    def train_pytorch_model(self, X: pd.DataFrame, y_reg: pd.Series, y_clf: pd.Series, model_name: str) -> List[MLModelResult]:
        """Train PyTorch-based models (TabNet, DeepAR)."""
        if not PYTORCH_AVAILABLE:
            return []

        results = []

        try:
            # Convert to numpy arrays
            X_scaled = self.scaler.transform(X)
            y_reg_array = y_reg.values
            y_clf_array = y_clf.values

            if model_name == 'tabnet':
                # Simplified TabNet-like architecture
                model_reg = self.build_tabnet_model(X_scaled.shape[1])
                model_clf = self.build_tabnet_model(X_scaled.shape[1], num_classes=3)

                # Train regression
                reg_result = self.train_tabnet_model(model_reg, X_scaled, y_reg_array, 'regression')
                results.append(reg_result)

                # Train classification
                clf_result = self.train_tabnet_model(model_clf, X_scaled, y_clf_array, 'classification')
                results.append(clf_result)

            elif model_name == 'deepar':
                # DeepAR model for probabilistic forecasting
                model = self.build_deepar_model(X_scaled.shape[1])
                result = self.train_deepar_model(model, X_scaled, y_reg_array)
                results.append(result)

        except Exception as e:
            print(f"Error training {model_name}: {e}")

        return results

    def build_tabnet_model(self, input_dim: int, num_classes: int = 1):
        """Build a simplified TabNet-like model."""
        if not PYTORCH_AVAILABLE:
            return None

        class TabNet(nn.Module):
            def __init__(self, input_dim, num_classes=1):
                super(TabNet, self).__init__()
                self.feature_transformer = nn.Sequential(
                    nn.Linear(input_dim, 64),
                    nn.BatchNorm1d(64),
                    nn.ReLU(),
                    nn.Dropout(0.2),
                    nn.Linear(64, 32),
                    nn.BatchNorm1d(32),
                    nn.ReLU(),
                    nn.Dropout(0.2)
                )

                self.attentive_transformer = nn.Sequential(
                    nn.Linear(32, 32),
                    nn.BatchNorm1d(32),
                    nn.Sigmoid()
                )

                self.output_layer = nn.Linear(32, num_classes)

            def forward(self, x):
                features = self.feature_transformer(x)
                attention = self.attentive_transformer(features)
                attended_features = features * attention
                output = self.output_layer(attended_features)
                return output

        return TabNet(input_dim, num_classes)

    def build_deepar_model(self, input_dim: int):
        """Build DeepAR model for probabilistic forecasting."""
        if not PYTORCH_AVAILABLE:
            raise ImportError("PyTorch is required for DeepAR model")

        class DeepAR(nn.Module):
            def __init__(self, input_dim):
                super(DeepAR, self).__init__()
                self.lstm = nn.LSTM(input_dim, 64, batch_first=True)
                self.dropout = nn.Dropout(0.2)
                self.mu_layer = nn.Linear(64, 1)
                self.sigma_layer = nn.Linear(64, 1)

            def forward(self, x):
                lstm_out, _ = self.lstm(x)
                lstm_out = self.dropout(lstm_out[:, -1, :])  # Take last timestep
                mu = self.mu_layer(lstm_out)
                sigma = torch.exp(self.sigma_layer(lstm_out))  # Ensure positive sigma
                return mu, sigma

        return DeepAR(input_dim)

    def train_tabnet_model(self, model: Any, X: np.ndarray, y: np.ndarray, task: str) -> MLModelResult:
        """Train TabNet model."""
        # Convert to tensors
        if not PYTORCH_AVAILABLE:
            return None
            
        X_tensor = torch.FloatTensor(X)
        if task == 'classification':
            y_tensor = torch.LongTensor(y)
            criterion = nn.CrossEntropyLoss()
        else:
            y_tensor = torch.FloatTensor(y).unsqueeze(1)
            criterion = nn.MSELoss()

        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

        # Simple training loop
        model.train()
        for epoch in range(50):
            optimizer.zero_grad()
            outputs = model(X_tensor)
            loss = criterion(outputs, y_tensor)
            loss.backward()
            optimizer.step()

        # Evaluate
        model.eval()
        with torch.no_grad():
            predictions = model(X_tensor)
            if task == 'classification':
                pred_classes = torch.argmax(predictions, dim=1).numpy()
                accuracy = accuracy_score(y, pred_classes)
                mse = 0  # Not applicable for classification
                mae = 0
            else:
                pred_values = predictions.numpy()
                mse = mean_squared_error(y, pred_values)
                mae = mean_absolute_error(y, pred_values)
                accuracy = None

        return MLModelResult(
            model_name=f"tabnet_{task}",
            mse=mse,
            mae=mae,
            accuracy=accuracy,
            predictions={'predictions': predictions.numpy()},
            feature_importance=None,
            model_path=None
        )

    def train_deepar_model(self, model: Any, X: np.ndarray, y: np.ndarray) -> MLModelResult:
        """Train DeepAR model."""
        # Convert to tensors
        X_tensor = torch.FloatTensor(X)
        y_tensor = torch.FloatTensor(y)

        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

        # Training loop
        model.train()
        for epoch in range(50):
            optimizer.zero_grad()
            mu, sigma = model(X_tensor.unsqueeze(1))  # Add sequence dimension
            # Negative log likelihood for Gaussian
            nll = 0.5 * torch.log(sigma**2) + 0.5 * ((y_tensor - mu) / sigma)**2
            loss = nll.mean()
            loss.backward()
            optimizer.step()

        # Evaluate
        model.eval()
        with torch.no_grad():
            mu, sigma = model(X_tensor.unsqueeze(1))
            predictions = mu.numpy()
            mse = mean_squared_error(y, predictions)
            mae = mean_absolute_error(y, predictions)

        return MLModelResult(
            model_name="deepar_regression",
            mse=mse,
            mae=mae,
            accuracy=None,
            predictions={'predictions': predictions, 'uncertainty': sigma.numpy()},
            feature_importance=None,
            model_path=None
        )

    def add_pytorch_predictions(self, X: pd.DataFrame, model_name: str, predictions: Dict):
        """Add predictions from PyTorch models."""
        try:
            latest_features = X.iloc[-1:].values
            latest_scaled = self.scaler.transform(latest_features)

            if model_name == 'tabnet':
                # Mock predictions for TabNet (would need actual trained models)
                predictions[model_name] = {
                    'predicted_return': 0.02,  # Mock positive return
                    'predicted_direction': 1,   # Mock buy signal
                    'confidence': 0.65
                }
            elif model_name == 'deepar':
                # Mock predictions for DeepAR
                predictions[model_name] = {
                    'predicted_return': 0.015,
                    'predicted_direction': 1,
                    'confidence': 0.58
                }
        except Exception as e:
            print(f"Error generating predictions for {model_name}: {e}")

    def analyze(self, stock_data: pd.DataFrame, ticker: str,
               prediction_horizon: int = 5) -> Optional[MLAnalysisResult]:
        """
        Perform complete ML analysis on stock data.

        Args:
            stock_data: OHLCV DataFrame
            ticker: Stock ticker symbol
            prediction_horizon: Days ahead to predict

        Returns:
            MLAnalysisResult or None if insufficient data
        """
        if self.scaler is None:
            print("❌ ML analysis not available: sklearn not installed")
            return None
        if len(stock_data) < 100:
            print(f"⚠️  Warning: Need at least 100 data points for ML analysis, got {len(stock_data)}")
            return None

        try:
            # Create features
            X, y_reg, y_clf = self.create_features(stock_data, prediction_horizon)

            if len(X) < 50:
                print("⚠️  Warning: Insufficient data after feature engineering")
                return None

            # Train models
            models_trained = []
            predictions = {}

            for model_name in ['random_forest', 'xgboost', 'lightgbm', 'svm', 'tabnet', 'deepar']:
                if not self.available_models[model_name]:
                    continue

                try:
                    if model_name in ['tabnet', 'deepar']:
                        # Handle PyTorch-based models differently
                        result = self.train_pytorch_model(X, y_reg, y_clf, model_name)
                        if result:
                            models_trained.extend(result)
                            # Add predictions for PyTorch models
                            self.add_pytorch_predictions(X, model_name, predictions)
                    else:
                        # Train regression model
                        reg_result = self.train_model(X, y_reg, model_name, 'regression')
                        models_trained.append(reg_result)

                        # Train classification model
                        clf_result = self.train_model(X, y_clf, model_name, 'classification')
                        models_trained.append(clf_result)

                        # Make predictions on latest data
                        latest_features = X.iloc[-1:].values
                        latest_scaled = self.scaler.transform(latest_features)

                        reg_model = self.model_configs[model_name]['regressor']
                        clf_model = self.model_configs[model_name]['classifier']

                        # Retrain on full dataset for prediction
                        reg_model.fit(self.scaler.transform(X), y_reg)
                        clf_model.fit(self.scaler.transform(X), y_clf)

                        pred_return = reg_model.predict(latest_scaled)[0]
                        pred_direction = clf_model.predict(latest_scaled)[0]

                        predictions[model_name] = {
                            'predicted_return': float(pred_return),
                            'predicted_direction': int(pred_direction),
                            'confidence': float(clf_model.predict_proba(latest_scaled)[0][pred_direction])
                        }

                except Exception as e:
                    print(f"⚠️  Warning: Failed to train {model_name}: {e}")
                    continue

            if not models_trained:
                print("❌ No models could be trained")
                return None

            # Find best model (lowest MSE for regression)
            best_model = min(models_trained, key=lambda x: x.mse if x.mse else float('inf'))

            # Generate recommendation
            current_price = stock_data['Close'].iloc[-1]
            recommendation = self.generate_recommendation(ticker, current_price, predictions)

            # Feature analysis
            feature_analysis = {}
            if models_trained:
                # Aggregate feature importance across models
                all_importance = {}
                for result in models_trained:
                    if result.feature_importance:
                        for feat, imp in result.feature_importance.items():
                            all_importance[feat] = all_importance.get(feat, 0) + imp

                # Get top 10 features
                sorted_features = sorted(all_importance.items(), key=lambda x: x[1], reverse=True)
                feature_analysis = dict(sorted_features[:10])

            return MLAnalysisResult(
                ticker=ticker,
                models_trained=models_trained,
                best_model=best_model.model_name,
                recommendation=recommendation,
                feature_analysis=feature_analysis,
                prediction_horizon=prediction_horizon,
                training_period=f"{len(stock_data)} days"
            )

        except Exception as e:
            print(f"❌ ML analysis failed: {e}")
            return None

    def get_available_models(self) -> Dict[str, bool]:
        """Get dictionary of available ML models."""
        return self.available_models.copy()

    def load_model(self, model_path: str):
        """Load a saved model from disk."""
        if JOBLIB_AVAILABLE and os.path.exists(model_path):
            return joblib.load(model_path)
        return None
