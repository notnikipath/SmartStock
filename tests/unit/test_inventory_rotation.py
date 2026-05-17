from datetime import UTC, date, datetime, timedelta

from shared.smartstock_common.inventory import consume_stock
from shared.smartstock_common.schemas import RotationPolicy, StockBatch


def test_fefo_consumes_earliest_expiry_first() -> None:
    now = datetime.now(UTC)
    batches = [
        StockBatch(
            sku="SKU-1",
            batch_id="A",
            quantity=10,
            expiry_date=date.today() + timedelta(days=12),
            received_at=now,
        ),
        StockBatch(
            sku="SKU-1",
            batch_id="B",
            quantity=10,
            expiry_date=date.today() + timedelta(days=3),
            received_at=now,
        ),
    ]
    updated, consumed = consume_stock(batches, requested_qty=8, policy=RotationPolicy.FEFO)
    assert consumed == 8
    assert updated[0].batch_id == "B"
    assert updated[0].quantity == 2
    assert updated[1].batch_id == "A"
    assert updated[1].quantity == 10


def test_fifo_consumes_oldest_received_first() -> None:
    now = datetime.now(UTC)
    batches = [
        StockBatch(sku="SKU-2", batch_id="OLD", quantity=5, received_at=now),
        StockBatch(sku="SKU-2", batch_id="NEW", quantity=5, received_at=now + timedelta(minutes=10)),
    ]
    updated, consumed = consume_stock(batches, requested_qty=7, policy=RotationPolicy.FIFO)
    assert consumed == 7
    assert updated[0].batch_id == "NEW"
    assert updated[0].quantity == 3
