/**
 * Financial report page for VN stocks
 */
import React, { useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, FileText, TrendingUp, DollarSign, PieChart } from 'lucide-react';
import { FinancialReportTable } from '@/components/FinancialReportTable';
import { useMarketStore } from '@/store/useMarketStore';

const FinancialReport: React.FC = () => {
  const { symbol } = useParams<{ symbol: string }>();
  const { selectedSymbol, setSymbol, fetchStockData } = useMarketStore();

  useEffect(() => {
    if (symbol && symbol !== selectedSymbol) {
      setSymbol(symbol, 'stock');
      fetchStockData(symbol);
    }
  }, [symbol]);

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                to="/"
                className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
                <span className="text-sm font-medium">Back to Dashboard</span>
              </Link>
            </div>

            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-purple-600 rounded-lg flex items-center justify-center">
                <FileText className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">
                  Financial Report
                </h1>
                <p className="text-sm text-gray-500">
                  {selectedSymbol} - Detailed Financial Analysis
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <a
                href={`https://www.hsx.vn/Modules/Listed/Web/SymbolDetail/${selectedSymbol}`}
                target="_blank"
                rel="noopener noreferrer"
                className="px-4 py-2 bg-purple-50 text-purple-700 rounded-lg hover:bg-purple-100 transition-colors text-sm font-medium"
              >
                View on HOSE
              </a>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Key Metrics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                <TrendingUp className="w-4 h-4 text-blue-600" />
              </div>
              <span className="text-sm text-gray-500">Stock Symbol</span>
            </div>
            <p className="text-2xl font-bold text-gray-900">{selectedSymbol}</p>
            <p className="text-xs text-gray-400">HOSE Listed</p>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                <DollarSign className="w-4 h-4 text-green-600" />
              </div>
              <span className="text-sm text-gray-500">Exchange</span>
            </div>
            <p className="text-2xl font-bold text-gray-900">HOSE</p>
            <p className="text-xs text-gray-400">Ho Chi Minh Stock Exchange</p>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                <PieChart className="w-4 h-4 text-purple-600" />
              </div>
              <span className="text-sm text-gray-500">Data Source</span>
            </div>
            <p className="text-2xl font-bold text-gray-900">vnstock</p>
            <p className="text-xs text-gray-400">TCBS/VCI Data</p>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-8 h-8 bg-orange-100 rounded-lg flex items-center justify-center">
                <FileText className="w-4 h-4 text-orange-600" />
              </div>
              <span className="text-sm text-gray-500">Reports</span>
            </div>
            <p className="text-2xl font-bold text-gray-900">Quarterly</p>
            <p className="text-xs text-gray-400">Last 8 quarters</p>
          </div>
        </div>

        {/* Financial Report Table */}
        <FinancialReportTable />

        {/* Additional Information */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Data Sources */}
          <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Data Sources</h3>
            <ul className="space-y-3">
              <li className="flex items-start gap-3">
                <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                <div>
                  <p className="font-medium text-gray-900">TCBS (Techcombank Securities)</p>
                  <p className="text-sm text-gray-500">Primary source for OHLCV and financial data</p>
                </div>
              </li>
              <li className="flex items-start gap-3">
                <div className="w-2 h-2 bg-green-500 rounded-full mt-2"></div>
                <div>
                  <p className="font-medium text-gray-900">VCI (Viet Capital Securities)</p>
                  <p className="text-sm text-gray-500">Secondary source for verification</p>
                </div>
              </li>
              <li className="flex items-start gap-3">
                <div className="w-2 h-2 bg-purple-500 rounded-full mt-2"></div>
                <div>
                  <p className="font-medium text-gray-900">HOSE/HNX Official</p>
                  <p className="text-sm text-gray-500">Official exchange filings and announcements</p>
                </div>
              </li>
            </ul>
          </div>

          {/* Metrics Explanation */}
          <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Key Metrics</h3>
            <ul className="space-y-3">
              <li className="flex items-start gap-3">
                <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                <div>
                  <p className="font-medium text-gray-900">P/E Ratio</p>
                  <p className="text-sm text-gray-500">Price-to-Earnings ratio indicates valuation relative to earnings</p>
                </div>
              </li>
              <li className="flex items-start gap-3">
                <div className="w-2 h-2 bg-green-500 rounded-full mt-2"></div>
                <div>
                  <p className="font-medium text-gray-900">ROE</p>
                  <p className="text-sm text-gray-500">Return on Equity measures profitability relative to shareholder equity</p>
                </div>
              </li>
              <li className="flex items-start gap-3">
                <div className="w-2 h-2 bg-purple-500 rounded-full mt-2"></div>
                <div>
                  <p className="font-medium text-gray-900">Debt/Equity</p>
                  <p className="text-sm text-gray-500">Indicates financial leverage and risk level</p>
                </div>
              </li>
            </ul>
          </div>
        </div>
      </main>
    </div>
  );
};

export default FinancialReport;
