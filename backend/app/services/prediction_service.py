"""Prediction service that orchestrates model inference."""
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import structlog
import asyncio

from app.config import get_settings
from app.ml.model_registry import load_classical, load_deep, check_model_exists, check_regressor_exists
from app.ml.features import engineer_features, prepare_ml_data, get_default_feature_columns
from app.ml.evaluate import format_prediction_response
from app.ml.train_classical import predict as classical_predict
from app.ml.train_deep import predict as deep_predict
from app.db.database import AsyncSessionLocal
from app.db import crud

settings = get_settings()
logger = structlog.get_logger()

# Asset type mapping
ASSET_TYPES = {
    "BTC/USD": "crypto",
    "ETH/USD": "crypto",
    "SOL/USD": "crypto",
    "USDT/USD": "stable",
    "USDC/USD": "stable"
}


def get_asset_type(symbol: str) -> str:
    """Get asset type for a symbol."""
    if symbol in ASSET_TYPES:
        return ASSET_TYPES[symbol]
    return "stock"  # Default to stock for VN symbols


def determine_direction(current_close: float, predicted_close: float, threshold: float = 0.001) -> str:
    """
    Determine price direction based on current and predicted close.

    Args:
        current_close: Current close price
        predicted_close: Predicted close price
        threshold: Threshold for "flat" classification

    Returns:
        Direction string: "up", "down", or "flat"
    """
    change = (predicted_close - current_close) / current_close

    if change > threshold:
        return "up"
    elif change < -threshold:
        return "down"
    else:
        return "flat"


async def get_historical_data(
    symbol: str,
    asset_type: str,
    days: int = 90
) -> pd.DataFrame:
    """
    Fetch historical data for prediction.

    Args:
        symbol: Asset symbol
        asset_type: Asset type
        days: Number of days of history

    Returns:
        DataFrame with OHLCV data
    """
    async with AsyncSessionLocal() as db:
        if asset_type in ["crypto", "stable"]:
            from datetime import datetime, timedelta
            start = datetime.utcnow() - timedelta(days=days)
            bars = await crud.get_crypto_bars(db, symbol, start=start, limit=1000)

            if not bars:
                raise ValueError(f"No historical data found for {symbol}")

            df = pd.DataFrame([
                {
                    "ts": bar.ts,
                    "open": float(bar.open),
                    "high": float(bar.high),
                    "low": float(bar.low),
                    "close": float(bar.close),
                    "volume": float(bar.volume)
                }
                for bar in bars
            ])
        else:
            from datetime import date, timedelta
            start = date.today() - timedelta(days=days)
            bars = await crud.get_stock_bars(db, symbol, start=start, limit=1000)

            if not bars:
                raise ValueError(f"No historical data found for {symbol}")

            df = pd.DataFrame([
                {
                    "ts": bar.ts,
                    "open": float(bar.open),
                    "high": float(bar.high),
                    "low": float(bar.low),
                    "close": float(bar.close),
                    "volume": float(bar.volume)
                }
                for bar in bars
            ])

        return df


def _compute_next_close_target(df: pd.DataFrame) -> np.ndarray:
    """Compute regression target: next day's close price."""
    return df["close"].shift(-1).dropna().to_numpy()


async def predict_crypto(
    symbol: str,
    model_key: str = "rf"
) -> Dict[str, Any]:
    """
    Generate prediction for a cryptocurrency using regressor for predicted_close.

    Args:
        symbol: Crypto symbol (e.g., "BTC/USD")
        model_key: Model type ('rf', 'xgb', or 'lstm')

    Returns:
        Prediction response dictionary with predicted_close from regressor or None
    """
    logger.info(
        "Generating crypto prediction",
        symbol=symbol,
        model=model_key
    )

    # Check if model exists
    if not check_model_exists(symbol, model_key):
        logger.warning(
            "Model not found for prediction",
            symbol=symbol,
            model=model_key
        )
        raise FileNotFoundError(f"Model not found: {symbol}/{model_key}")

    # Fetch historical data
    df = await get_historical_data(symbol, "crypto", days=90)

    if len(df) < 30:
        raise ValueError(f"Insufficient data for prediction: {len(df)} rows")

    # Get current close price
    current_close = df["close"].iloc[-1]

    # Engineer features
    df_features = engineer_features(df)

    # Prepare ML data
    X, _, feature_names = prepare_ml_data(df_features, drop_na=True)

    if len(X) == 0:
        raise ValueError("No valid samples after feature engineering")

    # Make prediction based on model type
    if model_key in ["rf", "xgb"]:
        # Load classifier for direction
        clf = load_classical(symbol, model_key, "clf")
        if clf is None:
            raise RuntimeError(f"Failed to load classifier: {symbol}/{model_key}")

        # Load regressor for predicted_close (may be None)
        reg = load_classical(symbol, model_key, "reg")

        result = classical_predict(clf, X[-1:])  # Predict on latest sample
        prediction = result["predictions"][0]
        confidence = result.get("confidence", [0.5])[0]

        # Use regression model for predicted_close -- or None if not trained
        predicted_close = None
        if reg is not None:
            reg_result = classical_predict(reg, X[-1:], return_proba=False)
            predicted_close = round(float(reg_result["predictions"][0]), 4)

    elif model_key == "lstm":
        model_result = load_deep(symbol)
        if model_result is None:
            raise RuntimeError(f"Failed to load model: {symbol}/{model_key}")

        model, _ = model_result
        result = deep_predict(model, X)
        prediction = result["predictions"][-1]  # Last prediction
        confidence = result["confidence"][-1]

        # LSTM does not have a regressor yet -- predicted_close is None
        predicted_close = None
    else:
        raise ValueError(f"Unknown model key: {model_key}")

    # Determine direction
    if predicted_close is not None:
        direction = determine_direction(current_close, predicted_close)
    else:
        # Fallback to classification-based direction
        direction = "up" if prediction == 1 else "down"

    asset_type = get_asset_type(symbol)

    response = format_prediction_response(
        symbol=symbol,
        asset_type=asset_type,
        model=model_key,
        predicted_close=predicted_close if predicted_close is not None else 0.0,
        direction=direction,
        confidence=float(confidence),
        features_used=feature_names[:10]  # First 10 features
    )

    # Set predicted_close to None in response if regressor not available
    if predicted_close is None:
        response["predicted_close"] = None

    logger.info(
        "Prediction generated",
        symbol=symbol,
        model=model_key,
        direction=direction,
        confidence=confidence,
        predicted_close=predicted_close,
    )

    return response


async def predict_stock(
    symbol: str,
    model_key: str = "rf"
) -> Dict[str, Any]:
    """
    Generate prediction for a Vietnamese stock using regressor for predicted_close.

    Args:
        symbol: Stock symbol (e.g., "VNM")
        model_key: Model type ('rf', 'xgb', or 'lstm')

    Returns:
        Prediction response dictionary with predicted_close from regressor or None
    """
    logger.info(
        "Generating stock prediction",
        symbol=symbol,
        model=model_key
    )

    # Check if model exists
    if not check_model_exists(symbol, model_key):
        logger.warning(
            "Model not found for prediction",
            symbol=symbol,
            model=model_key
        )
        raise FileNotFoundError(f"Model not found: {symbol}/{model_key}")

    # Fetch historical data
    df = await get_historical_data(symbol, "stock", days=90)

    if len(df) < 30:
        raise ValueError(f"Insufficient data for prediction: {len(df)} rows")

    # Get current close price
    current_close = df["close"].iloc[-1]

    # Engineer features (without financials for now)
    df_features = engineer_features(df, include_financials=False)

    # Prepare ML data
    X, _, feature_names = prepare_ml_data(df_features, drop_na=True)

    if len(X) == 0:
        raise ValueError("No valid samples after feature engineering")

    # Make prediction
    if model_key in ["rf", "xgb"]:
        # Load classifier for direction
        clf = load_classical(symbol, model_key, "clf")
        if clf is None:
            raise RuntimeError(f"Failed to load classifier: {symbol}/{model_key}")

        # Load regressor for predicted_close (may be None)
        reg = load_classical(symbol, model_key, "reg")

        result = classical_predict(clf, X[-1:])  # Predict on latest sample
        prediction = result["predictions"][0]
        confidence = result.get("confidence", [0.5])[0]

        # Use regression model for predicted_close -- or None if not trained
        predicted_close = None
        if reg is not None:
            reg_result = classical_predict(reg, X[-1:], return_proba=False)
            predicted_close = round(float(reg_result["predictions"][0]), 4)

    elif model_key == "lstm":
        model_result = load_deep(symbol)
        if model_result is None:
            raise RuntimeError(f"Failed to load model: {symbol}/{model_key}")

        model, _ = model_result
        result = deep_predict(model, X)
        prediction = result["predictions"][-1]
        confidence = result["confidence"][-1]

        # LSTM does not have a regressor yet -- predicted_close is None
        predicted_close = None
    else:
        raise ValueError(f"Unknown model key: {model_key}")

    # Determine direction
    if predicted_close is not None:
        direction = determine_direction(current_close, predicted_close)
    else:
        direction = "up" if prediction == 1 else "down"

    response = format_prediction_response(
        symbol=symbol,
        asset_type="stock",
        model=model_key,
        predicted_close=predicted_close if predicted_close is not None else 0.0,
        direction=direction,
        confidence=float(confidence),
        features_used=feature_names[:10]
    )

    # Set predicted_close to None in response if regressor not available
    if predicted_close is None:
        response["predicted_close"] = None

    logger.info(
        "Prediction generated",
        symbol=symbol,
        model=model_key,
        direction=direction,
        confidence=confidence,
        predicted_close=predicted_close,
    )

    return response


async def retrain_model(
    symbol: str,
    asset_type: str,
    model_key: str
) -> Dict[str, Any]:
    """
    Trigger async model retraining.

    Args:
        symbol: Asset symbol
        asset_type: Asset type
        model_key: Model type

    Returns:
        Training job status
    """
    logger.info(
        "Triggering model retrain",
        symbol=symbol,
        asset_type=asset_type,
        model=model_key
    )

    # This would typically queue a background job
    # For MVP, we return immediately with job ID
    job_id = f"retrain_{symbol}_{model_key}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    return {
        "job_id": job_id,
        "status": "queued",
        "symbol": symbol,
        "model": model_key,
        "message": "Retraining job queued. Model will be updated when complete."
    }

async def _execute_retrain_background(symbol: str, model_key: str):
    logger.info("Retraining triggered", symbol=symbol, model=model_key)
    # In the future, call the actual training functions here.
    # For now this is a placeholder.
    return