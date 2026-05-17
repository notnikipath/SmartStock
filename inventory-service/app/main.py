from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

from fastapi import FastAPI, HTTPException

from shared.smartstock_common import (
    Settings,
    apply_arrival,
    build_audit_event,
    consume_stock,
    has_permission,
    total_available,
)
from shared.smartstock_common.events import EventPublisher, build_event
from shared.smartstock_common.schemas import (
    InventoryMovementRequest,
    MovementType,
    RotationPolicy,
    StockBatch,
)

settings = Settings(service_name="inventory-service", service_port=8001)
app = FastAPI(title="SmartStock Inventory Service", version="1.0.0")

stock_state: dict[str, dict[str, list[StockBatch]]] = defaultdict(lambda: defaultdict(list))
audit_log: list[dict] = []


def _assert_permission(role: str, action: str) -> None:
    if not has_permission(role, action):
        raise HTTPException(status_code=403, detail=f"Role {role} cannot perform {action}")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.post("/movements/register")
async def register_movement(request: InventoryMovementRequest) -> dict:
    _assert_permission(request.actor_role, "inventory:write")

    movement_id = str(uuid4())
    updated_skus: list[str] = []
    warnings: list[str] = []

    warehouse_stock = stock_state[request.warehouse_id]
    for item in request.items:
        sku_batches = warehouse_stock[item.sku]
        if request.movement_type == MovementType.ARRIVAL:
            batch = StockBatch(
                sku=item.sku,
                batch_id=item.batch_id or f"BATCH-{uuid4().hex[:8]}",
                quantity=item.quantity,
                expiry_date=item.expiry_date,
                serial_numbers=item.serial_numbers,
                unit_cost=item.unit_cost,
                temperature_band=item.temperature_band,
            )
            warehouse_stock[item.sku] = apply_arrival(sku_batches, batch)
            updated_skus.append(item.sku)
            continue

        if request.movement_type in {MovementType.SHIPMENT, MovementType.TRANSFER}:
            updated_batches, consumed = consume_stock(
                sku_batches,
                item.quantity,
                request.policy or RotationPolicy.FIFO,
            )
            warehouse_stock[item.sku] = updated_batches
            updated_skus.append(item.sku)
            if consumed < item.quantity:
                warnings.append(f"Insufficient stock for {item.sku}: {consumed}/{item.quantity}")
            continue

        if request.movement_type == MovementType.ADJUSTMENT:
            batch = StockBatch(
                sku=item.sku,
                batch_id=item.batch_id or f"ADJ-{uuid4().hex[:8]}",
                quantity=item.quantity,
                expiry_date=item.expiry_date,
                serial_numbers=item.serial_numbers,
                unit_cost=item.unit_cost,
                temperature_band=item.temperature_band,
            )
            warehouse_stock[item.sku] = apply_arrival(sku_batches, batch)
            updated_skus.append(item.sku)

    audit_event = build_audit_event(
        event_type=f"inventory.{request.movement_type.value}",
        actor_id=request.actor_id,
        actor_role=request.actor_role,
        details={
            "movement_id": movement_id,
            "warehouse_id": request.warehouse_id,
            "updated_skus": updated_skus,
            "warnings": warnings,
        },
    )
    audit_log.append(audit_event.model_dump(mode="json"))

    publisher = EventPublisher(settings.rabbitmq_url)
    await publisher.publish(
        routing_key=f"inventory.{request.movement_type.value}",
        event=build_event(
            name="inventory_movement",
            payload={
                "movement_id": movement_id,
                "warehouse_id": request.warehouse_id,
                "movement_type": request.movement_type.value,
                "updated_skus": updated_skus,
            },
        ),
    )

    return {"movement_id": movement_id, "updated_skus": updated_skus, "warnings": warnings}


@app.get("/stock/{warehouse_id}/{sku}")
async def get_stock(warehouse_id: str, sku: str, role: str = "logistician") -> dict:
    _assert_permission(role, "inventory:read")
    sku_batches = stock_state[warehouse_id].get(sku, [])
    return {
        "warehouse_id": warehouse_id,
        "sku": sku,
        "total_qty": total_available(sku_batches),
        "batches": [batch.model_dump(mode="json") for batch in sku_batches],
    }


@app.get("/stock/critical/{warehouse_id}")
async def critical_stock(
    warehouse_id: str,
    min_threshold: int = 20,
    max_threshold: int = 5_000,
    role: str = "logistician",
) -> dict:
    _assert_permission(role, "inventory:read")
    critical_shortage = []
    critical_overstock = []
    for sku, batches in stock_state[warehouse_id].items():
        qty = total_available(batches)
        if qty <= min_threshold:
            critical_shortage.append({"sku": sku, "qty": qty})
        if qty >= max_threshold:
            critical_overstock.append({"sku": sku, "qty": qty})
    return {
        "warehouse_id": warehouse_id,
        "critical_shortage": critical_shortage,
        "critical_overstock": critical_overstock,
    }


@app.get("/stock/expiring/{warehouse_id}")
async def expiring_stock(warehouse_id: str, days: int = 7, role: str = "warehouse_worker") -> dict:
    _assert_permission(role, "inventory:read")
    deadline = date.today() + timedelta(days=days)
    expiring = []
    for sku, batches in stock_state[warehouse_id].items():
        for batch in batches:
            if batch.expiry_date and batch.expiry_date <= deadline:
                expiring.append(
                    {
                        "sku": sku,
                        "batch_id": batch.batch_id,
                        "expiry_date": str(batch.expiry_date),
                        "qty": batch.quantity,
                    }
                )
    return {"warehouse_id": warehouse_id, "days": days, "expiring": expiring}


@app.post("/scanner/ingest")
async def ingest_scanner_stream(
    requests: list[InventoryMovementRequest],
    concurrency: int = 8,
) -> dict:
    """
    Optional improvement (Group C-1):
    parallel handling of scanner streams.
    """
    sem = asyncio.Semaphore(max(concurrency, 1))
    started_at = datetime.now(UTC)

    async def _worker(req: InventoryMovementRequest) -> dict:
        async with sem:
            return await register_movement(req)

    processed = await asyncio.gather(*[_worker(request) for request in requests], return_exceptions=True)
    success = sum(1 for item in processed if isinstance(item, dict))
    failed = len(processed) - success

    elapsed_ms = int((datetime.now(UTC) - started_at).total_seconds() * 1000)
    return {"total": len(requests), "success": success, "failed": failed, "elapsed_ms": elapsed_ms}


@app.get("/audit")
async def get_audit(limit: int = 100, role: str = "admin") -> dict:
    _assert_permission(role, "audit:read")
    return {"items": audit_log[-limit:]}
