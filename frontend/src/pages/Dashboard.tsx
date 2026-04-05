/**
 * Main dashboard page
 */
import React, { useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AssetSelector } from '@/components/AssetSelector';
import { PriceChart } from '@/components/PriceChart';
import { PredictionCard } from '@/components/PredictionCard';
import { StatusBar } from '@/components/StatusBar';
import { useMarketStore } from '@/store/useMarketStore';
import { useAuthStore } from '@/store/useAuthStore';
import { TrendingUp, BarChart3, Activity, Shield, LogOut } from 'lucide-react';

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
  } = useMarketStore();
  const { role, username, logout } = useAuthStore();

  // Initial data fetch
  useEffect(() => {
    if (assetType === 'stock') {
      fetchStockData(selectedSymbol);
    } else {
      fetchCryptoData(selectedSymbol);
    }
  }, []);

  // Get predicted price from available predictions
  const getPredictedPrice = (): number | null => {
    const availablePredictions = Object.values(predictions);
    if (availablePredictions.length > 0) {
      return availablePredictions[0].predicted_close;
    }
    return null;
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">
                  Stock & Crypto Prediction Platform
                </h1>
                <p className="text-sm text-gray-500">
                  ML-powered price predictions for crypto and Vietnamese stocks
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              {/* Admin link - only visible to admins */}
              {role === 'admin' && (
                <Link
                  to="/admin"
                  className="flex items-center gap-2 px-4 py-2 bg-purple-50 text-purple-700 rounded-lg hover:bg-purple-100 transition-colors"
                >
                  <Shield className="w-4 h-4" />
                  Admin
                </Link>
              )}

              <div className="flex items-center gap-2 px-4 py-2 bg-blue-50 rounded-lg">
                <Activity className="w-5 h-5 text-blue-600" />
                <span className="text-sm font-medium text-blue-700">
                  {selectedSymbol}
                </span>
              </div>

              <div className="flex items-center gap-2 px-4 py-2 bg-gray-100 rounded-lg">
                <span className="text-sm text-gray-600">{username}</span>
              </div>

              <button
                onClick={handleLogout}
                className="flex items-center gap-2 px-4 py-2 text-gray-600 hover:text-red-600 transition-colors"
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
          {/* Sidebar - Asset Selector */}
          <div className="lg:col-span-1">
            <AssetSelector />
          </div>

          {/* Main content area */}
          <div className="lg:col-span-3 space-y-6">
            {/* Price Chart */}
            <PriceChart
              showSMA={true}
              showBollinger={false}
              predictedPrice={getPredictedPrice()}
            />

            {/* Predictions Section */}
            <div>
              <div className="flex items-center gap-2 mb-4">
                <BarChart3 className="w-5 h-5 text-blue-600" />
                <h2 className="text-lg font-bold text-gray-900">ML Predictions</h2>
                <span className="text-sm text-gray-500">
                  Next-day price direction predictions
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <PredictionCard
                  prediction={predictions['rf']}
                  modelName="rf"
                  isLoading={isLoading}
                />
                <PredictionCard
                  prediction={predictions['xgb']}
                  modelName="xgb"
                  isLoading={isLoading}
                />
                <PredictionCard
                  prediction={predictions['lstm']}
                  modelName="lstm"
                  isLoading={isLoading}
                />
              </div>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                <p className="text-sm text-gray-500">Selected Asset</p>
                <p className="text-lg font-bold text-gray-900">{selectedSymbol}</p>
                <p className="text-xs text-gray-400 capitalize">{assetType}</p>
              </div>
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                <p className="text-sm text-gray-500">Models Available</p>
                <p className="text-lg font-bold text-gray-900">
                  {Object.keys(predictions).length}/3
                </p>
                <p className="text-xs text-gray-400">RF, XGB, LSTM</p>
              </div>
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                <p className="text-sm text-gray-500">Prediction Horizon</p>
                <p className="text-lg font-bold text-gray-900">1 Day</p>
                <p className="text-xs text-gray-400">Next close price</p>
              </div>
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                <p className="text-sm text-gray-500">Data Source</p>
                <p className="text-lg font-bold text-gray-900">
                  {assetType === 'stock' ? 'vnstock' : 'Alpaca'}
                </p>
                <p className="text-xs text-gray-400">Real-time market data</p>
              </div>
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
