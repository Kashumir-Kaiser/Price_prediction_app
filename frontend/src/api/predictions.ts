/**Prediction API methods.*/
import { apiGet, apiPost } from "./client";
import type { PredictionResponse } from "../types";

/**
 * Fetch prediction for a symbol.
 * Used by react-query (lazy-loaded on component mount).
 */
export async function fetchPrediction(
  symbol: string,
  model: string = "rf"
): Promise<PredictionResponse> {
  return apiGet<PredictionResponse>(
    `/predictions?symbol=${encodeURIComponent(symbol)}&model=${encodeURIComponent(model)}`
  );
}

/**
 * Trigger model retrain (admin only).
 */
export async function retrainModel(symbol: string, model: string = "rf"): Promise<unknown> {
  return apiPost("/predictions/retrain", { symbol, model });
}
