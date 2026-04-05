"""Tests for feature engineering."""
import pytest
import numpy as np
import pandas as pd

from app.ml.features import (
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands,
    engineer_features,
    create_target,
    prepare_ml_data
)


class TestCalculateRSI:
    """Test RSI calculation."""
    
    def test_rsi_range(self, sample_ohlcv_data):
        """Test RSI values are in [0, 100]."""
        rsi = calculate_rsi(sample_ohlcv_data['close'])
        
        assert rsi.min() >= 0
        assert rsi.max() <= 100
        assert not rsi.isna().all()
    
    def test_rsi_increasing_prices(self):
        """Test RSI with consistently increasing prices."""
        prices = pd.Series([100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110] * 2)
        rsi = calculate_rsi(prices)
        
        # RSI should be high (trending up)
        assert rsi.iloc[-1] > 50


class TestCalculateMACD:
    """Test MACD calculation."""
    
    def test_macd_output(self, sample_ohlcv_data):
        """Test MACD returns three series."""
        macd_line, signal_line, histogram = calculate_macd(sample_ohlcv_data['close'])
        
        assert len(macd_line) == len(sample_ohlcv_data)
        assert len(signal_line) == len(sample_ohlcv_data)
        assert len(histogram) == len(sample_ohlcv_data)
        assert histogram.equals(macd_line - signal_line)


class TestCalculateBollingerBands:
    """Test Bollinger Bands calculation."""
    
    def test_bollinger_structure(self, sample_ohlcv_data):
        """Test Bollinger Bands structure."""
        upper, lower, percent_b, bandwidth = calculate_bollinger_bands(sample_ohlcv_data['close'])
        
        assert len(upper) == len(sample_ohlcv_data)
        valid_band_rows = upper.notna() & lower.notna()
        assert (upper[valid_band_rows] >= lower[valid_band_rows]).all()
        assert percent_b.dropna().min() >= -0.5  # Allow some margin
        assert percent_b.dropna().max() <= 1.5


class TestEngineerFeatures:
    """Test feature engineering pipeline."""
    
    def test_lag_features(self, sample_ohlcv_data):
        """Test lag features are created correctly."""
        df = engineer_features(sample_ohlcv_data)
        
        assert 'close_lag1' in df.columns
        assert 'close_lag2' in df.columns
        assert 'close_lag3' in df.columns
        assert 'close_lag5' in df.columns
        assert 'close_lag10' in df.columns
    
    def test_returns_calculated(self, sample_ohlcv_data):
        """Test returns are calculated."""
        df = engineer_features(sample_ohlcv_data)
        
        assert 'return_1d' in df.columns
        assert 'return_5d' in df.columns
        assert 'return_10d' in df.columns
    
    def test_rsi_added(self, sample_ohlcv_data):
        """Test RSI is added."""
        df = engineer_features(sample_ohlcv_data)
        
        assert 'rsi_14' in df.columns
        assert df['rsi_14'].min() >= 0
        assert df['rsi_14'].max() <= 100
    
    def test_macd_added(self, sample_ohlcv_data):
        """Test MACD is added."""
        df = engineer_features(sample_ohlcv_data)
        
        assert 'macd_line' in df.columns
        assert 'macd_signal' in df.columns
        assert 'macd_histogram' in df.columns
    
    def test_bollinger_added(self, sample_ohlcv_data):
        """Test Bollinger Bands are added."""
        df = engineer_features(sample_ohlcv_data)
        
        assert 'bb_upper' in df.columns
        assert 'bb_lower' in df.columns
        assert 'bb_percent' in df.columns
        assert 'bb_bandwidth' in df.columns
    
    def test_volume_zscore(self, sample_ohlcv_data):
        """Test volume z-score is calculated."""
        df = engineer_features(sample_ohlcv_data)
        
        assert 'volume_zscore' in df.columns


class TestCreateTarget:
    """Test target creation."""
    
    def test_classification_target(self, sample_ohlcv_data):
        """Test binary classification target."""
        df = engineer_features(sample_ohlcv_data)
        df = create_target(df, classification=True)
        
        assert 'target_classification' in df.columns
        assert 'target_regression' in df.columns
        assert df['target_classification'].isin([0, 1]).all()
    
    def test_regression_target(self, sample_ohlcv_data):
        """Test regression target."""
        df = engineer_features(sample_ohlcv_data)
        df = create_target(df, classification=False)
        
        assert 'target_regression' in df.columns
        assert 'target_classification' not in df.columns


class TestPrepareMLData:
    """Test ML data preparation."""
    
    def test_output_shapes(self, sample_ohlcv_data):
        """Test output shapes are correct."""
        df = engineer_features(sample_ohlcv_data)
        df = create_target(df)
        
        X, y, feature_names = prepare_ml_data(df)
        
        assert X.shape[0] == len(y)
        assert X.shape[1] == len(feature_names)
        assert len(feature_names) > 0
    
    def test_no_nan_in_output(self, sample_ohlcv_data):
        """Test no NaN values in output."""
        df = engineer_features(sample_ohlcv_data)
        df = create_target(df)
        
        X, y, _ = prepare_ml_data(df)
        
        assert not np.isnan(X).any()
        assert not np.isnan(y).any()
