"""Predictions API router."""
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import Optional
from pydantic import BaseModel
import structlog

from app.services.prediction_service import (
    predict_crypto, predict_stock, retrain_model, get_asset_type
)
from app.ml.model_registry import check_model_exists

logger = structlog.get_logger()
router = APIRouter()


# Response model
class PredictionResponse(BaseModel):
    symbol: str
    asset_type: str
    model: str
    predicted_close: float
    direction: str
    confidence: float
    horizon: str
    generated_at: str
    features_used: list


class RetrainResponse(BaseModel):
    job_id: str
    status: str
    symbol: str
    model: str
    message: str


@router.get("/crypto", response_model=PredictionResponse)
async def get_crypto_prediction(
    symbol: str = Query(..., description="Crypto symbol (e.g., BTC/USD)"),
    model: str = Query("rf", description="Model type (rf, xgb, lstm)")
):
    """
    Get price prediction for a cryptocurrency.
    
    Returns:
        Prediction with confidence score
    """
    try:
        # Validate model
        valid_models = ["rf", "xgb", "lstm"]
        if model not in valid_models:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid model. Choose from: {valid_models}"
            )
        
        # Validate symbol
        valid_symbols = ["BTC/USD", "ETH/USD", "SOL/USD", "USDT/USD", "USDC/USD"]
        if symbol not in valid_symbols:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid symbol. Supported: {valid_symbols}"
            )
        
        # Check if model exists
        if not check_model_exists(symbol, model):
            raise HTTPException(
                status_code=404,
                detail={
                    "type": "about:blank",
                    "title": "Model Not Found",
                    "status": 404,
                    "detail": f"Model '{model}' for '{symbol}' not found. Please train the model first.",
                    "model": model
                }
            )
        
        # Generate prediction
        prediction = await predict_crypto(symbol, model)
        return prediction
        
    except HTTPException:
        raise
    except FileNotFoundError as e:
        logger.error("Model not found", symbol=symbol, model=model, error=str(e))
        raise HTTPException(
            status_code=503,
            detail={
                "type": "about:blank",
                "title": "Model Not Available",
                "status": 503,
                "detail": "Model not available",
                "model": model
            }
        )
    except Exception as e:
        logger.error("Error generating crypto prediction", symbol=symbol, model=model, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock", response_model=PredictionResponse)
async def get_stock_prediction(
    symbol: str = Query(..., description="Stock symbol (e.g., VNM)"),
    model: str = Query("rf", description="Model type (rf, xgb, lstm)")
):
    """
    Get price prediction for a Vietnamese stock.
    
    Returns:
        Prediction with confidence score
    """
    try:
        # Validate model
        valid_models = ["rf", "xgb", "lstm"]
        if model not in valid_models:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid model. Choose from: {valid_models}"
            )
        
        # Check if model exists
        if not check_model_exists(symbol, model):
            raise HTTPException(
                status_code=404,
                detail={
                    "type": "about:blank",
                    "title": "Model Not Found",
                    "status": 404,
                    "detail": f"Model '{model}' for '{symbol}' not found. Please train the model first.",
                    "model": model
                }
            )
        
        # Generate prediction
        prediction = await predict_stock(symbol, model)
        return prediction
        
    except HTTPException:
        raise
    except FileNotFoundError as e:
        logger.error("Model not found", symbol=symbol, model=model, error=str(e))
        raise HTTPException(
            status_code=503,
            detail={
                "type": "about:blank",
                "title": "Model Not Available",
                "status": 503,
                "detail": "Model not available",
                "model": model
            }
        )
    except Exception as e:
        logger.error("Error generating stock prediction", symbol=symbol, model=model, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retrain", response_model=RetrainResponse)
async def trigger_retrain(
    background_tasks: BackgroundTasks,
    symbol: str = Query(..., description="Asset symbol"),
    asset_type: str = Query(..., description="Asset type (crypto, stock)")
):
    """
    Trigger async model retraining.
    
    Returns:
        Training job status
    """
    try:
        # Validate asset type
        valid_types = ["crypto", "stock", "stable"]
        if asset_type not in valid_types:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid asset_type. Choose from: {valid_types}"
            )
        
        # Trigger retrain for all models
        result = await retrain_model(symbol, asset_type, "all")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error triggering retrain", symbol=symbol, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
