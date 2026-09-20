"""Small forecast builders used by ARIMA edge-case handling."""

from __future__ import annotations

import warnings

import numpy as np

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


def compute_z_score_fallback(
    series: list[float], metric_name: str, sigma_multiplier: float = 2.0
) -> ArimaForecast:
    """Fallback when < min_observations or auto_arima fails. Uses ±2σ Z-score detection."""
    arr = np.array(series, dtype=np.float64)
    mean = float(np.mean(arr))
    std = float(np.std(arr)) if len(arr) > 1 else 1.0
    observed = arr[-1]

    lower = mean - sigma_multiplier * std
    upper = mean + sigma_multiplier * std
    deviation_sigma = (observed - mean) / std if std > 0 else 0.0

    return ArimaForecast(
        metric_name=metric_name,
        observed=float(observed),
        predicted=mean,
        lower_bound=lower,
        upper_bound=upper,
        is_anomaly=bool(observed < lower or observed > upper),
        deviation_sigma=deviation_sigma,
        n_observations=len(series),
        fallback_method="z_score",
    )


def build_arima_forecast(
    metric_name: str,
    observed: float,
    predicted: float,
    lower: float,
    upper: float,
    deviation_sigma: float,
    n_observations: int,
) -> ArimaForecast:
    """Construct an ArimaForecast from model prediction and bounds."""
    return ArimaForecast(
        metric_name=metric_name,
        observed=float(observed),
        predicted=predicted,
        lower_bound=lower,
        upper_bound=upper,
        is_anomaly=bool(observed < lower or observed > upper),
        deviation_sigma=deviation_sigma,
        n_observations=n_observations,
        fallback_method="",
    )


def fit_arima_prediction(
    train: list[float],
    observed: float,
    confidence_level: float,
    window_len: int,
    metric_name: str,
) -> ArimaForecast:
    """Fit auto_arima on training window and generate single-step prediction."""
    from pmdarima import auto_arima

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = auto_arima(
            train,
            stepwise=True,
            suppress_warnings=True,
            error_action="ignore",
            max_p=3,
            max_q=3,
            information_criterion="aic",
        )

    forecast_result = model.predict(
        n_periods=1, return_conf_int=True, alpha=1.0 - confidence_level
    )
    predicted_arr, conf_int = forecast_result
    predicted = float(predicted_arr[0])
    lower = float(conf_int[0][0])
    upper = float(conf_int[0][1])

    residuals = np.array(model.resid(), dtype=np.float64)
    std_err = float(np.std(residuals)) if len(residuals) > 1 else 1.0
    deviation_sigma = (observed - predicted) / std_err if std_err > 0 else 0.0

    return build_arima_forecast(
        metric_name=metric_name,
        observed=float(observed),
        predicted=predicted,
        lower=lower,
        upper=upper,
        deviation_sigma=deviation_sigma,
        n_observations=window_len,
    )
