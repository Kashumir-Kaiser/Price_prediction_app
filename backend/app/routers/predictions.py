"""Prediction router with support for both classification and regression outputs."""
import asyncio
from typing import Optional, Literal
from datetime import datetime

from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel, Field
import structlog

from app.services.prediction_service import predict_crypto, predict_stock
from app.ml.model_registry import check_model_exists
from app.utils.rate_limiter import RateLimitExceeded
from app.routers.auth import get_current_active_user, require_admin
from app.db.models import User

router = APIRouter()
logger = structlog.get_logger()


class PredictionRequest(BaseModel):
    """Prediction request schema."""
    symbol: str
    model: Literal["rf", "xgb", "lstm"] = "rf"


class PredictionResponse(BaseModel):
    """
    Prediction response schema.

    predicted_close: float | null
      - null  -> regression model not available (classification-only or not yet trained)
      - float -> regression model generated a concrete next-day close price
    """
    symbol: str
    asset_type: str
    model: str
    predicted_close: Optional[float] = Field(
        default=None,
        description="Predicted next-day close price. Null when regressor not available."
    )
    direction: str
    confidence: float
    features_used: list
    timestamp: str


@router.get("/predictions", response_model=PredictionResponse)
async def get_prediction(
    symbol: str = Query(..., description="Asset symbol (e.g., BTC/USD, VNM)"),
    model: Literal["rf", "xgb", "lstm"] = Query("rf", description="Model type"),
    _: User = Depends(get_current_active_user),  # Auth required
):
    """
    Get prediction for a given symbol and model.

    Returns predicted_close from regressor when available,
    null when only classifier is trained.
    """
    try:
        if "/" in symbol:
            # Crypto
            prediction = await predict_crypto(symbol, model)
        else:
            # Stock
            prediction = await predict_stock(symbol, model)

        return PredictionResponse(**prediction)

    except FileNotFoundError:
        logger.warning(
            "Model not found for prediction request",
            symbol=symbol,
            model=model
        )
        raise HTTPException(
            status_code=404,
            detail=f"Model not trained for {symbol} with {model}"
        )

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    except RateLimitExceeded:
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please try again later.",
            headers={"Retry-After": "60"}
        )

    except Exception as e:
        logger.error(
            "Prediction generation failed",
            symbol=symbol,
            model=model,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to generate prediction"
        )


@router.post("/predictions/retrain")
async def retrain_prediction_model(
    request: PredictionRequest,
    admin: User = Depends(require_admin),  # Admin only
):
    """
    Trigger model retraining (admin only).

    Creates a background retrain job and returns the job ID.
    """
    from app.services.prediction_service import retrain_model

    asset_type = "crypto" if "/" in request.symbol else "stock"

    result = await retrain_model(request.symbol, asset_type, request.model)
    return result
