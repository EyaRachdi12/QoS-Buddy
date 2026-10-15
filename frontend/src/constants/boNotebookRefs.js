/**
 * Alignement explicite avec les notebooks du dépôt (source métier BO1–BO3).
 * Le CSV unifié utilise source_bo=BO1|BO2|BO3 ; les mêmes familles de KPIs
 * que dans ces notebooks sont exposées dans le dashboard.
 */
export const BO_NOTEBOOK_SPECS = {
  BO1: {
    files: ['BO1_Anomaly_Detection_UPDATED.ipynb'],
    headline: 'Détection d’anomalies 4G / eNB — qualité avant impact abonné',
    bullets: [
      'Objectif notebook : anticiper les comportements anormaux (surcharges, évènements) avant dégradation service.',
      'Axes KPI : charge radio (PRB, débits, UE), enrichissement SINR / CQI / handover / ERAB / CSSR comme dans le notebook.',
      'Le dashboard met l’accent sur taux d’anomalie, PRB et santé RAN pour ce périmètre.',
    ],
  },
  BO2: {
    files: ['BO2_QoSBuddy_SLA_UPDATED.ipynb', 'BO2_QoSBuddy_SLA_MOS.ipynb'],
    headline: 'Prévention ruptures SLA B2B et expérience voix/données (MOS)',
    bullets: [
      'Notebook SLA : série TelecomTS — cible construite depuis seuils p10/p90 sur KPIs réels (RSRP, BLER, MCS, NPRB…).',
      'Notebook MOS : Mean Opinion Score dérivé (BLER, RSRP, SINR) — logique proche ITU-T G.107.',
      'Dans l’app : sla_breach_risk, MOS, latence et stress SLA pour les lignes source_bo=BO2.',
    ],
  },
  BO3: {
    files: ['BO3_CAPEX_Zone_UPDATED.ipynb'],
    headline: 'Scoring CAPEX et pilotage des investissements par zone',
    bullets: [
      'Objectif ODS3 / BO3 : prioriser les zones géo avant que la QoS ne baisse.',
      'Variables cœur : score CAPEX 0–100, priorités (ex. URGENT, moyen terme, faible), corrélation avec KPIs réseau par ville.',
      'Le dashboard met en avant capex_score, zones critiques et tendances pour source_bo=BO3.',
    ],
  },
};

export function notebookSpecForBo(boId) {
  if (!boId || !BO_NOTEBOOK_SPECS[boId]) return null;
  return { boId, ...BO_NOTEBOOK_SPECS[boId] };
}
