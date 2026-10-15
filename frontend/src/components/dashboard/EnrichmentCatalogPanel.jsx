import { useCallback, useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Globe2, RefreshCw, Sparkles } from 'lucide-react';
import { mlAPI, getApiError } from '../../services/api';

/**
 * Makes scraped metadata actionable: why it matters for QoS dashboards, refresh, sample rows.
 */
export default function EnrichmentCatalogPanel() {
  const [total, setTotal] = useState(null);
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [scraping, setScraping] = useState(false);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await mlAPI.enrichmentCatalog(0, 12);
      setTotal(data?.total ?? 0);
      setRows(Array.isArray(data?.records) ? data.records : []);
    } catch (e) {
      setError(getApiError(e));
      setRows([]);
      setTotal(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const runScrape = async () => {
    setScraping(true);
    setMessage(null);
    setError(null);
    try {
      const res = await mlAPI.enrichmentScrape();
      setMessage(
        res?.total_in_catalog != null
          ? `Catalogue mis à jour — ${res.total_in_catalog} entrées au total.`
          : 'Collecte terminée.',
      );
      await load();
    } catch (e) {
      setError(getApiError(e));
    } finally {
      setScraping(false);
    }
  };

  return (
    <motion.section
      id="enrichment-catalog"
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="scroll-mt-24 rounded-2xl border border-amber-500/20 bg-gradient-to-br from-slate-900/95 to-slate-950/95 backdrop-blur-xl p-6 shadow-xl"
    >
      <div className="flex flex-wrap items-start justify-between gap-4 mb-4">
        <div className="flex gap-3">
          <div className="p-2.5 rounded-xl bg-amber-500/15 border border-amber-500/35">
            <Globe2 className="w-7 h-7 text-amber-300" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              Sources ouvertes — contexte QoS
              <Sparkles className="w-5 h-5 text-amber-400/90" />
            </h3>
            <p className="text-sm text-slate-400 mt-1 max-w-3xl leading-relaxed">
              Les scrapers agrègent des <strong className="text-slate-300">métadonnées</strong> (titres,
              portails, liens) sur des jeux publics liés au réseau mobile, broadband, QoS et trafic. Cela{' '}
              <strong className="text-slate-300">n’altère pas</strong> votre fichier{' '}
              <code className="text-amber-200/90 text-sm">unified_telecom_dataset_FILLED.csv</code> — c’est une
              couche d’aide pour l’Advisor, les benchmarks et la veille réglementaire.
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={runScrape}
          disabled={scraping}
          className="inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold bg-amber-500/20 text-amber-100 border border-amber-500/40 hover:bg-amber-500/30 disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${scraping ? 'animate-spin' : ''}`} />
          {scraping ? 'Collecte…' : 'Rafraîchir le catalogue'}
        </button>
      </div>

      {message && <p className="text-sm text-emerald-300 mb-3">{message}</p>}
      {error && <p className="text-sm text-rose-300 mb-3">{error}</p>}

      <div className="rounded-xl border border-white/10 bg-white/[0.04] p-4">
        {loading ? (
          <div className="h-40 rounded-lg bg-white/5 animate-pulse" />
        ) : (
          <>
            <p className="text-base font-medium text-slate-200 mb-3">
              <span className="tabular-nums text-white text-lg">{total ?? 0}</span> entrées indexées
            </p>
            <ul className="space-y-3 max-h-72 overflow-y-auto pr-1">
              {rows.length === 0 && (
                <li className="text-sm text-slate-500">
                  Aucune entrée — exécutez « Rafraîchir le catalogue » pour lancer les scrapers (connexion
                  Internet requise).
                </li>
              )}
              {rows.map((r, i) => (
                <li
                  key={i}
                  className="text-sm border-b border-white/5 pb-3 last:border-0 last:pb-0 leading-relaxed"
                >
                  <a
                    href={r.url}
                    target="_blank"
                    rel="noreferrer"
                    className="font-semibold text-cyan-200 hover:underline text-base"
                  >
                    {r.title || 'Sans titre'}
                  </a>
                  <p className="text-slate-500 text-xs mt-0.5">{r.source_portal}</p>
                  {r.description && (
                    <p className="text-slate-400 mt-1 line-clamp-2 text-sm">{r.description}</p>
                  )}
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
    </motion.section>
  );
}
