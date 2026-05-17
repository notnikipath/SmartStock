from shared.smartstock_common.optimization import dynamic_price, generate_reorder_recommendation


def test_recommendation_for_low_stock() -> None:
    recommendation = generate_reorder_recommendation(
        sku="SKU-1",
        warehouse_id="WH-001",
        current_stock=5,
        demand_history=[12, 10, 11, 13, 12, 15, 14],
        forecast_values=[14, 15, 16, 15, 14, 13, 12],
        lead_time_days=3,
        min_order_qty=10,
    )
    assert recommendation.recommended_qty >= 10
    assert recommendation.reason == "stock_below_reorder_point"


def test_dynamic_price_increase_when_cover_is_low() -> None:
    price = dynamic_price(base_price=100.0, days_of_cover=3.0, demand_score=1.3)
    assert price > 100.0


def test_dynamic_price_decrease_when_cover_is_high() -> None:
    price = dynamic_price(base_price=100.0, days_of_cover=60.0, demand_score=0.7)
    assert price < 100.0
