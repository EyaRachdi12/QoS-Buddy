import { useState, useEffect } from 'react';
import { Play, Square, RotateCw } from 'lucide-react';
import { simulatorAPI, getApiError } from '../../services/api';

export default function SimulatorToggle() {
  const [status, setStatus] = useState({ running: false, total_runs: 0 });
  const [loading, setLoading] = useState(false);
  const [interval, setInterval_] = useState(5);

  useEffect(() => {
    simulatorAPI.status().then(setStatus).catch(() => {});
  }, []);

  const handleToggle = async () => {
    setLoading(true);
    try {
      if (status.running) {
        const res = await simulatorAPI.stop();
        setStatus(res);
      } else {
        const res = await simulatorAPI.start(interval);
        setStatus(res);
      }
    } catch (err) {
      console.error(getApiError(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-3 flex items-center gap-3">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <RotateCw className={`w-3.5 h-3.5 ${status.running ? 'text-emerald-400 animate-spin' : 'text-slate-500'}`} />
          <span className="text-xs font-medium text-slate-200">Agent Simulator</span>
          <span
            className={`text-[10px] px-1.5 py-0.5 rounded-full ${
              status.running ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-700 text-slate-400'
            }`}
          >
            {status.running ? 'RUNNING' : 'STOPPED'}
          </span>
        </div>
        {status.running && (
          <div className="text-[10px] text-slate-500 mt-0.5">
            {status.total_runs} cycles · every {status.interval_minutes}min
          </div>
        )}
      </div>

      {!status.running && (
        <select
          value={interval}
          onChange={(e) => setInterval_(Number(e.target.value))}
          className="text-xs bg-slate-800 border border-white/10 rounded-lg px-2 py-1 text-slate-300"
        >
          <option value={1}>1 min</option>
          <option value={5}>5 min</option>
          <option value={10}>10 min</option>
          <option value={30}>30 min</option>
        </select>
      )}

      <button
        type="button"
        onClick={handleToggle}
        disabled={loading}
        className={`p-2 rounded-lg transition-colors ${
          status.running
            ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30'
            : 'bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30'
        } disabled:opacity-50`}
        title={status.running ? 'Stop Simulator' : 'Start Simulator'}
      >
        {loading ? (
          <div className="w-4 h-4 border-2 border-current/30 border-t-current rounded-full animate-spin" />
        ) : status.running ? (
          <Square className="w-4 h-4" />
        ) : (
          <Play className="w-4 h-4" />
        )}
      </button>
    </div>
  );
}
