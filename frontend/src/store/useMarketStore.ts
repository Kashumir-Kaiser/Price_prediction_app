/**
 * Zustand store for market data state management
 */
import { create } from 'zustand';
import { MarketState, TimeFrame, Prediction } from '@/types/market';
import { pricesApi, predictionsApi } from '@/api/client';

interface MarketActions {
  setSymbol: (symbol: string, assetType: 'crypto' | 'stable' | 'stock') => void;
  setTimeframe: (timeframe: TimeFrame) => void;
  fetchCryptoData: (symbol: string) => Promise<void>;
  fetchStockData: (symbol: string) => Promise<void>;
  fetchPredictions: (symbol: string) => Promise<void>;
  refreshAll: () => Promise<void>;
  clearError: () => void;
}

const getDaysFromTimeframe = (timeframe: TimeFrame): number => {
  switch (timeframe) {
    case '30D':
      return 30;
    case '90D':
      return 90;
    case '365D':
      return 365;
    default:
      return 90;
  }
};

const getEndDate = (): string => {
  return new Date().toISOString().split('T')[0];
};

const getStartDate = (days: number): string => {
  const date = new Date();
  date.setDate(date.getDate() - days);
  return date.toISOString().split('T')[0];
};

export const useMarketStore = create<MarketState & MarketActions>((set, get) => ({
  // Initial state
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

  // Actions
  setSymbol: (symbol: string, assetType: 'crypto' | 'stable' | 'stock') => {
    set({ selectedSymbol: symbol, assetType, error: null });
    // Auto-fetch data for new symbol
    if (assetType === 'stock') {
      get().fetchStockData(symbol);
    } else {
      get().fetchCryptoData(symbol);
    }
  },

  setTimeframe: (timeframe: TimeFrame) => {
    set({ timeframe });
    // Refetch data with new timeframe
    const { selectedSymbol, assetType } = get();
    if (assetType === 'stock') {
      get().fetchStockData(selectedSymbol);
    } else {
      get().fetchCryptoData(selectedSymbol);
    }
  },

  fetchCryptoData: async (symbol: string) => {
    set({ isLoading: true, error: null });
    try {
      const days = getDaysFromTimeframe(get().timeframe);
      const data = await pricesApi.getCryptoHistory(
        symbol,
        '1Day',
        getStartDate(days),
        getEndDate()
      );
      
      set({
        cryptoBars: data.data || [],
        lastUpdated: new Date(),
        isLoading: false,
      });
      
      // Also fetch predictions
      await get().fetchPredictions(symbol);
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to fetch crypto data',
        isLoading: false,
      });
    }
  },

  fetchStockData: async (symbol: string) => {
    set({ isLoading: true, error: null });
    try {
      const days = getDaysFromTimeframe(get().timeframe);
      const [historyData, financialsData] = await Promise.all([
        pricesApi.getStockHistory(symbol, getStartDate(days), getEndDate()),
        pricesApi.getStockFinancials(symbol),
      ]);
      
      set({
        stockBars: historyData.data || [],
        financials: financialsData.data || null,
        lastUpdated: new Date(),
        isLoading: false,
      });
      
      // Also fetch predictions
      await get().fetchPredictions(symbol);
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to fetch stock data',
        isLoading: false,
      });
    }
  },

  fetchPredictions: async (symbol: string) => {
    try {
      const { assetType } = get();
      const models = ['rf', 'xgb', 'lstm'] as const;
      const predictions: Record<string, Prediction> = {};
      
      for (const model of models) {
        try {
          const prediction = assetType === 'stock'
            ? await predictionsApi.getStockPrediction(symbol, model)
            : await predictionsApi.getCryptoPrediction(symbol, model);
          predictions[model] = prediction;
        } catch (e) {
          console.warn(`Failed to fetch prediction for ${model}:`, e);
        }
      }
      
      set({ predictions });
    } catch (error) {
      console.error('Failed to fetch predictions:', error);
    }
  },

  refreshAll: async () => {
    const { selectedSymbol, assetType } = get();
    if (assetType === 'stock') {
      await get().fetchStockData(selectedSymbol);
    } else {
      await get().fetchCryptoData(selectedSymbol);
    }
  },

  clearError: () => set({ error: null }),
}));
