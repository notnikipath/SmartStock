from __future__ import annotations

from collections import defaultdict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from shared.smartstock_common import PlacementRequest, Settings, has_permission, recommend_zone
from shared.smartstock_common.schemas import PlacementRecommendation

settings = Settings(service_name="placement-service", service_port=8004)
app = FastAPI(title="SmartStock Placement Service", version="1.0.0")

zones_by_warehouse: dict[str, list[dict]] = defaultdict(
    lambda: [
        {
            "name": "ZONE_COLD_A",
            "temperature_band": "cool",
            "max_weight_kg": 1500,
            "max_volume_m3": 400,
            "fast_pick": True,
            "supports_medical": True,
            "high_security": False,
            "shelf_template": "C-A-{index}",
        },
        {
            "name": "ZONE_SECURE_E",
            "temperature_band": "ambient",
            "max_weight_kg": 1200,
            "max_volume_m3": 600,
            "fast_pick": True,
            "supports_medical": False,
            "high_security": True,
            "shelf_template": "E-S-{index}",
        },
        {
            "name": "ZONE_BULK_RM",
            "temperature_band": "ambient",
            "max_weight_kg": 5000,
            "max_volume_m3": 5000,
            "fast_pick": False,
            "supports_medical": False,
            "high_security": False,
            "shelf_template": "RM-{index}",
        },
    ]
)
assignments: list[dict] = []


class PlacementAssignRequest(BaseModel):
    warehouse_id: str
    recommendation: PlacementRecommendation
    actor_role: str = "warehouse_worker"


class ZoneConfigRequest(BaseModel):
    warehouse_id: str
    zones: list[dict] = Field(min_length=1)
    actor_role: str = "admin"


def _assert_permission(role: str, action: str) -> None:
    if not has_permission(role, action):
        raise HTTPException(status_code=403, detail=f"Role {role} cannot perform {action}")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.post("/placement/recommend", response_model=PlacementRecommendation)
async def placement_recommendation(
    request: PlacementRequest,
    warehouse_id: str = "WH-001",
    role: str = "warehouse_worker",
) -> PlacementRecommendation:
    _assert_permission(role, "placement:read")
    zone = recommend_zone(
        category=request.category,
        weight_kg=request.weight_kg,
        volume_m3=request.volume_m3,
        temperature_band=request.temperature_band,
        turnover_class=request.turnover_class,
        zones=zones_by_warehouse[warehouse_id],
    )
    shelf = f"{zone}-S{(hash(request.sku) % 48) + 1:02d}"
    reason = f"Zone selected by constraints (temp={request.temperature_band}, turnover={request.turnover_class})"
    return PlacementRecommendation(sku=request.sku, zone=zone, shelf=shelf, reason=reason)


@app.post("/placement/assign")
async def assign_placement(request: PlacementAssignRequest) -> dict:
    _assert_permission(request.actor_role, "placement:write")
    assignments.append(request.model_dump(mode="json"))
    return {"status": "assigned", "total_assignments": len(assignments)}


@app.put("/warehouse/zones")
async def update_zones(request: ZoneConfigRequest) -> dict:
    _assert_permission(request.actor_role, "placement:write")
    zones_by_warehouse[request.warehouse_id] = request.zones
    return {"status": "updated", "warehouse_id": request.warehouse_id, "zones": len(request.zones)}


@app.get("/warehouse/map/{warehouse_id}")
async def warehouse_map(warehouse_id: str, role: str = "warehouse_worker") -> dict:
    _assert_permission(role, "placement:read")
    zones = zones_by_warehouse[warehouse_id]
    return {
        "warehouse_id": warehouse_id,
        "zones": zones,
        "render_hint": {
            "type": "2d-grid",
            "legend": ["cool", "ambient", "secure", "bulk"],
            "frontend_library": "ECharts",
        },
    }
