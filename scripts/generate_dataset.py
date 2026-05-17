from __future__ import annotations

import argparse
import csv
import random
from datetime import date, timedelta
from pathlib import Path

CATEGORIES = ["food", "fmcg", "electronics", "raw_material", "medical"]
WAREHOUSES = ["WH-001", "WH-002", "WH-003"]


def _seasonal_multiplier(day_index: int) -> float:
    weekday = day_index % 7
    if weekday in (5, 6):
        return 1.12
    if day_index % 30 in (0, 1, 2):
        return 1.08
    return 1.0


def generate_dataset(sku_count: int, days: int, output_dir: Path, seed: int = 42) -> None:
    random.seed(seed)
    output_dir.mkdir(parents=True, exist_ok=True)

    products_path = output_dir / "products.csv"
    sales_path = output_dir / "sales_history.csv"
    stock_path = output_dir / "stock_snapshot.csv"

    today = date.today()
    start_day = today - timedelta(days=days)

    with (
        products_path.open("w", newline="", encoding="utf-8") as products_fp,
        sales_path.open("w", newline="", encoding="utf-8") as sales_fp,
        stock_path.open("w", newline="", encoding="utf-8") as stock_fp,
    ):
        products_writer = csv.writer(products_fp)
        sales_writer = csv.writer(sales_fp)
        stock_writer = csv.writer(stock_fp)

        products_writer.writerow(
            [
                "sku",
                "name_ru",
                "name_en",
                "category",
                "warehouse_id",
                "unit_cost",
                "base_price",
                "lead_time_days",
                "shelf_life_days",
            ]
        )
        sales_writer.writerow(["date", "warehouse_id", "sku", "units_sold", "promo_flag", "holiday_flag"])
        stock_writer.writerow(["warehouse_id", "sku", "current_qty", "reserved_qty", "updated_at"])

        for idx in range(1, sku_count + 1):
            sku = f"SKU-{idx:05d}"
            category = CATEGORIES[idx % len(CATEGORIES)]
            warehouse = WAREHOUSES[idx % len(WAREHOUSES)]

            unit_cost = round(random.uniform(5.0, 200.0), 2)
            base_price = round(unit_cost * random.uniform(1.15, 1.8), 2)
            lead_time_days = random.randint(1, 14)
            shelf_life_days = random.choice([7, 14, 30, 60, 180, 365])

            products_writer.writerow(
                [
                    sku,
                    f"Товар {idx}",
                    f"Product {idx}",
                    category,
                    warehouse,
                    unit_cost,
                    base_price,
                    lead_time_days,
                    shelf_life_days,
                ]
            )

            baseline = random.randint(3, 40)
            for day_idx in range(days):
                day = start_day + timedelta(days=day_idx)
                promo_flag = 1 if day_idx % 21 in (0, 1, 2) else 0
                holiday_flag = 1 if day_idx % 60 in (20, 21) else 0
                seasonal = _seasonal_multiplier(day_idx)
                promo_boost = 1.35 if promo_flag else 1.0
                holiday_boost = 1.2 if holiday_flag else 1.0
                noise = random.uniform(0.94, 1.06)
                demand = max(0, round(baseline * seasonal * promo_boost * holiday_boost * noise))
                sales_writer.writerow([day.isoformat(), warehouse, sku, demand, promo_flag, holiday_flag])

            current_qty = random.randint(0, 1200)
            reserved_qty = random.randint(0, min(current_qty, 200))
            stock_writer.writerow([warehouse, sku, current_qty, reserved_qty, today.isoformat()])

    print(f"Generated {products_path}")
    print(f"Generated {sales_path}")
    print(f"Generated {stock_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate SmartStock demo dataset")
    parser.add_argument("--skus", type=int, default=10_000)
    parser.add_argument("--days", type=int, default=180)
    parser.add_argument("--output", type=Path, default=Path("data/dataset"))
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    generate_dataset(sku_count=args.skus, days=args.days, output_dir=args.output, seed=args.seed)
