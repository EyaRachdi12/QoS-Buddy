import { useMemo } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from 'recharts';
import { useDashboard } from '../../context/DashboardContext';

export default function AlertTrendChart() {
  const { diagnosticAlerts } = useDashboard();

  const trendData = useMemo(() => {
    if (!diagnosticAlerts || !diagnosticAlerts.length) return [];

    // Group alerts by hour buckets
    const buckets = {};
    diagnosticAlerts.forEach((alert) => {
      const ts = alert.timestamp || '';
      const hourKey = ts.slice(0, 13) || 'unknown'; // YYYY-MM-DDTHH
      if (!buckets[hourKey]) {
        buckets[hourKey] = { critical: 0, high: 0, medium: 0 };
      }
      const sev = (alert.severity || '').toUpperCase();
      if (sev === 'CRITICAL') buckets[hourKey].critical++;
      else if (sev === 'HIGH') buckets[hourKey].high++;
      else buckets[hourKey].medium++;
    });

    return Object.entries(buckets)
      .sort(([a], [b]) => a.localeCompare(b))
      .slice(-24)
      .map(([key, counts]) => ({
        hour: key.slice(11, 16) || key.slice(-5),
        ...counts,
      }));
  }, [diagnosticAlerts]);

  if (!trendData.length) {
    return (
      <div className="rounded-2xl border border-white/10 bg-white/5 p-8 text-center text-slate-500">
        No alert history to display trends.
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-slate-900/80 to-slate-950/80 p-5">
      <h4 className="text-sm font-semibold text-slate-200 mb-1">Alert Trend (by Hour)</h4>
      <p className="text-xs text-slate-500 mb-4">Alert count distribution over the last analysis window</p>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={trendData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis dataKey="hour" tick={{ fill: '#64748b', fontSize: 10 }} />
          <YAxis tick={{ fill: '#64748b', fontSize: 10 }} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#0f172a',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: 12,
              fontSize: 12,
            }}
          />
          <Legend wrapperStyle={{ fontSize: 11 }} />
          <Bar dataKey="critical" stackId="a" fill="#ef4444" name="Critical" radius={[0, 0, 0, 0]} />
          <Bar dataKey="high" stackId="a" fill="#f59e0b" name="High" radius={[0, 0, 0, 0]} />
          <Bar dataKey="medium" stackId="a" fill="#3b82f6" name="Medium" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
