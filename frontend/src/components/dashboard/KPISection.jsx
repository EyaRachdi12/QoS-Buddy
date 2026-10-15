import { useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  Gauge,
  Timer,
  Activity,
  BellRing,
  Users,
  ShieldAlert,
  Radio,
  Landmark,
} from 'lucide-react';
import { useDashboard } from '../../context/DashboardContext';
import { kpiBlueprintForBo } from '../../constants/boKpiConfig';
import { menuItemForBo } from '../../constants/boMenu';
import SparklineMini from './SparklineMini';

const cardVariants = {
  hidden: { opacity: 0, y: 12 },
  show: (i) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.05, duration: 0.35, ease: [0.22, 1, 0.36, 1] },
  }),
};

function GlassCard({ children, className = '' }) {
  return (
    <div
      className={`rounded-2xl border border-white/10 bg-white/[0.06] backdrop-blur-xl shadow-xl ${className}`}
    >
      {children}
    </div>
  );
}

/** Build numeric series from overview trends for sparklines. */
function seriesFromTrends(trends, key, n = 24) {
  if (!trends?.length) return [];
  return trends
    .slice(-n)
    .map((t) => t[key])
    .filter((v) => v != null && !Number.isNaN(Number(v)))
    .map(Number);
}

export default function KPISection() {
  const {
    selectedBoId,
    overview,
    overviewLoading,
    overviewError,
    diagnosticSummary,
    kpiPayload,
    kpiLoading,
    boBundle,
    detectResult,
    predictResult,
  } = useDashboard();

  const blueprint = kpiBlueprintForBo(selectedBoId);

  const boAlertsCount = useMemo(() => {
    if (selectedBoId && Array.isArray(boBundle?.alerts)) return boBundle.alerts.length;
    return null;
  }, [selectedBoId, boBundle]);

  const metrics = useMemo(() => {
    const trends = overview?.trends || [];
    const agg = boBundle?.aggregates || {};
    const tail = trends.slice(-40);

    let avgLatency = agg.avg_latency_ms ?? null;
    let packetLossProxy = null;
    if (tail.length) {
      const latVals = tail.map((t) => t.latency_ms).filter((v) => v != null && !Number.isNaN(+v));
      if (latVals.length && avgLatency == null) {
        avgLatency = latVals.reduce((a, b) => a + Number(b), 0) / latVals.length;
      }
      const sla = tail.map((t) => t.sla_breach_risk).filter((v) => v != null);
      if (sla.length) {
        packetLossProxy = (sla.reduce((a, b) => a + Number(b), 0) / sla.length) * 100;
      }
    }

    const kpis = kpiPayload?.kpis || [];
    const recentK = kpis.slice(-30);
    if (avgLatency == null && recentK.length) {
      const lv = recentK.map((r) => r.latency_ms).filter((v) => v != null);
      if (lv.length) {
        avgLatency = lv.reduce((a, b) => a + Number(b), 0) / lv.length;
      }
    }

    const mos =
      agg.avg_mos != null ? agg.avg_mos : overview?.bo2?.avg_mos != null ? overview.bo2.avg_mos : null;
    const qosScore =
      mos != null && !Number.isNaN(Number(mos))
        ? Math.round(Math.min(100, Math.max(0, (Number(mos) / 5) * 100)))
        : null;

    const records = overview?.bo1?.records ?? (boBundle?.row_count != null ? boBundle.row_count : 0);
    const alertsCount =
      boAlertsCount != null ? boAlertsCount : diagnosticSummary?.total_alerts ?? diagnosticSummary?.critical ?? null;

    const anomalyRate = overview?.bo1?.anomaly_rate_pct ?? null;
    const anomalyCount = agg.anomaly_count ?? null;

    const avgPrb =
      agg.avg_prb_dl != null && agg.avg_prb_ul != null
        ? (Number(agg.avg_prb_dl) + Number(agg.avg_prb_ul)) / 2
        : agg.avg_prb_dl ?? agg.avg_prb_ul ?? null;

    const capex = agg.avg_capex_score ?? overview?.bo3?.avg_capex_score ?? null;
    const criticalZones = overview?.bo3?.critical_risk_count ?? overview?.zones?.filter((z) => (z.critical_count ?? 0) > 0).length ?? null;

    const ifRatio = detectResult?.isolation_forest?.outlier_ratio;
    const predMae = predictResult?.metrics?.mae;

    return {
      avgLatency,
      packetLossProxy,
      qosScore,
      records,
      alertsCount,
      mos,
      anomalyRate,
      anomalyCount,
      avgPrb,
      capex,
      criticalZones,
      ifRatio,
      predMae,
      latSpark: seriesFromTrends(trends, 'latency_ms'),
      mosSpark: seriesFromTrends(trends, 'MOS'),
      slaSpark: seriesFromTrends(trends, 'sla_breach_risk').map((v) => v * 100),
    };
  }, [overview, kpiPayload, diagnosticSummary, boBundle, detectResult, predictResult, boAlertsCount]);

  const cardDefs = useMemo(() => {
    const defs = {
      latency: {
        key: 'latency',
        label: 'Avg latency',
        value: metrics.avgLatency != null ? `${metrics.avgLatency.toFixed(0)} ms` : '—',
        sub: 'Bundle + trend window',
        icon: Timer,
        gradient: 'from-cyan-500/80 to-blue-600/80',
        spark: metrics.latSpark,
        sparkColor: '#22d3ee',
        meter: metrics.avgLatency != null ? Math.min(100, (metrics.avgLatency / 200) * 100) : null,
        meterTone: metrics.avgLatency > 120 ? 'bg-rose-500' : metrics.avgLatency > 80 ? 'bg-amber-400' : 'bg-emerald-500',
      },
      sla_risk: {
        key: 'sla_risk',
        label: 'SLA stress',
        value: metrics.packetLossProxy != null ? `${metrics.packetLossProxy.toFixed(1)}` : '—',
        sub: 'Breach risk ×100 (proxy)',
        icon: Activity,
        gradient: 'from-amber-500/80 to-orange-600/80',
        spark: metrics.slaSpark,
        sparkColor: '#fb923c',
        meter: metrics.packetLossProxy,
        meterTone:
          metrics.packetLossProxy > 70 ? 'bg-rose-500' : metrics.packetLossProxy > 40 ? 'bg-amber-400' : 'bg-emerald-500',
      },
      qos_score: {
        key: 'qos_score',
        label: 'QoS score',
        value: metrics.qosScore != null ? `${metrics.qosScore}/100` : '—',
        sub: metrics.mos != null ? `MOS ${Number(metrics.mos).toFixed(2)}` : 'From MOS',
        icon: Gauge,
        gradient: 'from-emerald-500/80 to-teal-600/80',
        spark: metrics.mosSpark,
        sparkColor: '#34d399',
        reverseMeter: true,
        meter: metrics.qosScore,
        meterTone:
          metrics.qosScore < 50 ? 'bg-rose-500' : metrics.qosScore < 70 ? 'bg-amber-400' : 'bg-emerald-500',
      },
      samples: {
        key: 'samples',
        label: 'Samples',
        value: metrics.records ? `${Number(metrics.records).toLocaleString()}` : '—',
        sub: selectedBoId
          ? `Segment « ${menuItemForBo(selectedBoId).label} » (fenêtre agrégée)`
          : 'Toutes les lignes dans la fenêtre temps',
        icon: Users,
        gradient: 'from-violet-500/80 to-fuchsia-600/80',
        spark: [],
      },
      alerts: {
        key: 'alerts',
        label: 'Alerts (24h)',
        value: metrics.alertsCount != null ? `${metrics.alertsCount}` : '—',
        sub: selectedBoId ? 'Alertes agrégées pour cet objectif uniquement' : 'Vue globale (diagnostic)',
        icon: BellRing,
        gradient: 'from-rose-500/80 to-red-600/80',
        spark: [],
      },
      anomaly_rate: {
        key: 'anomaly_rate',
        label: 'Anomaly rate',
        value: metrics.anomalyRate != null ? `${metrics.anomalyRate}%` : metrics.anomalyCount != null ? `${metrics.anomalyCount} rows` : '—',
        sub: 'Santé Anomaly / flags',
        icon: ShieldAlert,
        gradient: 'from-rose-500/80 to-pink-600/80',
        spark: [],
        meter: metrics.ifRatio != null ? Math.min(100, metrics.ifRatio * 100) : null,
        meterTone: metrics.ifRatio > 0.12 ? 'bg-rose-500' : metrics.ifRatio > 0.06 ? 'bg-amber-400' : 'bg-slate-600',
        meterLabel: 'IF outlier share',
      },
      mos: {
        key: 'mos',
        label: 'MOS (avg)',
        value: metrics.mos != null ? Number(metrics.mos).toFixed(2) : '—',
        sub: 'Voice / experience proxy',
        icon: Gauge,
        gradient: 'from-teal-500/80 to-cyan-600/80',
        spark: metrics.mosSpark,
        sparkColor: '#2dd4bf',
      },
      capex: {
        key: 'capex',
        label: 'CAPEX score',
        value: metrics.capex != null ? String(metrics.capex) : '—',
        sub: 'Priorité investissement (Zones & CAPEX)',
        icon: Landmark,
        gradient: 'from-indigo-500/80 to-violet-600/80',
        spark: seriesFromTrends(overview?.trends || [], 'capex_score'),
        sparkColor: '#a78bfa',
      },
      critical_zones: {
        key: 'critical_zones',
        label: 'Hot zones',
        value: metrics.criticalZones != null ? `${metrics.criticalZones}` : '—',
        sub: 'Critical-labelled clusters',
        icon: ShieldAlert,
        gradient: 'from-orange-500/80 to-red-600/80',
        spark: [],
      },
      prb: {
        key: 'prb',
        label: 'PRB (avg)',
        value: metrics.avgPrb != null ? `${metrics.avgPrb.toFixed(1)}%` : '—',
        sub: 'Congestion proxy',
        icon: Radio,
        gradient: 'from-yellow-500/80 to-amber-600/80',
        spark: [],
        meter: metrics.avgPrb,
        meterTone: metrics.avgPrb > 85 ? 'bg-rose-500' : metrics.avgPrb > 70 ? 'bg-amber-400' : 'bg-emerald-500',
      },
    };
    return defs;
  }, [metrics, overview, selectedBoId]);

  const items = blueprint.map((k) => cardDefs[k]).filter(Boolean);

  const loading = overviewLoading || kpiLoading;

  if (overviewError && !overview && !boBundle?.aggregates) {
    return (
      <GlassCard className="p-6">
        <p className="text-amber-300 text-base leading-relaxed">No KPI data: {overviewError}</p>
      </GlassCard>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6 gap-4 sm:gap-5">
      {loading &&
        blueprint.map((_, i) => (
          <div key={i} className="h-40 rounded-2xl bg-white/5 animate-pulse border border-white/5" />
        ))}
      {!loading &&
        items.map((item, i) => {
          const Icon = item.icon;
          return (
            <motion.div
              key={item.key}
              custom={i}
              variants={cardVariants}
              initial="hidden"
              animate="show"
              whileHover={{ scale: 1.02, transition: { duration: 0.2 } }}
            >
              <GlassCard className="p-5 h-full relative overflow-hidden group flex flex-col">
                <div
                  className={`absolute inset-0 opacity-35 bg-gradient-to-br ${item.gradient} blur-2xl group-hover:opacity-50 transition-opacity`}
                />
                <div className="relative flex flex-col flex-1 min-h-0">
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wide">
                      {item.label}
                    </span>
                    <div className="p-2 rounded-lg bg-white/10">
                      <Icon className="w-4 h-4 text-white" />
                    </div>
                  </div>
                  <p className="text-2xl sm:text-3xl font-bold text-white tabular-nums leading-tight">
                    {item.value}
                  </p>
                  <p className="text-xs text-slate-500 mt-1 line-clamp-2 leading-snug">{item.sub}</p>
                  {item.spark?.length > 1 && (
                    <div className="mt-3 shrink-0">
                      <SparklineMini data={item.spark} color={item.sparkColor} height={36} />
                    </div>
                  )}
                  {item.meter != null && (
                    <div className="mt-3 space-y-1">
                      {item.meterLabel && (
                        <p className="text-[11px] text-slate-500">{item.meterLabel}</p>
                      )}
                      <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
                        <motion.div
                          className={`h-full rounded-full ${item.meterTone}`}
                          initial={{ width: 0 }}
                          animate={{ width: `${Math.min(100, item.meter)}%` }}
                          transition={{ duration: 0.5 }}
                        />
                      </div>
                    </div>
                  )}
                  {item.key === 'latency' && predictResult?.metrics?.mae != null && (
                    <p className="text-xs text-violet-300 mt-1.5">
                      Pred MAE: {Number(predictResult.metrics.mae).toFixed(2)} ms
                    </p>
                  )}
                </div>
              </GlassCard>
            </motion.div>
          );
        })}
    </div>
  );
}
