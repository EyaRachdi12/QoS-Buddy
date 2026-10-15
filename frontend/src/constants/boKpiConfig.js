/**
 * Per-BO KPI visibility — aligné notebooks :
 * BO1 → BO1_Anomaly_Detection_UPDATED.ipynb
 * BO2 → BO2_QoSBuddy_SLA_UPDATED.ipynb + BO2_QoSBuddy_SLA_MOS.ipynb
 * BO3 → BO3_CAPEX_Zone_UPDATED.ipynb
 *
 * Keys map to builders in KPISection (latency, sla_risk, qos_score, samples, alerts,
 * anomaly_rate, mos, capex, critical_zones, prb).
 */
export const BO_KPI_BLUEPRINT = {
  /** Unified view — full tower */
  null: ['latency', 'sla_risk', 'qos_score', 'samples', 'alerts', 'prb'],
  all: ['latency', 'sla_risk', 'qos_score', 'samples', 'alerts', 'prb'],
  /** Rows where unified CSV column source_bo === BO1 */
  BO1: ['anomaly_rate', 'latency', 'qos_score', 'samples', 'alerts', 'prb'],
  BO2: ['latency', 'mos', 'sla_risk', 'samples', 'alerts'],
  BO3: ['capex', 'critical_zones', 'mos', 'samples', 'alerts'],
};

/**
 * Charts visibility per BO (only metrics that match each objective).
 * line: which series to show on the time-series chart.
 * bar: zone aggregation emphasis for the bar chart.
 */
export const BO_CHART_PROFILE = {
  null: {
    line: ['latency_ms', 'packet_loss_proxy', 'MOS', 'throughput_DL'],
    bar: 'mos',
    pie: true,
  },
  all: {
    line: ['latency_ms', 'packet_loss_proxy', 'MOS', 'throughput_DL'],
    bar: 'mos',
    pie: true,
  },
  BO1: {
    line: ['latency_ms', 'packet_loss_proxy'],
    bar: 'critical',
    pie: true,
  },
  BO2: {
    line: ['latency_ms', 'packet_loss_proxy', 'MOS'],
    bar: 'mos',
    pie: true,
  },
  BO3: {
    line: ['capex_score', 'latency_ms'],
    bar: 'capex',
    pie: true,
  },
};

/**
 * Which “agent” widget IDs render for each BO (see components/agents).
 */
export const BO_AGENT_LAYOUT = {
  null: ['anomaly', 'latency', 'congestion', 'enrichment'],
  all: ['anomaly', 'latency', 'congestion', 'enrichment'],
  BO1: ['anomaly', 'congestion', 'network', 'enrichment'],
  BO2: ['latency', 'network', 'congestion', 'enrichment'],
  BO3: ['capex', 'anomaly', 'congestion', 'enrichment'],
};

export function kpiBlueprintForBo(boId) {
  if (boId == null || boId === '') return BO_KPI_BLUEPRINT.null;
  return BO_KPI_BLUEPRINT[boId] || BO_KPI_BLUEPRINT.null;
}

export function agentLayoutForBo(boId) {
  if (boId == null || boId === '') return BO_AGENT_LAYOUT.null;
  return BO_AGENT_LAYOUT[boId] || BO_AGENT_LAYOUT.null;
}

export function chartProfileForBo(boId) {
  if (boId == null || boId === '') return BO_CHART_PROFILE.null;
  return BO_CHART_PROFILE[boId] || BO_CHART_PROFILE.null;
}
