import { useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { TrendingUp, PieChart as PieIcon, BarChart3 } from 'lucide-react';
import { useDashboard } from '../../context/DashboardContext';
import { chartProfileForBo } from '../../constants/boKpiConfig';
import { menuItemForBo } from '../../constants/boMenu';

const PIE_COLORS = ['#22c55e', '#eab308', '#ef4444'];

const LINE_STROKE = {
  latency_ms: '#22d3ee',
  packet_loss_proxy: '#f472b6',
  MOS: '#34d399',
  throughput_DL: '#a78bfa',
  capex_score: '#c4b5fd',
};

export default function ChartsSection() {
  const { overview, overviewLoading, overviewError, selectedBoId } = useDashboard();
  const profile = chartProfileForBo(selectedBoId);
  const boKey = selectedBoId ?? 'all';
  const scopeTitle = menuItemForBo(selectedBoId).label;

  const trendData = useMemo(() => {
    const t = (overview?.trends || []).slice(-100).map((row) => ({
      ...row,
      tshort: row.timestamp
        ? new Date(row.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        : '',
      packet_loss_proxy:
        row.sla_breach_risk != null && !Number.isNaN(+row.sla_breach_risk)
          ? Number(row.sla_breach_risk) * 100
          : null,
    }));
    return t;
  }, [overview]);

  const barRows = useMemo(() => {
    const zones = overview?.zones || [];
    const sorted = [...zones].sort((a, b) => {
      if (profile.bar === 'capex') {
        return (
          Number(b.avg_capex_score ?? 0) - Number(a.avg_capex_score ?? 0)
        );
      }
      return (b.critical_count ?? 0) - (a.critical_count ?? 0);
    });
    const slice = sorted.slice(0, 14);
    if (profile.bar === 'capex') {
      return slice.map((z) => ({
        name: z.zone?.slice(0, 14) || 'Z',
        metric: z.avg_capex_score != null ? Number(z.avg_capex_score) : 0,
      }));
    }
    if (profile.bar === 'critical') {
      return slice.map((z) => ({
        name: z.zone?.slice(0, 14) || 'Z',
        metric: z.critical_count ?? 0,
      }));
    }
    return slice.map((z) => ({
      name: z.zone?.slice(0, 14) || 'Z',
      metric: z.avg_mos != null ? Number(z.avg_mos) : 0,
      critical: z.critical_count ?? 0,
    }));
  }, [overview, profile.bar]);

  const pieQoS = useMemo(() => {
    const zones = overview?.zones || [];
    let good = 0;
    let medium = 0;
    let poor = 0;
    zones.forEach((z) => {
      const m = z.avg_mos;
      if (m == null) return;
      if (m >= 4) good += 1;
      else if (m >= 3) medium += 1;
      else poor += 1;
    });
    if (good + medium + poor === 0) {
      return [
        { name: 'Good', value: 1 },
        { name: 'Medium', value: 0 },
        { name: 'Poor', value: 0 },
      ];
    }
    return [
      { name: 'Good (MOS≥4)', value: good },
      { name: 'Medium', value: medium },
      { name: 'Poor', value: poor },
    ];
  }, [overview]);

  const lineTitle =
    selectedBoId === 'BO1'
      ? `Latence & stress — ${scopeTitle}`
      : selectedBoId === 'BO2'
        ? `Latence, MOS & stress SLA — ${scopeTitle}`
        : selectedBoId === 'BO3'
          ? `Score CAPEX & latence — ${scopeTitle}`
          : 'Latence, proxy perte, MOS & débit — vue unifiée';

  const barTitle =
    profile.bar === 'capex'
      ? 'Score CAPEX par zone'
      : profile.bar === 'critical'
        ? 'Incidents critiques par zone'
        : 'QoS par zone (MOS)';

  const lineKeys = profile.line || [];

  if (overviewLoading) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {[1, 2, 3].map((k) => (
          <div key={k} className="h-72 rounded-2xl bg-white/5 animate-pulse border border-white/5" />
        ))}
      </div>
    );
  }

  if (overviewError && !overview) {
    return null;
  }

  if (!trendData.length && !barRows.length) {
    return (
      <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-8 text-center text-slate-400 text-base">
        Pas de série temporelle pour cette sélection (fenêtre temps ou filtre métier).
      </div>
    );
  }

  const chartWrap =
    'rounded-2xl border border-white/10 bg-white/[0.06] backdrop-blur-xl p-5 shadow-xl';

  const barDataKey = 'metric';
  const barDomain = profile.bar === 'mos' ? [0, 5] : undefined;

  return (
    <motion.div
      key={boKey}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="grid grid-cols-1 xl:grid-cols-3 gap-4"
    >
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className={chartWrap}
      >
        <div className="flex items-center gap-2 mb-4 text-slate-200">
          <TrendingUp className="w-6 h-6 text-cyan-400 shrink-0" />
          <h3 className="font-semibold text-base">{lineTitle}</h3>
        </div>
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={trendData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
            <XAxis dataKey="tshort" stroke="#94a3b8" tick={{ fontSize: 12 }} />
            <YAxis yAxisId="left" stroke="#94a3b8" tick={{ fontSize: 12 }} />
            <YAxis yAxisId="right" orientation="right" stroke="#94a3b8" tick={{ fontSize: 12 }} />
            <Tooltip
              contentStyle={{
                background: '#0f172a',
                border: '1px solid #334155',
                borderRadius: '12px',
                fontSize: '13px',
              }}
            />
            <Legend wrapperStyle={{ fontSize: '13px' }} />
            {lineKeys.includes('latency_ms') && (
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="latency_ms"
                stroke={LINE_STROKE.latency_ms}
                strokeWidth={2}
                dot={false}
                name="Latence (ms)"
              />
            )}
            {lineKeys.includes('packet_loss_proxy') && (
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="packet_loss_proxy"
                stroke={LINE_STROKE.packet_loss_proxy}
                strokeWidth={2}
                dot={false}
                name="Proxy perte %"
              />
            )}
            {lineKeys.includes('MOS') && (
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="MOS"
                stroke={LINE_STROKE.MOS}
                strokeWidth={2}
                dot={false}
                name="MOS"
              />
            )}
            {lineKeys.includes('capex_score') && (
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="capex_score"
                stroke={LINE_STROKE.capex_score}
                strokeWidth={2}
                dot={false}
                name="Score CAPEX"
              />
            )}
            {lineKeys.includes('throughput_DL') && trendData.some((r) => r.throughput_DL != null) && (
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="throughput_DL"
                stroke={LINE_STROKE.throughput_DL}
                strokeWidth={1.5}
                dot={false}
                name="Débit DL"
              />
            )}
          </LineChart>
        </ResponsiveContainer>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.08 }}
        className={chartWrap}
      >
        <div className="flex items-center gap-2 mb-4 text-slate-200">
          <BarChart3 className="w-6 h-6 text-amber-400 shrink-0" />
          <h3 className="font-semibold text-base">{barTitle}</h3>
        </div>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={barRows} layout="vertical" margin={{ left: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
            <XAxis type="number" stroke="#94a3b8" domain={barDomain} tick={{ fontSize: 12 }} />
            <YAxis type="category" dataKey="name" stroke="#94a3b8" width={80} tick={{ fontSize: 12 }} />
            <Tooltip
              contentStyle={{
                background: '#0f172a',
                border: '1px solid #334155',
                borderRadius: '12px',
                fontSize: '13px',
              }}
            />
            <Bar
              dataKey={barDataKey}
              fill={profile.bar === 'capex' ? '#818cf8' : profile.bar === 'critical' ? '#f87171' : '#a78bfa'}
              radius={[0, 8, 8, 0]}
              name={profile.bar === 'capex' ? 'CAPEX' : profile.bar === 'critical' ? 'Critiques' : 'MOS'}
            />
          </BarChart>
        </ResponsiveContainer>
      </motion.div>

      {profile.pie && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.16 }}
          className={chartWrap}
        >
          <div className="flex items-center gap-2 mb-4 text-slate-200">
            <PieIcon className="w-6 h-6 text-pink-400 shrink-0" />
            <h3 className="font-semibold text-base">Répartition QoS des zones (MOS)</h3>
          </div>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={pieQoS}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                innerRadius={56}
                outerRadius={92}
                paddingAngle={3}
                animationDuration={600}
              >
                {pieQoS.map((_, i) => (
                  <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} stroke="#0f172a89" />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  background: '#0f172a',
                  border: '1px solid #334155',
                  borderRadius: '12px',
                  fontSize: '13px',
                }}
              />
              <Legend wrapperStyle={{ fontSize: '13px' }} />
            </PieChart>
          </ResponsiveContainer>
        </motion.div>
      )}
    </motion.div>
  );
}
