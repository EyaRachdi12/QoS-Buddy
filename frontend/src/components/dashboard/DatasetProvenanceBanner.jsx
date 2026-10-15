import { Database } from 'lucide-react';
import { useDashboard } from '../../context/DashboardContext';
import { BO_MENU_ITEMS, menuItemForBo } from '../../constants/boMenu';
import { BO_NOTEBOOK_SPECS } from '../../constants/boNotebookRefs';

const API_SEGMENT_ORDER = ['BO1', 'BO2', 'BO3'];

/**
 * Dataset unifié + volumes ; puces affichent les titres métier (Anomaly, SLA, …), pas les codes API.
 */
export default function DatasetProvenanceBanner() {
  const { selectedBoId, boBundle, sourceBoSummary } = useDashboard();

  const counts = sourceBoSummary?.counts || {};
  const total = sourceBoSummary?.total_rows;
  const dataset = sourceBoSummary?.dataset || 'unified_telecom_dataset_FILLED.csv';
  const sliceRows = boBundle?.row_count;
  const activeMenu = menuItemForBo(selectedBoId);

  return (
    <div className="rounded-2xl border border-cyan-500/25 bg-slate-900/70 backdrop-blur-xl px-5 py-4 flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-3">
        <div className="p-2.5 rounded-xl bg-cyan-500/15 border border-cyan-500/30">
          <Database className="w-6 h-6 text-cyan-300" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-base font-semibold text-white">
            Jeu de données — <span className="text-cyan-200">{dataset}</span>
          </p>
          <p className="text-sm text-slate-400 mt-0.5 leading-relaxed">
            Segmentation technique <code className="text-cyan-300/90 text-sm">source_bo</code> ; à l’écran, les
            vues portent les noms métier (Anomaly, SLA &amp; QoS, Zones &amp; CAPEX).
          </p>
        </div>
      </div>

      <div className="flex flex-wrap gap-2 text-sm">
        {API_SEGMENT_ORDER.map((apiId) => {
          const m = menuItemForBo(apiId);
          const n = counts[apiId];
          const dim = selectedBoId && selectedBoId !== apiId;
          return (
            <span
              key={apiId}
              className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 border font-medium ${
                selectedBoId === apiId
                  ? 'bg-cyan-500/20 border-cyan-400/50 text-white'
                  : 'bg-white/5 border-white/10 text-slate-300'
              } ${dim ? 'opacity-60' : ''}`}
            >
              <span className="text-slate-100">{m.short}</span>
              <span className="tabular-nums text-slate-400">
                {n != null ? Number(n).toLocaleString() : '—'} rows
              </span>
            </span>
          );
        })}
        {total != null && (
          <span className="inline-flex items-center rounded-lg px-3 py-1.5 border border-white/10 bg-white/5 text-slate-400">
            Total <span className="ml-2 tabular-nums text-slate-200">{Number(total).toLocaleString()}</span>
          </span>
        )}
      </div>

      <div className="rounded-xl border border-white/10 bg-black/20 px-3 py-3 text-xs sm:text-sm">
        <p className="font-semibold text-slate-300 mb-2">Notebooks → segment données</p>
        <ul className="space-y-1.5 text-slate-400 leading-relaxed break-words">
          {API_SEGMENT_ORDER.map((apiId) => {
            const m = menuItemForBo(apiId);
            const files = BO_NOTEBOOK_SPECS[apiId]?.files?.join(', ') ?? '';
            return (
              <li key={apiId}>
                <span className="text-slate-200 font-medium">{m.label}</span>
                <span className="text-slate-600 mx-1">·</span>
                <span className="font-mono text-[11px] sm:text-xs">{files}</span>
              </li>
            );
          })}
        </ul>
      </div>

      {selectedBoId && (
        <p className="text-sm text-slate-300 border-t border-white/10 pt-3">
          <span className="font-medium text-white">{activeMenu.label}</span> — fenêtre bundle{' '}
          <span className="text-cyan-200 tabular-nums">
            {sliceRows != null ? Number(sliceRows).toLocaleString() : '—'}
          </span>{' '}
          lignes (agrégats, alertes de cette vue uniquement).
        </p>
      )}
    </div>
  );
}
