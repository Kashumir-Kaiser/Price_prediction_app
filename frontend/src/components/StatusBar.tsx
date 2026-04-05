/**
 * Status bar component showing data freshness and system status
 */
import React from 'react';
import { RefreshCw, Clock, Database, Wifi, AlertCircle } from 'lucide-react';
import { useMarketStore } from '@/store/useMarketStore';

interface StatusBarProps {
  onRefresh?: () => void;
}

export const StatusBar: React.FC<StatusBarProps> = ({ onRefresh }) => {
  const { lastUpdated, isLoading, error } = useMarketStore();

  const getTimeAgo = (date: Date | null): string => {
    if (!date) return 'Never';
    
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return `${seconds}s ago`;
  };

  return (
    <div className="bg-white border-t border-gray-200 px-4 py-3">
      <div className="flex flex-wrap items-center justify-between gap-4">
        {/* Status indicators */}
        <div className="flex items-center gap-6">
          {/* Data freshness */}
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-gray-500" />
            <span className="text-sm text-gray-600">
              Last updated:{' '}
              <span className="font-medium text-gray-900">
                {getTimeAgo(lastUpdated)}
              </span>
            </span>
          </div>

          {/* Database status */}
          <div className="flex items-center gap-2">
            <Database className="w-4 h-4 text-green-500" />
            <span className="text-sm text-gray-600">Database Connected</span>
          </div>

          {/* API status */}
          <div className="flex items-center gap-2">
            <Wifi className="w-4 h-4 text-green-500" />
            <span className="text-sm text-gray-600">API Online</span>
          </div>
        </div>

        {/* Right side */}
        <div className="flex items-center gap-4">
          {/* Error indicator */}
          {error && (
            <div className="flex items-center gap-2 text-red-600">
              <AlertCircle className="w-4 h-4" />
              <span className="text-sm">{error}</span>
            </div>
          )}

          {/* Refresh button */}
          <button
            onClick={onRefresh}
            disabled={isLoading}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            <span className="text-sm font-medium">
              {isLoading ? 'Refreshing...' : 'Refresh'}
            </span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default StatusBar;
