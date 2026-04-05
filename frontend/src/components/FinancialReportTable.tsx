/**
 * Financial report table component for VN stocks
 */
import React, { useState } from 'react';
import { ExternalLink } from 'lucide-react';
import { useMarketStore } from '@/store/useMarketStore';

interface FinancialMetric {
  label: string;
  key: string;
  format?: 'number' | 'percent' | 'currency';
}

const RATIO_METRICS: FinancialMetric[] = [
  { label: 'P/E Ratio', key: 'P/E', format: 'number' },
  { label: 'P/B Ratio', key: 'P/B', format: 'number' },
  { label: 'EPS', key: 'EPS', format: 'currency' },
  { label: 'ROE', key: 'ROE', format: 'percent' },
  { label: 'ROA', key: 'ROA', format: 'percent' },
  { label: 'Debt/Equity', key: 'Debt/Equity', format: 'number' },
];

const INCOME_METRICS: FinancialMetric[] = [
  { label: 'Revenue', key: 'revenue', format: 'currency' },
  { label: 'Net Profit', key: 'net_profit', format: 'currency' },
  { label: 'Gross Margin', key: 'gross_margin', format: 'percent' },
  { label: 'Operating Margin', key: 'operating_margin', format: 'percent' },
  { label: 'Net Margin', key: 'net_margin', format: 'percent' },
];

const formatValue = (value: number | string | undefined, format?: string): string => {
  if (value === undefined || value === null) return '-';
  
  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(num)) return String(value);
  
  switch (format) {
    case 'percent':
      return `${(num * 100).toFixed(2)}%`;
    case 'currency':
      if (Math.abs(num) >= 1e9) {
        return `${(num / 1e9).toFixed(2)}B`;
      } else if (Math.abs(num) >= 1e6) {
        return `${(num / 1e6).toFixed(2)}M`;
      }
      return num.toLocaleString(undefined, { maximumFractionDigits: 2 });
    default:
      return num.toLocaleString(undefined, { maximumFractionDigits: 2 });
  }
};

export const FinancialReportTable: React.FC = () => {
  const { financials, selectedSymbol, isLoading } = useMarketStore();
  const [showQuarterly, setShowQuarterly] = useState(true);

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  const ratios = financials?.ratios || [];
  const incomeStatements = financials?.income_statement || [];

  // Get unique periods
  const allPeriods = new Set<string>();
  ratios.forEach((r: any) => {
    if (r.period) allPeriods.add(r.period);
  });
  incomeStatements.forEach((i: any) => {
    if (i.period) allPeriods.add(i.period);
  });

  const periods = Array.from(allPeriods).sort().reverse().slice(0, showQuarterly ? 4 : 4);

  return (
    <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Financial Reports</h2>
          <p className="text-sm text-gray-500">
            {selectedSymbol} - Key Financial Metrics
          </p>
        </div>

        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={showQuarterly}
              onChange={(e) => setShowQuarterly(e.target.checked)}
              className="w-4 h-4 text-blue-600 rounded"
            />
            <span className="text-sm text-gray-700">Quarterly View</span>
          </label>

          <a
            href={`https://finance.vietstock.vn/${selectedSymbol}/tai-chinh.htm`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800"
          >
            View on VietStock
            <ExternalLink className="w-4 h-4" />
          </a>
        </div>
      </div>

      {/* Financial Ratios Table */}
      {periods.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 font-semibold text-gray-700">Metric</th>
                {periods.map((period) => (
                  <th key={period} className="text-right py-3 px-4 font-semibold text-gray-700">
                    {period}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {/* Ratio Metrics */}
              <tr className="bg-gray-50">
                <td colSpan={periods.length + 1} className="py-2 px-4 font-medium text-gray-900">
                  Valuation Ratios
                </td>
              </tr>
              {RATIO_METRICS.map((metric) => (
                <tr key={metric.key} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-3 px-4 text-gray-700">{metric.label}</td>
                  {periods.map((period) => {
                    const ratioData = ratios.find((r: any) => r.period === period)?.data || {};
                    const value = ratioData[metric.key];
                    return (
                      <td key={period} className="text-right py-3 px-4 text-gray-900">
                        {formatValue(value, metric.format)}
                      </td>
                    );
                  })}
                </tr>
              ))}

              {/* Income Metrics */}
              <tr className="bg-gray-50">
                <td colSpan={periods.length + 1} className="py-2 px-4 font-medium text-gray-900">
                  Income Statement
                </td>
              </tr>
              {INCOME_METRICS.map((metric) => (
                <tr key={metric.key} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-3 px-4 text-gray-700">{metric.label}</td>
                  {periods.map((period) => {
                    const incomeData = incomeStatements.find((i: any) => i.period === period)?.data || {};
                    const value = incomeData[metric.key];
                    return (
                      <td key={period} className="text-right py-3 px-4 text-gray-900">
                        {formatValue(value, metric.format)}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <p className="text-gray-500">No financial data available</p>
          <p className="text-sm text-gray-400 mt-1">
            Financial reports may not be available for this symbol
          </p>
        </div>
      )}
    </div>
  );
};

export default FinancialReportTable;
