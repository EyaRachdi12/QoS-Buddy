import { motion } from 'framer-motion';
import { Radar, FlaskConical, RefreshCw, Database } from 'lucide-react';
import { useDashboard } from '../../context/DashboardContext';
import { menuItemForBo } from '../../constants/boMenu';
import { useState } from 'react';

export default function ActionsPanel() {
  const {
    selectedBoId,
    detectLoading,
    predictLoading,
    runMlOrchestrated,
    detectResult,
    predictResult,
    mlPromptAction,
    mlBanner,
    refreshDataCache,
    cacheMessage,
  } = useDashboard();
  const [prompt, setPrompt] = useState('');
  const [promptError, setPromptError] = useState(null);

  const boLabel = menuItemForBo(selectedBoId).label;
  const actionRunning = detectLoading || predictLoading;
  const selectedActionLabel =
    mlPromptAction === 'predict'
      ? 'Prediction'
      : mlPromptAction === 'detect'
        ? 'Detection'
        : null;

  const merged = detectResult?.merged_alerts || [];
  const preds = predictResult?.predictions?.slice(-8) || [];

  const ACTION_HINT_REGEX =
    /\b(detect|detection|detecter|détecter|predict|prediction|predire|prédire|prevoir|prévoir|prevision|prévision|anomaly|anomalies|anomalie|incident|incidents|alert|alerte|alertes|latency|latence|sla|forecast)\b/i;

  const validatePrompt = () => {
    const clean = prompt.trim();
    if (clean.length < 8) {
      return 'Prompt non reconnu, merci de préciser.';
    }
    if (!ACTION_HINT_REGEX.test(clean)) {
      return 'Prompt non reconnu, merci de préciser.';
    }
    return null;
  };

  const handleAnalyzePrompt = () => {
    const err = validatePrompt();
    setPromptError(err);
    if (err) return;
    runMlOrchestrated(prompt);
  };

  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.06] backdrop-blur-xl p-5 shadow-xl space-y-4">
      <div>
        <h3 className="font-semibold text-slate-100 flex items-center gap-2">
          <Radar className="w-5 h-5 text-violet-400" />
          AI actions
        </h3>
        <p className="text-xs text-slate-500 mt-1">
          Scoped to <span className="text-cyan-400 font-medium">{boLabel}</span> — prompt routing to{' '}
          <code className="text-slate-400">/api/ml/orchestrate</code>
        </p>
      </div>

      <div className="space-y-2">
        <textarea
          value={prompt}
          onChange={(e) => {
            setPrompt(e.target.value);
            if (promptError) setPromptError(null);
          }}
          placeholder="Ex: detect anomalies in this BO / predict latency for next hours"
          className="w-full min-h-[90px] rounded-xl border border-white/15 bg-black/20 px-3 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-violet-500/40"
        />
        {promptError && <p className="text-sm text-rose-300">{promptError}</p>}
        <motion.button
          type="button"
          whileTap={{ scale: 0.98 }}
          onClick={handleAnalyzePrompt}
          disabled={actionRunning}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 text-white text-sm font-medium disabled:opacity-50 shadow-lg shadow-violet-900/30"
        >
          <FlaskConical className={`w-4 h-4 ${actionRunning ? 'animate-pulse' : ''}`} />
          {actionRunning ? 'Running request…' : 'Lancer'}
        </motion.button>
      </div>

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={refreshDataCache}
          className="inline-flex items-center gap-2 px-3 py-2.5 rounded-xl border border-white/15 text-slate-200 text-sm hover:bg-white/5"
        >
          <RefreshCw className="w-4 h-4" />
          Reload CSV cache
        </button>
      </div>

      {selectedActionLabel && (
        <p className="text-xs text-slate-400">
          Routed action: <span className="text-cyan-300 font-medium">{selectedActionLabel}</span>
        </p>
      )}

      {cacheMessage && (
        <p className="text-xs flex items-center gap-2 text-slate-400">
          <Database className="w-3.5 h-3.5" />
          {cacheMessage}
        </p>
      )}

      {mlBanner && (
        <motion.div
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          className={`text-sm rounded-xl px-3 py-2 border ${
            mlBanner.type === 'success'
              ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-200'
              : mlBanner.type === 'error'
                ? 'bg-rose-500/15 border-rose-500/40 text-rose-200'
                : 'bg-amber-500/15 border-amber-500/40 text-amber-200'
          }`}
        >
          {mlBanner.text}
        </motion.div>
      )}

      {(detectResult?.error || (detectResult && !detectResult.success && detectResult.message)) && (
        <p className="text-sm text-rose-300">{detectResult.error || detectResult.message}</p>
      )}

      {detectResult?.success && (
        <div className="rounded-xl border border-white/10 bg-black/20 p-3">
          <p className="text-xs text-slate-400 mb-2">
            {detectResult.isolation_forest
              ? `Isolation Forest: ${detectResult.isolation_forest.n_outliers} / ${detectResult.isolation_forest.n_samples} outliers`
              : 'Rule-based alerts'}
          </p>
          <div className="max-h-40 overflow-y-auto space-y-1">
            {merged.slice(0, 8).map((a, i) => (
              <div key={i} className="text-xs text-slate-300 font-mono truncate">
                [{a.severity}] {a.issue_type} · {a.cell_id}
              </div>
            ))}
            {!merged.length && (
              <span className="text-xs text-slate-500">No merged alerts.</span>
            )}
          </div>
        </div>
      )}

      {(predictResult?.error || (predictResult && !predictResult.success && predictResult.message)) && (
        <p className="text-sm text-rose-300">{predictResult.error || predictResult.message}</p>
      )}

      {predictResult?.success && (
        <div className="rounded-xl border border-white/10 bg-black/20 p-3">
          <p className="text-xs text-slate-400 mb-2">
            {predictResult.metrics
              ? `MAE ${predictResult.metrics.mae?.toFixed?.(3) ?? predictResult.metrics.mae} · R² ${
                  predictResult.metrics.r2?.toFixed?.(3) ?? predictResult.metrics.r2
                }`
              : 'Latency model'}
          </p>
          <div className="max-h-40 overflow-y-auto space-y-1">
            {preds.map((p, i) => (
              <div key={i} className="text-xs text-slate-300 font-mono">
                {p.cell_id}: pred {p.predicted?.toFixed?.(1) ?? p.predicted} ms
                {p.actual != null ? ` (act ${p.actual?.toFixed?.(1)})` : ''}
              </div>
            ))}
            {!preds.length && (
              <span className="text-xs text-slate-500">No prediction rows.</span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
