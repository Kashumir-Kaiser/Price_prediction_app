/**
 * Price chart component using Recharts
 */
import React, { useState } from 'react';
import {
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  Area,
} from 'recharts';
import { useMarketStore } from '@/store/useMarketStore';
import { TimeFrame } from '@/types/market';

interface ChartData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  sma20?: number;
  sma50?: number;
  bbUpper?: number;
  bbLower?: number;
}

interface PriceChartProps {
  showSMA?: boolean;
  showBollinger?: boolean;
  predictedPrice?: number | null;
}

const calculateSMA = (data: ChartData[], period: number): number[] => {
  const closes = data.map((d) => d.close);
  const sma: number[] = [];
  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) {
      sma.push(NaN);
    } else {
      const sum = closes.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0);
      sma.push(sum / period);
    }
  }
  return sma;
};

const calculateBollingerBands = (
  data: ChartData[],
  period: number = 20,
  numStd: number = 2
): { upper: number[]; lower: number[] } => {
  const closes = data.map((d) => d.close);
  const upper: number[] = [];
  const lower: number[] = [];

  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) {
      upper.push(NaN);
      lower.push(NaN);
    } else {
      const slice = closes.slice(i - period + 1, i + 1);
      const mean = slice.reduce((a, b) => a + b, 0) / period;
      const variance = slice.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / period;
      const std = Math.sqrt(variance);
      upper.push(mean + numStd * std);
      lower.push(mean - numStd * std);
    }
  }

  return { upper, lower };
};

export const PriceChart: React.FC<PriceChartProps> = ({
  showSMA = true,
  showBollinger = false,
  predictedPrice = null,
}) => {
  const { cryptoBars, stockBars, assetType, timeframe, setTimeframe, isLoading } = useMarketStore();
  const [showVolume, setShowVolume] = useState(true);

  const bars = assetType === 'stock' ? stockBars : cryptoBars;

  // Transform data for chart
  const chartData: ChartData[] = bars
    .slice()
    .reverse()
    .map((bar) => ({
      date: new Date(bar.ts).toLocaleDateString(),
      open: bar.open,
      high: bar.high,
      low: bar.low,
      close: bar.close,
      volume: bar.volume,
    }));

  // Calculate indicators
  if (chartData.length > 0) {
    const sma20 = calculateSMA(chartData, 20);
    const sma50 = calculateSMA(chartData, 50);
    const bb = calculateBollingerBands(chartData);

    chartData.forEach((d, i) => {
      d.sma20 = sma20[i];
      d.sma50 = sma50[i];
      d.bbUpper = bb.upper[i];
      d.bbLower = bb.lower[i];
    });
  }

  const latestClose = chartData.length > 0 ? chartData[chartData.length - 1].close : 0;

  const timeframes: { label: string; value: TimeFrame }[] = [
    { label: '30D', value: '30D' },
    { label: '90D', value: '90D' },
    { label: '1Y', value: '365D' },
  ];

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-96 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Price Chart</h2>
          <p className="text-sm text-gray-500">
            {assetType === 'stock' ? 'Vietnamese Stock' : 'Cryptocurrency'} OHLCV Data
          </p>
        </div>

        {/* Timeframe selector */}
        <div className="flex gap-2">
          {timeframes.map((tf) => (
            <button
              key={tf.value}
              onClick={() => setTimeframe(tf.value)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                timeframe === tf.value
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {tf.label}
            </button>
          ))}
        </div>
      </div>

      {/* Indicators toggle */}
      <div className="flex flex-wrap gap-4 mb-4">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={showSMA}
            onChange={(e) => showSMA !== e.target.checked}
            className="w-4 h-4 text-blue-600 rounded"
          />
          <span className="text-sm text-gray-700">SMA (20, 50)</span>
        </label>
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={showBollinger}
            onChange={(e) => showBollinger !== e.target.checked}
            className="w-4 h-4 text-blue-600 rounded"
          />
          <span className="text-sm text-gray-700">Bollinger Bands</span>
        </label>
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={showVolume}
            onChange={(e) => setShowVolume(e.target.checked)}
            className="w-4 h-4 text-blue-600 rounded"
          />
          <span className="text-sm text-gray-700">Volume</span>
        </label>
      </div>

      {/* Chart */}
      {chartData.length > 0 ? (
        <div className="h-96">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData} data-testid="market-overview-chart" margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
              <XAxis dataKey="date" tick={{ fontSize: 12 }} />
              <YAxis
                yAxisId="price"
                domain={['auto', 'auto']}
                tick={{ fontSize: 12 }}
                tickFormatter={(value) =>
                  value >= 1000 ? `$${(value / 1000).toFixed(1)}k` : `$${value.toFixed(2)}`
                }
              />
              {showVolume && (
                <YAxis
                  yAxisId="volume"
                  orientation="right"
                  tick={{ fontSize: 10 }}
                  tickFormatter={(value) => `${(value / 1000000).toFixed(0)}M`}
                />
              )}
              <Tooltip
                contentStyle={{
                  backgroundColor: 'white',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  padding: '12px',
                }}
                formatter={(value: number, name: string) => {
                  if (name === 'Volume') return [value.toLocaleString(), name];
                  return [`$${value.toFixed(2)}`, name];
                }}
              />
              <Legend />

              {/* Bollinger Bands */}
              {showBollinger && (
                <>
                  <Area
                    yAxisId="price"
                    type="monotone"
                    dataKey="bbUpper"
                    stroke="none"
                    fill="#e0e7ff"
                    fillOpacity={0.3}
                  />
                  <Area
                    yAxisId="price"
                    type="monotone"
                    dataKey="bbLower"
                    stroke="none"
                    fill="#ffffff"
                    fillOpacity={1}
                  />
                  <Line
                    yAxisId="price"
                    type="monotone"
                    dataKey="bbUpper"
                    stroke="#6366f1"
                    strokeDasharray="5 5"
                    dot={false}
                    name="BB Upper"
                  />
                  <Line
                    yAxisId="price"
                    type="monotone"
                    dataKey="bbLower"
                    stroke="#6366f1"
                    strokeDasharray="5 5"
                    dot={false}
                    name="BB Lower"
                  />
                </>
              )}

              {/* Price line */}
              <Line
                yAxisId="price"
                type="monotone"
                dataKey="close"
                stroke="#2563eb"
                strokeWidth={2}
                dot={false}
                name="Close Price"
              />

              {/* SMA lines */}
              {showSMA && (
                <>
                  <Line
                    yAxisId="price"
                    type="monotone"
                    dataKey="sma20"
                    stroke="#f59e0b"
                    strokeWidth={1.5}
                    dot={false}
                    name="SMA 20"
                  />
                  <Line
                    yAxisId="price"
                    type="monotone"
                    dataKey="sma50"
                    stroke="#10b981"
                    strokeWidth={1.5}
                    dot={false}
                    name="SMA 50"
                  />
                </>
              )}

              {/* Predicted price */}
              {predictedPrice && (
                <ReferenceLine
                  yAxisId="price"
                  y={predictedPrice}
                  stroke="#dc2626"
                  strokeDasharray="10 5"
                  label={{ value: 'Predicted', fill: '#dc2626', fontSize: 12 }}
                />
              )}

              {/* Volume bars */}
              {showVolume && (
                <Bar
                  yAxisId="volume"
                  dataKey="volume"
                  fill="#e5e7eb"
                  opacity={0.5}
                  name="Volume"
                />
              )}
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <div className="h-96 flex items-center justify-center bg-gray-50 rounded-lg">
          <p className="text-gray-500">No data available</p>
        </div>
      )}

      {/* Stats */}
      {latestClose > 0 && (
        <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-500">Latest Close</p>
            <p className="text-lg font-semibold text-gray-900">
              ${latestClose.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </p>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-500">Data Points</p>
            <p className="text-lg font-semibold text-gray-900">{chartData.length}</p>
          </div>
          {predictedPrice && (
            <div className="bg-red-50 rounded-lg p-3">
              <p className="text-xs text-red-600">Predicted</p>
              <p className="text-lg font-semibold text-red-700">
                ${predictedPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default PriceChart;
