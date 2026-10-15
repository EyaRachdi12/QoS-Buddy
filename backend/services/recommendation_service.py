"""
Rule-based recommendations by congestion, latency, packet loss, and issue type.
Shared by Alert pipeline and chat context.
"""

from __future__ import annotations

from typing import Dict, List, Optional

# Mirrors DiagnosticAgent issue types -> same action lists (centralized)
RECOMMENDATIONS_BY_ISSUE: Dict[str, List[str]] = {
    "Capacity Problem": [
        "URGENT: Ajouter carrier",
        "Activer Carrier Aggregation (CA)",
        "Considérer sectorisation 3 → 6",
        "Activer Massive MIMO",
        "Implémenter load balancing inter-cellule",
    ],
    "High Latency": [
        "Optimiser buffers réseau",
        "Vérifier routage IP",
        "Vérifier configuration MTU",
        "Optimiser scheduling",
        "Considérer local breakout",
    ],
    "Call Drop": [
        "Optimiser tilt mécanique/électrique",
        "Ajuster puissance cellule",
        "Vérifier et optimiser liste voisins",
        "Analyser paramètres handover",
    ],
    "Handover Failure": [
        "Vérifier et nettoyer plan PCI",
        "Optimiser A3 offset",
        "Ajuster TTT (Time-To-Trigger)",
        "Auditer relations de voisinage",
    ],
    "Low Throughput": [
        "Optimiser tilt antenne",
        "Activer Carrier Aggregation (CA)",
        "Vérifier configuration MIMO",
        "Optimiser paramètres CQI",
    ],
    "Low MOS (Voice Quality)": [
        "Activer AMR adaptatif",
        "Optimiser puissance UL",
        "Ajuster scheduler priorité VoLTE",
        "Vérifier couverture indoor",
    ],
    "Session Drop": [
        "Optimiser seuils handover",
        "Ajuster timer T310",
        "Considérer ajout cellule 800 MHz",
        "Analyser drive test logs (événements L3)",
    ],
}

CONGESTION_RECOMMENDATIONS = RECOMMENDATIONS_BY_ISSUE["Capacity Problem"]
LATENCY_RECOMMENDATIONS = RECOMMENDATIONS_BY_ISSUE["High Latency"]
PACKET_LOSS_RECOMMENDATIONS = [
    "Vérifier configuration RLC/PDCP et rétransmissions",
    "Analyser qualité lien transport et pertes IP",
    "Optimiser scheduling et priorité QoS par bearer",
    "Contrôler interférences et planification MU-MIMO",
]


def recommendations_for_issue(issue_type: Optional[str]) -> List[str]:
    if not issue_type:
        return []
    return list(RECOMMENDATIONS_BY_ISSUE.get(issue_type, []))


def recommendations_from_kpis(
    *,
    prb_dl: Optional[float] = None,
    prb_ul: Optional[float] = None,
    latency_ms: Optional[float] = None,
    packet_loss_rate: Optional[float] = None,
) -> List[str]:
    """Heuristic buckets for live KPIs (thresholds aligned with DiagnosticAgent)."""
    out: List[str] = []
    prb_max = None
    if prb_dl is not None and prb_ul is not None:
        prb_max = max(prb_dl, prb_ul)
    elif prb_dl is not None:
        prb_max = prb_dl
    elif prb_ul is not None:
        prb_max = prb_ul

    if prb_max is not None and prb_max > 85:
        out.extend(CONGESTION_RECOMMENDATIONS[:3])

    if latency_ms is not None and latency_ms > 150:
        out.extend(LATENCY_RECOMMENDATIONS[:3])

    if packet_loss_rate is not None and packet_loss_rate >= 2.5:
        out.extend(PACKET_LOSS_RECOMMENDATIONS)

    # Dedupe preserving order
    seen = set()
    deduped = []
    for r in out:
        if r not in seen:
            seen.add(r)
            deduped.append(r)
    return deduped
