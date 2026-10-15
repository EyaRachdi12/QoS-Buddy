import { useEffect, useMemo, useState } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  ScatterChart,
  Scatter,
  ZAxis,
} from 'recharts';
import { AlertTriangle, ShieldCheck, Wallet, MapPin, Loader } from 'lucide-react';
import { boAPI } from '../services/api';

function MetricCard({ title, value, subtitle, icon: Icon, colorClass }) {
  return (
    <div className="bg-white rounded-2xl border border-gray-200 shadow-lg p-5">
      <div className="flex items-center justify-between mb-2">
        <p className="text-sm text-gray-500 font-medium">{title}</p>
        <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${colorClass}`}>
          <Icon className="w-5 h-5 text-white" />
        </div>
      </div>
      <p className="text-3xl font-bold text-gray-800">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </div>
  );
}

export default function BusinessOverview({ boFilter = null }) {
  const [overview, setOverview] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchOverview = async () => {
    try {
      const data = await boAPI.getOverview(24, 120, boFilter || null);
      setOverview(data);
    } catch (error) {
      console.error('Error loading BO overview:', error);
      const detail = error.response?.data?.detail;
      setOverview({
        error:
          typeof detail === 'string'
            ? detail
            : detail?.message || error.message || 'Request failed',
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    setIsLoading(true);
    fetchOverview();
    const interval = setInterval(fetchOverview, 30000);
    return () => clearInterval(interval);
  }, [boFilter]);

  const trendData = useMemo(() => (overview?.trends || []).slice(-120), [overview]);
  const zoneData = useMemo(() => overview?.zones || [], [overview]);

  if (isLoading) {
    return (
      <div className="bg-white rounded-2xl border border-gray-200 shadow-xl p-8 flex items-center justify-center">
        <Loader className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (!overview) return null;

  if (overview.error) {
    return (
      <div className="bg-amber-50 border border-amber-200 rounded-2xl p-6 text-amber-900 text-sm">
        BO overview: {overview.error}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricCard
          title="BO1 - Anomaly Rate"
          value={`${overview.bo1?.anomaly_rate_pct ?? 0}%`}
          subtitle={`${overview.bo1?.anomalies ?? 0} anomalies / ${overview.bo1?.records ?? 0} records`}
          icon={AlertTriangle}
          colorClass="bg-gradient-to-br from-red-500 to-red-700"
        />
        <MetricCard
          title="BO2 - SLA / MOS"
          value={`${overview.bo2?.avg_mos ?? 'N/A'}`}
          subtitle={`SLA risk avg: ${overview.bo2?.avg_sla_breach_risk ?? 'N/A'}`}
          icon={ShieldCheck}
          colorClass="bg-gradient-to-br from-blue-500 to-blue-700"
        />
        <MetricCard
          title="BO3 - CAPEX Score"
          value={`${overview.bo3?.avg_capex_score ?? 'N/A'}`}
          subtitle={`Urgent zones: ${overview.bo3?.urgent_count ?? 0}`}
          icon={Wallet}
          colorClass="bg-gradient-to-br from-purple-500 to-purple-700"
        />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="bg-white rounded-2xl border border-gray-200 shadow-xl p-5">
          <h3 className="text-lg font-bold text-gray-800 mb-4">BO Trends (24h)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis
                dataKey="timestamp"
                tick={{ fill: '#6b7280', fontSize: 11 }}
                tickFormatter={(value) => new Date(value).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              />
              <YAxis yAxisId="left" tick={{ fill: '#6b7280', fontSize: 11 }} />
              <YAxis yAxisId="right" orientation="right" tick={{ fill: '#6b7280', fontSize: 11 }} />
              <Tooltip />
              <Line yAxisId="left" type="monotone" dataKey="sla_breach_risk" stroke="#ef4444" dot={false} strokeWidth={2.5} name="SLA Risk" />
              <Line yAxisId="left" type="monotone" dataKey="MOS" stroke="#10b981" dot={false} strokeWidth={2.5} name="MOS" />
              <Line yAxisId="right" type="monotone" dataKey="capex_score" stroke="#8b5cf6" dot={false} strokeWidth={2.5} name="CAPEX Score" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-2xl border border-gray-200 shadow-xl p-5">
          <div className="flex items-center gap-2 mb-4">
            <MapPin className="w-5 h-5 text-blue-600" />
            <h3 className="text-lg font-bold text-gray-800">Zone Map (City-Level)</h3>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <ScatterChart margin={{ top: 10, right: 10, left: 10, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis type="number" dataKey="lon" domain={[-180, 180]} tick={{ fontSize: 10 }} name="Longitude" />
              <YAxis type="number" dataKey="lat" domain={[-70, 85]} tick={{ fontSize: 10 }} name="Latitude" />
              <ZAxis type="number" dataKey="critical_count" range={[50, 400]} name="Critical Count" />
              <Tooltip
                cursor={{ strokeDasharray: '3 3' }}
                formatter={(value, name) => [value, name]}
                labelFormatter={(_, payload) => payload?.[0]?.payload?.zone || 'Zone'}
              />
              <Scatter data={zoneData} fill="#2563eb" />
            </ScatterChart>
          </ResponsiveContainer>
          <p className="text-xs text-gray-500 mt-3">
            Point size is proportional to critical issues. Use this as a quick zone prioritization view for BO3.
          </p>
        </div>
      </div>
    </div>
  );
}

