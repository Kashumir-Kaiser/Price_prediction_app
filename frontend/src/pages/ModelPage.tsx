import { useState } from 'react';
import { useGlobalStore } from '../store/useGlobalStore';
import { useThemeStore } from '../store/useThemeStore';
import { retrainModel } from '../api/predictions';
import { Moon, Sun } from 'lucide-react';

const MODELS = [
  {
    key: 'rf',
    name: 'Random Forest',
    description: 'Ensemble of 200 decision trees. Fast training, good baseline accuracy.\nRecommended for: MVP phase, daily retraining.\nRegressor: Trains alongside classifier for price predictions.',
  },
  {
    key: 'xgb',
    name: 'XGBoost',
    description: 'Gradient boosting with 200 estimators. Often better accuracy than RF.\nRecommended for: Production use after A/B testing.\nRegressor: Trains alongside classifier for price predictions.',
  },
  {
    key: 'lstm',
    name: 'LSTM (Deep Learning)',
    description: 'PyTorch LSTM with 64 hidden units, 2 layers. Best for sequential patterns.\nRecommended for: Long-term trend prediction.\nGPU: Set DEVICE=cuda for GPU training (requires CUDA).\nRegressor: Not yet available (direction classification only).',
  },
];

export default function ModelPage() {
  const [selectedSymbol, setSelectedSymbol] = useState('BTC/USD');
  const [retraining, setRetraining] = useState<string | null>(null);
  const addToast = useGlobalStore((s) => s.addToast);
  const role = useGlobalStore((s) => s.role);
  const { theme, toggleTheme } = useThemeStore();

  const handleRetrain = async (modelKey: string) => {
    if (role !== 'admin') {
      addToast('error', 'Permission denied', 'Only admins can trigger retraining.');
      return;
    }

    setRetraining(modelKey);
    try {
      const result = (await retrainModel(selectedSymbol, modelKey)) as any;
      addToast('info', 'Retraining queued', result.message || `Job ${result.job_id} started.`);
    } catch (err: any) {
      addToast('error', 'Retraining failed', err.message || 'Could not start retraining job.');
    } finally {
      setRetraining(null);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 p-6 max-w-4xl mx-auto transition-colors">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">ML Models</h1>
        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
          aria-label="Toggle dark mode"
        >
          {theme === 'light' ? <Moon size={20} /> : <Sun size={20} />}
        </button>
      </div>

      <div className="mb-6">
        <label htmlFor="retrain-symbol" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Symbol for retraining:
        </label>
        <input
          id="retrain-symbol"
          type="text"
          value={selectedSymbol}
          onChange={(e) => setSelectedSymbol(e.target.value)}
          className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
          aria-label="Symbol for model retraining"
        />
      </div>

      <div className="space-y-4">
        {MODELS.map((model) => (
          <div key={model.key} className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 border border-gray-200 dark:border-gray-700 transition-colors">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">{model.name}</h2>
              <span className="text-xs font-mono bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded text-gray-600 dark:text-gray-400">
                {model.key}
              </span>
            </div>

            <pre className="mt-3 text-sm text-gray-600 dark:text-gray-300 whitespace-pre-wrap font-sans bg-gray-50 dark:bg-gray-900 p-3 rounded">
              {model.description}
            </pre>

            {role === 'admin' && (
              <button
                onClick={() => handleRetrain(model.key)}
                disabled={retraining === model.key}
                className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                aria-label={`Retrain ${model.name} model for ${selectedSymbol}`}
              >
                {retraining === model.key ? 'Retraining...' : 'Retrain'}
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}