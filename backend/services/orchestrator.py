"""Coordinates Data Manager, Detection, Prediction, Alert, and Drift Detection."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from agent2_diagnostic import DiagnosticAgent

from services.alert_agent import AlertAgent
from services.data_manager import DataManagerAgent
from services.detection_agent import DetectionAgent
from services.drift_detector import DriftDetector
from services.prediction_agent import PredictionAgent


class QoSOrchestrator:
    def __init__(self):
        self.data_manager = DataManagerAgent()
        self.detection = DetectionAgent()
        self.prediction = PredictionAgent()
        self.alerts = AlertAgent()
        self.drift = DriftDetector()
        self._diagnostic = DiagnosticAgent()

    def wire_agent1(self, agent1):
        """Connect Agent 2's diagnostic context to Agent 1's chat pipeline."""
        if agent1 is None:
            return

        def diagnostic_provider(cell_id: str = None) -> str:
            if cell_id:
                return self._diagnostic.get_cell_diagnostic_context(cell_id)
            # General: return summary
            try:
                summ = self._diagnostic.generate_summary_report()
                if "error" in summ:
                    return ""
                return (
                    f"Active alerts: {summ.get('total_alerts', 0)} "
                    f"(CRITICAL: {summ.get('critical', 0)}, HIGH: {summ.get('high', 0)}, "
                    f"Compound: {summ.get('compound_issues', 0)}). "
                    f"Cells with issues: {summ.get('cells_with_issues', 0)}."
                )
            except Exception:
                return ""

        agent1.set_diagnostic_provider(diagnostic_provider)

    def refresh_data(self, force: bool = False):
        result = self.data_manager.refresh(force=force)
        # Update drift reference when data is refreshed
        df = self.data_manager.get_working_frame(time_window_hours=168, max_rows=10000)
        if df is not None and not df.empty and not self.drift.has_reference():
            self.drift.set_reference(df)
        return result

    def run_detection(
        self,
        time_window_hours: int = 24,
        bo_filter: Optional[str] = None,
        include_rule_alerts: bool = True,
        max_rows: int = 5000,
    ) -> Dict[str, Any]:
        df = self.data_manager.get_working_frame(
            time_window_hours=time_window_hours,
            bo_filter=bo_filter,
            max_rows=max_rows,
        )
        if df is None or df.empty:
            return {
                "success": False,
                "message": "No data",
                "anomaly_records": [],
                "rule_alerts": [],
                "isolation_forest": None,
                "merged_alerts": [],
            }

        clf, meta, if_records = self.detection.detect(df)

        rule_alerts: List[Dict[str, Any]] = []
        if include_rule_alerts:
            rule_alerts = self._diagnostic.analyze_batch(df, time_window_hours=time_window_hours)

        high_pred: Optional[List[Dict[str, Any]]] = None
        try:
            if self.prediction.status().get("trained"):
                high_pred = self.prediction.predict_latest(df, n=80)
        except Exception:
            high_pred = None

        merged = self.alerts.merge_alerts(rule_alerts, if_records, high_pred)

        return {
            "success": True,
            "message": None,
            "isolation_forest": meta if "error" not in meta else None,
            "anomaly_records": if_records,
            "rule_alerts": rule_alerts,
            "merged_alerts": merged,
        }

    def run_predict(
        self,
        target: str = "latency_ms",
        time_window_hours: int = 48,
        bo_filter: Optional[str] = None,
        max_train_rows: int = 20000,
        retrain: bool = False,
    ) -> Dict[str, Any]:
        df = self.data_manager.get_working_frame(
            time_window_hours=time_window_hours,
            bo_filter=bo_filter,
            max_rows=max_train_rows + 2000,
        )
        if df is None or df.empty:
            return {"success": False, "message": "No data", "predictions": [], "metrics": {}}

        st = self.prediction.status()
        if retrain or not st.get("trained") or st.get("target") != target:
            try:
                metrics = self.prediction.fit(df, target=target, max_train_rows=max_train_rows)
                # Update drift reference with training data
                self.drift.set_reference(df)
            except ValueError as e:
                return {"success": False, "message": str(e), "predictions": [], "metrics": {}}

        preds = self.prediction.predict_latest(df, n=60)
        return {
            "success": True,
            "metrics": self.prediction._last_metrics,
            "predictions": preds,
            "model": "RandomForestRegressor",
            "version": self.prediction._version,
        }

    def check_drift(self, time_window_hours: int = 24, bo_filter: Optional[str] = None) -> Dict[str, Any]:
        """Check data drift against training reference."""
        df = self.data_manager.get_working_frame(
            time_window_hours=time_window_hours,
            bo_filter=bo_filter,
            max_rows=5000,
        )
        if df is None or df.empty:
            return {"error": "No data available for drift check"}
        return self.drift.check_drift(df)

    def live_insights_snapshot(self) -> str:
        """Compact text for chatbot system context."""
        self.data_manager.refresh()
        lines: List[str] = []
        df = self.data_manager.get_working_frame(time_window_hours=72, max_rows=5000)
        if df is not None and not df.empty and "cell_id" in df.columns:
            lines.append(
                f"Dataset window (~72h): {len(df)} rows, {df['cell_id'].nunique()} cells."
            )
        else:
            lines.append("Dataset: unavailable or empty.")

        lines.append(f"Enrichment catalog entries: {self.data_manager.enrichment_catalog_count()}.")

        try:
            summ = self._diagnostic.generate_summary_report()
            if "error" not in summ:
                lines.append(
                    f"Diagnostics summary (24h window): {summ.get('total_alerts', 0)} alerts, "
                    f"{summ.get('cells_with_issues', 0)} cells with issues."
                )
        except Exception:
            pass

        return "\n".join(lines)
