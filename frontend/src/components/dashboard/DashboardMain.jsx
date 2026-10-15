import { useEffect, useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Volume2, Square } from 'lucide-react';
import { useDashboard } from '../../context/DashboardContext';
import { BO_MENU_ITEMS, menuItemForBo } from '../../constants/boMenu';
import KPISection from './KPISection';
import AgentsSection from './AgentsSection';
import ChartsSection from './ChartsSection';
import ZoneMap from './ZoneMap';
import AlertsPanel from './AlertsPanel';
import DatasetProvenanceBanner from './DatasetProvenanceBanner';
import EnrichmentCatalogPanel from './EnrichmentCatalogPanel';
import BoNotebookCallout from './BoNotebookCallout';
import SlaTimelineChart from './SlaTimelineChart';
import CapexHeatmapPanel from './CapexHeatmapPanel';
import AlertTrendChart from './AlertTrendChart';
import ModelPerformancePanel from './ModelPerformancePanel';
import SimulatorToggle from './SimulatorToggle';
import ExportPanel from './ExportPanel';

function buildVoiceSummary({ selectedBoId, menuLabel, overview, zones, worstZoneKey }) {
  const bo1 = overview?.bo1 || {};
  const bo2 = overview?.bo2 || {};
  const bo3 = overview?.bo3 || {};
  const records = bo1.records ?? null;
  const anomalyRate = bo1.anomaly_rate_pct ?? null;
  const mos = bo2.avg_mos ?? null;
  const criticalRisks = bo3.critical_risk_count ?? null;
  const impactedUsers = bo3.impacted_users_est ?? null;
  const summaryScope = selectedBoId ? `focused on ${menuLabel}` : 'for the global dashboard';

  const parts = [
    `Here is your telecom report summary ${summaryScope}.`,
    records != null ? `The current window includes ${Number(records).toLocaleString()} samples.` : null,
    mos != null ? `Average voice quality is ${Number(mos).toFixed(2)} MOS.` : null,
    anomalyRate != null ? `Detected anomaly rate is ${Number(anomalyRate).toFixed(2)} percent.` : null,
    criticalRisks != null ? `There are ${criticalRisks} critical risk events identified.` : null,
    impactedUsers != null ? `Estimated impacted users are ${Number(impactedUsers).toLocaleString()}.` : null,
    zones?.length ? `The map currently tracks ${zones.length} zones.` : null,
    worstZoneKey ? `The most critical zone right now is ${worstZoneKey}.` : null,
  ].filter(Boolean);

  return parts.join(' ');
}

export default function DashboardMain() {
  const { overview, overviewError, selectedBoId, focusedZone, setFocusedZone, overviewLoading } =
    useDashboard();
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [voiceMessage, setVoiceMessage] = useState(null);

  const zones = overview?.zones || [];

  const worstZoneKey = useMemo(() => {
    if (!zones.length) return null;
    let worst = zones[0];
    zones.forEach((z) => {
      const c = z.critical_count ?? 0;
      const wc = worst.critical_count ?? 0;
      if (c > wc) worst = z;
      else if (c === wc && (z.avg_mos ?? 99) < (worst.avg_mos ?? 99)) worst = z;
    });
    return worst?.zone ?? null;
  }, [zones]);

  const showGeographicMap = selectedBoId == null || selectedBoId === 'BO3';
  const showObjectiveAlerts = selectedBoId != null;
  const showSlaChart = selectedBoId == null || selectedBoId === 'BO2';
  const showCapexHeatmap = selectedBoId == null || selectedBoId === 'BO3';

  const menu = menuItemForBo(selectedBoId);
  const title = menu.label;
  const description =
    BO_MENU_ITEMS.find((b) => b.id === selectedBoId)?.description ?? BO_MENU_ITEMS[0].description;
  const voiceSummary = useMemo(
    () =>
      buildVoiceSummary({
        selectedBoId,
        menuLabel: title,
        overview,
        zones,
        worstZoneKey,
      }),
    [selectedBoId, title, overview, zones, worstZoneKey],
  );

  useEffect(() => {
    return () => {
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const handleToggleVoiceSummary = () => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
      setVoiceMessage('Voice playback is not supported by this browser.');
      return;
    }

    if (isSpeaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      setVoiceMessage('Voice summary stopped.');
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(voiceSummary);
    utterance.rate = 0.95;
    utterance.pitch = 1;
    utterance.lang = 'en-US';
    utterance.onend = () => {
      setIsSpeaking(false);
      setVoiceMessage('Voice summary completed.');
    };
    utterance.onerror = () => {
      setIsSpeaking(false);
      setVoiceMessage('Could not play the voice summary.');
    };

    setIsSpeaking(true);
    setVoiceMessage('Reading report summary...');
    window.speechSynthesis.speak(utterance);
  };

  return (
    <div className="space-y-6 pb-12">
      <AnimatePresence mode="wait">
        <motion.div
          key={selectedBoId ?? 'all'}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -6 }}
          transition={{ duration: 0.25 }}
          className="rounded-2xl border border-white/10 bg-gradient-to-br from-slate-900/90 to-slate-950/90 backdrop-blur-xl p-7 shadow-2xl"
        >
          <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div className="min-w-0">
              <h2 className="text-3xl md:text-4xl font-bold text-white tracking-tight">{title}</h2>
              <p className="text-base text-slate-300 mt-2 max-w-3xl leading-relaxed">{description}</p>
            </div>
            <button
              type="button"
              onClick={handleToggleVoiceSummary}
              className={`inline-flex items-center gap-2 rounded-xl border px-4 py-2.5 text-sm font-semibold transition ${
                isSpeaking
                  ? 'bg-rose-500/20 border-rose-400/40 text-rose-200 hover:bg-rose-500/25'
                  : 'bg-cyan-500/15 border-cyan-400/40 text-cyan-200 hover:bg-cyan-500/25'
              }`}
              title={isSpeaking ? 'Stop voice summary' : 'Read report summary'}
              aria-label={isSpeaking ? 'Stop voice summary' : 'Read report summary'}
            >
              {isSpeaking ? <Square className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
              {isSpeaking ? 'Stop summary' : 'Read summary'}
            </button>
          </div>
          {voiceMessage && <p className="text-xs text-cyan-300/90 mt-2">{voiceMessage}</p>}
          {overviewError && (
            <p className="text-sm text-amber-400 mt-3">Apercu indisponible : {overviewError}</p>
          )}
          <BoNotebookCallout selectedBoId={selectedBoId} />
        </motion.div>
      </AnimatePresence>

      <DatasetProvenanceBanner />

      {/* Simulator toggle + KPIs */}
      <div className="grid grid-cols-1 xl:grid-cols-[1fr_280px] gap-4">
        <KPISection />
        <SimulatorToggle />
      </div>

      <AgentsSection />

      {/* BO-specific charts: SLA timeline for BO2, CAPEX heatmap for BO3 */}
      {(showSlaChart || showCapexHeatmap) && (
        <div className={`grid grid-cols-1 gap-4 ${showSlaChart && showCapexHeatmap ? 'xl:grid-cols-2' : ''}`}>
          {showSlaChart && <SlaTimelineChart />}
          {showCapexHeatmap && <CapexHeatmapPanel />}
        </div>
      )}

      {/* Alert trend chart */}
      <AlertTrendChart />

      {(showGeographicMap || showObjectiveAlerts) && (
        <div
          className={`grid grid-cols-1 gap-4 ${showGeographicMap && showObjectiveAlerts ? 'xl:grid-cols-2' : ''}`}
        >
          {showGeographicMap && (
            <div className="space-y-2 min-w-0">
              <h3 className="text-lg font-semibold text-slate-200 px-1">Carte geographique</h3>
              <p className="text-sm text-slate-500 px-1">
                {selectedBoId == null
                  ? 'Vue globale des zones (tous segments).'
                  : 'Carte reservee a la vue investissement par zones.'}
              </p>
              {!overviewLoading && !zones.length ? (
                <div className="rounded-2xl border border-white/10 bg-white/5 p-8 text-center text-slate-500 text-base">
                  Aucune zone sur la fenetre temps.
                </div>
              ) : (
                <ZoneMap
                  zones={zones}
                  focusedZone={focusedZone}
                  onSelectZone={setFocusedZone}
                  worstZoneKey={worstZoneKey}
                />
              )}
            </div>
          )}

          {showObjectiveAlerts && (
            <div className="space-y-2 min-w-0">
              <h3 className="text-lg font-semibold text-slate-200 px-1">
                Alertes — {menuItemForBo(selectedBoId).label}
              </h3>
              <p className="text-sm text-slate-500 px-1">
                File d'alertes pour cet objectif uniquement.
              </p>
              <AlertsPanel />
            </div>
          )}
        </div>
      )}

      <div>
        <h3 className="text-lg font-semibold text-slate-200 mb-3 px-1">Analytique</h3>
        <ChartsSection />
      </div>

      {/* Model Performance + Drift Detection */}
      <ModelPerformancePanel />

      {/* Export */}
      <ExportPanel />

      <EnrichmentCatalogPanel />
    </div>
  );
}
