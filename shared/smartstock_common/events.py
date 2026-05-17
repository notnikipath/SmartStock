from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

try:
    import aio_pika
except ImportError:  # pragma: no cover
    aio_pika = None


@dataclass
class Event:
    name: str
    payload: dict[str, Any]
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def as_dict(self) -> dict[str, Any]:
        return {"name": self.name, "payload": self.payload, "created_at": self.created_at}


def build_event(name: str, payload: dict[str, Any]) -> Event:
    return Event(name=name, payload=payload)


class EventPublisher:
    def __init__(self, amqp_url: str, exchange: str = "smartstock.events") -> None:
        self.amqp_url = amqp_url
        self.exchange_name = exchange

    async def publish(self, routing_key: str, event: Event) -> bool:
        if aio_pika is None:
            return False
        try:
            connection = await aio_pika.connect_robust(self.amqp_url)
            async with connection:
                channel = await connection.channel()
                exchange = await channel.declare_exchange(self.exchange_name, aio_pika.ExchangeType.TOPIC, durable=True)
                body = json.dumps(event.as_dict(), default=str).encode("utf-8")
                message = aio_pika.Message(body=body, delivery_mode=aio_pika.DeliveryMode.PERSISTENT)
                await exchange.publish(message, routing_key=routing_key)
            return True
        except Exception:
            return False


async def publish_batch(publisher: EventPublisher, items: list[tuple[str, Event]]) -> int:
    if not items:
        return 0
    tasks = [publisher.publish(rk, evt) for rk, evt in items]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return sum(1 for result in results if result is True)
