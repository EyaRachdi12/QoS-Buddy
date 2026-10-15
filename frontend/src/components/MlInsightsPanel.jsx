import { useState } from 'react';
import { Radar, FlaskConical, RefreshCw, Database } from 'lucide-react';
import { mlAPI } from '../services/api';

export default function MlInsightsPanel({ boFilter = null }) {
  const [loadingD, setLoadingD] = useState(false);
  const [loadingP, setLoadingP] = useState(false);
  const [detectResult, setDetectResult] = useState(null);
  const [predictResult, setPredictResult] = useState(null);
  const [modelsInfo, setModelsInfo] = useState(null);
  const [refreshMsg, setRefreshMsg] = useState(null);

  const runDetect = async () => {
    setLoadingD(true);
    setDetectResult(null);
    try {
      const data = await mlAPI.detect({
        time_window_hours: 24,
        bo_filter: boFilter || undefined,
        include_rule_alerts: true,
        max_rows: 5000,
      });
      setDetectResult(data);
    } catch (e) {
      setDetectResult({ error: e.message || 'Detection failed' });
    } finally {
      setLoadingD(false);
    }
  };

  const runPredict = async () => {
    setLoadingP(true);
    setPredictResult(null);
    try {
      const data = await mlAPI.predict({
        target: 'latency_ms',
        time_window_hours: 48,
        bo_filter: boFilter || undefined,
        retrain: false,
      });
      setPredictResult(data);
    } catch (e) {
      setPredictResult({ error: e.message || 'Prediction failed' });
    } finally {
      setLoadingP(false);
    }
  };

  const loadModels = async () => {
    try {
      const data = await mlAPI.modelsStatus();
      setModelsInfo(data);
    } catch (e) {
      setModelsInfo({ error: e.message });
    }
  };

  const refreshData = async () => {
    setRefreshMsg(null);
    try {
      const data = await mlAPI.refreshData();
      setRefreshMsg(`Reloaded ${data.rows} rows from ${data.source_path}`);
    } catch (e) {
      setRefreshMsg(e.message || 'Refresh failed');
    }
  };

  const mergedPreview = detectResult?.merged_alerts?.slice(0, 5) || [];
  const predPreview = predictResult?.predictions?.slice(-5) || [];

  return (
    <div className="bg-white rounded-2xl border border-gray-200 shadow-xl p-6 space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
            <Radar className="w-6 h-6 text-blue-600" />
            ML detection & prediction
          </h2>
          <p className="text-sm text-gray-500">
            Runs on the unified dataset (Isolation Forest + rule alerts; RF for latency).
            {boFilter ? ` Filter: ${boFilter}` : ''}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={runDetect}
            disabled={loadingD}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-red-600 text-white font-medium hover:bg-red-700 disabled:opacity-60"
          >
            <Radar className="w-4 h-4" />
            {loadingD ? 'Detecting…' : 'Detection'}
          </button>
          <button
            type="button"
            onClick={runPredict}
            disabled={loadingP}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 text-white font-medium hover:bg-indigo-700 disabled:opacity-60"
          >
            <FlaskConical className="w-4 h-4" />
            {loadingP ? 'Predicting…' : 'Prediction'}
          </button>
          <button
            type="button"
            onClick={loadModels}
            className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50"
          >
            Model status
          </button>
          <button
            type="button"
            onClick={refreshData}
            className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh data cache
          </button>
        </div>
      </div>

      {refreshMsg && (
        <p className="text-sm flex items-center gap-2 text-gray-600">
          <Database className="w-4 h-4" />
          {refreshMsg}
        </p>
      )}

      {detectResult && (
        <div className="rounded-xl bg-red-50 border border-red-100 p-4 text-sm">
          {detectResult.error && (
            <p className="text-red-700">{detectResult.error}</p>
          )}
          {detectResult.isolation_forest && (
            <p className="text-gray-800 mb-2">
              Isolation Forest: {detectResult.isolation_forest.n_outliers} outliers /{' '}
              {detectResult.isolation_forest.n_samples} samples (
              {(detectResult.isolation_forest.outlier_ratio * 100).toFixed(2)}%)
            </p>
          )}
          {mergedPreview.length > 0 && (
            <ul className="list-disc list-inside space-y-1 text-gray-700">
              {mergedPreview.map((a, i) => (
                <li key={i}>
                  [{a.severity}] {a.issue_type} — cell {a.cell_id}
                </li>
              ))}
            </ul>
          )}
          {detectResult.success && !mergedPreview.length && !detectResult.error && (
            <p className="text-gray-600">No merged alerts in this window.</p>
          )}
        </div>
      )}

      {predictResult && (
        <div className="rounded-xl bg-indigo-50 border border-indigo-100 p-4 text-sm">
          {predictResult.error && (
            <p className="text-red-700">{predictResult.error}</p>
          )}
          {predictResult.metrics && (
            <p className="text-gray-800 mb-2">
              Validation MAE: {predictResult.metrics.mae?.toFixed?.(3) ?? predictResult.metrics.mae},{' '}
              R²: {predictResult.metrics.r2?.toFixed?.(3) ?? predictResult.metrics.r2}
            </p>
          )}
          {predPreview.length > 0 && (
            <ul className="list-disc list-inside space-y-1 text-gray-700 font-mono text-xs">
              {predPreview.map((p, i) => (
                <li key={i}>
                  {p.cell_id}: pred {p.predicted?.toFixed?.(1) ?? p.predicted} ms
                  {p.actual != null ? ` (actual ${p.actual?.toFixed?.(1)})` : ''}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {modelsInfo && !modelsInfo.error && (
        <pre className="text-xs bg-gray-900 text-green-200 p-3 rounded-lg overflow-x-auto">
          {JSON.stringify(modelsInfo, null, 2)}
        </pre>
      )}
      {modelsInfo?.error && (
        <p className="text-sm text-red-600">{modelsInfo.error}</p>
      )}
    </div>
  );
}
