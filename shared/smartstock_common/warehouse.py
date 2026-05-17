from __future__ import annotations

from .schemas import ProductCategory


def _temperature_match(zone_temp: str, requested_temp: str) -> int:
    if zone_temp == requested_temp:
        return 50
    if zone_temp == "ambient" and requested_temp == "cool":
        return -20
    return -100


def _turnover_bonus(zone_fast_pick: bool, turnover_class: str) -> int:
    if turnover_class == "A":
        return 25 if zone_fast_pick else -5
    if turnover_class == "C":
        return 5 if not zone_fast_pick else -5
    return 10


def recommend_zone(
    category: ProductCategory,
    weight_kg: float,
    volume_m3: float,
    temperature_band: str,
    turnover_class: str,
    zones: list[dict[str, object]],
) -> str:
    best_zone = "ZONE_DEFAULT"
    best_score = -10_000

    for zone in zones:
        score = 0
        zone_temp = str(zone.get("temperature_band", "ambient"))
        zone_name = str(zone.get("name", "ZONE_DEFAULT"))
        max_weight = float(zone.get("max_weight_kg", 1000))
        max_volume = float(zone.get("max_volume_m3", 500))
        fast_pick = bool(zone.get("fast_pick", False))
        supports_medical = bool(zone.get("supports_medical", False))
        high_security = bool(zone.get("high_security", False))

        score += _temperature_match(zone_temp, temperature_band)
        score += _turnover_bonus(fast_pick, turnover_class)

        if weight_kg > max_weight or volume_m3 > max_volume:
            score -= 150

        if category == ProductCategory.MEDICAL and not supports_medical:
            score -= 120
        if category == ProductCategory.ELECTRONICS and high_security:
            score += 30
        if category == ProductCategory.RAW_MATERIAL and fast_pick:
            score -= 20

        if score > best_score:
            best_score = score
            best_zone = zone_name

    return best_zone
