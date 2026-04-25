"""Classical ML model training with scikit-learn."""
import os
import joblib
import numpy as np
from typing import Dict, Any, Optional, List
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import (
    RandomForestClassifier, RandomForestRegressor, GradientBoostingClassifier
)
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import (
    accuracy_score, roc_auc_score, precision_score, recall_score, f1_score,
    mean_squared_error, mean_absolute_error, r2_score,
)
import structlog

from app.config import get_settings
settings = get_settings()

logger = structlog.get_logger()

# Model definitions
CLASSIFIERS = {
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

REGRESSORS = {
    "rf": RandomForestRegressor(
        n_estimators=200,
        max_depth=6,
        random_state=42,
        n_jobs=2
    ),
    "xgb": None,  # GradientBoostingRegressor can be added if needed
}


def train_and_save(
    symbol: str,
    X: np.ndarray,
    y_class: np.ndarray,
    y_regress: Optional[np.ndarray] = None,
    model_key: str = "rf",
    cache_dir: Optional[str] = None,
    feature_names: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Train BOTH a classifier (direction: up/down) and a regressor (next close price).

    Saves two files:
    - {symbol}_{model_key}_clf.joblib -- direction classifier
    - {symbol}_{model_key}_reg.joblib -- price regressor (if y_regress provided)

    Args:
        symbol: Asset symbol
        X: Feature matrix
        y_class: Target vector for classification (direction)
        y_regress: Target vector for regression (next close price). If None, regressor is skipped.
        model_key: Model type ('rf' or 'xgb')
        cache_dir: Directory to save model
        feature_names: List of feature names

    Returns:
        Dictionary with training metrics and model paths
    """
    if model_key not in CLASSIFIERS:
        raise ValueError(f"Unknown model key: {model_key}. Use: {list(CLASSIFIERS.keys())}")

    if cache_dir is None:
        cache_dir = settings.model_cache_dir

    os.makedirs(cache_dir, exist_ok=True)

    sym_safe = symbol.replace("/", "_")
    results = {
        "symbol": symbol,
        "model_key": model_key,
    }

    # ---- Classifier ----
    clf_pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", CLASSIFIERS[model_key])
    ])

    # Time-series cross-validation for classifier
    tscv = TimeSeriesSplit(n_splits=5)
    cv_scores = []
    cv_auc_scores = []

    logger.info(
        "Starting classifier cross-validation",
        symbol=symbol,
        model=model_key,
        samples=len(X)
    )

    for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
        X_train, X_val = X[train_idx], X[val_idx]
        y_train, y_val = y_class[train_idx], y_class[val_idx]

        clf_pipe.fit(X_train, y_train)
        y_pred = clf_pipe.predict(X_val)
        y_proba = clf_pipe.predict_proba(X_val)[:, 1] if hasattr(clf_pipe, 'predict_proba') else None

        acc = accuracy_score(y_val, y_pred)
        cv_scores.append(acc)

        if y_proba is not None and len(np.unique(y_val)) > 1:
            auc = roc_auc_score(y_val, y_proba)
            cv_auc_scores.append(auc)

        logger.debug(
            "CV fold completed (classifier)",
            fold=fold + 1,
            accuracy=acc,
            train_size=len(X_train),
            val_size=len(X_val)
        )

    # Fit classifier on all data
    logger.info(
        "Fitting final classifier on all data",
        symbol=symbol,
        model=model_key
    )
    clf_pipe.fit(X, y_class)

    clf_path = os.path.join(cache_dir, f"{sym_safe}_{model_key}_clf.joblib")
    clf_package = {
        "pipeline": clf_pipe,
        "symbol": symbol,
        "model_type": model_key,
        "model_role": "classifier",
        "feature_names": feature_names,
        "training_samples": len(X),
        "cv_accuracy_mean": float(np.mean(cv_scores)),
        "cv_accuracy_std": float(np.std(cv_scores)),
    }
    if cv_auc_scores:
        clf_package["cv_auc_mean"] = float(np.mean(cv_auc_scores))
        clf_package["cv_auc_std"] = float(np.std(cv_auc_scores))

    joblib.dump(clf_package, clf_path)
    results["clf_path"] = clf_path
    results["cv_accuracy_mean"] = clf_package["cv_accuracy_mean"]
    results["cv_accuracy_std"] = clf_package["cv_accuracy_std"]

    logger.info(
        "Classifier saved",
        symbol=symbol,
        model=model_key,
        path=clf_path,
        cv_accuracy_mean=clf_package["cv_accuracy_mean"]
    )

    # ---- Regressor (only if y_regress is provided) ----
    if y_regress is not None and REGRESSORS.get(model_key) is not None:
        reg_pipe = Pipeline([
            ("scaler", StandardScaler()),
            ("reg", REGRESSORS[model_key])
        ])

        # Time-series cross-validation for regressor
        reg_cv_mse = []
        reg_cv_mae = []
        reg_cv_r2 = []

        logger.info(
            "Starting regressor cross-validation",
            symbol=symbol,
            model=model_key,
            samples=len(X)
        )

        for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
            X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y_regress[train_idx], y_regress[val_idx]

            reg_pipe.fit(X_train, y_train)
            y_pred = reg_pipe.predict(X_val)

            reg_cv_mse.append(mean_squared_error(y_val, y_pred))
            reg_cv_mae.append(mean_absolute_error(y_val, y_pred))
            reg_cv_r2.append(r2_score(y_val, y_pred))

        # Fit regressor on all data
        logger.info(
            "Fitting final regressor on all data",
            symbol=symbol,
            model=model_key
        )
        reg_pipe.fit(X, y_regress)

        reg_path = os.path.join(cache_dir, f"{sym_safe}_{model_key}_reg.joblib")
        reg_package = {
            "pipeline": reg_pipe,
            "symbol": symbol,
            "model_type": model_key,
            "model_role": "regressor",
            "feature_names": feature_names,
            "training_samples": len(X),
            "cv_mse_mean": float(np.mean(reg_cv_mse)),
            "cv_mae_mean": float(np.mean(reg_cv_mae)),
            "cv_r2_mean": float(np.mean(reg_cv_r2)),
        }

        joblib.dump(reg_package, reg_path)
        results["reg_path"] = reg_path
        results["cv_r2_mean"] = reg_package["cv_r2_mean"]

        logger.info(
            "Regressor saved",
            symbol=symbol,
            model=model_key,
            path=reg_path,
            cv_r2_mean=reg_package["cv_r2_mean"]
        )
    else:
        results["reg_path"] = None
        logger.info(
            "Regressor skipped (no y_regress provided or regressor not configured)",
            symbol=symbol,
            model=model_key,
        )

    return results


def load_model(
    symbol: str,
    model_key: str,
    model_role: str = "clf",
    cache_dir: Optional[str] = None
) -> Optional[Pipeline]:
    """
    Load a trained classical model (classifier or regressor).

    Args:
        symbol: Asset symbol
        model_key: Model type ('rf' or 'xgb')
        model_role: 'clf' for classifier, 'reg' for regressor
        cache_dir: Directory containing saved models

    Returns:
        Loaded pipeline or None if not found
    """
    if cache_dir is None:
        cache_dir = settings.model_cache_dir

    safe_symbol = symbol.replace("/", "_")
    filename = f"{safe_symbol}_{model_key}_{model_role}.joblib"
    path = os.path.join(cache_dir, filename)

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
        logger.info(
            "Model loaded",
            symbol=symbol,
            model=model_key,
            role=model_role,
            path=path
        )
        return model_package["pipeline"]
    except Exception as e:
        logger.error(
            "Failed to load model",
            symbol=symbol,
            model=model_key,
            role=model_role,
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
        return_proba: Whether to return probabilities (for classifiers)

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
