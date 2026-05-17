from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from shared.smartstock_common.schemas import InventoryMovementRequest, MovementType


class GatewaySettings(BaseSettings):
    service_name: str = "api-gateway"
    service_port: int = 8000
    inventory_service_url: str = "http://inventory-service:8001"
    forecast_service_url: str = "http://forecast-service:8002"
    optimization_service_url: str = "http://optimization-service:8003"
    placement_service_url: str = "http://placement-service:8004"
    analytics_service_url: str = "http://analytics-service:8005"
    integration_service_url: str = "http://integration-service:8006"
    notification_service_url: str = "http://notification-service:8007"
    storage_service_url: str = "http://storage-service:8008"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = GatewaySettings()
app = FastAPI(title="SmartStock API Gateway", version="1.0.0")


class NewShipmentRequest(BaseModel):
    movement: InventoryMovementRequest
    history_by_sku: dict[str, list[float]] = Field(default_factory=dict)
    manager_recipient: str = "manager@smartstock.local"


class RecalculateRequest(BaseModel):
    warehouse_id: str
    sku_histories: dict[str, list[float]]
    current_stock: dict[str, int]


def _service_urls() -> dict[str, str]:
    return {
        "inventory": settings.inventory_service_url,
        "forecast": settings.forecast_service_url,
        "optimization": settings.optimization_service_url,
        "placement": settings.placement_service_url,
        "analytics": settings.analytics_service_url,
        "integration": settings.integration_service_url,
        "notification": settings.notification_service_url,
        "storage": settings.storage_service_url,
    }


async def _post_json(client: httpx.AsyncClient, url: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = await client.post(url, json=payload)
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.get("/services/health")
async def services_health() -> dict:
    urls = _service_urls()
    timeout = httpx.Timeout(6.0, connect=2.0)
    result: dict[str, Any] = {}
    async with httpx.AsyncClient(timeout=timeout) as client:
        for name, base_url in urls.items():
            try:
                response = await client.get(f"{base_url}/health")
                result[name] = {"status_code": response.status_code, "body": response.json()}
            except Exception as exc:
                result[name] = {"status": "unreachable", "error": str(exc)}
    return result


@app.post("/workflow/new-shipment")
async def process_new_shipment(request: NewShipmentRequest) -> dict:
    """
    Pipeline:
    1. Register arrival/shipment
    2. Recalculate forecasts
    3. Build purchase recommendations
    4. Notify manager if needed
    5. Persist operation audit
    """
    if request.movement.movement_type not in {MovementType.ARRIVAL, MovementType.SHIPMENT, MovementType.TRANSFER}:
        raise HTTPException(status_code=400, detail="Unsupported movement_type for shipment workflow")

    urls = _service_urls()
    timeout = httpx.Timeout(15.0, connect=5.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        movement_response = await _post_json(
            client,
            f"{urls['inventory']}/movements/register",
            request.movement.model_dump(mode="json"),
        )

        forecast_results: dict[str, Any] = {}
        recommendations: list[dict[str, Any]] = []

        for sku in movement_response.get("updated_skus", []):
            history = request.history_by_sku.get(sku, [12, 13, 12, 14, 15, 14, 16, 13, 12, 14, 17, 18, 19, 18])
            forecast_payload = {
                "sku": sku,
                "warehouse_id": request.movement.warehouse_id,
                "history": history,
                "horizon_days": 7,
                "season_period": 7,
            }
            forecast_result = await _post_json(client, f"{urls['forecast']}/forecast/predict", forecast_payload)
            forecast_results[sku] = forecast_result

            stock_response = await client.get(
                f"{urls['inventory']}/stock/{request.movement.warehouse_id}/{sku}",
                params={"role": "logistician"},
            )
            stock_response.raise_for_status()
            current_stock = stock_response.json().get("total_qty", 0)

            rec_payload = {
                "sku": sku,
                "warehouse_id": request.movement.warehouse_id,
                "current_stock": current_stock,
                "demand_history": history[-30:],
                "forecast_values": forecast_result.get("values", []),
                "base_price": 100.0,
            }
            recommendation = await _post_json(client, f"{urls['optimization']}/recommendation", rec_payload)
            recommendations.append(recommendation)

        actionable = [item for item in recommendations if item.get("recommended_qty", 0) > 0]
        if actionable:
            notify_payload = {
                "channel": "push",
                "subject": "SmartStock reorder recommendations",
                "body": f"{len(actionable)} SKU require reordering",
                "recipient": request.manager_recipient,
            }
            await _post_json(client, f"{urls['notification']}/notify/send", notify_payload)

        await _post_json(
            client,
            f"{urls['storage']}/logs/operation",
            {
                "operation_type": "shipment_workflow",
                "payload": {
                    "movement_id": movement_response.get("movement_id"),
                    "warehouse_id": request.movement.warehouse_id,
                    "recommendations": recommendations,
                },
                "actor_id": request.movement.actor_id,
                "actor_role": request.movement.actor_role,
            },
        )

    return {
        "movement": movement_response,
        "forecasts": forecast_results,
        "recommendations": recommendations,
        "processed_at": datetime.now(UTC).isoformat(),
    }


@app.post("/workflow/recalculate")
async def recalculate_all(request: RecalculateRequest) -> dict:
    urls = _service_urls()
    timeout = httpx.Timeout(20.0, connect=4.0)
    results: list[dict[str, Any]] = []

    async with httpx.AsyncClient(timeout=timeout) as client:
        for sku, history in request.sku_histories.items():
            forecast_result = await _post_json(
                client,
                f"{urls['forecast']}/forecast/predict",
                {
                    "sku": sku,
                    "warehouse_id": request.warehouse_id,
                    "history": history,
                    "horizon_days": 7,
                    "season_period": 7,
                },
            )
            recommendation = await _post_json(
                client,
                f"{urls['optimization']}/recommendation",
                {
                    "sku": sku,
                    "warehouse_id": request.warehouse_id,
                    "current_stock": request.current_stock.get(sku, 0),
                    "demand_history": history,
                    "forecast_values": forecast_result["values"],
                },
            )
            results.append({"sku": sku, "forecast": forecast_result, "recommendation": recommendation})
    return {"warehouse_id": request.warehouse_id, "items": results}
