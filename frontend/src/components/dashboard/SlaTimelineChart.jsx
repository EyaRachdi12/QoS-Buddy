import { useMemo } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  CartesianGrid,
  Area,
  ComposedChart,
} from 'recharts';
import { useDashboard } from '../../context/DashboardContext';

const SLA_BREACH_THRESHOLD = 0.7;

export default function SlaTimelineChart() {
  const { overview } = useDashboard();

  const data = useMemo(() => {
    if (!overview?.trends) return [];
    return overview.trends
      .filter((t) => t.sla_breach_risk != null)
      .map((t, i) => ({
        idx: i,
        time: t.timestamp?.slice(11, 16) || `T${i}`,
        sla_risk: parseFloat(t.sla_breach_risk) || 0,
        mos: parseFloat(t.MOS) || 0,
      }));
  }, [overview]);

  if (!data.length) {
    return (
      <div className="rounded-2xl border border-white/10 bg-white/5 p-8 text-center text-slate-500">
        No SLA risk data available for this time window.
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-slate-900/80 to-slate-950/80 p-5">
      <h4 className="text-sm font-semibold text-slate-200 mb-1">SLA Breach Risk Timeline</h4>
      <p className="text-xs text-slate-500 mb-4">
        Risk over time — red zone indicates breach threshold ({SLA_BREACH_THRESHOLD})
      </p>
      <ResponsiveContainer width="100%" height={260}>
        <ComposedChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis dataKey="time" tick={{ fill: '#64748b', fontSize: 10 }} />
          <YAxis
            yAxisId="risk"
            domain={[0, 1]}
            tick={{ fill: '#64748b', fontSize: 10 }}
            label={{ value: 'SLA Risk', angle: -90, position: 'insideLeft', fill: '#94a3b8', fontSize: 10 }}
          />
          <YAxis
            yAxisId="mos"
            orientation="right"
            domain={[1, 5]}
            tick={{ fill: '#64748b', fontSize: 10 }}
            label={{ value: 'MOS', angle: 90, position: 'insideRight', fill: '#94a3b8', fontSize: 10 }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#0f172a',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: 12,
              fontSize: 12,
            }}
          />
          <ReferenceLine
            yAxisId="risk"
            y={SLA_BREACH_THRESHOLD}
            stroke="#ef4444"
            strokeDasharray="6 3"
            label={{ value: 'Breach Threshold', fill: '#ef4444', fontSize: 10, position: 'top' }}
          />
          <Area
            yAxisId="risk"
            type="monotone"
            dataKey="sla_risk"
            stroke="#f59e0b"
            fill="#f59e0b"
            fillOpacity={0.15}
            strokeWidth={2}
            name="SLA Risk"
          />
          <Line
            yAxisId="mos"
            type="monotone"
            dataKey="mos"
            stroke="#22d3ee"
            strokeWidth={2}
            dot={false}
            name="MOS"
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
