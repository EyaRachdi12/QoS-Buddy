import { useMemo } from 'react';
import { useDashboard } from '../../context/DashboardContext';

function scoreToColor(score) {
  if (score == null) return 'bg-slate-800';
  if (score >= 80) return 'bg-red-500/80';
  if (score >= 60) return 'bg-orange-500/70';
  if (score >= 40) return 'bg-amber-500/60';
  if (score >= 20) return 'bg-emerald-500/50';
  return 'bg-cyan-500/40';
}

function scoreToText(score) {
  if (score == null) return 'N/A';
  if (score >= 80) return 'URGENT';
  if (score >= 60) return 'HIGH';
  if (score >= 40) return 'MEDIUM';
  if (score >= 20) return 'LOW';
  return 'MINIMAL';
}

export default function CapexHeatmapPanel() {
  const { overview } = useDashboard();

  const zones = useMemo(() => {
    if (!overview?.zones) return [];
    return [...overview.zones]
      .sort((a, b) => (b.avg_capex_score ?? 0) - (a.avg_capex_score ?? 0))
      .slice(0, 30);
  }, [overview]);

  if (!zones.length) {
    return (
      <div className="rounded-2xl border border-white/10 bg-white/5 p-8 text-center text-slate-500">
        No CAPEX zone data available.
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-slate-900/80 to-slate-950/80 p-5">
      <h4 className="text-sm font-semibold text-slate-200 mb-1">CAPEX Investment Heatmap</h4>
      <p className="text-xs text-slate-500 mb-4">Top 30 zones ranked by investment priority score</p>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2">
        {zones.map((z) => (
          <div
            key={z.zone}
            className={`rounded-xl p-3 ${scoreToColor(z.avg_capex_score)} transition-all hover:scale-105 cursor-default`}
            title={`${z.zone}: CAPEX score ${z.avg_capex_score ?? 'N/A'}`}
          >
            <div className="text-xs font-semibold text-white truncate">{z.zone}</div>
            <div className="text-lg font-bold text-white">
              {z.avg_capex_score != null ? z.avg_capex_score.toFixed(0) : '—'}
            </div>
            <div className="text-[10px] text-white/70">{scoreToText(z.avg_capex_score)}</div>
            <div className="text-[10px] text-white/50 mt-1">
              {z.critical_count} critical · {z.records} records
            </div>
          </div>
        ))}
      </div>

      <div className="flex items-center gap-2 mt-4 text-[10px] text-slate-400">
        <span>Priority:</span>
        <span className="inline-block w-3 h-3 rounded bg-cyan-500/40" /> Minimal
        <span className="inline-block w-3 h-3 rounded bg-emerald-500/50" /> Low
        <span className="inline-block w-3 h-3 rounded bg-amber-500/60" /> Medium
        <span className="inline-block w-3 h-3 rounded bg-orange-500/70" /> High
        <span className="inline-block w-3 h-3 rounded bg-red-500/80" /> Urgent
      </div>
    </div>
  );
}
