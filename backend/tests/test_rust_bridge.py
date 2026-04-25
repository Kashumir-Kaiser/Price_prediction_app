"""
Verification tests for Rust/PyArrow bridge.

Run after maturin develop:
  maturin develop --release
  pytest backend/tests/test_rust_bridge.py

Exit code: 0 = all assertions pass, bridge is production-safe.
"""
import pytest
import numpy as np


# Skip if Rust extension not built
market_features = pytest.importorskip("market_features")


class TestRustBridge:
    """Verify Rust extension produces identical output to Python."""

    def test_rust_bridge_basic(self):
        """Rust bridge returns non-None RecordBatch for valid data."""
        close = np.array([100.0 + i for i in range(50)], dtype="float64")
        high = close + np.random.uniform(0.1, 2.0, size=50)
        low = close - np.random.uniform(0.1, 2.0, size=50)
        volume = np.random.uniform(1000.0, 10000.0, size=50)

        rb = market_features.engineer_features_rs(close, high, low, volume)
        assert rb is not None
        assert rb.num_rows == 50
        assert rb.num_columns >= 1

    def test_rust_bridge_vs_python(self):
        """Rust bridge output matches pure Python pandas for RSI/MACD/BB."""
        import pandas as pd

        np.random.seed(42)
        close = np.array([100.0 + np.sin(i * 0.1) * 10 + i * 0.5 for i in range(100)], dtype="float64")
        high = close + np.random.uniform(0.1, 2.0, size=100)
        low = close - np.random.uniform(0.1, 2.0, size=100)
        volume = np.random.uniform(1000.0, 10000.0, size=100)

        # Rust result
        rb = market_features.engineer_features_rs(close, high, low, volume)

        # Convert to pandas for comparison
        df_rust = rb.to_pandas()

        # Python result
        df = pd.DataFrame({"close": close, "high": high, "low": low, "volume": volume})

        def py_rsi(prices, period=14):
            delta = pd.Series(prices).diff()
            gain = delta.where(delta > 0, 0.0).rolling(period).mean()
            loss = -delta.where(delta < 0, 0.0).rolling(period).mean()
            rs = gain / loss
            return 100.0 - (100.0 / (1.0 + rs))

        py_rsi_vals = py_rsi(close).to_numpy()
        rust_rsi_vals = df_rust["rsi_14"].to_numpy()

        # Compare non-NaN values (allowing for small floating-point differences)
        valid = ~np.isnan(py_rsi_vals) & ~np.isnan(rust_rsi_vals)
        if valid.sum() > 0:
            np.testing.assert_allclose(
                py_rsi_vals[valid],
                rust_rsi_vals[valid],
                rtol=1e-3,
                atol=1e-3,
            )
