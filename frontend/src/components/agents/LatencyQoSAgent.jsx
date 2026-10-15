import { Timer } from 'lucide-react';
import AgentShell from './AgentShell';

/** BO2 — SLA / MOS comme BO2_QoSBuddy_SLA_* .ipynb */
export default function LatencyQoSAgent({ aggregates, overview, onRunPredict }) {
  const lat = aggregates?.avg_latency_ms;
  const mos = aggregates?.avg_mos ?? overview?.bo2?.avg_mos;
  const sla = aggregates?.avg_sla_breach_risk ?? overview?.bo2?.avg_sla_breach_risk;

  const latBad = lat != null && lat > 100;
  const slaBad = sla != null && Number(sla) > 0.5;

  return (
    <AgentShell
      title="Latency & QoS agent"
      subtitle="SLA & MOS — risque B2B & qualité perçue (TelecomTS / G.107)"
      icon={Timer}
      tint="cyan"
    >
      <p>
        Avg latency: <strong className="text-white">{lat != null ? `${lat} ms` : '—'}</strong>
      </p>
      <p>
        MOS: <strong className="text-white">{mos != null ? Number(mos).toFixed(2) : '—'}</strong> · SLA
        risk:{' '}
        <strong className="text-white">{sla != null ? Number(sla).toFixed(3) : '—'}</strong>
      </p>
      {latBad && <p className="text-cyan-200">Latency above comfort zone — inspect transport & scheduling.</p>}
      {slaBad && !latBad && <p className="text-amber-200">SLA breach risk elevated — review bearer QoS & capacity.</p>}
      {onRunPredict && (
        <button
          type="button"
          onClick={onRunPredict}
          className="mt-2 text-[11px] px-3 py-1.5 rounded-lg bg-cyan-500/20 border border-cyan-500/40 text-cyan-200 hover:bg-cyan-500/30"
        >
          Refresh latency prediction
        </button>
      )}
    </AgentShell>
  );
}
