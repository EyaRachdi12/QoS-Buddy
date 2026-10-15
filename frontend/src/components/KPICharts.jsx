import { useState, useEffect } from 'react';
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
import { Activity, TrendingUp, Radio } from 'lucide-react';
import { kpiAPI } from '../services/api';

export default function KPICharts() {
  const [kpiData, setKpiData] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchKPIs();
    const interval = setInterval(fetchKPIs, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchKPIs = async () => {
    try {
      const response = await kpiAPI.getRealtimeKPIs(50);
      setKpiData(response.kpis || []);
    } catch (error) {
      console.error('Error fetching KPIs:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const COLORS = {
    RSRP: '#2563eb',
    SINR: '#10b981',
    PRB: '#f59e0b',
    Throughput: '#8b5cf6',
    Latency: '#ef4444',
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64 bg-white rounded-2xl shadow-xl border border-gray-200">
        <div className="text-center">
          <div className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-3">
            <Activity className="w-6 h-6 text-white animate-pulse" />
          </div>
          <p className="text-gray-600 font-medium">Loading KPIs...</p>
        </div>
      </div>
    );
  }

  const recentData = kpiData.slice(-30);

  return (
    <div className="space-y-6">
      {/* Signal Quality Trends */}
      <div className="bg-white p-6 rounded-2xl shadow-xl border border-gray-200">
        <div className="flex items-center gap-3 mb-5">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-700 rounded-xl flex items-center justify-center shadow-md">
            <Radio className="w-5 h-5 text-white" />
          </div>
          <h3 className="text-lg font-bold text-gray-800">
            Signal Quality (RSRP & SINR)
          </h3>
        </div>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={recentData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="timestamp"
              stroke="#6b7280"
              tick={{ fill: '#6b7280', fontSize: 12 }}
              tickFormatter={(value) => new Date(value).toLocaleTimeString()}
            />
            <YAxis stroke="#6b7280" tick={{ fill: '#6b7280', fontSize: 12 }} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#ffffff',
                border: '1px solid #e5e7eb',
                borderRadius: '12px',
                boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
              }}
              labelStyle={{ color: '#1f2937', fontWeight: 'bold' }}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="RSRP"
              stroke={COLORS.RSRP}
              strokeWidth={3}
              dot={false}
              name="RSRP (dBm)"
            />
            <Line
              type="monotone"
              dataKey="SINR"
              stroke={COLORS.SINR}
              strokeWidth={3}
              dot={false}
              name="SINR (dB)"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Resource Utilization & Throughput */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-2xl shadow-xl border border-gray-200">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-10 h-10 bg-gradient-to-br from-orange-500 to-orange-700 rounded-xl flex items-center justify-center shadow-md">
              <Activity className="w-5 h-5 text-white" />
            </div>
            <h3 className="text-lg font-bold text-gray-800">
              PRB Utilization (%)
            </h3>
          </div>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={recentData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis
                dataKey="timestamp"
                stroke="#6b7280"
                tick={{ fill: '#6b7280', fontSize: 10 }}
                tickFormatter={(value) =>
                  new Date(value).toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit',
                  })
                }
              />
              <YAxis
                stroke="#6b7280"
                tick={{ fill: '#6b7280', fontSize: 12 }}
                domain={[0, 100]}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#ffffff',
                  border: '1px solid #e5e7eb',
                  borderRadius: '12px',
                  boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                }}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="PRB_DL"
                stroke={COLORS.PRB}
                strokeWidth={3}
                dot={false}
                name="PRB DL"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white p-6 rounded-2xl shadow-xl border border-gray-200">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-purple-700 rounded-xl flex items-center justify-center shadow-md">
              <TrendingUp className="w-5 h-5 text-white" />
            </div>
            <h3 className="text-lg font-bold text-gray-800">
              Throughput (Mbps)
            </h3>
          </div>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={recentData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis
                dataKey="timestamp"
                stroke="#6b7280"
                tick={{ fill: '#6b7280', fontSize: 10 }}
                tickFormatter={(value) =>
                  new Date(value).toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit',
                  })
                }
              />
              <YAxis stroke="#6b7280" tick={{ fill: '#6b7280', fontSize: 12 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#ffffff',
                  border: '1px solid #e5e7eb',
                  borderRadius: '12px',
                  boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                }}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="throughput_DL"
                stroke={COLORS.Throughput}
                strokeWidth={3}
                dot={false}
                name="DL Throughput"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
