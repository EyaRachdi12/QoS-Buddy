import { useState, useEffect } from 'react';
import { AlertTriangle, CheckCircle, XCircle, Clock, RefreshCw, Loader } from 'lucide-react';
import { diagnosticAPI } from '../services/api';

export default function DiagnosticPanel() {
  const [alerts, setAlerts] = useState([]);
  const [summary, setSummary] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchAlerts = async () => {
    setIsLoading(true);
    try {
      const [alertsData, summaryData] = await Promise.all([
        diagnosticAPI.getLatestAlerts(20),
        diagnosticAPI.getSummary(),
      ]);

      setAlerts(alertsData.alerts || []);
      setSummary(summaryData);
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Error fetching alerts:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();

    if (autoRefresh) {
      const interval = setInterval(fetchAlerts, 30000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const getSeverityColor = (severity) => {
    const colors = {
      CRITICAL: 'bg-red-600 text-white border-red-700',
      HIGH: 'bg-orange-500 text-white border-orange-600',
      MEDIUM: 'bg-yellow-500 text-white border-yellow-600',
      LOW: 'bg-blue-500 text-white border-blue-600',
      NONE: 'bg-green-500 text-white border-green-600',
    };
    return colors[severity] || 'bg-gray-500 text-white border-gray-600';
  };

  const getSeverityIcon = (severity) => {
    if (severity === 'CRITICAL' || severity === 'HIGH') {
      return <XCircle className="w-5 h-5" />;
    }
    if (severity === 'MEDIUM') {
      return <AlertTriangle className="w-5 h-5" />;
    }
    return <CheckCircle className="w-5 h-5" />;
  };

  return (
    <div className="flex flex-col h-full bg-slate-900/70 rounded-2xl shadow-2xl border border-white/10 backdrop-blur-xl">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 p-5 rounded-t-2xl">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center">
              <AlertTriangle className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">
                Agent 2: Diagnostic Monitor
              </h2>
              <p className="text-blue-100 text-sm">Autonomous Network Analysis</p>
            </div>
          </div>
          <button
            onClick={fetchAlerts}
            disabled={isLoading}
            className="p-2.5 bg-white/20 hover:bg-white/30 rounded-xl transition backdrop-blur-sm"
            title="Refresh"
          >
            <RefreshCw
              className={`w-5 h-5 text-white ${isLoading ? 'animate-spin' : ''}`}
            />
          </button>
        </div>
      </div>

      {/* Summary Stats */}
      {summary && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-5 bg-gradient-to-br from-slate-900/80 to-slate-800/80 border-b border-white/10">
          <div className="bg-white/5 p-4 rounded-xl shadow-md border border-white/10">
            <p className="text-slate-500 text-xs font-medium mb-1">Total Alerts</p>
            <p className="text-3xl font-bold text-white">{summary.total_alerts}</p>
          </div>
          <div className="bg-gradient-to-br from-red-50 to-red-100 p-4 rounded-xl shadow-md border border-red-200">
            <p className="text-red-600 text-xs font-medium mb-1">Critical</p>
            <p className="text-3xl font-bold text-red-600">{summary.critical}</p>
          </div>
          <div className="bg-gradient-to-br from-orange-50 to-orange-100 p-4 rounded-xl shadow-md border border-orange-200">
            <p className="text-orange-600 text-xs font-medium mb-1">High Priority</p>
            <p className="text-3xl font-bold text-orange-600">{summary.high}</p>
          </div>
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-xl shadow-md border border-blue-200">
            <p className="text-blue-600 text-xs font-medium mb-1">Cells Monitored</p>
            <p className="text-3xl font-bold text-blue-600">
              {summary.cells_monitored}
            </p>
          </div>
        </div>
      )}

      {/* Controls */}
      <div className="p-4 border-b border-white/10 flex items-center justify-between bg-slate-900/60">
        <div className="flex items-center gap-2 text-slate-400 text-sm">
          <Clock className="w-4 h-4" />
          <span className="font-medium">
            {lastUpdate
              ? `Updated ${lastUpdate.toLocaleTimeString()}`
              : 'Not updated'}
          </span>
        </div>
        <label className="flex items-center gap-2 text-slate-400 text-sm cursor-pointer font-medium">
          <input
            type="checkbox"
            checked={autoRefresh}
            onChange={(e) => setAutoRefresh(e.target.checked)}
            className="rounded text-blue-600 focus:ring-blue-500"
          />
          Auto-refresh (30s)
        </label>
      </div>

      {/* Alerts List */}
      <div className="flex-1 overflow-y-auto p-5 bg-slate-950/50">
        {isLoading && alerts.length === 0 ? (
          <div className="flex items-center justify-center h-full text-blue-600">
            <Loader className="w-8 h-8 animate-spin" />
          </div>
        ) : alerts.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <CheckCircle className="w-20 h-20 text-green-500 mb-4" />
            <p className="text-white text-lg font-bold">
              All Systems Nominal
            </p>
            <p className="text-slate-500 text-sm">No issues detected</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {alerts.map((alert, idx) => (
            <div
              key={idx}
              className="bg-slate-800/60 rounded-xl p-5 hover:shadow-lg transition border border-white/10 flex flex-col h-full"
            >
              {/* Alert Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2 flex-wrap">
                  {getSeverityIcon(alert.severity)}
                  <span
                    className={`px-3 py-1 rounded-lg text-xs font-bold shadow-md border ${getSeverityColor(
                      alert.severity
                    )}`}
                  >
                    {alert.severity}
                  </span>
                  <span className="text-slate-100 font-bold text-sm">
                    {alert.issue_type}
                  </span>
                </div>
                <span className="text-slate-400 text-xs font-mono bg-slate-900 px-2 py-1 rounded-lg">
                  {alert.cell_id}
                </span>
              </div>

              {/* KPIs */}
              <div className="flex flex-wrap gap-2 mb-4">
                {Object.entries(alert.kpis || {}).map(([key, value]) => (
                  <span
                    key={key}
                    className="text-xs bg-cyan-500/10 px-3 py-1.5 rounded-lg text-cyan-300 border border-cyan-500/20 font-medium"
                  >
                    {key}: {typeof value === 'number' ? value.toFixed(1) : value}
                  </span>
                ))}
              </div>

              {/* Causes */}
              <div className="mb-4">
                <p className="text-slate-500 text-xs font-bold mb-2 uppercase tracking-wide">Causes:</p>
                <ul className="text-sm text-slate-300 space-y-1.5">
                  {alert.causes?.map((cause, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-orange-500 mt-0.5 font-bold">•</span>
                      <span>{cause}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Recommendations */}
              <div>
                <p className="text-slate-500 text-xs font-bold mb-2 uppercase tracking-wide">
                  Recommendations:
                </p>
                <ul className="text-sm text-slate-300 space-y-1.5">
                  {alert.recommendations?.slice(0, 3).map((rec, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-blue-600 mt-0.5 font-bold">→</span>
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
