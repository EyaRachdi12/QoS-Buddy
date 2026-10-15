import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, Bell, MapPin } from 'lucide-react';
import { useDashboard } from '../../context/DashboardContext';
import SparklineMini from './SparklineMini';

function severityStyles(sev) {
  const u = (sev || '').toUpperCase();
  if (u === 'CRITICAL' || u === 'HIGH') {
    return 'border-rose-500/50 bg-rose-500/10 text-rose-100';
  }
  if (u === 'MEDIUM') {
    return 'border-amber-500/50 bg-amber-500/10 text-amber-100';
  }
  return 'border-sky-500/40 bg-sky-500/10 text-sky-100';
}

/** Mini bar chart from KPI numbers on a single alert. */
function AlertKpiViz({ kpis }) {
  const pairs = Object.entries(kpis || {})
    .filter(([, v]) => typeof v === 'number' && !Number.isNaN(v))
    .slice(0, 8);
  if (!pairs.length) return null;
  const max = Math.max(...pairs.map(([, v]) => Math.abs(v)), 1e-6);
  return (
    <div className="flex items-end gap-0.5 h-7 mt-2 opacity-90">
      {pairs.map(([k, v]) => (
        <div key={k} className="flex-1 flex flex-col items-center gap-0.5 min-w-0">
          <div
            className="w-full rounded-sm bg-gradient-to-t from-fuchsia-600 to-pink-400"
            style={{ height: `${Math.min(100, (Math.abs(v) / max) * 100)}%`, minHeight: '4px' }}
            title={`${k}: ${v}`}
          />
        </div>
      ))}
    </div>
  );
}

export default function AlertsPanel() {
  const {
    selectedBoId,
    alertsLoading,
    mergedAlertsPreview,
    boBundle,
    cellZoneMap,
    setFocusedZone,
  } = useDashboard();

  const boScoped = boBundle?.alerts || [];

  /** Uniquement le périmètre métier choisi : bundle BO + dernier run ML (déjà filtré par bo_filter). Pas d’alertes globales cross-BO. */
  const rows = (() => {
    if (selectedBoId == null) return [];
    const seen = new Set();
    const out = [];
    for (const a of [...boScoped, ...mergedAlertsPreview]) {
      const k = `${a.cell_id}|${a.issue_type}|${a.timestamp}`;
      if (seen.has(k)) continue;
      seen.add(k);
      out.push(a);
      if (out.length >= 22) break;
    }
    return out;
  })();

  const sparkFromKpis = (kpis) => {
    const vals = Object.values(kpis || {})
      .filter((v) => typeof v === 'number' && !Number.isNaN(v))
      .slice(0, 20);
    return vals.length > 2 ? vals : [];
  };

  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.06] backdrop-blur-xl p-6 shadow-xl">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2 text-slate-100">
          <Bell className="w-6 h-6 text-rose-400" />
          <h3 className="font-semibold text-lg">File d’alertes</h3>
        </div>
        {alertsLoading && (
          <span className="text-sm text-slate-500 animate-pulse">Sync…</span>
        )}
      </div>
      {boScoped.length > 0 && (
        <p className="text-xs text-slate-500 mb-3 leading-relaxed">
          Primary queue from <code className="text-cyan-400/90">/api/bo/dashboard-bundle</code> (sorted by
          severity). Click to fly map to city zone when cell mapping exists.
        </p>
      )}

      {!rows.length && !alertsLoading && (
        <p className="text-base text-slate-500 py-6 text-center">Aucune alerte pour cet objectif sur la fenêtre temps.</p>
      )}

      <ul className="space-y-2 max-h-[340px] overflow-y-auto pr-1">
        <AnimatePresence initial={false}>
          {rows.map((a, idx) => {
            const zone = a.cell_id != null ? cellZoneMap[String(a.cell_id)] : null;
            const spark = sparkFromKpis(a.kpis);
            return (
              <motion.li
                key={`${a.cell_id}-${a.issue_type}-${idx}`}
                layout
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.25 }}
              >
                <button
                  type="button"
                  onClick={() => zone && setFocusedZone(zone)}
                  className={`w-full text-left rounded-xl border px-3 py-3 transition hover:brightness-110 ${severityStyles(
                    a.severity,
                  )} ${zone ? 'cursor-pointer' : 'cursor-default'}`}
                >
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5 opacity-80" />
                    <div className="min-w-0 flex-1">
                      <p className="text-base font-medium truncate">
                        [{a.severity || 'INFO'}] {a.issue_type || 'Issue'}
                      </p>
                      <p className="text-sm opacity-80 truncate">
                        Cell {a.cell_id ?? '—'}
                        {a.timestamp ? ` · ${String(a.timestamp).slice(0, 19)}` : ''}
                        {zone && (
                          <span className="inline-flex items-center gap-1 ml-1 text-cyan-300">
                            <MapPin className="w-3 h-3" />
                            {zone}
                          </span>
                        )}
                      </p>
                      <AlertKpiViz kpis={a.kpis} />
                      {spark.length > 2 && (
                        <div className="mt-1">
                          <SparklineMini data={spark} color="#e879f9" height={28} />
                        </div>
                      )}
                    </div>
                  </div>
                </button>
              </motion.li>
            );
          })}
        </AnimatePresence>
      </ul>
    </div>
  );
}
