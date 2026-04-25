/**
 * Frontend type definitions.
 */

export interface User {
  id: number;
  username: string;
  email: string;
  role: "user" | "admin";
  is_active: boolean;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  role: string;
}

export interface PriceBar {
  ts: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface PredictionResponse {
  symbol: string;
  asset_type: string;
  model: string;
  /** Predicted next-day close price. Null when regressor not available. */
  predicted_close: number | null;
  direction: "up" | "down" | "flat";
  confidence: number;
  features_used: string[];
  timestamp: string;
}

export interface ModelInfo {
  name: string;
  description: string;
  available: boolean;
}

export interface WatchlistItem {
  symbol: string;
  source: string;
}

export interface TrafficStats {
  total_requests: number;
  requests_by_status: Array<{ status_code: number; count: number }>;
  requests_by_method: Array<{ method: string; count: number }>;
  avg_duration_ms: number;
  top_paths: Array<{ path: string; count: number }>;
  period_days: number;
}

export interface ApiError {
  type: string;
  title: string;
  status: number;
  detail: string;
  instance: string;
}

export type ToastType = "error" | "warning" | "info";

export interface Toast {
  id: string;
  type: ToastType;
  title: string;
  message: string;
}
