import { Radio } from 'lucide-react';
import AgentShell from './AgentShell';

/** Focus: PRB / capacity — congestion-oriented recommendations. */
export default function CongestionAgent({ aggregates, overview, onRunDetect }) {
  const prbDl = aggregates?.avg_prb_dl;
  const prbUl = aggregates?.avg_prb_ul;
  const hot = prbDl != null && prbDl > 80;

  return (
    <AgentShell
      title="Congestion agent"
      subtitle="PRB utilization & busy-hour risk"
      icon={Radio}
      tint="amber"
    >
      <p>
        DL PRB avg:{' '}
        <strong className="text-white">{prbDl != null ? `${prbDl}%` : '—'}</strong> · UL:{' '}
        <strong className="text-white">{prbUl != null ? `${prbUl}%` : '—'}</strong>
      </p>
      {hot ? (
        <p className="text-amber-200">
          Elevated DL usage — consider CA, load balancing, or sector split.
        </p>
      ) : (
        <p className="text-slate-500">Utilization within typical range for this slice.</p>
      )}
      {overview?.bo3?.urgent_count != null && overview.bo3.urgent_count > 0 && (
        <p className="text-slate-400">CAPEX urgent hints: {overview.bo3.urgent_count} zone flags.</p>
      )}
      {onRunDetect && (
        <button
          type="button"
          onClick={onRunDetect}
          className="mt-2 text-[11px] px-3 py-1.5 rounded-lg bg-amber-500/20 border border-amber-500/40 text-amber-200 hover:bg-amber-500/30"
        >
          Cross-check with ML detection
        </button>
      )}
    </AgentShell>
  );
}
