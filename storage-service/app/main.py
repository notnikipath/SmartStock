from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from shared.smartstock_common import Settings, decrypt_sensitive, encrypt_sensitive, has_permission

settings = Settings(service_name="storage-service", service_port=8008)
app = FastAPI(title="SmartStock Storage Service", version="1.0.0")

operation_logs: list[dict[str, Any]] = []
documents: list[dict[str, Any]] = []


class OperationLogRequest(BaseModel):
    operation_type: str
    payload: dict[str, Any]
    actor_id: str
    actor_role: str


class DocumentMetaRequest(BaseModel):
    filename: str
    content_type: str
    size_bytes: int = Field(ge=0)
    bucket_path: str
    counterparty: str | None = None
    price: float | None = None
    actor_role: str = "admin"


def _assert_permission(role: str, action: str) -> None:
    if not has_permission(role, action):
        raise HTTPException(status_code=403, detail=f"Role {role} cannot perform {action}")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.post("/logs/operation")
async def log_operation(request: OperationLogRequest) -> dict:
    _assert_permission(request.actor_role, "audit:write")
    log_item = {
        "id": str(uuid4()),
        "operation_type": request.operation_type,
        "payload": request.payload,
        "actor_id": request.actor_id,
        "actor_role": request.actor_role,
        "created_at": datetime.now(UTC).isoformat(),
    }
    operation_logs.append(log_item)
    return {"status": "stored", "id": log_item["id"]}


@app.get("/logs/operation")
async def get_operations(limit: int = 100, role: str = "admin") -> dict:
    _assert_permission(role, "audit:read")
    return {"items": operation_logs[-limit:]}


@app.post("/documents/metadata")
async def create_document_metadata(request: DocumentMetaRequest) -> dict:
    _assert_permission(request.actor_role, "audit:write")
    encrypted_counterparty = encrypt_sensitive(request.counterparty or "", settings.encryption_key)
    encrypted_price = encrypt_sensitive(
        str(request.price) if request.price is not None else "",
        settings.encryption_key,
    )

    item = {
        "id": str(uuid4()),
        "filename": request.filename,
        "content_type": request.content_type,
        "size_bytes": request.size_bytes,
        "bucket_path": request.bucket_path,
        "counterparty_enc": encrypted_counterparty,
        "price_enc": encrypted_price,
        "created_at": datetime.now(UTC).isoformat(),
    }
    documents.append(item)
    return {"status": "stored", "id": item["id"]}


@app.get("/documents/metadata")
async def get_document_metadata(limit: int = 100, reveal_sensitive: bool = False, role: str = "admin") -> dict:
    _assert_permission(role, "audit:read")
    items = documents[-limit:]
    if not reveal_sensitive:
        return {"items": items}

    decrypted = []
    for item in items:
        copy = dict(item)
        copy["counterparty"] = decrypt_sensitive(copy.get("counterparty_enc", ""), settings.encryption_key)
        copy["price"] = decrypt_sensitive(copy.get("price_enc", ""), settings.encryption_key)
        decrypted.append(copy)
    return {"items": decrypted}
