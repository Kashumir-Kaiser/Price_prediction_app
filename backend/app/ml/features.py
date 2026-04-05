"""Feature engineering for price prediction models."""
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
import structlog

logger = structlog.get_logger()


def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index."""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_macd(
    prices: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate MACD line, signal line, and histogram."""
    ema_fast = prices.ewm(span=fast).mean()
    ema_slow = prices.ewm(span=slow).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def calculate_bollinger_bands(
    prices: pd.Series,
    window: int = 20,
    num_std: int = 2
) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
    """Calculate Bollinger Bands."""
    sma = prices.rolling(window=window).mean()
    std = prices.rolling(window=window).std()
    upper_band = sma + (std * num_std)
    lower_band = sma - (std * num_std)
    
    # %B indicator
    percent_b = (prices - lower_band) / (upper_band - lower_band)
    
    # Bandwidth
    bandwidth = (upper_band - lower_band) / sma
    
    return upper_band, lower_band, percent_b, bandwidth


def calculate_volume_zscore(volume: pd.Series, window: int = 30) -> pd.Series:
    """Calculate volume z-score."""
    rolling_mean = volume.rolling(window=window).mean()
    rolling_std = volume.rolling(window=window).std()
    zscore = (volume - rolling_mean) / rolling_std
    return zscore


def engineer_features(
    df: pd.DataFrame,
    include_financials: bool = False,
    financial_data: Optional[Dict[str, Any]] = None
) -> pd.DataFrame:
    """
    Engineer features from OHLCV data.
    
    Args:
        df: DataFrame with OHLCV columns (open, high, low, close, volume)
        include_financials: Whether to include financial features
        financial_data: Financial data dictionary for VN stocks
        
    Returns:
        DataFrame with engineered features
    """
    df = df.copy()
    
    # Ensure required columns exist
    required_cols = ['open', 'high', 'low', 'close', 'volume']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' not found in DataFrame")
    
    # Convert to numeric
    for col in required_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Sort by timestamp
    if 'ts' in df.columns:
        df = df.sort_values('ts')
    
    # Lag features for close price
    for lag in [1, 2, 3, 5, 10]:
        df[f'close_lag{lag}'] = df['close'].shift(lag)
    
    # Returns
    df['return_1d'] = np.log(df['close'] / df['close'].shift(1))
    df['return_5d'] = np.log(df['close'] / df['close'].shift(5))
    df['return_10d'] = np.log(df['close'] / df['close'].shift(10))
    
    # Rolling statistics
    for window in [7, 14, 30]:
        df[f'close_sma{window}'] = df['close'].rolling(window=window).mean()
        df[f'close_std{window}'] = df['close'].rolling(window=window).std()
        df[f'volume_sma{window}'] = df['volume'].rolling(window=window).mean()
        df[f'volume_std{window}'] = df['volume'].rolling(window=window).std()
    
    # RSI
    df['rsi_14'] = calculate_rsi(df['close'], period=14)
    
    # MACD
    df['macd_line'], df['macd_signal'], df['macd_histogram'] = calculate_macd(df['close'])
    
    # Bollinger Bands
    df['bb_upper'], df['bb_lower'], df['bb_percent'], df['bb_bandwidth'] = calculate_bollinger_bands(df['close'])
    
    # Volume z-score
    df['volume_zscore'] = calculate_volume_zscore(df['volume'], window=30)
    
    # Price-based features
    df['high_low_range'] = df['high'] - df['low']
    df['open_close_range'] = abs(df['close'] - df['open'])
    df['body_ratio'] = df['open_close_range'] / df['high_low_range']
    
    # Financial features (VN stocks only)
    if include_financials and financial_data:
        ratios = financial_data.get('ratios', [])
        if ratios:
            latest = ratios[0] if isinstance(ratios, list) else ratios
            df['pe_ratio'] = latest.get('P/E', np.nan)
            df['pb_ratio'] = latest.get('P/B', np.nan)
            df['eps'] = latest.get('EPS', np.nan)
            df['debt_to_equity'] = latest.get('Debt/Equity', np.nan)
    
    logger.info(
        "Engineered features",
        rows=len(df),
        features=len(df.columns),
        include_financials=include_financials
    )
    
    return df


def create_target(
    df: pd.DataFrame,
    horizon: int = 1,
    classification: bool = True
) -> pd.DataFrame:
    """
    Create target variable for prediction.
    
    Args:
        df: DataFrame with 'close' column
        horizon: Prediction horizon (days)
        classification: If True, create binary direction target
        
    Returns:
        DataFrame with target column added
    """
    df = df.copy()
    
    # Future close price
    df['future_close'] = df['close'].shift(-horizon)
    
    # Regression target: raw future close
    df['target_regression'] = df['future_close']
    
    # Classification target: 1 if price goes up, 0 if down
    if classification:
        df['target_classification'] = (df['future_close'] > df['close']).astype(int)
    
    logger.info(
        "Created target variables",
        horizon=horizon,
        classification=classification
    )
    
    return df


def prepare_ml_data(
    df: pd.DataFrame,
    feature_cols: Optional[List[str]] = None,
    target_col: str = 'target_classification',
    drop_na: bool = True
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Prepare data for machine learning.
    
    Args:
        df: DataFrame with features and target
        feature_cols: List of feature column names (auto-detected if None)
        target_col: Name of target column
        drop_na: Whether to drop rows with NaN values
        
    Returns:
        Tuple of (X, y, feature_names)
    """
    if feature_cols is None:
        # Auto-detect feature columns (exclude target and metadata)
        exclude_cols = [
            'target_classification', 'target_regression', 'future_close',
            'open', 'high', 'low', 'close', 'volume', 'ts', 'symbol'
        ]
        feature_cols = [c for c in df.columns if c not in exclude_cols]
    
    # Select columns
    X_df = df[feature_cols].copy()
    y_series = df[target_col].copy()
    
    # Drop NaN
    if drop_na:
        valid_idx = X_df.dropna().index
        X_df = X_df.loc[valid_idx]
        y_series = y_series.loc[valid_idx]
    
    X = X_df.values
    y = y_series.values
    
    logger.info(
        "Prepared ML data",
        samples=len(X),
        features=len(feature_cols),
        target=target_col
    )
    
    return X, y, feature_cols


def get_default_feature_columns() -> List[str]:
    """Get list of default feature column names."""
    return [
        'close_lag1', 'close_lag2', 'close_lag3', 'close_lag5', 'close_lag10',
        'return_1d', 'return_5d', 'return_10d',
        'close_sma7', 'close_sma14', 'close_sma30',
        'close_std7', 'close_std14', 'close_std30',
        'volume_sma30', 'volume_std30',
        'rsi_14',
        'macd_line', 'macd_signal', 'macd_histogram',
        'bb_upper', 'bb_lower', 'bb_percent', 'bb_bandwidth',
        'volume_zscore',
        'high_low_range', 'open_close_range', 'body_ratio'
    ]
