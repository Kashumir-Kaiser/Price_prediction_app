/**
 * Prediction card component showing model predictions
 */
import React from 'react';
import { TrendingUp, TrendingDown, Minus, Brain, BarChart3, Cpu } from 'lucide-react';
import { Prediction } from '@/types/market';

interface PredictionCardProps {
  prediction?: Prediction;
  modelName: string;
  isLoading?: boolean;
}

const getModelIcon = (model: string) => {
  switch (model) {
    case 'rf':
      return <BarChart3 className="w-5 h-5" />;
    case 'xgb':
      return <Cpu className="w-5 h-5" />;
    case 'lstm':
      return <Brain className="w-5 h-5" />;
    default:
      return <BarChart3 className="w-5 h-5" />;
  }
};

const getModelDisplayName = (model: string) => {
  switch (model) {
    case 'rf':
      return 'Random Forest';
    case 'xgb':
      return 'XGBoost';
    case 'lstm':
      return 'LSTM Neural Net';
    default:
      return model.toUpperCase();
  }
};

const getDirectionIcon = (direction: string) => {
  switch (direction) {
    case 'up':
      return <TrendingUp className="w-6 h-6" />;
    case 'down':
      return <TrendingDown className="w-6 h-6" />;
    default:
      return <Minus className="w-6 h-6" />;
  }
};

const getDirectionColor = (direction: string) => {
  switch (direction) {
    case 'up':
      return {
        bg: 'bg-green-50',
        border: 'border-green-500',
        text: 'text-green-700',
        badge: 'bg-green-100 text-green-800',
        progress: 'bg-green-500',
      };
    case 'down':
      return {
        bg: 'bg-red-50',
        border: 'border-red-500',
        text: 'text-red-700',
        badge: 'bg-red-100 text-red-800',
        progress: 'bg-red-500',
      };
    default:
      return {
        bg: 'bg-gray-50',
        border: 'border-gray-500',
        text: 'text-gray-700',
        badge: 'bg-gray-100 text-gray-800',
        progress: 'bg-gray-500',
      };
  }
};

export const PredictionCard: React.FC<PredictionCardProps> = ({
  prediction,
  modelName,
  isLoading = false,
}) => {
  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6 animate-pulse">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 bg-gray-200 rounded-lg"></div>
          <div className="h-5 bg-gray-200 rounded w-32"></div>
        </div>
        <div className="h-8 bg-gray-200 rounded w-24 mb-3"></div>
        <div className="h-4 bg-gray-200 rounded w-full mb-2"></div>
        <div className="h-2 bg-gray-200 rounded w-full"></div>
      </div>
    );
  }

  if (!prediction) {
    return (
      <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center text-gray-400">
            {getModelIcon(modelName)}
          </div>
          <h3 className="font-semibold text-gray-700">{getModelDisplayName(modelName)}</h3>
        </div>
        <p className="text-gray-500 text-sm">No prediction available</p>
        <p className="text-gray-400 text-xs mt-2">Model may need training</p>
      </div>
    );
  }

  const colors = getDirectionColor(prediction.direction);
  const confidencePercent = Math.round(prediction.confidence * 100);

  return (
    <div className={`bg-white rounded-lg shadow-md border-2 ${colors.border} p-6`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 ${colors.bg} rounded-lg flex items-center justify-center ${colors.text}`}>
            {getModelIcon(modelName)}
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">{getModelDisplayName(modelName)}</h3>
            <p className="text-xs text-gray-500">Horizon: {prediction.horizon}</p>
          </div>
        </div>
        <div className={`px-3 py-1 rounded-full text-sm font-medium ${colors.badge}`}>
          {prediction.direction.toUpperCase()}
        </div>
      </div>

      {/* Direction Icon */}
      <div className="flex items-center gap-4 mb-4">
        <div className={`w-16 h-16 ${colors.bg} rounded-xl flex items-center justify-center ${colors.text}`}>
          {getDirectionIcon(prediction.direction)}
        </div>
        <div>
          <p className="text-sm text-gray-500">Predicted Close</p>
          <p className={`text-2xl font-bold ${colors.text}`}>
            ${prediction.predicted_close.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </p>
        </div>
      </div>

      {/* Confidence Bar */}
      <div className="mb-4">
        <div className="flex justify-between text-sm mb-1">
          <span className="text-gray-600">Confidence</span>
          <span className="font-medium text-gray-900">{confidencePercent}%</span>
        </div>
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={`h-full ${colors.progress} transition-all duration-500`}
            style={{ width: `${confidencePercent}%` }}
          ></div>
        </div>
      </div>

      {/* Features Used */}
      <div className="border-t border-gray-100 pt-3">
        <p className="text-xs text-gray-500 mb-2">Key Features:</p>
        <div className="flex flex-wrap gap-1">
          {prediction.features_used.slice(0, 5).map((feature: any, idx: number) => (
            <span
              key={idx}
              className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded"
            >
              {feature}
            </span>
          ))}
        </div>
      </div>

      {/* Timestamp */}
      <p className="text-xs text-gray-400 mt-3">
        Generated: {new Date(prediction.generated_at).toLocaleString()}
      </p>
    </div>
  );
};

export default PredictionCard;
