from __future__ import annotations

from datetime import UTC, datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from shared.smartstock_common import KPIResult, Settings, has_permission

settings = Settings(service_name="analytics-service", service_port=8005)
app = FastAPI(title="SmartStock Analytics Service", version="1.0.0")

dashboard_templates: dict[str, dict] = {
    "warehouse_worker": {
        "widgets": ["current_stock_heatmap", "expiring_items", "pending_putaway"],
        "refresh_sec": 15,
    },
    "logistician": {
        "widgets": ["reorder_alerts", "supplier_lead_time", "route_eta"],
        "refresh_sec": 30,
    },
    "analyst": {
        "widgets": ["mape_trend", "turnover_ratio", "spoilage_loss", "anomaly_stream"],
        "refresh_sec": 60,
    },
    "admin": {
        "widgets": ["warehouse_kpi", "integration_failures", "user_audit", "financial_overview"],
        "refresh_sec": 30,
    },
}


class KPIInput(BaseModel):
    warehouse_id: str
    average_inventory_value: float = Field(gt=0)
    cogs_value: float = Field(gt=0, description="Cost of goods sold")
    spoiled_value: float = Field(ge=0)
    stockout_events: int = Field(ge=0)
    total_order_lines: int = Field(gt=0)


class DashboardUpdateRequest(BaseModel):
    role: str
    widgets: list[str] = Field(min_length=1)
    refresh_sec: int = Field(default=30, ge=5, le=3600)
    actor_role: str = "admin"


def _assert_permission(role: str, action: str) -> None:
    if not has_permission(role, action):
        raise HTTPException(status_code=403, detail=f"Role {role} cannot perform {action}")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.post("/kpi/calculate", response_model=KPIResult)
async def calculate_kpi(request: KPIInput, role: str = "analyst") -> KPIResult:
    _assert_permission(role, "analytics:read")
    turnover_ratio = request.cogs_value / request.average_inventory_value
    spoilage_loss = request.spoiled_value
    stockout_rate = request.stockout_events / request.total_order_lines
    return KPIResult(
        warehouse_id=request.warehouse_id,
        turnover_ratio=round(turnover_ratio, 4),
        spoilage_loss=round(spoilage_loss, 2),
        stockout_rate=round(stockout_rate, 4),
        generated_at=datetime.now(UTC),
    )


@app.get("/dashboards/{role}")
async def role_dashboard(role: str) -> dict:
    config = dashboard_templates.get(role, dashboard_templates["analyst"])
    return {"role": role, "dashboard": config, "i18n": ["ru", "en"]}


@app.put("/dashboards")
async def update_dashboard(request: DashboardUpdateRequest) -> dict:
    _assert_permission(request.actor_role, "analytics:read")
    dashboard_templates[request.role] = {"widgets": request.widgets, "refresh_sec": request.refresh_sec}
    return {"status": "updated", "role": request.role}


@app.get("/reports/turnover/{warehouse_id}")
async def turnover_report(warehouse_id: str, role: str = "analyst") -> dict:
    _assert_permission(role, "analytics:read")
    return {
        "warehouse_id": warehouse_id,
        "series": [
            {"month": "2026-01", "turnover_ratio": 4.1},
            {"month": "2026-02", "turnover_ratio": 4.4},
            {"month": "2026-03", "turnover_ratio": 4.6},
        ],
    }


@app.get("/reports/spoilage/{warehouse_id}")
async def spoilage_report(warehouse_id: str, role: str = "analyst") -> dict:
    _assert_permission(role, "analytics:read")
    return {
        "warehouse_id": warehouse_id,
        "series": [
            {"month": "2026-01", "spoilage_loss": 14500.0},
            {"month": "2026-02", "spoilage_loss": 13900.0},
            {"month": "2026-03", "spoilage_loss": 12600.0},
        ],
    }
