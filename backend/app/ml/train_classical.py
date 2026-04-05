"""Classical ML model training with scikit-learn."""
import os
import joblib
import numpy as np
from typing import Dict, Any, Optional, List
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score, roc_auc_score, precision_score, recall_score, f1_score
import structlog

from app.config import get_settings
settings = get_settings()

logger = structlog.get_logger()

# Model definitions
MODELS = {
    "rf": RandomForestClassifier(
        n_estimators=200,
        max_depth=6,
        class_weight="balanced",
        random_state=42,
        n_jobs=2
    ),
    "xgb": GradientBoostingClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        random_state=42
    ),
}


def train_and_save(
    symbol: str,
    X: np.ndarray,
    y: np.ndarray,
    model_key: str,
    cache_dir: Optional[str] = None,
    feature_names: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Train and save a classical ML model.
    
    Args:
        symbol: Asset symbol
        X: Feature matrix
        y: Target vector
        model_key: Model type ('rf' or 'xgb')
        cache_dir: Directory to save model
        feature_names: List of feature names
        
    Returns:
        Dictionary with training metrics and model path
    """
    if model_key not in MODELS:
        raise ValueError(f"Unknown model key: {model_key}. Use: {list(MODELS.keys())}")
    
    if cache_dir is None:
        cache_dir = settings.model_cache_dir
    
    # Ensure cache directory exists
    os.makedirs(cache_dir, exist_ok=True)
    
    # Create pipeline
    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", MODELS[model_key])
    ])
    
    # Time-series cross-validation
    tscv = TimeSeriesSplit(n_splits=5)
    cv_scores = []
    cv_auc_scores = []
    
    logger.info(
        "Starting cross-validation",
        symbol=symbol,
        model=model_key,
        samples=len(X)
    )
    
    for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
        X_train, X_val = X[train_idx], X[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]
        
        # Fit and predict
        pipe.fit(X_train, y_train)
        y_pred = pipe.predict(X_val)
        y_proba = pipe.predict_proba(X_val)[:, 1] if hasattr(pipe, 'predict_proba') else None
        
        # Calculate metrics
        acc = accuracy_score(y_val, y_pred)
        cv_scores.append(acc)
        
        if y_proba is not None and len(np.unique(y_val)) > 1:
            auc = roc_auc_score(y_val, y_proba)
            cv_auc_scores.append(auc)
        
        logger.debug(
            "CV fold completed",
            fold=fold + 1,
            accuracy=acc,
            train_size=len(X_train),
            val_size=len(X_val)
        )
    
    # Fit on all data
    logger.info(
        "Fitting final model on all data",
        symbol=symbol,
        model=model_key
    )
    pipe.fit(X, y)
    
    # Save model
    safe_symbol = symbol.replace("/", "_")
    filename = f"{safe_symbol}_{model_key}.joblib"
    path = os.path.join(cache_dir, filename)
    
    # Save with metadata
    model_package = {
        "pipeline": pipe,
        "symbol": symbol,
        "model_type": model_key,
        "feature_names": feature_names,
        "training_samples": len(X),
        "cv_accuracy_mean": float(np.mean(cv_scores)),
        "cv_accuracy_std": float(np.std(cv_scores)),
    }
    
    if cv_auc_scores:
        model_package["cv_auc_mean"] = float(np.mean(cv_auc_scores))
        model_package["cv_auc_std"] = float(np.std(cv_auc_scores))
    
    joblib.dump(model_package, path)
    
    logger.info(
        "Model saved",
        symbol=symbol,
        model=model_key,
        path=path,
        cv_accuracy_mean=model_package["cv_accuracy_mean"]
    )
    
    return {
        "cv_accuracy_mean": model_package["cv_accuracy_mean"],
        "cv_accuracy_std": model_package["cv_accuracy_std"],
        "cv_auc_mean": model_package.get("cv_auc_mean"),
        "cv_auc_std": model_package.get("cv_auc_std"),
        "path": path,
        "training_samples": len(X)
    }


def load_model(symbol: str, model_key: str, cache_dir: Optional[str] = None) -> Optional[Pipeline]:
    """
    Load a trained classical model.
    
    Args:
        symbol: Asset symbol
        model_key: Model type ('rf' or 'xgb')
        cache_dir: Directory containing saved models
        
    Returns:
        Loaded pipeline or None if not found
    """
    if cache_dir is None:
        cache_dir = settings.model_cache_dir
    
    safe_symbol = symbol.replace("/", "_")
    filename = f"{safe_symbol}_{model_key}.joblib"
    path = os.path.join(cache_dir, filename)
    
    if not os.path.exists(path):
        logger.warning(
            "Model file not found",
            symbol=symbol,
            model=model_key,
            path=path
        )
        return None
    
    try:
        model_package = joblib.load(path)
        logger.info(
            "Model loaded",
            symbol=symbol,
            model=model_key,
            path=path
        )
        return model_package["pipeline"]
    except Exception as e:
        logger.error(
            "Failed to load model",
            symbol=symbol,
            model=model_key,
            error=str(e)
        )
        return None


def predict(
    model: Pipeline,
    X: np.ndarray,
    return_proba: bool = True
) -> Dict[str, np.ndarray]:
    """
    Make predictions with a trained model.
    
    Args:
        model: Trained pipeline
        X: Feature matrix
        return_proba: Whether to return probabilities
        
    Returns:
        Dictionary with predictions and optionally probabilities
    """
    predictions = model.predict(X)
    result = {"predictions": predictions}
    
    if return_proba and hasattr(model, 'predict_proba'):
        probabilities = model.predict_proba(X)
        result["probabilities"] = probabilities
        result["confidence"] = np.max(probabilities, axis=1)
    
    return result
