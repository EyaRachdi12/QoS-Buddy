"""Alert Agent: merge ML detection, predictions, and rule alerts; attach recommendations.

Refinement v2: Time-window deduplication — suppress repeat alerts for the same
(cell_id, issue_type) within a configurable window (default 30 min).
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from sqlalchemy.orm import Session

from services.recommendation_service import recommendations_for_issue, recommendations_from_kpis

# Default dedup window in minutes
DEDUP_WINDOW_MINUTES = 30


def _key(a: Dict[str, Any]) -> Tuple:
    return (
        str(a.get("cell_id", "")),
        str(a.get("issue_type", a.get("source", ""))),
    )


def _parse_timestamp(ts) -> Optional[datetime]:
    if ts is None:
        return None
    if isinstance(ts, datetime):
        return ts
    try:
        return pd.to_datetime(ts)
    except Exception:
        return None


class AlertAgent:

    def __init__(self):
        # Track last alert time per (cell_id, issue_type) for dedup
        self._last_alert_time: Dict[Tuple[str, str], datetime] = {}

    def _is_duplicate(self, alert: Dict[str, Any], window_minutes: int = DEDUP_WINDOW_MINUTES) -> bool:
        """Check if an identical alert was already emitted within the time window."""
        key = _key(alert)
        ts = _parse_timestamp(alert.get("timestamp"))
        now = ts or datetime.utcnow()

        last = self._last_alert_time.get(key)
        if last and (now - last) < timedelta(minutes=window_minutes):
            return True

        self._last_alert_time[key] = now
        return False

    def _cleanup_old_entries(self, max_age_hours: int = 24):
        """Remove stale dedup entries older than max_age_hours."""
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        stale = [k for k, v in self._last_alert_time.items() if v < cutoff]
        for k in stale:
            del self._last_alert_time[k]

    def merge_alerts(
        self,
        rule_alerts: List[Dict[str, Any]],
        if_records: List[Dict[str, Any]],
        prediction_high_risk: Optional[List[Dict[str, Any]]] = None,
        dedup_window_minutes: int = DEDUP_WINDOW_MINUTES,
    ) -> List[Dict[str, Any]]:
        merged: List[Dict[str, Any]] = []
        seen_exact = set()  # exact dedup within this batch

        self._cleanup_old_entries()

        # ── Rule-based alerts ──
        for a in rule_alerts:
            enriched = dict(a)
            it = enriched.get("issue_type")
            recs = enriched.get("recommendations") or []
            if not recs and it:
                recs = recommendations_for_issue(it)
            if recs:
                enriched["recommendations"] = recs

            # Exact dedup within batch
            exact_key = (
                str(enriched.get("cell_id", "")),
                str(enriched.get("issue_type", "")),
                str(enriched.get("timestamp", "")),
            )
            if exact_key in seen_exact:
                continue
            seen_exact.add(exact_key)

            # Time-window dedup across calls
            if self._is_duplicate(enriched, dedup_window_minutes):
                continue

            merged.append(enriched)

        # ── Isolation Forest ML alerts ──
        for r in if_records:
            kpis = r.get("kpis") or {}
            lat = kpis.get("latency_ms")
            prb = kpis.get("PRB_DL") or kpis.get("prb_dl")
            prbu = kpis.get("PRB_UL") or kpis.get("prb_ul")
            extra_recs = recommendations_from_kpis(
                prb_dl=prb, prb_ul=prbu, latency_ms=lat,
                packet_loss_rate=kpis.get("packet_loss_rate"),
            )
            alert = {
                "issue_type": "ML Anomaly (Isolation Forest)",
                "severity": "HIGH" if r.get("if_score", 0) < -0.05 else "MEDIUM",
                "cell_id": r.get("cell_id"),
                "timestamp": r.get("timestamp"),
                "kpis": {**kpis, "if_score": r.get("if_score", kpis.get("if_score"))},
                "causes": [
                    "Score anomalie Isolation Forest sous le seuil",
                    "Combinaison KPI inhabituelle vs distribution recente",
                ],
                "recommendations": extra_recs or [
                    "Analyser correlation PRB / debit / latence sur la cellule",
                    "Verifier evenements reseau concurrents (maintenance, transport)",
                ],
                "priority": 2,
                "source": "detection_ml",
            }
            if "source_bo" in r:
                alert["source_bo"] = r["source_bo"]

            if self._is_duplicate(alert, dedup_window_minutes):
                continue
            merged.append(alert)

        # ── Prediction risk alerts ──
        if prediction_high_risk:
            for p in prediction_high_risk:
                if (p.get("error_pct") or 0) < 25:
                    continue
                alert = {
                    "issue_type": "Prediction Risk (latency)",
                    "severity": "MEDIUM",
                    "cell_id": p.get("cell_id"),
                    "timestamp": p.get("timestamp"),
                    "kpis": {
                        "predicted_latency_ms": p.get("predicted"),
                        "actual_latency_ms": p.get("actual"),
                        "error_pct": p.get("error_pct"),
                    },
                    "causes": ["Ecart important entre latence predite et observee"],
                    "recommendations": recommendations_from_kpis(
                        latency_ms=p.get("actual") or p.get("predicted")
                    ),
                    "priority": 3,
                    "source": "prediction_ml",
                }
                if self._is_duplicate(alert, dedup_window_minutes):
                    continue
                merged.append(alert)

        merged.sort(key=lambda x: x.get("priority", 9))
        return merged

    def persist_alerts(self, db: Session, alerts: List[Dict[str, Any]], limit: int = 500) -> int:
        from database import Alert as AlertORM

        n = 0
        for a in alerts[:limit]:
            ts = a.get("timestamp")
            if isinstance(ts, str):
                try:
                    ts_parsed = pd.to_datetime(ts)
                except Exception:
                    ts_parsed = datetime.utcnow()
            else:
                ts_parsed = datetime.utcnow()
            row = AlertORM(
                cell_id=str(a.get("cell_id", "")),
                timestamp=ts_parsed,
                issue_type=str(a.get("issue_type", "")),
                severity=str(a.get("severity", "")),
                kpis=a.get("kpis"),
                causes=a.get("causes"),
                recommendations=a.get("recommendations"),
                priority=int(a.get("priority", 0)),
            )
            db.add(row)
            n += 1
        db.commit()
        return n
