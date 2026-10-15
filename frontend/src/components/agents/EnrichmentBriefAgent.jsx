import { useEffect, useState } from 'react';
import { ExternalLink, Library } from 'lucide-react';
import AgentShell from './AgentShell';
import { mlAPI, getApiError } from '../../services/api';

/**
 * Surfaces scraped open-data catalog: telecom-relevant datasets for benchmarking & planning.
 * Does not modify the unified CSV — context only for dashboard users.
 */
export default function EnrichmentBriefAgent() {
  const [total, setTotal] = useState(null);
  const [samples, setSamples] = useState([]);
  const [err, setErr] = useState(null);

  useEffect(() => {
    let on = true;
    (async () => {
      try {
        const data = await mlAPI.enrichmentCatalog(0, 6);
        if (!on) return;
        setTotal(data?.total ?? null);
        setSamples(Array.isArray(data?.records) ? data.records : []);
        setErr(null);
      } catch (e) {
        if (!on) return;
        setErr(getApiError(e));
        setTotal(null);
        setSamples([]);
      }
    })();
    return () => {
      on = false;
    };
  }, []);

  return (
    <AgentShell
      title="Open data & enrichissement"
      subtitle="Catalogue scrapé (Data.gov, EU, UCI…) — utile pour benchmarks QoS"
      icon={Library}
      tint="amber"
    >
      {err && <p className="text-rose-300 text-sm leading-relaxed">{err}</p>}
      {!err && total != null && (
        <p className="text-slate-200 text-sm leading-relaxed">
          <span className="font-semibold text-white tabular-nums">{total}</span> jeux de données indexés.
          Lancez une mise à jour depuis le panneau « Sources ouvertes » ci-dessous.
        </p>
      )}
      {samples.length > 0 && (
        <ul className="space-y-2 mt-1">
          {samples.map((r, i) => (
            <li key={i} className="text-sm text-slate-300 leading-snug border-l-2 border-amber-500/40 pl-2">
              <span className="text-white font-medium line-clamp-2">{r.title || 'Sans titre'}</span>
              <span className="block text-xs text-slate-500 mt-0.5">{r.source_portal || 'source'}</span>
              {r.url && (
                <a
                  href={r.url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 text-amber-300/90 text-xs mt-1 hover:underline"
                >
                  <ExternalLink className="w-3 h-3 shrink-0" />
                  Ouvrir
                </a>
              )}
            </li>
          ))}
        </ul>
      )}
      <a href="#enrichment-catalog" className="inline-block text-xs font-medium text-amber-200/90 hover:underline mt-2">
        Voir le panneau détaillé ↓
      </a>
    </AgentShell>
  );
}
