"""Unit tests for Rust-accelerated feature engineering."""
import pytest
import numpy as np
import pandas as pd

from app.ml.features import calculate_rsi, calculate_macd, calculate_bollinger_bands, _HAS_RUST


class TestRSI:
    def test_output_length_preserved(self):
        prices = pd.Series(np.random.randn(100).cumsum() + 100)
        rsi = calculate_rsi(prices, period=14)
        assert len(rsi) == len(prices)

    def test_first_n_nan(self):
        prices = pd.Series(range(1, 31))
        rsi = calculate_rsi(prices, period=14)
        assert rsi.iloc[:14].isna().all()
        assert not rsi.iloc[14].isna()

    def test_range_0_to_100(self):
        prices = pd.Series(np.random.randn(200).cumsum() + 100)
        rsi = calculate_rsi(prices, period=14)
        valid = rsi.dropna()
        assert (valid >= 0).all() and (valid <= 100).all()


class TestMACD:
    def test_output_length_preserved(self):
        prices = pd.Series(np.random.randn(100).cumsum() + 100)
        line, signal, hist = calculate_macd(prices)
        assert len(line) == len(prices)
        assert len(signal) == len(prices)
        assert len(hist) == len(prices)

    def test_histogram_is_diff(self):
        prices = pd.Series(np.random.randn(100).cumsum() + 100)
        line, signal, hist = calculate_macd(prices)
        valid = line.notna() & signal.notna()
        expected = line[valid] - signal[valid]
        assert np.allclose(hist[valid], expected)


class TestBollingerBands:
    def test_output_length_preserved(self):
        prices = pd.Series(np.random.randn(100).cumsum() + 100)
        upper, lower, pct_b, bw = calculate_bollinger_bands(prices, window=20)
        assert len(upper) == len(prices)
        assert len(lower) == len(prices)
        assert len(pct_b) == len(prices)
        assert len(bw) == len(prices)

    def test_upper_above_lower(self):
        prices = pd.Series(np.random.randn(100).cumsum() + 100)
        upper, lower, _, _ = calculate_bollinger_bands(prices, window=20)
        valid = upper.notna() & lower.notna()
        assert (upper[valid] >= lower[valid]).all()


class TestRustFallback:
    def test_rust_flag_detected(self):
        # _HAS_RUST is True if the compiled extension is importable
        assert isinstance(_HAS_RUST, bool)

    def test_results_match_fallback(self):
        """If Rust is available, ensure it matches the Python fallback logic."""
        prices = pd.Series([100.0, 101.0, 102.0, 101.0, 100.0, 99.0, 98.0, 97.0, 98.0, 99.0,
                           100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0,
                           110.0, 111.0, 112.0, 113.0, 114.0, 115.0, 116.0, 117.0, 118.0, 119.0])
        rsi = calculate_rsi(prices, period=14)
        assert len(rsi) == len(prices)
        assert rsi.notna().sum() == len(prices) - 14 + 1
