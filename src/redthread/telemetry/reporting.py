"""ASI evidence metadata and recommendation helpers."""
from __future__ import annotations
from redthread.telemetry.drift import DriftDetector
from redthread.telemetry.models import ASIReport, ArimaForecast
from redthread.telemetry.collector import TelemetryCollector


def build_report_metadata(
    collector: TelemetryCollector,
    drift_detector: DriftDetector,
    forecasts: list[ArimaForecast],
    modes: dict[str, str],
) -> dict[str, object]:
    baseline_count = 0
    if drift_detector._baseline_embeddings is not None:
        baseline_count = int(drift_detector._baseline_embeddings.shape[0])
    warnings: list[str] = []
    if modes["response_consistency"] != "measured":
        warnings.append("Response Consistency defaulted high because canary history is missing or too thin.")
    if modes["semantic_drift"] == "no_baseline":
        warnings.append("Semantic Drift defaulted high because no benign baseline is fitted.")
    elif modes["semantic_drift"] == "no_organic_embeddings":
        warnings.append("Semantic Drift defaulted high because no organic response embeddings were available.")
    elif modes["semantic_drift"] == "embedding_dim_mismatch":
        warnings.append("Semantic Drift defaulted high because organic embeddings did not match baseline dimensions.")
    if modes["operational_health"] != "measured":
        warnings.append("Operational Health defaulted high because there was not enough organic history for ARIMA checks.")
    if modes["behavioral_stability"] != "measured":
        warnings.append("Behavioral Stability defaulted high because there was not enough organic history for variance checks.")
    if collector.total_records == collector.total_canary_records and collector.total_records > 0:
        warnings.append("Current telemetry is canary-only. It is useful for operator monitoring, not proof of full benign utility.")
    return {
        "organic_records": len(collector.get_organic_records()),
        "canary_records": collector.total_canary_records,
        "baseline_embeddings": baseline_count,
        "baseline_fitted": drift_detector._baseline_embeddings is not None,
        "arima_metrics_checked": len(forecasts),
        "response_consistency_mode": modes["response_consistency"],
        "semantic_drift_mode": modes["semantic_drift"],
        "operational_health_mode": modes["operational_health"],
        "behavioral_stability_mode": modes["behavioral_stability"],
        "evidence_warnings": warnings,
    }


def generate_recommendation(report: ASIReport) -> str:
    issues: list[str] = []
    warnings = report.metadata.get("evidence_warnings", [])
    if report.response_consistency < 70:
        issues.append(f"Response Consistency degraded ({report.response_consistency:.0f}/100) — canary outputs are diverging")
    if report.semantic_drift < 70:
        issues.append(f"Semantic Drift detected ({report.semantic_drift:.0f}/100) — output meaning has shifted from baseline")
    if report.operational_health < 70:
        issues.append(f"Operational anomalies in: {', '.join(a.metric_name for a in report.anomalies if a.is_anomaly)}")
    if report.behavioral_stability < 70:
        issues.append(f"Behavioral instability ({report.behavioral_stability:.0f}/100) — token count variance is high")
    caution = ""
    if warnings:
        caution = " Telemetry evidence is limited: " + " ".join(str(w) for w in warnings)
    if report.health_tier == "EXCELLENT":
        return "✅ Telemetry signal looks stable." + caution
    if report.health_tier == "GOOD":
        return "✅ Telemetry signal looks healthy with minor fluctuations." + caution
    action = "; ".join(issues) if issues else "Investigate with targeted validation."
    if report.health_tier == "WARNING":
        return f"⚠️ Warning — telemetry suggests rising drift. Investigate: {action}.{caution}"
    if report.health_tier == "DEGRADED":
        return "🔴 Degraded — telemetry indicates significant behavioral change. Recommended: bounded follow-up campaign and replay validation. Root causes: " + f"{action}.{caution}"
    return f"🚨 CRITICAL — ASI={report.overall_score:.1f}. Telemetry indicates severe instability. Use this as an operator signal and verify with campaign/replay evidence. Issues: {action}.{caution}"
