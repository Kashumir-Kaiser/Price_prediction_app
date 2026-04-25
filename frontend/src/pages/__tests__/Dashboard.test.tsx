/**Dashboard tests.*/
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Dashboard from "../Dashboard";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

vi.mock("../../api/predictions", () => ({
  fetchPrediction: vi.fn(() =>
    Promise.resolve({
      symbol: "BTC/USD",
      asset_type: "crypto",
      model: "rf",
      predicted_close: 65000,
      direction: "up",
      confidence: 0.85,
      features_used: ["rsi_14", "macd_line"],
      timestamp: "2024-01-01T00:00:00Z",
    })
  ),
}));

vi.mock("../../api/prices", () => ({
  fetchPrices: vi.fn(() => Promise.resolve([])),
}));

describe("Dashboard", () => {
  it("renders without crashing", () => {
    render(
      <QueryClientProvider client={queryClient}>
        <Dashboard />
      </QueryClientProvider>
    );
    expect(screen.getByRole("main")).toBeInTheDocument();
  });
});
