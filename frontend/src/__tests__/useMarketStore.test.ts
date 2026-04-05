/**
 * Tests for useMarketStore
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { useMarketStore } from '@/store/useMarketStore';
import { act } from '@testing-library/react';

describe('useMarketStore', () => {
  beforeEach(() => {
    // Reset store to initial state
    act(() => {
      useMarketStore.setState({
        selectedSymbol: 'BTC/USD',
        assetType: 'crypto',
        timeframe: '90D',
        cryptoBars: [],
        stockBars: [],
        financials: null,
        predictions: {},
        isLoading: false,
        error: null,
        lastUpdated: null,
      });
    });
  });

  it('initializes with correct defaults', () => {
    const state = useMarketStore.getState();
    
    expect(state.selectedSymbol).toBe('BTC/USD');
    expect(state.assetType).toBe('crypto');
    expect(state.timeframe).toBe('90D');
    expect(state.isLoading).toBe(false);
  });

  it('setSymbol updates selectedSymbol and assetType', () => {
    act(() => {
      useMarketStore.getState().setSymbol('VNM', 'stock');
    });
    
    const state = useMarketStore.getState();
    expect(state.selectedSymbol).toBe('VNM');
    expect(state.assetType).toBe('stock');
  });

  it('setTimeframe updates timeframe', () => {
    act(() => {
      useMarketStore.getState().setTimeframe('30D');
    });
    
    const state = useMarketStore.getState();
    expect(state.timeframe).toBe('30D');
  });

  it('clearError removes error', () => {
    act(() => {
      useMarketStore.setState({ error: 'Test error' });
    });
    
    expect(useMarketStore.getState().error).toBe('Test error');
    
    act(() => {
      useMarketStore.getState().clearError();
    });
    
    expect(useMarketStore.getState().error).toBeNull();
  });

  it('stores predictions correctly', () => {
    const mockPrediction = {
      symbol: 'BTC/USD',
      asset_type: 'crypto' as const,
      model: 'rf' as const,
      predicted_close: 45000,
      direction: 'up' as const,
      confidence: 0.75,
      horizon: '1D',
      generated_at: '2024-01-15T09:00:00Z',
      features_used: ['close_lag1'],
    };
    
    act(() => {
      useMarketStore.setState({
        predictions: { rf: mockPrediction },
      });
    });
    
    const state = useMarketStore.getState();
    expect(state.predictions.rf).toEqual(mockPrediction);
  });
});
