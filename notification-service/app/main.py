from __future__ import annotations

from datetime import UTC, datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from shared.smartstock_common import NotificationMessage, Settings, has_permission
from shared.smartstock_common.i18n import t

settings = Settings(service_name="notification-service", service_port=8007)
app = FastAPI(title="SmartStock Notification Service", version="1.0.0")

messages: list[dict] = []


class StockAlertRequest(BaseModel):
    sku: str
    warehouse_id: str
    current_qty: int = Field(ge=0)
    min_threshold: int = Field(default=20, ge=0)
    max_threshold: int = Field(default=5000, ge=0)
    recipient: str
    language: str = Field(default="ru", pattern="^(ru|en)$")
    actor_role: str = "logistician"


def _assert_permission(role: str) -> None:
    if not has_permission(role, "optimization:read"):
        raise HTTPException(status_code=403, detail=f"Role {role} cannot send alerts")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.post("/notify/send")
async def send_message(message: NotificationMessage) -> dict:
    messages.append(message.model_dump(mode="json"))
    return {"status": "queued", "count": len(messages)}


@app.post("/notify/stock-alert")
async def stock_alert(request: StockAlertRequest) -> dict:
    _assert_permission(request.actor_role)
    if request.current_qty <= request.min_threshold:
        key = "critical_shortage"
    elif request.current_qty >= request.max_threshold:
        key = "critical_overstock"
    else:
        return {"status": "normal", "sku": request.sku}

    text = f"{t(request.language, key)}: {request.sku} ({request.current_qty})"
    msg = NotificationMessage(
        channel="push",
        subject="Stock Alert",
        body=text,
        recipient=request.recipient,
        created_at=datetime.now(UTC),
    )
    messages.append(msg.model_dump(mode="json"))
    return {"status": "queued", "message": msg.model_dump(mode="json")}


@app.get("/notify/history")
async def history(limit: int = 100) -> dict:
    return {"items": messages[-limit:]}
