from __future__ import annotations

from math import sqrt


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mu = _mean(values)
    variance = sum((v - mu) ** 2 for v in values) / (len(values) - 1)
    return sqrt(variance)


def detect_anomalies(history: list[float], z_threshold: float = 3.0) -> list[int]:
    if len(history) < 7:
        return []
    mu = _mean(history)
    sigma = _std(history)
    if sigma == 0:
        return []
    anomalies = []
    for idx, value in enumerate(history):
        z = abs((value - mu) / sigma)
        if z >= z_threshold:
            anomalies.append(idx)
    return anomalies


def forecast_demand(
    history: list[float],
    horizon_days: int = 7,
    season_period: int = 7,
    promotion_calendar: dict[str, float] | None = None,
    holiday_calendar: dict[str, float] | None = None,
    manual_multiplier: float | None = None,
) -> list[float]:
    """
    Hybrid baseline:
    - trend from last seasonal window vs previous one
    - seasonal profile from last season_period points
    - multiplicative event effects (promo/holiday/manual)
    """
    if not history:
        return [0.0 for _ in range(horizon_days)]

    promotion_calendar = promotion_calendar or {}
    holiday_calendar = holiday_calendar or {}

    full_windows = max(1, len(history) // season_period)
    windows_to_use = min(8, full_windows)
    start = len(history) - windows_to_use * season_period
    seasonal_profile: list[float] = []
    for offset in range(season_period):
        bucket = []
        for win in range(windows_to_use):
            idx = start + win * season_period + offset
            if idx < len(history):
                bucket.append(history[idx])
        seasonal_profile.append(_mean(bucket) if bucket else history[-1])

    last_window = history[-season_period:]
    prev_window = history[-2 * season_period : -season_period] or last_window
    trend = _mean(last_window) - _mean(prev_window)
    forecasts: list[float] = []

    for day in range(horizon_days):
        seasonal = seasonal_profile[day % len(seasonal_profile)]
        trend_component = trend * ((day + 1) / max(season_period * windows_to_use, 1))
        base = max(0.0, seasonal + trend_component)
        promo_boost = promotion_calendar.get(str(day), 1.0)
        holiday_boost = holiday_calendar.get(str(day), 1.0)
        adjusted = base * promo_boost * holiday_boost
        if manual_multiplier:
            adjusted *= manual_multiplier
        forecasts.append(round(adjusted, 2))

    return forecasts


def mape(actual: list[float], predicted: list[float]) -> float:
    if not actual or not predicted:
        return 0.0
    length = min(len(actual), len(predicted))
    numerator = 0.0
    denominator = 0
    for idx in range(length):
        if actual[idx] == 0:
            continue
        numerator += abs((actual[idx] - predicted[idx]) / actual[idx])
        denominator += 1
    if denominator == 0:
        return 0.0
    return round((numerator / denominator) * 100, 2)
