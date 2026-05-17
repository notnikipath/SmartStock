from __future__ import annotations

from datetime import UTC, date, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ProductCategory(str, Enum):
    FOOD = "food"
    FMCG = "fmcg"
    ELECTRONICS = "electronics"
    RAW_MATERIAL = "raw_material"
    MEDICAL = "medical"


class MovementType(str, Enum):
    ARRIVAL = "arrival"
    SHIPMENT = "shipment"
    TRANSFER = "transfer"
    ADJUSTMENT = "adjustment"


class RotationPolicy(str, Enum):
    FIFO = "fifo"
    FEFO = "fefo"


class Role(str, Enum):
    WAREHOUSE = "warehouse_worker"
    LOGISTICIAN = "logistician"
    ANALYST = "analyst"
    ADMIN = "admin"


class MovementItem(BaseModel):
    sku: str
    quantity: int = Field(gt=0)
    unit_cost: float | None = None
    expiry_date: date | None = None
    serial_numbers: list[str] = Field(default_factory=list)
    batch_id: str | None = None
    temperature_band: str | None = None
    dimensions_cm: tuple[float, float, float] | None = None
    weight_kg: float | None = None


class InventoryMovementRequest(BaseModel):
    warehouse_id: str
    movement_type: MovementType
    policy: RotationPolicy = RotationPolicy.FIFO
    actor_id: str
    actor_role: Role
    items: list[MovementItem]
    source_zone: str | None = None
    target_zone: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class StockBatch(BaseModel):
    sku: str
    batch_id: str
    quantity: int = Field(ge=0)
    expiry_date: date | None = None
    serial_numbers: list[str] = Field(default_factory=list)
    unit_cost: float | None = None
    temperature_band: str | None = None
    received_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ForecastRequest(BaseModel):
    sku: str
    warehouse_id: str
    history: list[float] = Field(min_length=7)
    horizon_days: int = Field(default=7, ge=1, le=90)
    season_period: int = Field(default=7, ge=2, le=30)
    promotion_calendar: dict[str, float] = Field(default_factory=dict)
    holiday_calendar: dict[str, float] = Field(default_factory=dict)
    manual_multiplier: float | None = Field(default=None, gt=0.0)


class ForecastResult(BaseModel):
    sku: str
    warehouse_id: str
    generated_at: datetime
    horizon_days: int
    values: list[float]
    anomaly_indices: list[int] = Field(default_factory=list)
    model_name: str = "hybrid-seasonal-baseline"


class ReorderPolicy(BaseModel):
    sku: str
    warehouse_id: str
    lead_time_days: int = Field(default=3, ge=1, le=90)
    service_level_z: float = Field(default=1.65, ge=0.0, le=4.0)
    min_order_qty: int = Field(default=1, ge=1)
    max_stock_days: int = Field(default=45, ge=1)
    rotation_policy: RotationPolicy = RotationPolicy.FEFO


class ReorderRecommendation(BaseModel):
    sku: str
    warehouse_id: str
    recommended_qty: int
    reorder_point: float
    safety_stock: float
    expected_stockout_risk: float = Field(ge=0.0, le=1.0)
    reason: str
    dynamic_price: float | None = None


class PlacementRequest(BaseModel):
    sku: str
    category: ProductCategory
    quantity: int = Field(gt=0)
    temperature_band: str = "ambient"
    weight_kg: float = Field(default=1.0, gt=0.0)
    volume_m3: float = Field(default=0.01, gt=0.0)
    turnover_class: str = Field(default="B", pattern="^[ABC]$")


class PlacementRecommendation(BaseModel):
    sku: str
    zone: str
    shelf: str
    reason: str


class NotificationMessage(BaseModel):
    channel: str = Field(pattern="^(email|sms|push|webhook)$")
    subject: str
    body: str
    recipient: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AuditEvent(BaseModel):
    event_type: str
    actor_id: str
    actor_role: Role | str
    details: dict[str, Any]
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class KPIResult(BaseModel):
    warehouse_id: str
    turnover_ratio: float
    spoilage_loss: float
    stockout_rate: float
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class IntegrationJob(BaseModel):
    source: str
    target: str
    payload: dict[str, Any]
    retries: int = 0
    last_error: str | None = None


class ShipmentProcessingResult(BaseModel):
    movement_id: str
    updated_skus: list[str]
    recommendations: list[ReorderRecommendation]
    warnings: list[str] = Field(default_factory=list)
