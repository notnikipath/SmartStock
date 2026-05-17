from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from .schemas import AuditEvent, Role


def build_audit_event(
    event_type: str,
    actor_id: str,
    actor_role: Role | str,
    details: dict[str, Any],
) -> AuditEvent:
    return AuditEvent(
        event_type=event_type,
        actor_id=actor_id,
        actor_role=actor_role,
        details=details,
        created_at=datetime.now(UTC),
    )


def audit_event_json(event: AuditEvent) -> str:
    return json.dumps(event.model_dump(), ensure_ascii=False, default=str)
