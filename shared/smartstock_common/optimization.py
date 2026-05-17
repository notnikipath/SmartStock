from __future__ import annotations

from math import sqrt

from .schemas import ReorderRecommendation


def calculate_safety_stock(
    avg_daily_demand: float,
    demand_std: float,
    lead_time_days: int,
    service_level_z: float = 1.65,
) -> float:
    lead_time_variability = sqrt(max(lead_time_days, 1))
    return round(service_level_z * demand_std * lead_time_variability, 2)


def calculate_reorder_point(avg_daily_demand: float, lead_time_days: int, safety_stock: float) -> float:
    return round(avg_daily_demand * lead_time_days + safety_stock, 2)


def dynamic_price(
    base_price: float,
    days_of_cover: float,
    demand_score: float,
    min_margin: float = 0.05,
    max_markup: float = 0.35,
) -> float:
    """
    Dynamic pricing:
    - low cover + high demand => markup
    - high cover + low demand => markdown, but margin protected
    """
    if base_price <= 0:
        return 0.0

    pressure = (demand_score - 1.0) + (1.0 - min(days_of_cover / 30.0, 2.0))
    pressure = max(-1.0, min(1.0, pressure))

    if pressure >= 0:
        factor = 1.0 + pressure * max_markup
    else:
        max_discount = 1.0 - min_margin
        factor = max(min_margin, 1.0 + pressure * max_discount)
    return round(base_price * factor, 2)


def generate_reorder_recommendation(
    sku: str,
    warehouse_id: str,
    current_stock: int,
    demand_history: list[float],
    forecast_values: list[float],
    lead_time_days: int = 3,
    service_level_z: float = 1.65,
    min_order_qty: int = 1,
    base_price: float | None = None,
) -> ReorderRecommendation:
    avg_demand = (sum(demand_history) / len(demand_history)) if demand_history else 0.0
    variance = 0.0
    if len(demand_history) > 1:
        mu = avg_demand
        variance = sum((x - mu) ** 2 for x in demand_history) / (len(demand_history) - 1)
    demand_std = sqrt(variance)

    safety_stock = calculate_safety_stock(
        avg_daily_demand=avg_demand,
        demand_std=demand_std,
        lead_time_days=lead_time_days,
        service_level_z=service_level_z,
    )
    reorder_point = calculate_reorder_point(avg_demand, lead_time_days, safety_stock)

    near_term_demand = sum(forecast_values[:lead_time_days]) if forecast_values else avg_demand * lead_time_days
    gap = max(0.0, near_term_demand + safety_stock - current_stock)
    recommended_qty = int(max(min_order_qty, round(gap)))

    stockout_risk = 1.0 if current_stock <= 0 else max(0.0, min(1.0, gap / max(current_stock, 1)))
    reason = "stock_below_reorder_point" if current_stock < reorder_point else "stock_sufficient"

    dyn_price = None
    if base_price is not None:
        weekly_demand = sum(forecast_values[:7]) if forecast_values else max(avg_demand * 7, 1.0)
        days_cover = current_stock / max(weekly_demand / 7.0, 0.1)
        demand_score = max(0.5, min(1.5, weekly_demand / max(avg_demand * 7, 1.0)))
        dyn_price = dynamic_price(base_price, days_cover, demand_score)

    if reason == "stock_sufficient":
        recommended_qty = 0

    return ReorderRecommendation(
        sku=sku,
        warehouse_id=warehouse_id,
        recommended_qty=recommended_qty,
        reorder_point=reorder_point,
        safety_stock=safety_stock,
        expected_stockout_risk=round(stockout_risk, 3),
        reason=reason,
        dynamic_price=dyn_price,
    )
