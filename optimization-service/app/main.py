from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from shared.smartstock_common import (
    ReorderPolicy,
    Settings,
    build_audit_event,
    generate_reorder_recommendation,
    has_permission,
)
from shared.smartstock_common.optimization import dynamic_price
from shared.smartstock_common.schemas import ReorderRecommendation

settings = Settings(service_name="optimization-service", service_port=8003)
app = FastAPI(title="SmartStock Optimization Service", version="1.0.0")

policy_store: dict[str, ReorderPolicy] = {}
audit_log: list[dict] = []


class RecommendationRequest(BaseModel):
    sku: str
    warehouse_id: str
    current_stock: int = Field(ge=0)
    demand_history: list[float] = Field(min_length=7)
    forecast_values: list[float] = Field(min_length=7)
    base_price: float | None = None


class RecommendationBulkRequest(BaseModel):
    items: list[RecommendationRequest]
    concurrency: int = Field(default=64, ge=1, le=256)


class DynamicPriceRequest(BaseModel):
    base_price: float = Field(gt=0)
    days_of_cover: float = Field(ge=0)
    demand_score: float = Field(ge=0.1, le=2.0)


class PolicyUpdateRequest(BaseModel):
    policy: ReorderPolicy
    actor_id: str
    actor_role: str


def _assert_permission(role: str, action: str) -> None:
    if not has_permission(role, action):
        raise HTTPException(status_code=403, detail=f"Role {role} cannot perform {action}")


def _policy_key(warehouse_id: str, sku: str) -> str:
    return f"{warehouse_id}:{sku}"


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.put("/policy")
async def upsert_policy(request: PolicyUpdateRequest) -> dict:
    _assert_permission(request.actor_role, "optimization:write")
    key = _policy_key(request.policy.warehouse_id, request.policy.sku)
    policy_store[key] = request.policy
    event = build_audit_event(
        event_type="optimization.policy_update",
        actor_id=request.actor_id,
        actor_role=request.actor_role,
        details=request.policy.model_dump(mode="json"),
    )
    audit_log.append(event.model_dump(mode="json"))
    return {"status": "updated", "key": key}


@app.get("/policy/{warehouse_id}/{sku}")
async def get_policy(warehouse_id: str, sku: str, role: str = "logistician") -> dict:
    _assert_permission(role, "optimization:read")
    key = _policy_key(warehouse_id, sku)
    policy = policy_store.get(key)
    if policy is None:
        policy = ReorderPolicy(sku=sku, warehouse_id=warehouse_id)
        policy_store[key] = policy
    return policy.model_dump(mode="json")


@app.post("/recommendation", response_model=ReorderRecommendation)
async def recommendation(request: RecommendationRequest, role: str = "logistician") -> ReorderRecommendation:
    _assert_permission(role, "optimization:read")
    key = _policy_key(request.warehouse_id, request.sku)
    policy = policy_store.get(key) or ReorderPolicy(sku=request.sku, warehouse_id=request.warehouse_id)

    rec = generate_reorder_recommendation(
        sku=request.sku,
        warehouse_id=request.warehouse_id,
        current_stock=request.current_stock,
        demand_history=request.demand_history,
        forecast_values=request.forecast_values,
        lead_time_days=policy.lead_time_days,
        service_level_z=policy.service_level_z,
        min_order_qty=policy.min_order_qty,
        base_price=request.base_price,
    )
    return rec


@app.post("/recommendation/bulk")
async def recommendation_bulk(request: RecommendationBulkRequest) -> dict:
    started = datetime.now(UTC)
    sem = asyncio.Semaphore(request.concurrency)

    async def _worker(item: RecommendationRequest) -> ReorderRecommendation:
        async with sem:
            return await recommendation(item)

    results = await asyncio.gather(*[_worker(item) for item in request.items])
    elapsed_ms = int((datetime.now(UTC) - started).total_seconds() * 1000)
    target_met = elapsed_ms <= settings.recommendation_target_ms_10k_sku
    critical = [result.model_dump(mode="json") for result in results if result.reason == "stock_below_reorder_point"]
    return {
        "processed": len(results),
        "elapsed_ms": elapsed_ms,
        "target_ms": settings.recommendation_target_ms_10k_sku,
        "target_met": target_met,
        "critical_count": len(critical),
    }


@app.post("/dynamic-price")
async def suggest_dynamic_price(request: DynamicPriceRequest, role: str = "analyst") -> dict:
    _assert_permission(role, "optimization:read")
    price = dynamic_price(
        base_price=request.base_price,
        days_of_cover=request.days_of_cover,
        demand_score=request.demand_score,
    )
    return {"dynamic_price": price}


@app.get("/audit")
async def get_audit(limit: int = 100, role: str = "admin") -> dict:
    _assert_permission(role, "audit:read")
    return {"items": audit_log[-limit:]}
