"""Tests for model registry."""
import pytest
import os
import tempfile
import joblib
import torch
import numpy as np
from unittest.mock import patch

from app.ml.model_registry import (
    load_classical,
    load_deep,
    clear_cache,
    get_cache_info,
    check_model_exists,
    list_available_models
)
from app.ml.train_deep import PriceLSTM


class TestLoadClassical:
    """Test classical model loading."""
    
    def test_load_existing_model(self):
        """Test loading an existing classical model."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a mock model file
            model_path = os.path.join(tmpdir, "BTC_USD_rf.joblib")
            mock_model = {"pipeline": {"name": "dummy_pipeline"}, "symbol": "BTC/USD"}
            joblib.dump(mock_model, model_path)
            
            with patch('app.ml.model_registry.CACHE_DIR', tmpdir):
                with patch('app.ml.model_registry._cache', {}):
                    model = load_classical("BTC/USD", "rf")
                    
                    assert model is not None
    
    def test_load_nonexistent_model(self):
        """Test loading a non-existent model returns None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('app.ml.model_registry.CACHE_DIR', tmpdir):
                with patch('app.ml.model_registry._cache', {}):
                    model = load_classical("NONEXISTENT", "rf")
                    
                    assert model is None
    
    def test_caching(self):
        """Test that loaded models are cached."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = os.path.join(tmpdir, "BTC_USD_rf.joblib")
            mock_model = {"pipeline": {"name": "dummy_pipeline"}, "symbol": "BTC/USD"}
            joblib.dump(mock_model, model_path)
            
            with patch('app.ml.model_registry.CACHE_DIR', tmpdir):
                with patch('app.ml.model_registry._cache', {}):
                    # First load
                    model1 = load_classical("BTC/USD", "rf")
                    # Second load should use cache
                    model2 = load_classical("BTC/USD", "rf")
                    
                    assert model1 is model2


class TestLoadDeep:
    """Test deep model loading."""
    
    def test_load_existing_lstm(self):
        """Test loading an existing LSTM model."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a mock LSTM checkpoint
            model_path = os.path.join(tmpdir, "BTC_USD_lstm.pt")
            model = PriceLSTM(input_size=10, hidden=64, layers=2, dropout=0.2)
            checkpoint = {
                "state_dict": model.state_dict(),
                "config": {"input_size": 10, "hidden": 64, "layers": 2, "dropout": 0.2},
                "symbol": "BTC/USD"
            }
            torch.save(checkpoint, model_path)
            
            with patch('app.ml.model_registry.CACHE_DIR', tmpdir):
                with patch('app.ml.model_registry._cache', {}):
                    result = load_deep("BTC/USD")
                    
                    assert result is not None
                    model, config = result
                    assert isinstance(model, PriceLSTM)
    
    def test_load_nonexistent_lstm(self):
        """Test loading a non-existent LSTM returns None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('app.ml.model_registry.CACHE_DIR', tmpdir):
                with patch('app.ml.model_registry._cache', {}):
                    result = load_deep("NONEXISTENT")
                    
                    assert result is None
    
    def test_oom_graceful_degradation(self):
        """Test OOM error is handled gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('app.ml.model_registry.CACHE_DIR', tmpdir):
                with patch('app.ml.model_registry._cache', {}):
                    with patch('torch.load', side_effect=RuntimeError("CUDA out of memory")):
                        result = load_deep("BTC/USD")
                        
                        assert result is None


class TestCacheManagement:
    """Test cache management functions."""
    
    def test_clear_all_cache(self):
        """Test clearing all cache."""
        with patch('app.ml.model_registry._cache', {'key1': 'value1', 'key2': 'value2'}):
            clear_cache()
            
            from app.ml.model_registry import _cache
            assert len(_cache) == 0
    
    def test_clear_specific_symbol(self):
        """Test clearing cache for specific symbol."""
        with patch('app.ml.model_registry._cache', {'BTC_rf': 'v1', 'BTC_lstm': 'v2', 'ETH_rf': 'v3'}):
            clear_cache('BTC')
            
            from app.ml.model_registry import _cache
            assert 'BTC_rf' not in _cache
            assert 'BTC_lstm' not in _cache
            assert 'ETH_rf' in _cache
    
    def test_get_cache_info(self):
        """Test getting cache info."""
        with patch('app.ml.model_registry._cache', {'key1': 'v1', 'key2': 'v2'}):
            info = get_cache_info()
            
            assert info['cache_size'] == 2
            assert 'key1' in info['cached_models']


class TestModelExists:
    """Test model existence check."""
    
    def test_existing_model(self):
        """Test checking existing model."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = os.path.join(tmpdir, "BTC_USD_rf.joblib")
            with open(model_path, 'w') as f:
                f.write("")
            
            with patch('app.ml.model_registry.CACHE_DIR', tmpdir):
                exists = check_model_exists("BTC/USD", "rf")
                
                assert exists is True
    
    def test_nonexistent_model(self):
        """Test checking non-existent model."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('app.ml.model_registry.CACHE_DIR', tmpdir):
                exists = check_model_exists("NONEXISTENT", "rf")
                
                assert exists is False


class TestListAvailableModels:
    """Test listing available models."""
    
    def test_list_models(self):
        """Test listing all available models."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock model files
            open(os.path.join(tmpdir, "BTC_USD_rf.joblib"), 'w').close()
            open(os.path.join(tmpdir, "BTC_USD_xgb.joblib"), 'w').close()
            open(os.path.join(tmpdir, "BTC_USD_lstm.pt"), 'w').close()
            open(os.path.join(tmpdir, "ETH_USD_rf.joblib"), 'w').close()
            
            with patch('app.ml.model_registry.CACHE_DIR', tmpdir):
                models = list_available_models()
                
                assert 'rf' in models
                assert 'xgb' in models
                assert 'lstm' in models
                assert len(models['rf']) == 2
                assert len(models['lstm']) == 1
