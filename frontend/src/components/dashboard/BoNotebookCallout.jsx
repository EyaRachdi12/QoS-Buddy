import { BookOpen } from 'lucide-react';
import { BO_NOTEBOOK_SPECS, notebookSpecForBo } from '../../constants/boNotebookRefs';
import { BO_MENU_ITEMS } from '../../constants/boMenu';

/**
 * Références notebooks — titres métier (Anomaly, SLA, Zones) sans imposer BO1/BO2/BO3 à l’écran.
 */
export default function BoNotebookCallout({ selectedBoId }) {
  const spec = notebookSpecForBo(selectedBoId);
  const menu = BO_MENU_ITEMS.find((m) => m.id === selectedBoId);

  if (spec && menu) {
    return (
      <div className="mt-4 rounded-xl border border-violet-500/35 bg-violet-950/35 backdrop-blur-sm px-4 py-4 text-left">
        <div className="flex gap-3 items-start">
          <div className="p-2 rounded-lg bg-violet-500/20 border border-violet-400/30 shrink-0">
            <BookOpen className="w-6 h-6 text-violet-200" />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-bold text-violet-100 uppercase tracking-wide">
              Contexte analytique — {menu.label}
            </p>
            <p className="text-sm font-mono text-violet-300/90 mt-1 break-all">{spec.files.join(' · ')}</p>
            <p className="text-base text-slate-200 mt-3 font-medium leading-snug">{spec.headline}</p>
            <ul className="text-sm text-slate-400 mt-3 space-y-2 list-disc pl-5 leading-relaxed">
              {spec.bullets.map((b, i) => (
                <li key={i}>{b}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mt-4 rounded-xl border border-white/10 bg-slate-900/50 px-4 py-4 text-left">
      <div className="flex gap-3 items-start">
        <BookOpen className="w-6 h-6 text-slate-500 shrink-0 mt-1" />
        <div>
          <p className="text-base font-semibold text-slate-200">Vue unifiée — trois objectifs dans le même jeu de données</p>
          <p className="text-sm text-slate-400 mt-2 leading-relaxed">
            Chaque vue ci-dessous correspond à un notebook du dépôt ; le CSV commun est segmenté en interne par{' '}
            <code className="text-slate-500">source_bo</code>.
          </p>
          <ul className="text-sm mt-3 space-y-2 leading-relaxed">
            {BO_MENU_ITEMS.filter((m) => m.id != null).map((m) => {
              const s = BO_NOTEBOOK_SPECS[m.id];
              return (
                <li key={m.id} className="border-l-2 border-cyan-500/40 pl-3">
                  <span className="text-slate-100 font-medium">{m.label}</span>
                  <span className="text-slate-600"> · </span>
                  <span className="font-mono text-xs text-slate-500">{s?.files.join(', ')}</span>
                </li>
              );
            })}
          </ul>
        </div>
      </div>
    </div>
  );
}
