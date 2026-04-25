"""Model registry with lazy loading and caching."""
import os
import joblib
import torch
import threading
from typing import Dict, Any, Optional, Tuple
import structlog

from app.config import get_settings
settings = get_settings()

from app.ml.train_deep import PriceLSTM

logger = structlog.get_logger()

# Process-level in-memory cache
_cache: Dict[str, Any] = {}
_lock = threading.Lock()

CACHE_DIR = settings.model_cache_dir


def _get_cache_key(symbol: str, model_key: str, role: Optional[str] = None) -> str:
    """Generate cache key for a model."""
    if role:
        return f"{symbol}_{model_key}_{role}"
    return f"{symbol}_{model_key}"


def load_classical(symbol: str, model_key: str, model_role: str = "clf") -> Optional[Any]:
    """
    Lazy-load a classical ML model with caching.
    
    Args:
        symbol: Asset symbol
        model_key: Model type ('rf' or 'xgb')
        model_role: 'clf' for classifier, 'reg' for regressor
        
    Returns:
        Loaded model pipeline or None
    """
    key = _get_cache_key(symbol, model_key, model_role)
    
    with _lock:
        if key in _cache:
            logger.debug("Model cache hit", key=key)
            return _cache[key]
        
        # Load from disk
        safe_symbol = symbol.replace("/", "_")
        path = os.path.join(CACHE_DIR, f"{safe_symbol}_{model_key}_{model_role}.joblib")
        
        if not os.path.exists(path):
            logger.warning(
                "Model file not found",
                symbol=symbol,
                model=model_key,
                role=model_role,
                path=path
            )
            return None
        
        try:
            model_package = joblib.load(path)
            model = model_package["pipeline"]
            _cache[key] = model
            
            logger.info(
                "Classical model loaded and cached",
                symbol=symbol,
                model=model_key,
                role=model_role,
                path=path
            )
            return model
            
        except Exception as e:
            logger.error(
                "Failed to load classical model",
                symbol=symbol,
                model=model_key,
                role=model_role,
                error=str(e)
            )
            return None


def load_deep(symbol: str) -> Optional[Tuple[PriceLSTM, Dict[str, Any]]]:
    """
    Lazy-load a deep learning model with caching.
    
    Args:
        symbol: Asset symbol
        
    Returns:
        Tuple of (model, checkpoint) or None
    """
    key = _get_cache_key(symbol, "lstm")
    
    with _lock:
        if key in _cache:
            logger.debug("Deep model cache hit", key=key)
            return _cache[key]
        
        # Load from disk
        safe_symbol = symbol.replace("/", "_")
        path = os.path.join(CACHE_DIR, f"{safe_symbol}_lstm.pt")
        
        if not os.path.exists(path):
            logger.warning(
                "LSTM model file not found",
                symbol=symbol,
                path=path
            )
            return None
        
        try:
            # Load with map_location='cpu' for OOM safety
            checkpoint = torch.load(path, map_location="cpu")
            config = checkpoint["config"]
            
            model = PriceLSTM(**config)
            model.load_state_dict(checkpoint["state_dict"])
            model.eval()
            
            # Optional: Convert to half precision for memory savings
            # model = model.half()
            
            result = (model, checkpoint)
            _cache[key] = result
            
            logger.info(
                "LSTM model loaded and cached",
                symbol=symbol,
                path=path
            )
            return result
            
        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                logger.error(
                    "OOM error loading LSTM model",
                    symbol=symbol,
                    error=str(e)
                )
            else:
                logger.error(
                    "Runtime error loading LSTM model",
                    symbol=symbol,
                    error=str(e)
                )
            return None
            
        except Exception as e:
            logger.error(
                "Failed to load LSTM model",
                symbol=symbol,
                error=str(e)
            )
            return None


def clear_cache(symbol: Optional[str] = None, model_key: Optional[str] = None):
    """
    Clear model cache.
    
    Args:
        symbol: Optional symbol to clear (clears all if None)
        model_key: Optional model type to clear
    """
    global _cache
    
    with _lock:
        if symbol is None:
            _cache.clear()
            logger.info("Cleared all model cache")
        else:
            key = _get_cache_key(symbol, model_key or "*")
            keys_to_remove = [k for k in _cache.keys() if k.startswith(key.rstrip("*"))]
            for k in keys_to_remove:
                del _cache[k]
            logger.info(
                "Cleared model cache",
                symbol=symbol,
                model=model_key,
                count=len(keys_to_remove)
            )


def get_cache_info() -> Dict[str, Any]:
    """Get information about cached models."""
    with _lock:
        return {
            "cached_models": list(_cache.keys()),
            "cache_size": len(_cache)
        }


def check_model_exists(symbol: str, model_key: str) -> bool:
    """Check if a model file exists."""
    safe_symbol = symbol.replace("/", "_")
    
    if model_key == "lstm":
        path = os.path.join(CACHE_DIR, f"{safe_symbol}_lstm.pt")
    else:
        # Classical predictions always require the classifier artifact.
        path = os.path.join(CACHE_DIR, f"{safe_symbol}_{model_key}_clf.joblib")
    
    return os.path.exists(path)


def check_regressor_exists(symbol: str, model_key: str) -> bool:
    """Check if a classical regressor file exists."""
    safe_symbol = symbol.replace("/", "_")
    path = os.path.join(CACHE_DIR, f"{safe_symbol}_{model_key}_reg.joblib")
    return os.path.exists(path)


def list_available_models(symbol: Optional[str] = None) -> Dict[str, list]:
    """List all available trained models."""
    models = {"rf": set(), "xgb": set(), "lstm": set()}
    
    if not os.path.exists(CACHE_DIR):
        return models
    
    for filename in os.listdir(CACHE_DIR):
        if filename.endswith(".joblib"):
            parts = filename.replace(".joblib", "").split("_")
            # Classical naming is {symbol}_{model_key}_{role}.joblib.
            if len(parts) >= 3:
                role = parts[-1]
                model_type = parts[-2]
                sym = "_".join(parts[:-2])
                if role not in ["clf", "reg"]:
                    continue
                if model_type in ["rf", "xgb"]:
                    if symbol is None or sym == symbol.replace("/", "_"):
                        models[model_type].add(sym)
        
        elif filename.endswith(".pt"):
            parts = filename.replace(".pt", "").split("_")
            if len(parts) >= 2 and parts[-1] == "lstm":
                sym = "_".join(parts[:-1])
                if symbol is None or sym == symbol.replace("/", "_"):
                    models["lstm"].add(sym)
    
    return {k: sorted(list(v)) for k, v in models.items()}


# CLI commands for entrypoint script
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Model registry CLI")
    parser.add_argument("command", choices=["pull_all", "list", "clear_cache"])
    parser.add_argument("--cache-dir", default=CACHE_DIR)
    parser.add_argument("--symbol", default=None)
    
    args = parser.parse_args()
    
    if args.command == "pull_all":
        # In production, this would download from MODEL_BASE_URL
        logger.info(
            "Pull all models command received",
            cache_dir=args.cache_dir
        )
        # Placeholder for actual download logic
        print(f"Models would be pulled to {args.cache_dir}")
    
    elif args.command == "list":
        models = list_available_models(args.symbol)
        print(json.dumps(models, indent=2))
    
    elif args.command == "clear_cache":
        clear_cache(args.symbol)
        print("Cache cleared")
