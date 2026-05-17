from pathlib import Path

from fastapi.testclient import TestClient

from .helpers import load_module

ROOT = Path(__file__).resolve().parents[2]


def test_inventory_register_and_fetch_stock() -> None:
    module = load_module("inventory_app_module", ROOT / "inventory-service" / "app" / "main.py")
    client = TestClient(module.app)

    payload = {
        "warehouse_id": "WH-001",
        "movement_type": "arrival",
        "policy": "fifo",
        "actor_id": "u-1",
        "actor_role": "warehouse_worker",
        "items": [
            {
                "sku": "SKU-100",
                "quantity": 30,
                "batch_id": "B-1",
                "unit_cost": 12.5,
            }
        ],
    }
    movement_resp = client.post("/movements/register", json=payload)
    assert movement_resp.status_code == 200

    stock_resp = client.get("/stock/WH-001/SKU-100", params={"role": "logistician"})
    assert stock_resp.status_code == 200
    assert stock_resp.json()["total_qty"] == 30


def test_forecast_to_optimization_flow() -> None:
    forecast_module = load_module("forecast_app_module", ROOT / "forecast-service" / "app" / "main.py")
    optimization_module = load_module("optimization_app_module", ROOT / "optimization-service" / "app" / "main.py")

    forecast_client = TestClient(forecast_module.app)
    optimization_client = TestClient(optimization_module.app)

    forecast_payload = {
        "sku": "SKU-200",
        "warehouse_id": "WH-001",
        "history": [11, 12, 10, 13, 12, 14, 15, 13, 14, 15, 16, 18, 19, 17],
        "horizon_days": 7,
        "season_period": 7,
    }
    forecast_resp = forecast_client.post("/forecast/predict", json=forecast_payload, params={"role": "analyst"})
    assert forecast_resp.status_code == 200
    forecast_values = forecast_resp.json()["values"]

    recommendation_payload = {
        "sku": "SKU-200",
        "warehouse_id": "WH-001",
        "current_stock": 5,
        "demand_history": forecast_payload["history"],
        "forecast_values": forecast_values,
    }
    recommendation_resp = optimization_client.post(
        "/recommendation",
        json=recommendation_payload,
        params={"role": "logistician"},
    )
    assert recommendation_resp.status_code == 200
    assert recommendation_resp.json()["reason"] in {"stock_below_reorder_point", "stock_sufficient"}
