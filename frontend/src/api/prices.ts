/**Price data API methods.*/
import { apiGet } from "./client";
import type { PriceBar } from "../types";

/**
 * Fetch historical price data for a symbol.
 */
export async function fetchPrices(
  symbol: string,
  start?: string,
  end?: string
): Promise<PriceBar[]> {
  const params = new URLSearchParams();
  params.append("symbol", symbol);
  if (start) params.append("start", start);
  if (end) params.append("end", end);

  return apiGet<PriceBar[]>(`/prices?${params.toString()}`);
}
