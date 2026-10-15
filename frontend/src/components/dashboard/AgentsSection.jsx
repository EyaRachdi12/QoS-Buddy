/**
 * Renders 1–3 modular “agents” per BO (see constants/boKpiConfig BO_AGENT_LAYOUT).
 */
import { useDashboard } from '../../context/DashboardContext';
import { agentLayoutForBo } from '../../constants/boKpiConfig';
import CongestionAgent from '../agents/CongestionAgent';
import LatencyQoSAgent from '../agents/LatencyQoSAgent';
import AnomalyWatchAgent from '../agents/AnomalyWatchAgent';
import CapexZoneAgent from '../agents/CapexZoneAgent';
import NetworkInsightAgent from '../agents/NetworkInsightAgent';
import EnrichmentBriefAgent from '../agents/EnrichmentBriefAgent';

const REGISTRY = {
  congestion: CongestionAgent,
  latency: LatencyQoSAgent,
  anomaly: AnomalyWatchAgent,
  capex: CapexZoneAgent,
  network: NetworkInsightAgent,
  enrichment: EnrichmentBriefAgent,
};

export default function AgentsSection() {
  const {
    selectedBoId,
    boBundle,
    overview,
    detectResult,
    runDetect,
    runPredict,
  } = useDashboard();

  const layout = agentLayoutForBo(selectedBoId);
  const aggregates = boBundle?.aggregates || {};
  const zones = overview?.zones || [];
  const gridClass =
    layout.length >= 4
      ? 'grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4'
      : 'grid grid-cols-1 md:grid-cols-3 gap-4';

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between px-1 flex-wrap gap-2">
        <h3 className="text-lg font-semibold text-slate-200">Agents — recommandations & signaux</h3>
        {boBundle?.data_source && (
          <span className="text-xs text-slate-500 font-mono truncate max-w-[280px]">
            Données · {boBundle.data_source} · {boBundle.row_count ?? 0} lignes
          </span>
        )}
      </div>
      <div className={gridClass}>
        {layout.map((key) => {
          const Cmp = REGISTRY[key];
          if (!Cmp) return null;
          const extra =
            key === 'congestion'
              ? { onRunDetect: runDetect }
              : key === 'latency'
                ? { onRunPredict: runPredict }
                : {};
          return (
            <Cmp
              key={key}
              aggregates={aggregates}
              overview={overview}
              zones={zones}
              detectResult={detectResult}
              {...extra}
            />
          );
        })}
      </div>
    </section>
  );
}
