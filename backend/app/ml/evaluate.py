"""Model evaluation metrics and helpers."""
import numpy as np
from typing import Dict, Any, List
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report
)
import structlog

logger = structlog.get_logger()


def calculate_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_proba: np.ndarray = None
) -> Dict[str, float]:
    """
    Calculate classification metrics.
    
    Args:
        y_true: True labels
        y_pred: Predicted labels
        y_proba: Prediction probabilities (optional)
        
    Returns:
        Dictionary of metrics
    """
    metrics = {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
    }
    
    if y_proba is not None and len(np.unique(y_true)) > 1:
        try:
            metrics["auc_roc"] = roc_auc_score(y_true, y_proba)
        except ValueError:
            pass
    
    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    if cm.shape == (2, 2):
        tn, fp, fn, tp = cm.ravel()
        metrics["true_negatives"] = int(tn)
        metrics["false_positives"] = int(fp)
        metrics["false_negatives"] = int(fn)
        metrics["true_positives"] = int(tp)
    
    return metrics


def calculate_direction_accuracy(
    actual_prices: np.ndarray,
    predicted_directions: np.ndarray
) -> float:
    """
    Calculate direction prediction accuracy.
    
    Args:
        actual_prices: Actual price series
        predicted_directions: Predicted directions (1=up, 0=down)
        
    Returns:
        Direction accuracy
    """
    # Calculate actual directions
    actual_directions = (np.diff(actual_prices) > 0).astype(int)
    predicted_directions = predicted_directions[1:]  # Align with actual
    
    if len(actual_directions) == 0:
        return 0.0
    
    return accuracy_score(actual_directions, predicted_directions)


def calculate_sharpe_ratio(
    returns: np.ndarray,
    risk_free_rate: float = 0.0
) -> float:
    """
    Calculate Sharpe ratio.
    
    Args:
        returns: Array of returns
        risk_free_rate: Risk-free rate (annualized)
        
    Returns:
        Sharpe ratio
    """
    if len(returns) == 0 or np.std(returns) == 0:
        return 0.0
    
    excess_returns = returns - risk_free_rate / 252  # Daily
    return np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)


def calculate_max_drawdown(prices: np.ndarray) -> float:
    """
    Calculate maximum drawdown.
    
    Args:
        prices: Price series
        
    Returns:
        Maximum drawdown as percentage
    """
    peak = np.maximum.accumulate(prices)
    drawdown = (prices - peak) / peak
    return np.min(drawdown)


def backtest_strategy(
    prices: np.ndarray,
    predictions: np.ndarray,
    initial_capital: float = 10000.0,
    transaction_cost: float = 0.001
) -> Dict[str, Any]:
    """
    Simple backtest of a prediction-based strategy.
    
    Args:
        prices: Price series
        predictions: Predicted directions (1=buy/hold, 0=sell)
        initial_capital: Starting capital
        transaction_cost: Transaction cost per trade
        
    Returns:
        Backtest results
    """
    capital = initial_capital
    position = 0  # 0 = no position, 1 = long
    trades = []
    
    for i in range(len(prices) - 1):
        current_price = prices[i]
        next_price = prices[i + 1]
        prediction = predictions[i]
        
        # Buy signal
        if prediction == 1 and position == 0:
            position = 1
            shares = capital * (1 - transaction_cost) / current_price
            entry_price = current_price
            trades.append({"type": "buy", "price": current_price, "shares": shares})
        
        # Sell signal
        elif prediction == 0 and position == 1:
            capital = shares * current_price * (1 - transaction_cost)
            position = 0
            trades.append({"type": "sell", "price": current_price, "capital": capital})
    
    # Close final position
    if position == 1:
        capital = shares * prices[-1] * (1 - transaction_cost)
    
    # Calculate returns
    total_return = (capital - initial_capital) / initial_capital
    
    # Calculate returns series
    returns = np.diff(prices) / prices[:-1]
    strategy_returns = returns * predictions[:-1]  # Only trade when predicted up
    
    results = {
        "initial_capital": initial_capital,
        "final_capital": capital,
        "total_return": total_return,
        "total_trades": len(trades),
        "sharpe_ratio": calculate_sharpe_ratio(strategy_returns),
        "max_drawdown": calculate_max_drawdown(prices),
        "trades": trades[:10]  # First 10 trades for inspection
    }
    
    return results


def format_prediction_response(
    symbol: str,
    asset_type: str,
    model: str,
    predicted_close: float,
    direction: str,
    confidence: float,
    features_used: List[str],
    horizon: str = "1D"
) -> Dict[str, Any]:
    """
    Format prediction response according to API schema.
    
    Args:
        symbol: Asset symbol
        asset_type: Asset type (crypto, stable, stock)
        model: Model name (rf, xgb, lstm)
        predicted_close: Predicted close price
        direction: Direction (up, down, flat)
        confidence: Confidence score (0-1)
        features_used: List of feature names
        horizon: Prediction horizon
        
    Returns:
        Formatted response dictionary
    """
    from datetime import datetime, timezone
    
    return {
        "symbol": symbol,
        "asset_type": asset_type,
        "model": model,
        "predicted_close": round(predicted_close, 2),
        "direction": direction,
        "confidence": round(confidence, 2),
        "horizon": horizon,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "features_used": features_used
    }
