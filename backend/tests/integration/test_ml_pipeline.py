"""Integration test for ML feature engineering end-to-end."""
import pytest
import pandas as pd
import numpy as np
from app.ml.features import engineer_features, calculate_rsi, calculate_macd, calculate_bollinger_bands


def test_rust_rsi_output_length():
    """RSI output must match input length."""
    prices = pd.Series(np.random.randn(100).cumsum() + 100)
    rsi = calculate_rsi(prices, period=14)
    assert len(rsi) == len(prices)
    assert rsi.iloc[:14].isna().all()


def test_macd_output_structure():
    """MACD returns three Series of equal length."""
    prices = pd.Series(np.random.randn(100).cumsum() + 100)
    line, signal, hist = calculate_macd(prices)
    assert len(line) == len(prices)
    assert len(signal) == len(prices)
    assert len(hist) == len(prices)
    assert (hist == line - signal).all() or hist.isna().eq((line - signal).isna()).all()


def test_bollinger_bands_ordered():
    """Upper band must always be >= lower band."""
    prices = pd.Series(np.random.randn(100).cumsum() + 100)
    upper, lower, pct_b, bw = calculate_bollinger_bands(prices, window=20)
    valid = upper.notna() & lower.notna()
    assert (upper[valid] >= lower[valid]).all()


def test_engineer_features_columns():
    """Feature engineering should produce expected columns."""
    n = 200
    df = pd.DataFrame({
        "open": np.random.randn(n).cumsum() + 100,
        "high": np.random.randn(n).cumsum() + 102,
        "low": np.random.randn(n).cumsum() + 98,
        "close": np.random.randn(n).cumsum() + 100,
        "volume": np.random.randint(100000, 10000000, n),
    })
    result = engineer_features(df)
    expected_cols = [
        "close_lag1", "close_lag2", "close_lag3", "close_lag5", "close_lag10",
        "return_1d", "return_5d", "return_10d",
        "rsi_14", "macd_line", "macd_signal", "macd_histogram",
        "bb_upper", "bb_lower", "bb_percent", "bb_bandwidth",
        "volume_zscore", "high_low_range", "open_close_range", "body_ratio",
    ]
    for col in expected_cols:
        assert col in result.columns, f"Missing column: {col}"
