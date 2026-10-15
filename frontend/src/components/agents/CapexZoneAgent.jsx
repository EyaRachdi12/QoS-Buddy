import { MapPin } from 'lucide-react';
import AgentShell from './AgentShell';

/** BO3 — BO3_CAPEX_Zone_UPDATED.ipynb (scoring & priorités zone) */
export default function CapexZoneAgent({ overview, zones }) {
  const avgC = overview?.bo3?.avg_capex_score;
  const urg = overview?.bo3?.urgent_count;
  const nZ = zones?.length ?? 0;

  return (
    <AgentShell
      title="CAPEX zone agent"
      subtitle="Notebook Zones — score 0–100 & priorités géographiques"
      icon={MapPin}
      tint="violet"
    >
      <p>
        Avg CAPEX score: <strong className="text-white">{avgC != null ? avgC : '—'}</strong>
      </p>
      <p>
        Urgent hints: <strong className="text-white">{urg != null ? urg : '—'}</strong> · Map zones:{' '}
        <strong className="text-white">{nZ}</strong>
      </p>
      <p className="text-slate-500 text-[11px]">
        Prioritize red / orange markers — pivot budget to worst MOS & highest critical counts.
      </p>
    </AgentShell>
  );
}
