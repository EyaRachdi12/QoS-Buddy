import { motion } from 'framer-motion';
import { BrainCircuit } from 'lucide-react';
import { useDashboard } from '../../context/DashboardContext';
import { menuItemForBo } from '../../constants/boMenu';
import MlHealthStrip from './MlHealthStrip';
import ActionsPanel from './ActionsPanel';

/**
 * Page dédiée détection / prédiction (comme une section « agents »), isolée du tableau de bord principal.
 */
export default function MlStudioPanel() {
  const { selectedBoId, detectResult, predictResult, detectLoading, predictLoading } = useDashboard();
  const scope = menuItemForBo(selectedBoId);

  return (
    <div className="space-y-6 pb-12 max-w-5xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-2xl border border-white/10 bg-gradient-to-br from-slate-900/90 to-violet-950/40 backdrop-blur-xl p-7 shadow-2xl"
      >
        <div className="flex flex-wrap items-start gap-4">
          <div className="p-3 rounded-2xl bg-violet-500/20 border border-violet-400/40">
            <BrainCircuit className="w-8 h-8 text-violet-200" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-white tracking-tight">Détection &amp; prédiction</h1>
            <p className="text-base text-slate-300 mt-2 leading-relaxed max-w-2xl">
              Lancez les modèles <code className="text-violet-300/90 text-sm">/api/ml/detect</code> et{' '}
              <code className="text-violet-300/90 text-sm">/api/ml/predict</code> pour la vue actuellement
              sélectionnée dans le menu (<span className="text-white font-medium">{scope.label}</span>
              {selectedBoId == null ? ' — tout le jeu de données' : ''}).
            </p>
          </div>
        </div>
      </motion.div>

      <MlHealthStrip
        detectResult={detectResult}
        predictResult={predictResult}
        detectLoading={detectLoading}
        predictLoading={predictLoading}
      />

      <ActionsPanel />
    </div>
  );
}
