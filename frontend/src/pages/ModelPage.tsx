/**Model management page for training and viewing models.*/
import { useState } from "react";
import { useGlobalStore } from "../store/useGlobalStore";
import { retrainModel } from "../api/predictions";

const MODELS = [
  {
    key: "rf",
    name: "Random Forest",
    description:
      "Ensemble of 200 decision trees. Fast training, good baseline accuracy.\n" +
      "Recommended for: MVP phase, daily retraining.\n" +
      "Regressor: Trains alongside classifier for price predictions.",
  },
  {
    key: "xgb",
    name: "XGBoost",
    description:
      "Gradient boosting with 200 estimators. Often better accuracy than RF.\n" +
      "Recommended for: Production use after A/B testing.\n" +
      "Regressor: Trains alongside classifier for price predictions.",
  },
  {
    key: "lstm",
    name: "LSTM (Deep Learning)",
    description:
      "PyTorch LSTM with 64 hidden units, 2 layers. Best for sequential patterns.\n" +
      "Recommended for: Long-term trend prediction.\n" +
      "GPU: Set DEVICE=cuda for GPU training (requires CUDA).\n" +
      "Regressor: Not yet available (direction classification only).",
  },
];

export default function ModelPage() {
  const [selectedSymbol, setSelectedSymbol] = useState("BTC/USD");
  const [retraining, setRetraining] = useState<string | null>(null);
  const addToast = useGlobalStore((s) => s.addToast);
  const role = useGlobalStore((s) => s.role);

  const handleRetrain = async (modelKey: string) => {
    if (role !== "admin") {
      addToast("error", "Permission denied", "Only admins can trigger retraining.");
      return;
    }

    setRetraining(modelKey);
    try {
      const result = (await retrainModel(selectedSymbol, modelKey)) as any;
      addToast("info", "Retraining queued", result.message || `Job ${result.job_id} started.`);
    } catch (err: any) {
      addToast("error", "Retraining failed", err.message || "Could not start retraining job.");
    } finally {
      setRetraining(null);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">ML Models</h1>

      <div className="mb-6">
        <label htmlFor="retrain-symbol" className="block text-sm font-medium text-gray-700 mb-1">
          Symbol for retraining:
        </label>
        <input
          id="retrain-symbol"
          type="text"
          value={selectedSymbol}
          onChange={(e) => setSelectedSymbol(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          aria-label="Symbol for model retraining"
        />
      </div>

      <div className="space-y-4">
        {MODELS.map((model) => (
          <div
            key={model.key}
            className="bg-white rounded-lg shadow p-6 border border-gray-200"
          >
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">{model.name}</h2>
              <span className="text-xs font-mono bg-gray-100 px-2 py-1 rounded text-gray-600">
                {model.key}
              </span>
            </div>

            <pre className="mt-3 text-sm text-gray-600 whitespace-pre-wrap font-sans bg-gray-50 p-3 rounded">
              {model.description}
            </pre>

            {role === "admin" && (
              <button
                onClick={() => handleRetrain(model.key)}
                disabled={retraining === model.key}
                className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                aria-label={`Retrain ${model.name} model for ${selectedSymbol}`}
              >
                {retraining === model.key ? "Retraining..." : "Retrain"}
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
