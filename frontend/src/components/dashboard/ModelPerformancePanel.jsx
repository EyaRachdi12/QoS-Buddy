import { useState, useEffect } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
} from 'recharts';
import { Activity, TrendingUp, AlertTriangle } from 'lucide-react';
import { mlAPI, getApiError } from '../../services/api';
import { useDashboard } from '../../context/DashboardContext';

function MetricCard({ label, value, unit, color }) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-3 text-center">
      <div className="text-[10px] uppercase tracking-wider text-slate-500">{label}</div>
      <div className={`text-xl font-bold ${color || 'text-white'}`}>
        {value != null ? (typeof value === 'number' ? value.toFixed(4) : value) : '—'}
      </div>
      {unit && <div className="text-[10px] text-slate-500">{unit}</div>}
    </div>
  );
}

export default function ModelPerformancePanel() {
  const { predictResult } = useDashboard();
  const [modelsStatus, setModelsStatus] = useState(null);
  const [driftReport, setDriftReport] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    Promise.allSettled([mlAPI.modelsStatus(), mlAPI.driftCheck(24)])
      .then(([ms, dr]) => {
        if (ms.status === 'fulfilled') setModelsStatus(ms.value);
        if (dr.status === 'fulfilled') setDriftReport(dr.value);
      })
      .finally(() => setLoading(false));
  }, [predictResult]);

  const metrics = predictResult?.metrics || modelsStatus?.runtime?.metrics || {};
  const trainingStats = modelsStatus?.runtime?.training_stats;

  // Feature importance data for radar chart
  const featureData = trainingStats?.feature_importances
    ? Object.entries(trainingStats.feature_importances)
        .sort(([, a], [, b]) => b - a)
        .slice(0, 8)
        .map(([name, value]) => ({
          feature: name.length > 10 ? name.slice(0, 10) + '..' : name,
          importance: parseFloat((value * 100).toFixed(1)),
        }))
    : [];

  // CV scores bar chart
  const cvData = trainingStats?.cv_scores
    ? trainingStats.cv_scores.map((s, i) => ({
        fold: `Fold ${i + 1}`,
        r2: parseFloat(s.toFixed(4)),
      }))
    : [];

  const driftStatus = driftReport?.overall_status;

  return (
    <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-slate-900/80 to-slate-950/80 p-5 space-y-5">
      <div className="flex items-center gap-2">
        <Activity className="w-4 h-4 text-cyan-400" />
        <h4 className="text-sm font-semibold text-slate-200">Model Performance</h4>
        {driftStatus && (
          <span
            className={`ml-auto text-[10px] px-2 py-0.5 rounded-full font-medium ${
              driftStatus === 'ok'
                ? 'bg-emerald-500/20 text-emerald-400'
                : driftStatus === 'warning'
                  ? 'bg-amber-500/20 text-amber-400'
                  : 'bg-red-500/20 text-red-400'
            }`}
          >
            Drift: {driftStatus.toUpperCase()}
          </span>
        )}
      </div>

      {/* Metric cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        <MetricCard label="R² Score" value={metrics.r2} color="text-cyan-400" />
        <MetricCard label="MAE" value={metrics.mae} color="text-amber-400" />
        <MetricCard label="RMSE" value={metrics.rmse} color="text-orange-400" />
        <MetricCard
          label="CV R² Mean"
          value={metrics.cv_r2_mean}
          unit={metrics.cv_r2_std != null ? `± ${metrics.cv_r2_std.toFixed(4)}` : undefined}
          color="text-emerald-400"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Feature importance radar */}
        {featureData.length > 0 && (
          <div>
            <p className="text-xs text-slate-400 mb-2">Feature Importance (%)</p>
            <ResponsiveContainer width="100%" height={220}>
              <RadarChart data={featureData} cx="50%" cy="50%" outerRadius="75%">
                <PolarGrid stroke="#334155" />
                <PolarAngleAxis dataKey="feature" tick={{ fill: '#94a3b8', fontSize: 9 }} />
                <PolarRadiusAxis tick={{ fill: '#64748b', fontSize: 8 }} />
                <Radar
                  dataKey="importance"
                  stroke="#22d3ee"
                  fill="#22d3ee"
                  fillOpacity={0.25}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Cross-validation scores */}
        {cvData.length > 0 && (
          <div>
            <p className="text-xs text-slate-400 mb-2">Cross-Validation R² Scores</p>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={cvData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="fold" tick={{ fill: '#64748b', fontSize: 10 }} />
                <YAxis domain={[0, 1]} tick={{ fill: '#64748b', fontSize: 10 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: 12,
                    fontSize: 12,
                  }}
                />
                <Bar dataKey="r2" fill="#8b5cf6" radius={[4, 4, 0, 0]} name="R² Score" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Drift details */}
      {driftReport?.drifted_features?.length > 0 && (
        <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-3">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            <span className="text-xs font-medium text-amber-400">Drifted Features Detected</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {driftReport.drifted_features.map((f) => {
              const info = driftReport.features?.[f];
              return (
                <span
                  key={f}
                  className={`text-[10px] px-2 py-0.5 rounded-full ${
                    info?.status === 'critical'
                      ? 'bg-red-500/20 text-red-400'
                      : 'bg-amber-500/20 text-amber-400'
                  }`}
                >
                  {f} (PSI: {info?.psi ?? '?'})
                </span>
              );
            })}
          </div>
        </div>
      )}

      {!Object.keys(metrics).length && !loading && (
        <p className="text-xs text-slate-500 text-center py-4">
          Run a prediction to see model performance metrics, feature importance, and drift analysis.
        </p>
      )}
    </div>
  );
}
