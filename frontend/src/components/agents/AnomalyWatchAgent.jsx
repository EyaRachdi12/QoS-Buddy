import { Scan } from 'lucide-react';
import AgentShell from './AgentShell';

/** BO1 — même intention que BO1_Anomaly_Detection_UPDATED.ipynb */
export default function AnomalyWatchAgent({ aggregates, overview, detectResult }) {
  const ac = aggregates?.anomaly_count;
  const rate = overview?.bo1?.anomaly_rate_pct;
  const outliers = detectResult?.isolation_forest?.n_outliers;

  return (
    <AgentShell
      title="Anomaly watch"
      subtitle="Notebook Anomaly — charge eNB & signaux avant impact client"
      icon={Scan}
      tint="rose"
    >
      <p>
        Flagged rows (dataset):{' '}
        <strong className="text-white">{ac != null ? ac : '—'}</strong>
      </p>
      {rate != null && (
        <p>
          Window anomaly rate: <strong className="text-white">{rate}%</strong>
        </p>
      )}
      {outliers != null && (
        <p className="text-slate-400">
          Last ML run: <span className="text-white">{outliers}</span> IF outliers
        </p>
      )}
      <p className="text-slate-500 text-[11px]">
        Correlate spikes with PRB, handover, and latency in the charts below.
      </p>
    </AgentShell>
  );
}
