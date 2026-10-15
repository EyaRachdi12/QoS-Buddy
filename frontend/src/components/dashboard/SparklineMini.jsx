/**
 * Tiny sparkline for KPI / alert context (Recharts, no axes).
 */
import { AreaChart, Area, ResponsiveContainer, YAxis } from 'recharts';

export default function SparklineMini({ data = [], dataKey = 'v', color = '#22d3ee', height = 36 }) {
  const chartData = Array.isArray(data) ? data.map((v, i) => ({ i, [dataKey]: v })) : [];
  const gid = `spark-${String(color).replace(/[^a-zA-Z0-9]/g, '')}`;
  if (chartData.length < 2) {
    return <div style={{ height }} className="opacity-30 w-full rounded bg-white/5" />;
  }
  return (
    <div style={{ height }} className="w-full -mx-1">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ top: 2, right: 0, left: 0, bottom: 0 }}>
          <YAxis hide domain={['auto', 'auto']} />
          <defs>
            <linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.35} />
              <stop offset="100%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <Area
            type="monotone"
            dataKey={dataKey}
            stroke={color}
            strokeWidth={1.5}
            fill={`url(#${gid})`}
            isAnimationActive
            animationDuration={600}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
