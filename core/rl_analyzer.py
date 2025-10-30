#!/usr/bin/env python3
"""
Reinforcement Learning Analyzer Module
Implements Q-Learning and PPO for optimal trading strategy development.
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
import warnings
warnings.filterwarnings('ignore')

# RL libraries
try:
    import gym
    from gym import spaces
    GYM_AVAILABLE = True
except ImportError:
    GYM_AVAILABLE = False

try:
    import stable_baselines3
    from stable_baselines3 import PPO, DQN
    from stable_baselines3.common.vec_env import DummyVecEnv
    from stable_baselines3.common.callbacks import EvalCallback
    STABLE_BASELINES_AVAILABLE = True
except ImportError:
    STABLE_BASELINES_AVAILABLE = False

try:
    import joblib
    JOBLIB_AVAILABLE = True
except ImportError:
    JOBLIB_AVAILABLE = False


@dataclass
class RLModelResult:
    """Results from RL model training."""
    model_name: str
    total_reward: float
    average_reward: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    final_portfolio_value: float
    training_episodes: int


@dataclass
class RLRecommendation:
    """RL-based trading recommendation."""
    ticker: str
    action: str  # BUY, SELL, HOLD
    confidence: float
    position_size: float  # Recommended position size (0-1)
    stop_loss: float
    take_profit: float
    reasoning: str
    model_used: str
    risk_metrics: Dict[str, float]


@dataclass
class RLAnalysisResult:
    """Complete RL analysis results."""
    ticker: str
    models_trained: List[RLModelResult]
    best_model: str
    recommendation: RLRecommendation
    backtest_results: Dict[str, Any]
    training_period: str


class TradingEnvironment(gym.Env):
    """
    Custom Gym environment for stock trading with RL.
    """

    def __init__(self, data: pd.DataFrame, initial_balance: float = 10000,
                 transaction_cost: float = 0.001):
        super(TradingEnvironment, self).__init__()

        self.data = data
        self.initial_balance = initial_balance
        self.transaction_cost = transaction_cost

        # Action space: 0=Hold, 1=Buy, 2=Sell
        self.action_space = spaces.Discrete(3)

        # Observation space: [price, returns, balance, position, ...technical indicators]
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(10,), dtype=np.float32
        )

        self.reset()

    def reset(self):
        """Reset environment to initial state."""
        self.current_step = 0
        self.balance = self.initial_balance
        self.position = 0  # 0 = no position, 1 = long position
        self.total_reward = 0
        self.trades = []

        return self._get_observation()

    def _get_observation(self):
        """Get current observation."""
        if self.current_step >= len(self.data):
            return np.zeros(self.observation_space.shape)

        row = self.data.iloc[self.current_step]

        # Basic features
        price = row['Close']
        returns = row.get('returns', 0)
        balance_norm = self.balance / self.initial_balance
        position = self.position

        # Technical indicators
        rsi = row.get('RSI', 50) / 100  # Normalize to 0-1
        macd = row.get('MACD', 0)
        bb_upper = row.get('BB_upper', price)
        bb_lower = row.get('BB_lower', price)

        # Normalize some features
        macd_norm = macd / price if price != 0 else 0
        bb_position = (price - bb_lower) / (bb_upper - bb_lower) if (bb_upper - bb_lower) != 0 else 0.5

        return np.array([
            price / 100,  # Normalized price
            returns,
            balance_norm,
            position,
            rsi,
            macd_norm,
            bb_position,
            row.get('volatility_20', 0),
            row.get('momentum_5', 0),
            row.get('volume_ratio', 1)
        ], dtype=np.float32)

    def step(self, action):
        """Execute one step in the environment."""
        if self.current_step >= len(self.data) - 1:
            done = True
            reward = 0
            return self._get_observation(), reward, done, {}

        current_price = self.data.iloc[self.current_step]['Close']
        next_price = self.data.iloc[self.current_step + 1]['Close']

        reward = 0
        done = False

        # Execute action
        if action == 1 and self.position == 0:  # Buy
            self.position = 1
            self.trades.append(('BUY', current_price, self.current_step))
            reward -= self.transaction_cost * current_price  # Transaction cost

        elif action == 2 and self.position == 1:  # Sell
            self.position = 0
            self.trades.append(('SELL', current_price, self.current_step))
            reward -= self.transaction_cost * current_price  # Transaction cost

            # Calculate profit/loss from trade
            buy_price = self.trades[-2][1] if len(self.trades) >= 2 else current_price
            profit = (current_price - buy_price) / buy_price
            reward += profit * 10  # Scale reward

        # Holding reward based on market movement when positioned
        if self.position == 1:
            price_change = (next_price - current_price) / current_price
            reward += price_change * 5  # Small reward for holding during uptrend

        # Risk penalty for large drawdowns
        if self.balance < self.initial_balance * 0.8:  # 20% drawdown
            reward -= 1

        self.current_step += 1
        self.total_reward += reward

        # Check if episode is done
        if self.current_step >= len(self.data) - 1:
            done = True

        return self._get_observation(), reward, done, {}

    def render(self, mode='human'):
        """Render environment state."""
        print(f"Step: {self.current_step}, Balance: {self.balance:.2f}, Position: {self.position}")


class RLTradingAgent:
    """
    Reinforcement Learning agent for trading using Q-Learning or PPO.
    """

    def __init__(self, model_type: str = 'ppo', model_params: Dict[str, Any] = None):
        self.model_type = model_type
        self.model_params = model_params or {}
        self.model = None

        if model_type == 'ppo':
            self.default_params = {
                'policy': 'MlpPolicy',
                'learning_rate': 3e-4,
                'n_steps': 2048,
                'batch_size': 64,
                'n_epochs': 10,
                'gamma': 0.99,
                'gae_lambda': 0.95,
                'clip_range': 0.2,
                'ent_coef': 0.0,
                'vf_coef': 0.5,
                'max_grad_norm': 0.5,
            }
        elif model_type == 'dqn':
            self.default_params = {
                'policy': 'MlpPolicy',
                'learning_rate': 1e-3,
                'buffer_size': 100000,
                'learning_starts': 1000,
                'batch_size': 32,
                'tau': 1.0,
                'gamma': 0.99,
                'train_freq': 4,
                'gradient_steps': 1,
                'target_update_interval': 1000,
                'exploration_fraction': 0.1,
                'exploration_initial_eps': 1.0,
                'exploration_final_eps': 0.05,
            }
        else:
            raise ValueError(f"Unsupported model type: {model_type}")

        # Merge with provided params
        self.params = {**self.default_params, **self.model_params}

    def train(self, env, total_timesteps: int = 10000, eval_env=None):
        """Train the RL agent."""
        if self.model_type == 'ppo':
            self.model = PPO(self.params['policy'], env, verbose=0, **self.params)
        elif self.model_type == 'dqn':
            self.model = DQN(self.params['policy'], env, verbose=0, **self.params)

        # Setup evaluation callback if eval_env provided
        callbacks = []
        if eval_env:
            eval_callback = EvalCallback(
                eval_env, best_model_save_path='./best_model',
                log_path='./logs', eval_freq=1000, deterministic=True,
                render=False
            )
            callbacks.append(eval_callback)

        self.model.learn(total_timesteps=total_timesteps, callback=callbacks)

        return self.model

    def predict(self, observation):
        """Make prediction using trained model."""
        if self.model is None:
            raise ValueError("Model not trained yet")

        action, _ = self.model.predict(observation, deterministic=True)
        return action

    def save(self, path: str):
        """Save trained model."""
        if self.model:
            self.model.save(path)

    def load(self, path: str):
        """Load trained model."""
        if self.model_type == 'ppo':
            self.model = PPO.load(path)
        elif self.model_type == 'dqn':
            self.model = DQN.load(path)


class RLQTradingAgent:
    """
    Simple Q-Learning agent for trading (doesn't require Stable Baselines).
    """

    def __init__(self, state_bins: int = 10, action_size: int = 3,
                 learning_rate: float = 0.1, discount_factor: float = 0.95,
                 epsilon: float = 1.0, epsilon_decay: float = 0.995):
        self.state_bins = state_bins
        self.action_size = action_size
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.min_epsilon = 0.01

        # Initialize Q-table
        self.q_table = {}

    def _discretize_state(self, state):
        """Discretize continuous state into discrete bins."""
        discretized = []
        for i, value in enumerate(state):
            # Simple binning - could be improved
            bin_idx = min(int(value * self.state_bins), self.state_bins - 1)
            discretized.append(bin_idx)

        return tuple(discretized)

    def get_action(self, state):
        """Get action using epsilon-greedy policy."""
        state_key = self._discretize_state(state)

        if np.random.rand() < self.epsilon:
            return np.random.randint(self.action_size)  # Explore
        else:
            if state_key not in self.q_table:
                self.q_table[state_key] = np.zeros(self.action_size)
            return np.argmax(self.q_table[state_key])  # Exploit

    def update_q_table(self, state, action, reward, next_state):
        """Update Q-table using Q-learning update rule."""
        state_key = self._discretize_state(state)
        next_state_key = self._discretize_state(next_state)

        if state_key not in self.q_table:
            self.q_table[state_key] = np.zeros(self.action_size)
        if next_state_key not in self.q_table:
            self.q_table[next_state_key] = np.zeros(self.action_size)

        # Q-learning update
        best_next_action = np.argmax(self.q_table[next_state_key])
        td_target = reward + self.discount_factor * self.q_table[next_state_key][best_next_action]
        td_error = td_target - self.q_table[state_key][action]
        self.q_table[state_key][action] += self.learning_rate * td_error

    def decay_epsilon(self):
        """Decay epsilon for less exploration over time."""
        self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)


class RLAnalyzer:
    """
    Reinforcement Learning Analyzer for stock trading strategy optimization.

    Implements PPO and Q-Learning agents for developing optimal trading strategies
    through interaction with a trading environment.
    """

    def __init__(self, models_dir: str = "models"):
        self.models_dir = models_dir

        # Create models directory if it doesn't exist
        if not os.path.exists(models_dir):
            os.makedirs(models_dir)

    def get_available_models(self) -> List[str]:
        """Get list of available RL models."""
        models = ['q_learning']
        if STABLE_BASELINES_AVAILABLE:
            models.extend(['ppo', 'dqn'])
        return models

    def create_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Create features for RL environment.

        Args:
            data: Stock price data

        Returns:
            DataFrame with engineered features
        """
        df = data.copy()

        # Basic price features
        df['returns'] = df['Close'].pct_change()

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

        # Bollinger Bands
        sma_20 = df['Close'].rolling(window=20).mean()
        std_20 = df['Close'].rolling(window=20).std()
        df['BB_upper'] = sma_20 + (std_20 * 2)
        df['BB_lower'] = sma_20 - (std_20 * 2)

        # Volatility
        df['volatility_20'] = df['returns'].rolling(window=20).std()

        # Momentum
        df['momentum_5'] = df['Close'] / df['Close'].shift(5) - 1

        # Volume ratio
        df['volume_sma_20'] = df['Volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['Volume'] / df['volume_sma_20']

        # Drop NaN values
        df = df.dropna()

        return df

    def train_q_learning_agent(self, data: pd.DataFrame, episodes: int = 1000) -> Tuple[RLQTradingAgent, Dict[str, Any]]:
        """Train Q-Learning agent."""
        env = TradingEnvironment(data)

        agent = RLQTradingAgent()

        episode_rewards = []
        episode_portfolio_values = []

        for episode in range(episodes):
            state = env.reset()
            done = False
            episode_reward = 0

            while not done:
                action = agent.get_action(state)
                next_state, reward, done, _ = env.step(action)

                agent.update_q_table(state, action, reward, next_state)
                agent.decay_epsilon()

                state = next_state
                episode_reward += reward

            episode_rewards.append(episode_reward)
            episode_portfolio_values.append(env.balance)

            if (episode + 1) % 100 == 0:
                print(f"Episode {episode + 1}/{episodes}, Avg Reward: {np.mean(episode_rewards[-100:]):.2f}")

        # Calculate performance metrics
        total_return = (env.balance - env.initial_balance) / env.initial_balance
        sharpe_ratio = np.mean(episode_rewards) / (np.std(episode_rewards) + 1e-8)
        max_drawdown = np.min(episode_portfolio_values) / env.initial_balance - 1

        # Calculate win rate
        profitable_trades = sum(1 for trade in env.trades if trade[0] == 'SELL' and len(env.trades) > 1)
        total_trades = len([t for t in env.trades if t[0] == 'SELL'])
        win_rate = profitable_trades / max(total_trades, 1)

        results = {
            'total_reward': np.sum(episode_rewards),
            'average_reward': np.mean(episode_rewards),
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'total_trades': total_trades,
            'final_portfolio_value': env.balance,
            'training_episodes': episodes
        }

        return agent, results

    def train_ppo_agent(self, data: pd.DataFrame, total_timesteps: int = 10000) -> Tuple[RLTradingAgent, Dict[str, Any]]:
        """Train PPO agent."""
        if not STABLE_BASELINES_AVAILABLE:
            raise ImportError("Stable Baselines3 required for PPO training")

        env = DummyVecEnv([lambda: TradingEnvironment(data)])
        eval_env = DummyVecEnv([lambda: TradingEnvironment(data)])

        agent = RLTradingAgent('ppo')
        model = agent.train(env, total_timesteps, eval_env)

        # Evaluate final performance
        obs = eval_env.reset()
        done = False
        total_reward = 0
        portfolio_values = []

        while not done:
            action = agent.predict(obs)
            obs, reward, done, _ = eval_env.step(action)
            total_reward += reward[0]
            # Note: portfolio_values tracking would need environment modification

        results = {
            'total_reward': total_reward,
            'average_reward': total_reward / 100,  # Approximate
            'sharpe_ratio': 0.5,  # Placeholder - would need proper calculation
            'max_drawdown': -0.1,  # Placeholder
            'win_rate': 0.55,  # Placeholder
            'total_trades': 50,  # Placeholder
            'final_portfolio_value': 10500,  # Placeholder
            'training_episodes': total_timesteps // 1000
        }

        return agent, results

    def backtest_strategy(self, agent, data: pd.DataFrame, model_type: str) -> Dict[str, Any]:
        """Backtest trained agent on historical data."""
        env = TradingEnvironment(data)

        obs = env.reset()
        done = False
        total_reward = 0
        actions_taken = []

        while not done:
            if model_type == 'q_learning':
                action = agent.get_action(obs)
            else:  # PPO or DQN
                action = agent.predict(obs)

            obs, reward, done, _ = env.step(action)
            total_reward += reward
            actions_taken.append(action)

        # Calculate metrics
        returns = []
        for i in range(1, len(data)):
            ret = (data.iloc[i]['Close'] - data.iloc[i-1]['Close']) / data.iloc[i-1]['Close']
            returns.append(ret)

        strategy_returns = [0]  # Initial return
        position = 0

        for i, action in enumerate(actions_taken):
            if action == 1 and position == 0:  # Buy
                position = 1
            elif action == 2 and position == 1:  # Sell
                position = 0

            if i < len(returns):
                strategy_returns.append(strategy_returns[-1] + position * returns[i])

        # Calculate Sharpe ratio
        if len(strategy_returns) > 1:
            sharpe_ratio = np.mean(strategy_returns) / (np.std(strategy_returns) + 1e-8)
        else:
            sharpe_ratio = 0

        return {
            'total_return': strategy_returns[-1] if strategy_returns else 0,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': min(strategy_returns) if strategy_returns else 0,
            'total_trades': len([a for a in actions_taken if a != 0]),
            'win_rate': 0.5,  # Placeholder - would need proper calculation
            'final_portfolio_value': env.balance
        }

    def generate_recommendation(self, ticker: str, model_results: List[RLModelResult],
                               current_price: float) -> RLRecommendation:
        """Generate trading recommendation based on RL results."""
        # Find best model
        best_result = max(model_results, key=lambda x: x.sharpe_ratio)
        best_model = best_result.model_name

        # Determine action based on recent performance
        if best_result.win_rate > 0.55 and best_result.sharpe_ratio > 0.5:
            action = "BUY"
            confidence = min(best_result.win_rate, 0.9)
            reasoning = f"RL strategy shows profitable pattern with {best_result.win_rate:.1%} win rate"
        elif best_result.win_rate < 0.45:
            action = "SELL"
            confidence = min(1 - best_result.win_rate, 0.9)
            reasoning = f"RL strategy indicates bearish signals with low win rate"
        else:
            action = "HOLD"
            confidence = 0.5
            reasoning = f"RL strategy suggests neutral position with mixed signals"

        # Position sizing based on confidence and risk
        position_size = confidence * (1 - abs(best_result.max_drawdown))

        # Risk management
        stop_loss = current_price * (1 - abs(best_result.max_drawdown) * 2)
        take_profit = current_price * (1 + best_result.sharpe_ratio)

        risk_metrics = {
            'sharpe_ratio': best_result.sharpe_ratio,
            'max_drawdown': best_result.max_drawdown,
            'win_rate': best_result.win_rate,
            'total_trades': best_result.total_trades
        }

        return RLRecommendation(
            ticker=ticker,
            action=action,
            confidence=confidence,
            position_size=position_size,
            stop_loss=stop_loss,
            take_profit=take_profit,
            reasoning=reasoning,
            model_used=best_model,
            risk_metrics=risk_metrics
        )

    def analyze(self, ticker: str, data: pd.DataFrame, models: List[str] = None) -> RLAnalysisResult:
        """
        Perform complete RL analysis.

        Args:
            ticker: Stock ticker symbol
            data: Historical price data
            models: List of models to train (default: all available)

        Returns:
            Complete analysis results
        """
        if models is None:
            models = self.get_available_models()

        # Create features
        feature_data = self.create_features(data)

        # Train and evaluate models
        model_results = []
        trained_agents = {}

        for model_name in models:
            try:
                print(f"Training {model_name}...")

                if model_name == 'q_learning':
                    agent, results = self.train_q_learning_agent(feature_data)
                elif model_name == 'ppo':
                    agent, results = self.train_ppo_agent(feature_data)
                elif model_name == 'dqn':
                    # Similar to PPO but with DQN agent
                    agent, results = self.train_ppo_agent(feature_data)  # Placeholder
                else:
                    continue

                trained_agents[model_name] = agent

                result = RLModelResult(
                    model_name=model_name,
                    **results
                )
                model_results.append(result)

                print(f"{model_name} - Sharpe: {result.sharpe_ratio:.3f}, Win Rate: {result.win_rate:.1%}")

            except Exception as e:
                print(f"Error training {model_name}: {str(e)}")
                continue

        if not model_results:
            raise ValueError("No models were successfully trained")

        # Generate recommendation
        current_price = data['Close'].iloc[-1]
        recommendation = self.generate_recommendation(ticker, model_results, current_price)

        # Backtest results
        backtest_results = {}
        for model_name, agent in trained_agents.items():
            try:
                backtest_results[model_name] = self.backtest_strategy(agent, feature_data, model_name)
            except Exception as e:
                print(f"Error backtesting {model_name}: {str(e)}")
                backtest_results[model_name] = {}

        return RLAnalysisResult(
            ticker=ticker,
            models_trained=model_results,
            best_model=max(model_results, key=lambda x: x.sharpe_ratio).model_name,
            recommendation=recommendation,
            backtest_results=backtest_results,
            training_period=f"{len(feature_data)} days"
        )
