"""Small forecast builders used by ARIMA edge-case handling."""

from __future__ import annotations

from redthread.telemetry.models import ArimaForecast


def constant_forecast(series: list[float], metric_name: str) -> ArimaForecast:
    """Return a no-op forecast for a variance-free metric series."""
    constant = float(series[-1])
    return ArimaForecast(
        metric_name=metric_name,
        observed=constant,
        predicted=constant,
        lower_bound=constant,
        upper_bound=constant,
        is_anomaly=False,
        deviation_sigma=0.0,
        n_observations=len(series),
        fallback_method="constant",
    )
