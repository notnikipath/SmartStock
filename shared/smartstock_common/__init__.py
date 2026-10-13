"""Shared business primitives for SmartStock microservices."""

from .audit import build_audit_event
from .forecasting import detect_anomalies, forecast_demand, mape
from .inventory import apply_arrival, consume_stock, total_available
from .optimization import (
    calculate_reorder_point,
    calculate_safety_stock,
    dynamic_price,
    generate_reorder_recommendation,
)
from .schemas import (
    AuditEvent,
    ForecastRequest,
    ForecastResult,
    InventoryMovementRequest,
    KPIResult,
    NotificationMessage,
    PlacementRecommendation,
    PlacementRequest,
    ProductCategory,
    ReorderPolicy,
    Role,
    RotationPolicy,
)
from .security import decrypt_sensitive, encrypt_sensitive, has_permission
from .settings import Settings
from .warehouse import recommend_zone

__all__ = [
    "AuditEvent",
    "ForecastRequest",
    "ForecastResult",
    "KPIResult",
    "InventoryMovementRequest",
    "NotificationMessage",
    "PlacementRecommendation",
    "PlacementRequest",
    "ProductCategory",
    "ReorderPolicy",
    "Role",
    "RotationPolicy",
    "Settings",
    "apply_arrival",
    "build_audit_event",
    "calculate_reorder_point",
    "calculate_safety_stock",
    "consume_stock",
    "decrypt_sensitive",
    "detect_anomalies",
    "dynamic_price",
    "encrypt_sensitive",
    "forecast_demand",
    "generate_reorder_recommendation",
    "has_permission",
    "mape",
    "recommend_zone",
    "total_available",
]
