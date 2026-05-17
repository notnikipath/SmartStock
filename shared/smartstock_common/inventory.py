from __future__ import annotations

from datetime import datetime

from .schemas import RotationPolicy, StockBatch


def apply_arrival(existing_batches: list[StockBatch], new_batch: StockBatch) -> list[StockBatch]:
    """Merge arrival into existing stock by batch id, preserving traceability."""
    merged = list(existing_batches)
    for idx, batch in enumerate(merged):
        if batch.batch_id == new_batch.batch_id and batch.sku == new_batch.sku:
            updated_qty = batch.quantity + new_batch.quantity
            merged[idx] = batch.model_copy(
                update={
                    "quantity": updated_qty,
                    "serial_numbers": batch.serial_numbers + new_batch.serial_numbers,
                }
            )
            return merged
    merged.append(new_batch)
    return merged


def _sorted_batches(batches: list[StockBatch], policy: RotationPolicy) -> list[StockBatch]:
    if policy == RotationPolicy.FEFO:
        max_expiry = datetime.max.date()
        return sorted(
            batches,
            key=lambda batch: (
                batch.expiry_date or max_expiry,
                batch.received_at,
            ),
        )
    return sorted(batches, key=lambda batch: batch.received_at)


def consume_stock(
    batches: list[StockBatch],
    requested_qty: int,
    policy: RotationPolicy = RotationPolicy.FIFO,
) -> tuple[list[StockBatch], int]:
    """Consume stock by FIFO or FEFO and return updated batches plus consumed qty."""
    if requested_qty <= 0:
        return batches, 0

    working = _sorted_batches(list(batches), policy)
    remaining = requested_qty
    consumed = 0
    updated: list[StockBatch] = []

    for batch in working:
        if remaining <= 0:
            updated.append(batch)
            continue
        if batch.quantity <= remaining:
            consumed += batch.quantity
            remaining -= batch.quantity
            continue
        consumed += remaining
        updated.append(batch.model_copy(update={"quantity": batch.quantity - remaining}))
        remaining = 0

    return updated, consumed


def total_available(batches: list[StockBatch]) -> int:
    return sum(batch.quantity for batch in batches)
