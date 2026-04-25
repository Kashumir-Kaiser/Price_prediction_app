"""Evaluation utilities for model predictions."""
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List


def format_prediction_response(
    symbol: str,
    asset_type: str,
    model: str,
    predicted_close: Optional[float],
    direction: str,
    confidence: float,
    features_used: List[str],
    **kwargs
) -> Dict[str, Any]:
    """
    Format a prediction into the standard API response shape.

    Args:
        symbol: Asset symbol
        asset_type: Asset type (crypto/stock)
        model: Model key used
        predicted_close: Predicted next-day close price (None if regressor unavailable)
        direction: Predicted direction (up/down/flat)
        confidence: Prediction confidence (0-1)
        features_used: List of feature names used
        **kwargs: Additional fields

    Returns:
        Formatted prediction dictionary
    """
    return {
        "symbol": symbol,
        "asset_type": asset_type,
        "model": model,
        "predicted_close": predicted_close,
        "direction": direction,
        "confidence": confidence,
        "features_used": features_used,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **kwargs
    }
