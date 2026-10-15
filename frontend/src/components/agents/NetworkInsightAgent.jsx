import { Sparkles } from 'lucide-react';
import AgentShell from './AgentShell';

/** Generic insight from trend direction (latency vs MOS). */
export default function NetworkInsightAgent({ overview }) {
  const trends = overview?.trends || [];
  const tail = trends.slice(-12);
  let insight = 'Stable pattern in last samples — continue monitoring.';
  if (tail.length >= 2) {
    const a = tail[0];
    const b = tail[tail.length - 1];
    const la = Number(a.latency_ms);
    const lb = Number(b.latency_ms);
    const ma = Number(a.MOS);
    const mb = Number(b.MOS);
    if (!Number.isNaN(la) && !Number.isNaN(lb) && lb > la * 1.08) {
      insight = 'Latency trending up — check backhaul and RAN load on hot cells.';
    } else if (!Number.isNaN(ma) && !Number.isNaN(mb) && mb < ma - 0.15) {
      insight = 'MOS softening — voice/data quality drills recommended.';
    }
  }

  return (
    <AgentShell title="Network insight" subtitle="Heuristic read on recent trends" icon={Sparkles} tint="violet">
      <p className="text-slate-200 leading-relaxed">{insight}</p>
    </AgentShell>
  );
}
