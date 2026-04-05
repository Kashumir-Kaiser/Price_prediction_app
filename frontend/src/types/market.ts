export type TimeFrame = '30D' | '90D' | '365D';

export type AssetType = 'crypto' | 'stable' | 'stock';

export type PredictionDirection = 'up' | 'down' | 'flat';

export type PredictionModel = 'rf' | 'xgb' | 'lstm';

export interface Prediction {
  symbol: string;
  asset_type: AssetType;
  model: PredictionModel | string;
  predicted_close: number;
  direction: PredictionDirection | string;
  confidence: number;
  horizon: string;
  generated_at: string;
  features_used: string[];
}

export interface CryptoBar {
  ts: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface StockBar {
  ts: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface FinancialsData {
  ratios: Array<{
    period: string;
    data: Record<string, number>;
  }>;
  income_statement: Array<{
    period: string;
    data: Record<string, number>;
  }>;
}

export interface MarketState {
  selectedSymbol: string;
  assetType: AssetType;
  timeframe: TimeFrame;
  cryptoBars: CryptoBar[];
  stockBars: StockBar[];
  financials: FinancialsData | null;
  predictions: Record<string, Prediction>;
  isLoading: boolean;
  error: string | null;
  lastUpdated: Date | null;
}

