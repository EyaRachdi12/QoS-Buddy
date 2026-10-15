/**
 * `id` : filtre API `bo_filter` / colonne `source_bo` (null = tout le CSV).
 * `short` : libellé court dans le menu (pas de code BO1/BO2/BO3 pour l’utilisateur).
 * `label` : titre affiché dans le bandeau dashboard.
 */
export const BO_MENU_ITEMS = [
  {
    id: null,
    label: 'Vue unifiée',
    short: 'All',
    description:
      'Synthèse globale du CSV et carte géographique — comparez les zones sans filtre métier.',
  },
  {
    id: 'BO1',
    label: 'Détection d’anomalies',
    short: 'Anomaly',
    description:
      'Anticiper les comportements anormaux (charge eNB, PRB, débits) avant impact abonné — voir notebook Anomaly.',
  },
  {
    id: 'BO2',
    label: 'SLA & expérience (MOS)',
    short: 'SLA & QoS',
    description:
      'Risque de rupture SLA B2B et qualité perçue (MOS) — aligné notebooks SLA & MOS.',
  },
  {
    id: 'BO3',
    label: 'Investissement par zones',
    short: 'Zones & CAPEX',
    description:
      'Scores CAPEX, priorités et pilotage géographique — aligné notebook CAPEX / zones.',
  },
];

/** Entrée menu pour un id API (BO1, BO2, …) ou null (vue All). */
export function menuItemForBo(boId) {
  return BO_MENU_ITEMS.find((b) => b.id === boId) ?? BO_MENU_ITEMS[0];
}
