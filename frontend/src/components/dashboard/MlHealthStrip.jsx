import { motion } from 'framer-motion';
import { ShieldAlert, Wand2 } from 'lucide-react';

/** Threshold strip: detection outlier ratio + prediction error (MAE) as horizontal meters. */
export default function MlHealthStrip({ detectResult, predictResult, detectLoading, predictLoading }) {
  const ifMeta = detectResult?.isolation_forest;
  const outPct = ifMeta ? Math.min(100, (ifMeta.outlier_ratio || 0) * 100) : null;

  const mae = predictResult?.metrics?.mae;
  const errPct = mae != null ? Math.min(100, (Number(mae) / 80) * 100) : null;

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: 'auto' }}
      className="rounded-2xl border border-white/10 bg-slate-900/60 backdrop-blur-xl p-5 space-y-4"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm font-semibold uppercase tracking-widest text-slate-500">
          ML — aperçu rapide
        </p>
        {(detectLoading || predictLoading) && (
          <span className="text-xs text-cyan-400 animate-pulse">Modèle en cours…</span>
        )}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <div>
          <div className="flex items-center gap-2 text-sm text-slate-400 mb-1.5">
            <ShieldAlert className="w-4 h-4 text-rose-400 shrink-0" />
            Detection — outlier share
            {outPct != null && (
              <span
                className={`ml-auto tabular-nums ${
                  outPct > 15 ? 'text-rose-400' : outPct > 8 ? 'text-amber-300' : 'text-emerald-400'
                }`}
              >
                {outPct.toFixed(1)}%
              </span>
            )}
          </div>
          <div className="h-2.5 rounded-full bg-slate-800 overflow-hidden">
            <motion.div
              className={`h-full rounded-full ${
                outPct > 15 ? 'bg-rose-500' : outPct > 8 ? 'bg-amber-400' : 'bg-emerald-500'
              }`}
              initial={{ width: 0 }}
              animate={{ width: outPct != null ? `${outPct}%` : '0%' }}
              transition={{ duration: 0.6, ease: 'easeOut' }}
            />
          </div>
          {!ifMeta && !detectLoading && (
            <p className="text-xs text-slate-500 mt-1.5">Lancer la détection pour remplir.</p>
          )}
        </div>
        <div>
          <div className="flex items-center gap-2 text-sm text-slate-400 mb-1.5">
            <Wand2 className="w-4 h-4 text-violet-400 shrink-0" />
            Prediction — latency MAE (vs 80 ms ref)
            {mae != null && (
              <span
                className={`ml-auto tabular-nums ${
                  mae > 25 ? 'text-rose-400' : mae > 12 ? 'text-amber-300' : 'text-emerald-400'
                }`}
              >
                {typeof mae === 'number' ? mae.toFixed(2) : mae} ms
              </span>
            )}
          </div>
          <div className="h-2.5 rounded-full bg-slate-800 overflow-hidden">
            <motion.div
              className={`h-full rounded-full ${
                errPct > 60 ? 'bg-rose-500' : errPct > 35 ? 'bg-amber-400' : 'bg-violet-500'
              }`}
              initial={{ width: 0 }}
              animate={{ width: errPct != null ? `${errPct}%` : '0%' }}
              transition={{ duration: 0.6, ease: 'easeOut' }}
            />
          </div>
          {mae == null && !predictLoading && (
            <p className="text-xs text-slate-500 mt-1.5">Lancer la prédiction pour remplir.</p>
          )}
        </div>
      </div>
    </motion.div>
  );
}
