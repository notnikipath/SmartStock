from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from shared.smartstock_common import Settings, has_permission
from shared.smartstock_common.schemas import IntegrationJob

settings = Settings(service_name="integration-service", service_port=8006)
app = FastAPI(title="SmartStock Integration Service", version="1.0.0")

SUPPORTED_CONNECTORS = {
    "erp",
    "wms",
    "crm",
    "ozon",
    "wildberries",
    "gps_glonass",
    "one_c",
    "edi_supplier",
    "scanner_gateway",
}

jobs: list[IntegrationJob] = []


class SyncRequest(BaseModel):
    source: str
    target: str
    payload: dict
    callback_url: str | None = None
    max_retries: int = Field(default=3, ge=0, le=10)
    actor_role: str = "admin"


class WebhookRequest(BaseModel):
    provider: str
    event_type: str
    payload: dict


def _assert_permission(role: str, action: str) -> None:
    if not has_permission(role, action):
        raise HTTPException(status_code=403, detail=f"Role {role} cannot perform {action}")


async def _post_callback(callback_url: str, payload: dict) -> bool:
    timeout = httpx.Timeout(8.0, connect=3.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(callback_url, json=payload)
        return response.status_code < 300


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.get("/connectors")
async def connectors() -> dict:
    return {"supported": sorted(SUPPORTED_CONNECTORS)}


@app.post("/sync/{connector}")
async def sync_connector(connector: str, request: SyncRequest) -> dict:
    _assert_permission(request.actor_role, "integration:write")
    if connector not in SUPPORTED_CONNECTORS:
        raise HTTPException(status_code=404, detail=f"Connector {connector} is not configured")

    job = IntegrationJob(source=request.source, target=request.target, payload=request.payload)
    for attempt in range(request.max_retries + 1):
        try:
            await asyncio.sleep(0.02)
            if connector == "scanner_gateway" and request.payload.get("simulate_failure"):
                raise RuntimeError("scanner offline")
            if request.callback_url:
                callback_ok = await _post_callback(
                    request.callback_url,
                    {"connector": connector, "status": "synced", "payload": request.payload},
                )
                if not callback_ok:
                    raise RuntimeError("callback_failed")
            jobs.append(job)
            return {"status": "synced", "connector": connector, "attempt": attempt + 1}
        except Exception as exc:
            job.retries += 1
            job.last_error = str(exc)
            await asyncio.sleep(0.05 * (attempt + 1))
            if attempt == request.max_retries:
                jobs.append(job)
                return {
                    "status": "failed",
                    "connector": connector,
                    "retries": job.retries,
                    "last_error": job.last_error,
                }
    return {"status": "failed", "connector": connector}


@app.post("/webhooks")
async def incoming_webhook(request: WebhookRequest) -> dict:
    jobs.append(
        IntegrationJob(
            source=request.provider,
            target="smartstock",
            payload={
                "event_type": request.event_type,
                "payload": request.payload,
                "received_at": datetime.now(UTC).isoformat(),
            },
        )
    )
    return {"status": "accepted"}


@app.get("/jobs")
async def get_jobs(limit: int = 100, role: str = "admin") -> dict:
    _assert_permission(role, "integration:read")
    data = [job.model_dump(mode="json") for job in jobs[-limit:]]
    return {"items": data}
