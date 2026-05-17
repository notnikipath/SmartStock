from shared.smartstock_common.forecasting import detect_anomalies, forecast_demand, mape


def test_forecast_returns_horizon_values() -> None:
    history = [10, 12, 13, 11, 12, 15, 14, 16, 17, 15, 16, 19, 18, 20]
    values = forecast_demand(history=history, horizon_days=7, season_period=7)
    assert len(values) == 7
    assert all(value >= 0 for value in values)


def test_anomaly_detection_finds_outlier() -> None:
    history = [10, 11, 9, 10, 10, 95, 11, 9, 10, 10]
    anomalies = detect_anomalies(history, z_threshold=2.0)
    assert 5 in anomalies


def test_mape_computation() -> None:
    actual = [100, 110, 90, 100]
    predicted = [95, 120, 80, 110]
    metric = mape(actual, predicted)
    assert 0 < metric < 20
