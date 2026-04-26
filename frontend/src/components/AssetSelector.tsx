/**
 * Asset selector component with tabs for Crypto, Stablecoins, and VN Stocks
 */
import React, { useState } from 'react';
import { Search, TrendingUp, DollarSign, Building2 } from 'lucide-react';
import { useMarketStore } from '@/store/useMarketStore';

interface AssetSelectorProps {
  onSelect?: (symbol: string, assetType: 'crypto' | 'stable' | 'stock') => void;
}

const CRYPTO_ASSETS = [
  { symbol: 'BTC/USD', name: 'Bitcoin', icon: '₿' },
  { symbol: 'ETH/USD', name: 'Ethereum', icon: 'Ξ' },
  { symbol: 'SOL/USD', name: 'Solana', icon: '◎' },
];

const STABLE_ASSETS = [
  { symbol: 'USDT/USD', name: 'Tether', icon: '₮' },
  { symbol: 'USDC/USD', name: 'USD Coin', icon: '₵' },
];

const DEFAULT_STOCKS = [
  { symbol: 'VNM', name: 'Vinamilk' },
  { symbol: 'VIC', name: 'Vingroup' },
  { symbol: 'FPT', name: 'FPT Corp' },
  { symbol: 'SSI', name: 'SSI Securities' },
  { symbol: 'HPG', name: 'Hoa Phat Group' },
  { symbol: 'MWG', name: 'Mobile World' },
  { symbol: 'VCB', name: 'Vietcombank' },
  { symbol: 'BID', name: 'BIDV' },
];

type TabType = 'crypto' | 'stable' | 'stocks';

export const AssetSelector: React.FC<AssetSelectorProps> = ({ onSelect }) => {
  const [activeTab, setActiveTab] = useState<TabType>('crypto');
  const [searchQuery, setSearchQuery] = useState('');
  const { selectedSymbol, setSymbol } = useMarketStore();

  const handleSelect = (symbol: string, assetType: 'crypto' | 'stable' | 'stock') => {
    setSymbol(symbol, assetType);
    onSelect?.(symbol, assetType);
  };

  const filteredStocks = DEFAULT_STOCKS.filter(
    (stock) =>
      stock.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
      stock.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const isSelected = (symbol: string) => selectedSymbol === symbol;

  return (
    <div className="bg-white rounded-lg shadow-md border border-gray-200 overflow-hidden">
      {/* Tabs */}
      <div className="flex border-b border-gray-200">
        <button
          onClick={() => setActiveTab('crypto')}
          className={`flex-1 flex items-center justify-center gap-2 py-3 px-4 text-sm font-medium transition-colors ${
            activeTab === 'crypto'
              ? 'bg-blue-50 text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-600 hover:bg-gray-50'
          }`}
        >
          <TrendingUp className="w-4 h-4" />
          Crypto
        </button>
        <button
          onClick={() => setActiveTab('stable')}
          className={`flex-1 flex items-center justify-center gap-2 py-3 px-4 text-sm font-medium transition-colors ${
            activeTab === 'stable'
              ? 'bg-green-50 text-green-600 border-b-2 border-green-600'
              : 'text-gray-600 hover:bg-gray-50'
          }`}
        >
          <DollarSign className="w-4 h-4" />
          Stable
        </button>
        <button
          onClick={() => setActiveTab('stocks')}
          className={`flex-1 flex items-center justify-center gap-2 py-3 px-4 text-sm font-medium transition-colors ${
            activeTab === 'stocks'
              ? 'bg-purple-50 text-purple-600 border-b-2 border-purple-600'
              : 'text-gray-600 hover:bg-gray-50'
          }`}
        >
          <Building2 className="w-4 h-4" />
          VN Stocks
        </button>
      </div>

      {/* Content */}
      <div className="p-4">
        {activeTab === 'crypto' && (
          <div className="space-y-2">
            {CRYPTO_ASSETS.map((asset) => (
              <button
                key={asset.symbol}
                data-testid={`asset-${asset.symbol.toLowerCase().replace('/', '-')}`}
                onClick={() => handleSelect(asset.symbol, 'crypto')}
                className={`w-full flex items-center gap-3 p-3 rounded-lg transition-all ${
                  isSelected(asset.symbol)
                    ? 'bg-blue-100 border-2 border-blue-500'
                    : 'bg-gray-50 border-2 border-transparent hover:bg-gray-100'
                }`}
              >
                <span className="text-2xl">{asset.icon}</span>
                <div className="text-left">
                  <div className="font-semibold text-gray-900">{asset.symbol}</div>
                  <div className="text-sm text-gray-500">{asset.name}</div>
                </div>
                {isSelected(asset.symbol) && (
                  <span className="ml-auto text-blue-600 text-sm font-medium">Selected</span>
                )}
              </button>
            ))}
          </div>
        )}

        {activeTab === 'stable' && (
          <div className="space-y-2">
            {STABLE_ASSETS.map((asset) => (
              <button
                key={asset.symbol}
                onClick={() => handleSelect(asset.symbol, 'stable')}
                className={`w-full flex items-center gap-3 p-3 rounded-lg transition-all ${
                  isSelected(asset.symbol)
                    ? 'bg-green-100 border-2 border-green-500'
                    : 'bg-gray-50 border-2 border-transparent hover:bg-gray-100'
                }`}
              >
                <span className="text-2xl">{asset.icon}</span>
                <div className="text-left">
                  <div className="font-semibold text-gray-900">{asset.symbol}</div>
                  <div className="text-sm text-gray-500">{asset.name}</div>
                </div>
                {isSelected(asset.symbol) && (
                  <span className="ml-auto text-green-600 text-sm font-medium">Selected</span>
                )}
              </button>
            ))}
          </div>
        )}

        {activeTab === 'stocks' && (
          <div className="space-y-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search stocks..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {filteredStocks.map((stock) => (
                <button
                  key={stock.symbol}
                  onClick={() => handleSelect(stock.symbol, 'stock')}
                  className={`w-full flex items-center gap-3 p-3 rounded-lg transition-all ${
                    isSelected(stock.symbol)
                      ? 'bg-purple-100 border-2 border-purple-500'
                      : 'bg-gray-50 border-2 border-transparent hover:bg-gray-100'
                  }`}
                >
                  <div className="w-10 h-10 rounded-full bg-purple-100 flex items-center justify-center text-purple-600 font-bold text-sm">
                    {stock.symbol.slice(0, 2)}
                  </div>
                  <div className="text-left">
                    <div className="font-semibold text-gray-900">{stock.symbol}</div>
                    <div className="text-sm text-gray-500">{stock.name}</div>
                  </div>
                  {isSelected(stock.symbol) && (
                    <span className="ml-auto text-purple-600 text-sm font-medium">Selected</span>
                  )}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AssetSelector;
