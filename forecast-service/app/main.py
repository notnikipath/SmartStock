from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from statistics import mean

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from shared.smartstock_common import (
    ForecastRequest,
    ForecastResult,
    Settings,
    build_audit_event,
    detect_anomalies,
    forecast_demand,
    has_permission,
    mape,
)

settings = Settings(service_name="forecast-service", service_port=8002)
app = FastAPI(title="SmartStock Forecast Service", version="1.0.0")

forecast_cache: dict[str, ForecastResult] = {}
manual_adjustments: dict[str, float] = {}
audit_log: list[dict] = []


class BulkForecastItem(BaseModel):
    sku: str
    warehouse_id: str
    history: list[float] = Field(min_length=7)


class BulkForecastRequest(BaseModel):
    items: list[BulkForecastItem]
    horizon_days: int = Field(default=7, ge=1, le=30)
    season_period: int = Field(default=7, ge=2, le=30)
    concurrency: int = Field(default=32, ge=1, le=256)


class ManualAdjustmentRequest(BaseModel):
    sku: str
    warehouse_id: str
    multiplier: float = Field(gt=0.0, le=5.0)
    actor_id: str
    actor_role: str


class AccuracyRequest(BaseModel):
    actual: list[float]
    predicted: list[float]


def _assert_permission(role: str, action: str) -> None:
    if not has_permission(role, action):
        raise HTTPException(status_code=403, detail=f"Role {role} cannot perform {action}")


def _cache_key(warehouse_id: str, sku: str) -> str:
    return f"{warehouse_id}:{sku}"


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.post("/forecast/predict", response_model=ForecastResult)
async def predict(request: ForecastRequest, role: str = "analyst") -> ForecastResult:
    _assert_permission(role, "forecast:read")
    key = _cache_key(request.warehouse_id, request.sku)
    manual = manual_adjustments.get(key, request.manual_multiplier)
    values = forecast_demand(
        history=request.history,
        horizon_days=request.horizon_days,
        season_period=request.season_period,
        promotion_calendar=request.promotion_calendar,
        holiday_calendar=request.holiday_calendar,
        manual_multiplier=manual,
    )
    anomalies = detect_anomalies(request.history)
    result = ForecastResult(
        sku=request.sku,
        warehouse_id=request.warehouse_id,
        generated_at=datetime.now(UTC),
        horizon_days=request.horizon_days,
        values=values,
        anomaly_indices=anomalies,
    )
    forecast_cache[key] = result
    return result


@app.post("/forecast/bulk")
async def bulk_predict(request: BulkForecastRequest) -> dict:
    started = datetime.now(UTC)
    sem = asyncio.Semaphore(request.concurrency)

    async def _worker(item: BulkForecastItem) -> ForecastResult:
        async with sem:
            item_request = ForecastRequest(
                sku=item.sku,
                warehouse_id=item.warehouse_id,
                history=item.history,
                horizon_days=request.horizon_days,
                season_period=request.season_period,
            )
            return await predict(item_request, role="analyst")

    results = await asyncio.gather(*[_worker(item) for item in request.items])
    elapsed_ms = int((datetime.now(UTC) - started).total_seconds() * 1000)
    avg_first_day = round(mean([result.values[0] for result in results]) if results else 0.0, 2)
    return {"processed": len(results), "elapsed_ms": elapsed_ms, "avg_day1_forecast": avg_first_day}


@app.post("/forecast/manual-adjustment")
async def set_manual_adjustment(request: ManualAdjustmentRequest) -> dict:
    _assert_permission(request.actor_role, "forecast:write")
    key = _cache_key(request.warehouse_id, request.sku)
    manual_adjustments[key] = request.multiplier
    audit_event = build_audit_event(
        event_type="forecast.manual_adjustment",
        actor_id=request.actor_id,
        actor_role=request.actor_role,
        details={"sku": request.sku, "warehouse_id": request.warehouse_id, "multiplier": request.multiplier},
    )
    audit_log.append(audit_event.model_dump(mode="json"))
    return {"status": "updated", "key": key, "multiplier": request.multiplier}


@app.get("/forecast/{warehouse_id}/{sku}")
async def get_cached_forecast(warehouse_id: str, sku: str, role: str = "analyst") -> dict:
    _assert_permission(role, "forecast:read")
    key = _cache_key(warehouse_id, sku)
    result = forecast_cache.get(key)
    if not result:
        raise HTTPException(status_code=404, detail="Forecast not found")
    return result.model_dump(mode="json")


@app.post("/forecast/accuracy")
async def accuracy(request: AccuracyRequest, role: str = "analyst") -> dict:
    _assert_permission(role, "forecast:read")
    metric = mape(request.actual, request.predicted)
    return {"mape": metric, "target": settings.mape_target_7d, "target_met": metric < settings.mape_target_7d}


@app.get("/anomalies/{warehouse_id}/{sku}")
async def anomalies(warehouse_id: str, sku: str, role: str = "analyst") -> dict:
    _assert_permission(role, "forecast:read")
    key = _cache_key(warehouse_id, sku)
    result = forecast_cache.get(key)
    if not result:
        return {"warehouse_id": warehouse_id, "sku": sku, "anomaly_indices": []}
    return {"warehouse_id": warehouse_id, "sku": sku, "anomaly_indices": result.anomaly_indices}


@app.get("/audit")
async def get_audit(limit: int = 100, role: str = "admin") -> dict:
    _assert_permission(role, "audit:read")
    return {"items": audit_log[-limit:]}
