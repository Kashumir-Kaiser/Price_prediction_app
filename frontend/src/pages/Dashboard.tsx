import React, { useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AssetSelector } from '@/components/AssetSelector';
import { PriceChart } from '@/components/PriceChart';
import { PredictionCard } from '@/components/PredictionCard';
import { StatusBar } from '@/components/StatusBar';
import Watchlist from '@/components/Watchlist';
import { useMarketStore } from '@/store/useMarketStore';
import { useGlobalStore } from '@/store/useGlobalStore';
import { useThemeStore } from '@/store/useThemeStore';
import { TrendingUp, BarChart3, Activity, Shield, LogOut, Moon, Sun } from 'lucide-react';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const {
    selectedSymbol,
    assetType,
    predictions,
    refreshAll,
    isLoading,
    fetchCryptoData,
    fetchStockData,
    setSymbol,
  } = useMarketStore();
  const { user, role, logout } = useGlobalStore();
  const username = user?.username ?? '';
  const { watchlist, setWatchlist } = useGlobalStore();
  const { theme, toggleTheme } = useThemeStore();

  useEffect(() => {
    if (assetType === 'stock') {
      fetchStockData(selectedSymbol);
    } else {
      fetchCryptoData(selectedSymbol);
    }
  }, []);

  useEffect(() => {
    if (watchlist.length === 0) {
      setWatchlist(['BTC/USD', 'ETH/USD', 'SOL/USD', 'VNM', 'FPT']);
    }
  }, [watchlist.length, setWatchlist]);

  const getPredictedPrice = (): number | null => {
    const availablePredictions = Object.values(predictions);
    if (availablePredictions.length > 0) return availablePredictions[0].predicted_close;
    return null;
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 transition-colors">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 transition-colors">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                  Stock & Crypto Prediction Platform
                </h1>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  ML-powered price predictions for crypto and Vietnamese stocks
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <button
                onClick={toggleTheme}
                className="p-2 rounded-lg bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
                aria-label="Toggle dark mode"
              >
                {theme === 'light' ? <Moon size={20} /> : <Sun size={20} />}
              </button>

              {role === 'admin' && (
                <Link
                  to="/admin"
                  className="flex items-center gap-2 px-4 py-2 bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded-lg hover:bg-purple-100 dark:hover:bg-purple-800 transition-colors"
                >
                  <Shield className="w-4 h-4" />
                  Admin
                </Link>
              )}

              <div className="flex items-center gap-2 px-4 py-2 bg-blue-50 dark:bg-blue-900/30 rounded-lg">
                <Activity className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                <span className="text-sm font-medium text-blue-700 dark:text-blue-300">
                  {selectedSymbol}
                </span>
              </div>

              <div className="flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg">
                <span className="text-sm text-gray-600 dark:text-gray-300">{username}</span>
              </div>

              <button
                onClick={handleLogout}
                className="flex items-center gap-2 px-4 py-2 text-gray-600 dark:text-gray-300 hover:text-red-600 dark:hover:text-red-400 transition-colors"
              >
                <LogOut className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar */}
          <div className="lg:col-span-1">
            <div className="space-y-4">
              <AssetSelector />
              <Watchlist
                selectedSymbol={selectedSymbol}
                onSelectSymbol={(symbol) =>
                  setSymbol(symbol, symbol.includes('/') ? 'crypto' : 'stock')
                }
              />
            </div>
          </div>

          {/* Main content area */}
          <div className="lg:col-span-3 space-y-6">
            <PriceChart
              showSMA={true}
              showBollinger={false}
              predictedPrice={getPredictedPrice()}
            />

            {/* Predictions Section */}
            <div>
              <div className="flex items-center gap-2 mb-4">
                <BarChart3 className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                <h2 className="text-lg font-bold text-gray-900 dark:text-white">ML Predictions</h2>
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  Next-day price direction predictions
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <PredictionCard prediction={predictions['rf']} modelName="rf" isLoading={isLoading} />
                <PredictionCard prediction={predictions['xgb']} modelName="xgb" isLoading={isLoading} />
                <PredictionCard prediction={predictions['lstm']} modelName="lstm" isLoading={isLoading} />
              </div>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: 'Selected Asset', value: selectedSymbol, sub: assetType },
                { label: 'Models Available', value: `${Object.keys(predictions).length}/3`, sub: 'RF, XGB, LSTM' },
                { label: 'Prediction Horizon', value: '1 Day', sub: 'Next close price' },
                { label: 'Data Source', value: assetType === 'stock' ? 'vnstock' : 'Alpaca', sub: 'Real-time market data' },
              ].map((stat) => (
                <div key={stat.label} className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4 transition-colors">
                  <p className="text-sm text-gray-500 dark:text-gray-400">{stat.label}</p>
                  <p className="text-lg font-bold text-gray-900 dark:text-white">{stat.value}</p>
                  <p className="text-xs text-gray-400 dark:text-gray-500 capitalize">{stat.sub}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>

      {/* Status Bar */}
      <StatusBar onRefresh={refreshAll} />
    </div>
  );
};

export default Dashboard;