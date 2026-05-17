from __future__ import annotations

import asyncio

import httpx


async def process_new_shipment() -> None:
    shipment_payload = {
        "movement": {
            "warehouse_id": "WH-001",
            "movement_type": "arrival",
            "policy": "fefo",
            "actor_id": "demo-user",
            "actor_role": "warehouse_worker",
            "items": [
                {
                    "sku": "SKU-00042",
                    "quantity": 120,
                    "unit_cost": 38.5,
                    "batch_id": "DEMO-BATCH-42",
                    "expiry_date": "2026-05-30",
                }
            ],
        },
        "history_by_sku": {
            "SKU-00042": [21, 23, 24, 22, 25, 26, 27, 28, 30, 29, 31, 33, 34, 32]
        },
        "manager_recipient": "manager@smartstock.local",
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post("http://localhost:8000/workflow/new-shipment", json=shipment_payload)
        response.raise_for_status()
        print(response.json())


if __name__ == "__main__":
    asyncio.run(process_new_shipment())
