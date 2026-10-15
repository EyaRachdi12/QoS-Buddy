"""
Agent 2: Autonomous Diagnostic Worker
Real-time KPI monitoring, anomaly detection, and alert generation

Refinements v2:
- Compound issue detection (correlated alerts on same cell)
- Severity escalation over time (persistent issues auto-escalate)
- Cell health score (0-100 composite score)
- Root cause analysis chain (symptom vs root cause)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
import joblib
import os
import json
from pathlib import Path

from core.filled_transform import apply_filled_column_mapping, finalize_diagnostic_dataframe
from core.config import KPI_THRESHOLDS, BUSY_HOURS


# ── Root Cause Graph ──
# Maps issue_type -> list of issues it commonly *causes* (downstream symptoms).
# If root cause X is present alongside symptom Y, Y is demoted.

ROOT_CAUSE_GRAPH = {
    "Capacity Problem": ["Low Throughput", "High Latency", "Low MOS (Voice Quality)"],
    "Call Drop": ["Session Drop"],
    "Handover Failure": ["Call Drop", "Session Drop"],
}

# Compound issue patterns: when these co-occur on one cell, emit a compound alert
COMPOUND_PATTERNS = {
    "Coverage Hole": {
        "requires": ["Call Drop", "Session Drop"],
        "optional": ["Handover Failure"],
        "severity": "CRITICAL",
        "description": "Coverage hole detected — multiple signal-related failures co-occurring",
        "recommendations": [
            "Analyse drive test pour confirmer trou de couverture",
            "Considerer ajout site / small cell 800 MHz",
            "Verifier tilt et azimut des cellules voisines",
            "Optimiser seuils handover inter-frequence",
        ],
    },
    "Congestion Cascade": {
        "requires": ["Capacity Problem", "Low Throughput"],
        "optional": ["High Latency", "Low MOS (Voice Quality)"],
        "severity": "CRITICAL",
        "description": "Congestion cascade — PRB saturation causing throughput/latency/voice degradation",
        "recommendations": [
            "URGENT: Ajouter carrier ou activer CA",
            "Activer Massive MIMO",
            "Implementer load balancing inter-cellule",
            "Considerer sectorisation 3 -> 6",
            "Prioriser trafic VoLTE dans scheduler",
        ],
    },
    "Interference Storm": {
        "requires": ["Handover Failure", "Low Throughput"],
        "optional": ["Low MOS (Voice Quality)"],
        "severity": "HIGH",
        "description": "Interference pattern — handover failures + throughput degradation suggest PCI/overshooting issues",
        "recommendations": [
            "Verifier et nettoyer plan PCI",
            "Analyser overshooting cells",
            "Optimiser A3 offset et TTT",
            "Verifier interferences co-canal et canal adjacent",
        ],
    },
}

# ── Health Score Weights ──
# Each KPI contributes to a 0-100 cell health score

HEALTH_WEIGHTS = {
    "RSRP":                  {"weight": 0.15, "good": -80, "bad": -115, "higher_is_better": True},
    "SINR":                  {"weight": 0.12, "good": 20,  "bad": 0,    "higher_is_better": True},
    "PRB_DL":                {"weight": 0.12, "good": 50,  "bad": 95,   "higher_is_better": False},
    "throughput_DL":         {"weight": 0.12, "good": 80,  "bad": 5,    "higher_is_better": True},
    "latency_ms":            {"weight": 0.12, "good": 20,  "bad": 200,  "higher_is_better": False},
    "MOS":                   {"weight": 0.12, "good": 4.5, "bad": 1.5,  "higher_is_better": True},
    "handover_success_rate": {"weight": 0.15, "good": 99,  "bad": 80,   "higher_is_better": True},
    "call_drop_rate":        {"weight": 0.10, "good": 0,   "bad": 8,    "higher_is_better": False},
}


def _compute_health_score(row: pd.Series) -> float:
    """Compute a 0-100 composite health score for a single record."""
    total = 0.0
    weight_sum = 0.0
    for col, cfg in HEALTH_WEIGHTS.items():
        if col not in row or pd.isna(row[col]):
            continue
        val = float(row[col])
        good = cfg["good"]
        bad = cfg["bad"]
        w = cfg["weight"]

        if cfg["higher_is_better"]:
            # Score: 0 at bad, 100 at good
            if good == bad:
                score = 50.0
            else:
                score = (val - bad) / (good - bad) * 100.0
        else:
            # Score: 100 at good, 0 at bad
            if good == bad:
                score = 50.0
            else:
                score = (bad - val) / (bad - good) * 100.0

        score = max(0.0, min(100.0, score))
        total += score * w
        weight_sum += w

    return round(total / weight_sum, 1) if weight_sum > 0 else 50.0


class DiagnosticAgent:
    COUNTRY_COORDINATES = {
        "united states": (39.8283, -98.5795),
        "usa": (39.8283, -98.5795),
        "france": (46.2276, 2.2137),
        "united kingdom": (55.3781, -3.4360),
        "uk": (55.3781, -3.4360),
        "netherlands": (52.1326, 5.2913),
        "japan": (36.2048, 138.2529),
        "south korea": (35.9078, 127.7669),
        "singapore": (1.3521, 103.8198),
        "hong kong": (22.3193, 114.1694),
        "united arab emirates": (23.4241, 53.8478),
        "uae": (23.4241, 53.8478),
        "india": (20.5937, 78.9629),
        "brazil": (-14.2350, -51.9253),
    }

    """
    Agent 2: Diagnostic Worker
    Monitors KPIs, detects issues, generates alerts automatically
    """

    def __init__(self, data_path: str = None):
        repo_root = Path(__file__).resolve().parent.parent
        default_processed = repo_root / "data" / "processed" / "network_kpis_full.csv"
        default_filled = Path(__file__).resolve().parent / "unified_telecom_dataset_FILLED.csv"
        self.data_path = str(data_path) if data_path else str(default_filled if default_filled.exists() else default_processed)
        self.alerts = []
        self.models = {}

        # Thresholds loaded from core.config (externalized for easy tuning)
        self.thresholds = KPI_THRESHOLDS
        self.busy_hours = BUSY_HOURS

        # Severity escalation: track persistent issues per cell
        # key = (cell_id, issue_type), value = list of timestamps
        self._issue_history: Dict[Tuple[str, str], List[datetime]] = defaultdict(list)

        self.load_models()

    def load_models(self):
        model_dir = '../models/'
        model_files = {
            'anomaly_detector': 'anomaly_detector.pkl',
            'sla_predictor': 'sla_predictor.pkl',
            'zone_scorer': 'zone_scorer.pkl'
        }
        for model_name, filename in model_files.items():
            model_path = os.path.join(model_dir, filename)
            if os.path.exists(model_path):
                try:
                    self.models[model_name] = joblib.load(model_path)
                    print(f"  Loaded model: {model_name}")
                except Exception as e:
                    print(f"  Error loading {model_name}: {e}")

    def load_data(self) -> Optional[pd.DataFrame]:
        try:
            df = pd.read_csv(self.data_path)
            filled_cols = set(df.columns)
            is_filled = (
                "risk_tier" in filled_cols
                or "RSRP_dBm" in filled_cols
                or "signal_strength_dbm" in filled_cols
            )
            if is_filled:
                df = self._transform_filled_dataset(df)
            else:
                if "timestamp" in df.columns:
                    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
            return df
        except FileNotFoundError:
            print(f"  Data file not found: {self.data_path}")
            return None

    def _transform_filled_dataset(self, df: pd.DataFrame) -> pd.DataFrame:
        df = apply_filled_column_mapping(df)
        return finalize_diagnostic_dataframe(df)

    def _city_to_coordinates(self, city: str) -> Optional[Dict[str, float]]:
        """Return known coordinates for city-level map plotting."""
        known = {
            "New York": (40.7128, -74.0060),
            "Los Angeles": (34.0522, -118.2437),
            "Chicago": (41.8781, -87.6298),
            "Houston": (29.7604, -95.3698),
            "Phoenix": (33.4484, -112.0740),
            "Dallas": (32.7767, -96.7970),
            "San Diego": (32.7157, -117.1611),
            "San Antonio": (29.4241, -98.4936),
            "London": (51.5074, -0.1278),
            "Paris": (48.8566, 2.3522),
            "Amsterdam": (52.3676, 4.9041),
            "Tokyo": (35.6762, 139.6503),
            "Seoul": (37.5665, 126.9780),
            "Singapore": (1.3521, 103.8198),
            "Hong Kong": (22.3193, 114.1694),
            "Dubai": (25.2048, 55.2708),
            "Mumbai": (19.0760, 72.8777),
            "Sao Paulo": (-23.5505, -46.6333),
            "Bangalore": (12.9716, 77.5946),
            "Sydney": (-33.8688, 151.2093),
            "Toronto": (43.6532, -79.3832),
            "Bangkok": (13.7563, 100.5018),
            "Delhi": (28.6139, 77.2090),
            "Jacksonville": (30.3322, -81.6557),
            "Mexico City": (19.4326, -99.1332),
            "Berlin": (52.5200, 13.4050),
            "Madrid": (40.4168, -3.7038),
            "Buenos Aires": (-34.6037, -58.3816),
            "San Jose": (37.3382, -121.8863),
            "Austin": (30.2672, -97.7431),
            "Philadelphia": (39.9526, -75.1652),
            # Nigeria / Africa
            "Lagos": (6.5244, 3.3792),
            "Abuja": (9.0765, 7.3986),
            "Kano": (12.0022, 8.5920),
            "Ibadan": (7.3775, 3.9470),
            "Port Harcourt": (4.8156, 7.0498),
            "Benin City": (6.3350, 5.6037),
            "Kaduna": (10.5222, 7.4383),
            "Enugu": (6.4402, 7.4943),
            "Ilorin": (8.4966, 4.5421),
            "Aba": (5.1066, 7.3667),
            "Jos": (9.8965, 8.8583),
            "Calabar": (4.9517, 8.3220),
            "Abeokuta": (7.1608, 3.3483),
            "Onitsha": (6.1498, 6.7857),
            "Warri": (5.5544, 5.7932),
        }
        if city in known:
            lat, lon = known[city]
            return {"lat": lat, "lon": lon}

        # Unknown city: prefer hiding point rather than wrong placement.
        return None

    def _country_to_coordinates(self, country: str) -> Optional[Dict[str, float]]:
        if not country:
            return None
        key = str(country).strip().lower()
        coords = self.COUNTRY_COORDINATES.get(key)
        if not coords:
            return None
        lat, lon = coords
        return {"lat": float(lat), "lon": float(lon)}

    def _city_to_country(self, city: str) -> Optional[str]:
        if not city:
            return None
        city_map = {
            "New York": "United States",
            "Los Angeles": "United States",
            "Chicago": "United States",
            "Houston": "United States",
            "Phoenix": "United States",
            "Dallas": "United States",
            "San Diego": "United States",
            "San Antonio": "United States",
            "San Jose": "United States",
            "Austin": "United States",
            "Philadelphia": "United States",
            "Jacksonville": "United States",
            "London": "United Kingdom",
            "Paris": "France",
            "Amsterdam": "Netherlands",
            "Tokyo": "Japan",
            "Seoul": "South Korea",
            "Singapore": "Singapore",
            "Hong Kong": "Hong Kong",
            "Dubai": "United Arab Emirates",
            "Mumbai": "India",
            "Delhi": "India",
            "Bangalore": "India",
            "Sao Paulo": "Brazil",
            "Toronto": "Canada",
            "Sydney": "Australia",
            "Bangkok": "Thailand",
            "Mexico City": "Mexico",
            "Berlin": "Germany",
            "Madrid": "Spain",
            "Buenos Aires": "Argentina",
            "Lagos": "Nigeria",
            "Abuja": "Nigeria",
            "Kano": "Nigeria",
            "Ibadan": "Nigeria",
            "Port Harcourt": "Nigeria",
            "Benin City": "Nigeria",
            "Kaduna": "Nigeria",
            "Enugu": "Nigeria",
            "Ilorin": "Nigeria",
            "Aba": "Nigeria",
            "Jos": "Nigeria",
            "Calabar": "Nigeria",
            "Abeokuta": "Nigeria",
            "Onitsha": "Nigeria",
            "Warri": "Nigeria",
        }
        return city_map.get(str(city).strip())

    def _resolve_zone_coordinates(self, row: pd.Series) -> Optional[Dict[str, float]]:
        """
        Prefer dataset geo columns; fallback to known country; then known city.
        """
        lat = pd.to_numeric(row.get("avg_lat", pd.NA), errors="coerce")
        lon = pd.to_numeric(row.get("avg_lon", pd.NA), errors="coerce")
        if pd.notna(lat) and pd.notna(lon):
            return {"lat": float(lat), "lon": float(lon)}

        country_coords = self._country_to_coordinates(str(row.get("country", "")).strip())
        if country_coords:
            return country_coords

        return self._city_to_coordinates(str(row.get("zone", "")))

    def _jitter_coordinates(self, lat: float, lon: float, key: str, scale_deg: float = 0.35) -> Dict[str, float]:
        """Deterministic micro-offset so multiple bubbles are visible per city/country."""
        h = abs(hash(str(key)))
        dlat = ((h % 1000) / 1000.0 - 0.5) * 2 * scale_deg
        dlon = (((h // 1000) % 1000) / 1000.0 - 0.5) * 2 * scale_deg
        out_lat = max(min(lat + dlat, 89.9), -89.9)
        out_lon = lon + dlon
        if out_lon > 180:
            out_lon -= 360
        if out_lon < -180:
            out_lon += 360
        return {"lat": round(out_lat, 6), "lon": round(out_lon, 6)}

    # ── Cell Health Score ──

    def compute_cell_health(self, df: pd.DataFrame) -> Dict[str, Dict]:
        """Compute composite health score for each cell."""
        if df is None or df.empty or "cell_id" not in df.columns:
            return {}

        results = {}
        for cell_id, group in df.groupby("cell_id"):
            latest = group.iloc[-1]
            score = _compute_health_score(latest)

            # Status based on score
            if score >= 80:
                status = "HEALTHY"
            elif score >= 60:
                status = "DEGRADED"
            elif score >= 40:
                status = "POOR"
            else:
                status = "CRITICAL"

            results[cell_id] = {
                "health_score": score,
                "status": status,
                "kpis": {
                    col: float(latest[col])
                    for col in HEALTH_WEIGHTS
                    if col in latest and pd.notna(latest[col])
                },
            }
        return results

    # ── Severity Escalation ──

    def _check_escalation(self, cell_id: str, issue_type: str, current_severity: str) -> str:
        """Escalate severity if the same issue persists on the same cell over time."""
        key = (str(cell_id), issue_type)
        now = datetime.now()
        self._issue_history[key].append(now)

        # Keep only last 24h of history
        cutoff = now - timedelta(hours=24)
        self._issue_history[key] = [t for t in self._issue_history[key] if t > cutoff]

        count = len(self._issue_history[key])

        # Escalation rules
        if current_severity == "MEDIUM" and count >= 5:
            return "HIGH"
        if current_severity == "HIGH" and count >= 10:
            return "CRITICAL"

        return current_severity

    # ── Root Cause Analysis ──

    def _analyze_root_causes(self, cell_alerts: List[Dict]) -> List[Dict]:
        """
        Given alerts for a single cell, identify root causes vs symptoms.
        Demote symptoms and tag root causes.
        """
        if len(cell_alerts) <= 1:
            return cell_alerts

        issue_types = {a["issue_type"] for a in cell_alerts}

        for alert in cell_alerts:
            it = alert["issue_type"]
            # Check if this issue is a known root cause
            downstream = ROOT_CAUSE_GRAPH.get(it, [])
            if downstream:
                symptoms_present = [s for s in downstream if s in issue_types]
                if symptoms_present:
                    alert["is_root_cause"] = True
                    alert["explains"] = symptoms_present

            # Check if this issue is a symptom of something else
            for root, symptoms in ROOT_CAUSE_GRAPH.items():
                if it in symptoms and root in issue_types:
                    alert["is_symptom_of"] = root
                    # Don't lower priority if it's already low
                    alert["priority"] = max(alert.get("priority", 2), 3)

        return cell_alerts

    # ── Compound Issue Detection ──

    def _detect_compound_issues(self, cell_alerts: List[Dict], cell_id: str) -> List[Dict]:
        """Check if alerts on a single cell match a known compound pattern."""
        issue_types = {a["issue_type"] for a in cell_alerts}
        compounds = []

        for pattern_name, pattern in COMPOUND_PATTERNS.items():
            required = set(pattern["requires"])
            if required.issubset(issue_types):
                optional_present = [o for o in pattern.get("optional", []) if o in issue_types]
                compounds.append({
                    "issue_type": f"Compound: {pattern_name}",
                    "severity": pattern["severity"],
                    "cell_id": cell_id,
                    "timestamp": cell_alerts[0]["timestamp"] if cell_alerts else str(datetime.now()),
                    "kpis": {},
                    "causes": [
                        pattern["description"],
                        f"Co-occurring issues: {', '.join(required)}",
                    ] + ([f"Also present: {', '.join(optional_present)}"] if optional_present else []),
                    "recommendations": pattern["recommendations"],
                    "priority": 0,
                    "is_compound": True,
                    "component_issues": list(required | set(optional_present)),
                })

        return compounds

    # ── Individual Detectors ──

    def detect_call_drop(self, row: pd.Series) -> Optional[Dict]:
        if (row['RSRP'] < self.thresholds['RSRP']['critical'] and
            row['handover_success_rate'] < self.thresholds['handover_success_rate']['critical']):
            return {
                'issue_type': 'Call Drop', 'severity': 'HIGH',
                'cell_id': row['cell_id'], 'timestamp': row['timestamp'],
                'kpis': {'RSRP': row['RSRP'], 'SINR': row['SINR'], 'HO_success_rate': row['handover_success_rate']},
                'causes': ['Mauvais niveau signal (RSRP < -110 dBm)', 'Taux de succes handover faible (< 85%)', 'Possible overshooting ou mauvais voisinage'],
                'recommendations': ['Optimiser tilt mecanique/electrique', 'Ajuster puissance cellule', 'Verifier et optimiser liste voisins', 'Analyser parametres handover'],
                'priority': 1
            }
        return None

    def detect_low_mos(self, row: pd.Series) -> Optional[Dict]:
        if (row['MOS'] < self.thresholds['MOS']['poor'] and
            row['BLER_UL'] > self.thresholds['BLER']['moderate']):
            return {
                'issue_type': 'Low MOS (Voice Quality)', 'severity': 'MEDIUM',
                'cell_id': row['cell_id'], 'timestamp': row['timestamp'],
                'kpis': {'MOS': row['MOS'], 'BLER_UL': row['BLER_UL'], 'BLER_DL': row['BLER_DL'], 'PRB_DL': row['PRB_DL']},
                'causes': [f'MOS faible ({row["MOS"]:.2f} < 3.0)', f'BLER eleve ({row["BLER_UL"]:.1f}% uplink)', 'Possibles interferences ou congestion PRB'],
                'recommendations': ['Activer AMR adaptatif', 'Optimiser puissance UL', 'Ajuster scheduler priorite VoLTE', 'Verifier couverture indoor'],
                'priority': 2
            }
        return None

    def detect_low_throughput(self, row: pd.Series) -> Optional[Dict]:
        if (row['throughput_DL'] < self.thresholds['throughput_DL']['poor'] and
            row['SINR'] < self.thresholds['SINR']['poor']):
            return {
                'issue_type': 'Low Throughput', 'severity': 'MEDIUM',
                'cell_id': row['cell_id'], 'timestamp': row['timestamp'],
                'kpis': {'throughput_DL': row['throughput_DL'], 'SINR': row['SINR'], 'CQI': row['CQI'], 'PRB_DL': row['PRB_DL']},
                'causes': [f'Debit DL faible ({row["throughput_DL"]:.1f} Mbps)', f'SINR faible ({row["SINR"]:.1f} dB)', 'Possibles interferences ou congestion'],
                'recommendations': ['Optimiser tilt antenne', 'Activer Carrier Aggregation (CA)', 'Verifier configuration MIMO', 'Optimiser parametres CQI'],
                'priority': 2
            }
        return None

    def detect_high_latency(self, row: pd.Series) -> Optional[Dict]:
        if (row['latency_ms'] > self.thresholds['latency_ms']['poor'] and
            row['RLC_retransmissions'] > 10):
            return {
                'issue_type': 'High Latency', 'severity': 'MEDIUM',
                'cell_id': row['cell_id'], 'timestamp': row['timestamp'],
                'kpis': {'latency_ms': row['latency_ms'], 'RLC_retransmissions': row['RLC_retransmissions']},
                'causes': [f'Latence elevee ({row["latency_ms"]:.0f} ms)', 'Retransmissions RLC excessives', 'Possible congestion transport ou bufferbloat'],
                'recommendations': ['Optimiser buffers reseau', 'Verifier routage IP', 'Verifier configuration MTU', 'Optimiser scheduling', 'Considerer local breakout'],
                'priority': 2
            }
        return None

    def detect_session_drop(self, row: pd.Series) -> Optional[Dict]:
        if row['RSRP'] < -115 and row['handover_success_rate'] < 90:
            return {
                'issue_type': 'Session Drop', 'severity': 'HIGH',
                'cell_id': row['cell_id'], 'timestamp': row['timestamp'],
                'kpis': {'RSRP': row['RSRP'], 'handover_success_rate': row['handover_success_rate']},
                'causes': ['Coverage hole detecte (RSRP < -115 dBm)', 'Handover inter-frequence problematique', 'Possible ERAB drop'],
                'recommendations': ['Optimiser seuils handover', 'Ajuster timer T310', 'Considerer ajout cellule 800 MHz', 'Analyser drive test logs (evenements L3)'],
                'priority': 1
            }
        return None

    def detect_handover_failure(self, row: pd.Series) -> Optional[Dict]:
        if row['handover_success_rate'] < self.thresholds['handover_success_rate']['critical']:
            return {
                'issue_type': 'Handover Failure', 'severity': 'HIGH',
                'cell_id': row['cell_id'], 'timestamp': row['timestamp'],
                'kpis': {'handover_success_rate': row['handover_success_rate'], 'RSRP': row['RSRP']},
                'causes': [f'Taux succes HO tres faible ({row["handover_success_rate"]:.1f}%)', 'Possible mauvaise definition voisins', 'Possible overshooting cell ou confusion PCI'],
                'recommendations': ['Verifier et nettoyer plan PCI', 'Optimiser A3 offset', 'Ajuster TTT (Time-To-Trigger)', 'Auditer relations de voisinage'],
                'priority': 1
            }
        return None

    def detect_capacity_issue(self, row: pd.Series) -> Optional[Dict]:
        prb_max = max(row['PRB_UL'], row['PRB_DL'])
        is_busy_hour = row['hour'] in self.busy_hours
        if prb_max > self.thresholds['PRB']['moderate']:
            severity = 'CRITICAL' if (is_busy_hour and prb_max > 90) else 'HIGH'
            return {
                'issue_type': 'Capacity Problem', 'severity': severity,
                'cell_id': row['cell_id'], 'timestamp': row['timestamp'],
                'kpis': {'PRB_UL': row['PRB_UL'], 'PRB_DL': row['PRB_DL'], 'throughput_DL': row['throughput_DL'], 'hour': row['hour']},
                'causes': [f'PRB congestion severe (DL: {row["PRB_DL"]:.1f}%, UL: {row["PRB_UL"]:.1f}%)',
                           'Capacite insuffisante' + (' pendant busy hour' if is_busy_hour else ''), 'Degradation debit probable'],
                'recommendations': ['URGENT: Ajouter carrier', 'Activer Carrier Aggregation (CA)', 'Considerer sectorisation 3 -> 6', 'Activer Massive MIMO', 'Implementer load balancing inter-cellule'],
                'priority': 0 if severity == 'CRITICAL' else 1
            }
        return None

    # ── Analysis Pipeline ──

    def analyze_record(self, row: pd.Series) -> List[Dict]:
        alerts = []
        detectors = [
            self.detect_call_drop, self.detect_low_mos, self.detect_low_throughput,
            self.detect_high_latency, self.detect_session_drop,
            self.detect_handover_failure, self.detect_capacity_issue,
        ]
        for detector in detectors:
            alert = detector(row)
            if alert:
                # Apply severity escalation
                alert['severity'] = self._check_escalation(
                    alert['cell_id'], alert['issue_type'], alert['severity']
                )
                alerts.append(alert)
        return alerts

    def analyze_batch(self, df: pd.DataFrame, time_window_hours: int = 1) -> List[Dict]:
        """Analyze recent records with compound detection + root cause analysis."""
        if 'timestamp' not in df.columns:
            return []

        latest_time = df['timestamp'].max()
        cutoff_time = latest_time - timedelta(hours=time_window_hours)
        recent_df = df[df['timestamp'] >= cutoff_time]

        # Step 1: Run individual detectors on each row
        all_alerts = []
        for idx, row in recent_df.iterrows():
            alerts = self.analyze_record(row)
            all_alerts.extend(alerts)

        # Step 2: Group by cell for compound + root cause analysis
        cell_groups: Dict[str, List[Dict]] = defaultdict(list)
        for alert in all_alerts:
            cell_groups[str(alert['cell_id'])].append(alert)

        enhanced_alerts = []
        for cell_id, cell_alerts in cell_groups.items():
            # Root cause analysis
            cell_alerts = self._analyze_root_causes(cell_alerts)

            # Compound issue detection
            compounds = self._detect_compound_issues(cell_alerts, cell_id)
            enhanced_alerts.extend(compounds)
            enhanced_alerts.extend(cell_alerts)

        enhanced_alerts.sort(key=lambda x: x.get('priority', 9))
        return enhanced_alerts

    # ── Public API ──

    def get_latest_alerts(self, n: int = 20) -> List[Dict]:
        df = self.load_data()
        if df is None:
            return []
        alerts = self.analyze_batch(df, time_window_hours=1)
        return alerts[:n]

    def get_cell_status(self, cell_id: str) -> Dict:
        df = self.load_data()
        if df is None:
            return {'error': 'Data not available'}
        cell_data = df[df['cell_id'] == cell_id]
        if cell_data.empty:
            return {'error': f'Cell {cell_id} not found'}

        latest_record = cell_data.iloc[-1]
        alerts = self.analyze_record(latest_record)
        health = _compute_health_score(latest_record)
        status = 'NORMAL' if not alerts else alerts[0]['severity']

        return {
            'cell_id': cell_id,
            'status': status,
            'health_score': health,
            'last_update': str(latest_record['timestamp']),
            'kpis': {
                col: float(latest_record[col])
                for col in ['RSRP', 'SINR', 'PRB_DL', 'PRB_UL', 'throughput_DL', 'MOS', 'latency_ms', 'handover_success_rate']
                if col in latest_record and pd.notna(latest_record[col])
            },
            'alerts': alerts,
        }

    def get_cell_diagnostic_context(self, cell_id: str) -> str:
        """Produce a compact text summary for Agent 1 chat context."""
        status = self.get_cell_status(cell_id)
        if "error" in status:
            return f"Cell {cell_id}: {status['error']}"

        lines = [
            f"Cell {cell_id} — Status: {status['status']} | Health: {status['health_score']}/100",
        ]
        kpis = status.get("kpis", {})
        if kpis:
            kpi_str = ", ".join(f"{k}={v:.1f}" for k, v in kpis.items())
            lines.append(f"KPIs: {kpi_str}")
        for a in status.get("alerts", [])[:3]:
            tag = "[ROOT CAUSE] " if a.get("is_root_cause") else ""
            lines.append(f"  Alert: {tag}{a['issue_type']} ({a['severity']}) — {a['causes'][0]}")
        return "\n".join(lines)

    def get_realtime_kpis(self, limit: int = 100) -> List[Dict]:
        df = self.load_data()
        if df is None:
            return []
        recent = df.tail(limit)
        kpis = []
        for _, row in recent.iterrows():
            entry = {
                'timestamp': str(row['timestamp']),
                'cell_id': row['cell_id'],
                'RSRP': float(row['RSRP']),
                'SINR': float(row['SINR']),
                'PRB_DL': float(row['PRB_DL']),
                'throughput_DL': float(row['throughput_DL']),
                'MOS': float(row['MOS']),
                'latency_ms': float(row['latency_ms']),
            }
            # Add health score
            entry['health_score'] = _compute_health_score(row)
            kpis.append(entry)
        return kpis

    def generate_summary_report(self) -> Dict:
        df = self.load_data()
        if df is None:
            return {'error': 'Data not available'}

        alerts = self.analyze_batch(df, time_window_hours=24)
        critical_alerts = [a for a in alerts if a['severity'] == 'CRITICAL']
        high_alerts = [a for a in alerts if a['severity'] == 'HIGH']
        medium_alerts = [a for a in alerts if a['severity'] == 'MEDIUM']
        compound_alerts = [a for a in alerts if a.get('is_compound')]

        issue_counts = {}
        for alert in alerts:
            issue_type = alert['issue_type']
            issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1

        cells_with_issues = set(a['cell_id'] for a in alerts)

        # Cell health summary
        health_data = self.compute_cell_health(df)
        health_dist = defaultdict(int)
        for ch in health_data.values():
            health_dist[ch["status"]] += 1

        return {
            'timestamp': str(datetime.now()),
            'total_alerts': len(alerts),
            'critical': len(critical_alerts),
            'high': len(high_alerts),
            'medium': len(medium_alerts),
            'compound_issues': len(compound_alerts),
            'cells_monitored': int(df['cell_id'].nunique()),
            'cells_with_issues': len(cells_with_issues),
            'issue_breakdown': issue_counts,
            'health_distribution': dict(health_dist),
            'top_alerts': alerts[:10],
        }

    def get_bo_integrated_overview(
        self,
        time_window_hours: int = 24,
        max_zones: int = 120,
        bo_filter: Optional[str] = None,
    ) -> Dict:
        df = self.load_data()
        if df is None or df.empty:
            return {"error": "Data not available"}

        if bo_filter and "source_bo" in df.columns:
            df = df[df["source_bo"].astype(str) == str(bo_filter)]
        if df.empty:
            return {"error": "No data for selected filter"}

        if "timestamp" in df.columns:
            latest_time = df["timestamp"].max()
            cutoff_time = latest_time - timedelta(hours=time_window_hours)
            recent_df = df[df["timestamp"] >= cutoff_time].copy()
        else:
            recent_df = df.copy()

        # BO1 - anomaly monitoring
        anomaly_flag = pd.to_numeric(recent_df.get("anomaly_flag", 0), errors="coerce").fillna(0)
        anomaly_count = int((anomaly_flag > 0).sum())
        bo1 = {
            "records": int(len(recent_df)),
            "anomalies": anomaly_count,
            "anomaly_rate_pct": round((anomaly_count / max(len(recent_df), 1)) * 100, 2),
            "high_risk_cells": int(recent_df[recent_df.get("risk_tier", "").isin(["CRITICAL"])].get("cell_id", pd.Series(dtype=object)).nunique()) if "risk_tier" in recent_df.columns else 0,
        }

        # BO2 - SLA/MOS
        sla = pd.to_numeric(recent_df.get("sla_breach_risk", pd.NA), errors="coerce")
        mos = pd.to_numeric(recent_df.get("MOS", pd.NA), errors="coerce")
        bo2 = {
            "avg_sla_breach_risk": round(float(sla.mean()), 4) if sla.notna().any() else None,
            "high_sla_risk_count": int((sla >= 0.7).sum()) if sla.notna().any() else 0,
            "avg_mos": round(float(mos.mean()), 3) if mos.notna().any() else None,
            "low_mos_count": int((mos < 3.0).sum()) if mos.notna().any() else 0,
        }

        # BO3 - CAPEX zone prioritization
        capex = pd.to_numeric(recent_df.get("capex_score", pd.NA), errors="coerce")
        bo3 = {
            "avg_capex_score": round(float(capex.mean()), 2) if capex.notna().any() else None,
            "urgent_count": int((recent_df.get("capex_priority", pd.Series(dtype=object)).astype(str).isin(["5", "URGENT", "Urgent", "urgent"])).sum()) if "capex_priority" in recent_df.columns else 0,
            "critical_risk_count": int((recent_df.get("risk_tier", pd.Series(dtype=object)).astype(str) == "CRITICAL").sum()) if "risk_tier" in recent_df.columns else 0,
        }

        # Trend samples
        trend_cols = ["timestamp", "RSRP", "SINR", "PRB_DL", "throughput_DL", "latency_ms", "MOS", "sla_breach_risk", "capex_score"]
        trend_cols = [c for c in trend_cols if c in recent_df.columns]
        trends = recent_df[trend_cols].tail(180).copy()
        if "timestamp" in trends.columns:
            trends["timestamp"] = trends["timestamp"].astype(str)
        trend_data = trends.to_dict("records")

        # Zone map data by city/country.
        # Use a wider lookback than KPI cards so map keeps geographic coverage (e.g., African cities).
        if "timestamp" in df.columns:
            zone_cutoff = latest_time - timedelta(hours=max(time_window_hours * 3, 24 * 365))
            zone_df = df[df["timestamp"] >= zone_cutoff].copy()
        else:
            zone_df = df.copy()

        if "country" in zone_df.columns:
            raw_country = zone_df["country"]
            normalized = raw_country.where(raw_country.notna(), None).astype("object")
            normalized = normalized.map(lambda x: str(x).strip() if x is not None else None)
            normalized = normalized.replace({"": None, "nan": None, "None": None})
            if "city" in zone_df.columns:
                normalized = normalized.fillna(zone_df["city"].astype(str).map(self._city_to_country))
            zone_df["country"] = normalized.fillna("Unknown")
        elif "city" in zone_df.columns:
            zone_df["country"] = zone_df["city"].astype(str).map(self._city_to_country).fillna("Unknown")

        zone_col = "city" if "city" in zone_df.columns else ("country" if "country" in zone_df.columns else None)
        lat_col = next((c for c in ["lat", "latitude", "Latitude", "LAT"] if c in zone_df.columns), None)
        lon_col = next((c for c in ["lon", "lng", "longitude", "Longitude", "LON", "LNG"] if c in zone_df.columns), None)

        if "cell_id" in zone_df.columns and zone_col:
            grouped_df = zone_df.copy()
            grouped_df["zone"] = grouped_df[zone_col].astype(str)
            grouped_df["cell_key"] = grouped_df["zone"] + "::" + grouped_df["cell_id"].astype(str)
            grouped_df["cell_id"] = grouped_df["cell_id"].astype(str)
            if "country" in grouped_df.columns:
                grouped_df["country"] = grouped_df["country"].astype(str)
            if lat_col:
                grouped_df["_lat"] = pd.to_numeric(grouped_df[lat_col], errors="coerce")
            if lon_col:
                grouped_df["_lon"] = pd.to_numeric(grouped_df[lon_col], errors="coerce")

            agg_map = {
                "zone_records": ("cell_id", "count"),
                "avg_capex_score": ("capex_score", "mean"),
                "avg_sla_breach_risk": ("sla_breach_risk", "mean"),
                "avg_mos": ("MOS", "mean"),
                "critical_count": ("risk_tier", lambda x: (x.astype(str) == "CRITICAL").sum()),
                "max_priority": ("capex_priority", lambda x: x.astype(str).mode().iloc[0] if not x.astype(str).mode().empty else "N/A"),
                "zone": ("zone", lambda x: x.astype(str).mode().iloc[0] if not x.astype(str).mode().empty else "Unknown"),
                "cell_id": ("cell_id", lambda x: x.astype(str).mode().iloc[0] if not x.astype(str).mode().empty else "Unknown"),
            }
            if "country" in grouped_df.columns:
                agg_map["country"] = ("country", lambda x: x.astype(str).mode().iloc[0] if not x.astype(str).mode().empty else "")
            if lat_col:
                agg_map["avg_lat"] = ("_lat", "mean")
            if lon_col:
                agg_map["avg_lon"] = ("_lon", "mean")

            grouped = (
                grouped_df.groupby("cell_key", dropna=True).agg(**agg_map).reset_index()
            )
            grouped = grouped.sort_values(by=["critical_count", "avg_capex_score"], ascending=[False, False]).head(max_zones)
            zones = []
            for _, row in grouped.iterrows():
                coords = self._resolve_zone_coordinates(row)
                if not coords:
                    continue
                jitter = self._jitter_coordinates(coords["lat"], coords["lon"], row["cell_key"])
                zones.append(
                    {
                        "zone": str(row["zone"]),
                        "country": str(row["country"]) if "country" in row and pd.notna(row["country"]) else None,
                        "cell_id": str(row["cell_id"]),
                        "lat": jitter["lat"],
                        "lon": jitter["lon"],
                        "records": int(row["zone_records"]),
                        "avg_capex_score": round(float(row["avg_capex_score"]), 2) if pd.notna(row["avg_capex_score"]) else None,
                        "avg_sla_breach_risk": round(float(row["avg_sla_breach_risk"]), 4) if pd.notna(row["avg_sla_breach_risk"]) else None,
                        "avg_mos": round(float(row["avg_mos"]), 3) if pd.notna(row["avg_mos"]) else None,
                        "critical_count": int(row["critical_count"]),
                        "capex_priority": str(row["max_priority"]),
                    }
                )
        elif zone_col:
            grouped_df = zone_df.copy()
            grouped_df["zone"] = grouped_df[zone_col].astype(str)
            if "country" in grouped_df.columns:
                grouped_df["country"] = grouped_df["country"].astype(str)
            if lat_col:
                grouped_df["_lat"] = pd.to_numeric(grouped_df[lat_col], errors="coerce")
            if lon_col:
                grouped_df["_lon"] = pd.to_numeric(grouped_df[lon_col], errors="coerce")

            agg_map = {
                "zone_records": ("cell_id", "count"),
                "avg_capex_score": ("capex_score", "mean"),
                "avg_sla_breach_risk": ("sla_breach_risk", "mean"),
                "avg_mos": ("MOS", "mean"),
                "critical_count": ("risk_tier", lambda x: (x.astype(str) == "CRITICAL").sum()),
                "max_priority": ("capex_priority", lambda x: x.astype(str).mode().iloc[0] if not x.astype(str).mode().empty else "N/A"),
            }
            if "country" in grouped_df.columns:
                agg_map["country"] = ("country", lambda x: x.astype(str).mode().iloc[0] if not x.astype(str).mode().empty else "")
            if lat_col:
                agg_map["avg_lat"] = ("_lat", "mean")
            if lon_col:
                agg_map["avg_lon"] = ("_lon", "mean")

            grouped = (
                grouped_df.groupby("zone", dropna=True).agg(**agg_map)
                .reset_index()
            )
            grouped = grouped.sort_values(by=["critical_count", "avg_capex_score"], ascending=[False, False]).head(max_zones)
            zones = []
            for _, row in grouped.iterrows():
                coords = self._resolve_zone_coordinates(row)
                if not coords:
                    continue
                zones.append(
                    {
                        "zone": str(row["zone"]),
                        "lat": coords["lat"],
                        "lon": coords["lon"],
                        "records": int(row["zone_records"]),
                        "avg_capex_score": round(float(row["avg_capex_score"]), 2) if pd.notna(row["avg_capex_score"]) else None,
                        "avg_sla_breach_risk": round(float(row["avg_sla_breach_risk"]), 4) if pd.notna(row["avg_sla_breach_risk"]) else None,
                        "avg_mos": round(float(row["avg_mos"]), 3) if pd.notna(row["avg_mos"]) else None,
                        "critical_count": int(row["critical_count"]),
                        "capex_priority": str(row["max_priority"]),
                    }
                )
        else:
            zones = []

        models_status = {k: True for k in self.models.keys()}
        for key in ["anomaly_detector", "sla_predictor", "zone_scorer"]:
            models_status.setdefault(key, False)

        return {
            "timestamp": str(datetime.now()),
            "time_window_hours": int(time_window_hours),
            "bo1": bo1, "bo2": bo2, "bo3": bo3,
            "zones": zones, "trends": trend_data,
            "models": models_status,
        }

    def run_diagnostics(self):
        print("=" * 70)
        print("AGENT 2: AUTONOMOUS DIAGNOSTIC SCAN")
        print("=" * 70)
        print(f"Scan time: {datetime.now()}")
        df = self.load_data()
        if df is None:
            print("  Cannot run diagnostics without data")
            return
        alerts = self.analyze_batch(df, time_window_hours=1)
        if not alerts:
            print("\n  No issues detected - All systems nominal")
            return

        compounds = [a for a in alerts if a.get("is_compound")]
        roots = [a for a in alerts if a.get("is_root_cause")]
        print(f"\n  Detected {len(alerts)} alerts ({len(compounds)} compound, {len(roots)} root causes):\n")

        for i, alert in enumerate(alerts[:5], 1):
            tag = ""
            if alert.get("is_compound"):
                tag = "[COMPOUND] "
            elif alert.get("is_root_cause"):
                tag = "[ROOT CAUSE] "
            elif alert.get("is_symptom_of"):
                tag = f"[SYMPTOM of {alert['is_symptom_of']}] "
            print(f"{i}. {tag}[{alert['severity']}] {alert['issue_type']}")
            print(f"   Cell: {alert['cell_id']} | Primary action: {alert['recommendations'][0]}")

        self.alerts = alerts
        return alerts


def test_agent():
    print("=" * 70)
    print("TESTING AGENT 2: DIAGNOSTIC WORKER")
    print("=" * 70)
    agent = DiagnosticAgent()
    alerts = agent.run_diagnostics()
    print("\n" + "=" * 70)
    print("SUMMARY REPORT")
    print("=" * 70)
    summary = agent.generate_summary_report()
    print(json.dumps(summary, indent=2, default=str))

    print("\n" + "=" * 70)
    print("CELL HEALTH SCORES (top 10)")
    print("=" * 70)
    df = agent.load_data()
    if df is not None:
        health = agent.compute_cell_health(df)
        sorted_cells = sorted(health.items(), key=lambda x: x[1]["health_score"])
        for cell_id, info in sorted_cells[:10]:
            print(f"  {cell_id}: {info['health_score']}/100 ({info['status']})")


if __name__ == "__main__":
    test_agent()