from __future__ import annotations

import argparse
import csv
import importlib.util
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

spec = importlib.util.spec_from_file_location(
    "smartstock_forecasting",
    ROOT / "shared" / "smartstock_common" / "forecasting.py",
)
if spec is None or spec.loader is None:
    raise RuntimeError("Cannot import forecasting module")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
forecast_demand = module.forecast_demand
mape = module.mape


def evaluate(sales_csv: Path, sample_skus: int = 1000, horizon: int = 7) -> dict:
    demand_by_sku: dict[str, list[float]] = defaultdict(list)
    promo_by_sku: dict[str, list[int]] = defaultdict(list)
    holiday_by_sku: dict[str, list[int]] = defaultdict(list)
    with sales_csv.open("r", encoding="utf-8") as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            sku = row["sku"]
            demand_by_sku[sku].append(float(row["units_sold"]))
            promo_by_sku[sku].append(int(row["promo_flag"]))
            holiday_by_sku[sku].append(int(row["holiday_flag"]))

    all_skus = sorted(demand_by_sku.keys())[:sample_skus]
    sku_scores = []
    for sku in all_skus:
        series = demand_by_sku[sku]
        if len(series) < 30:
            continue
        train = series[:-horizon]
        actual = series[-horizon:]
        promo_future = promo_by_sku[sku][-horizon:]
        holiday_future = holiday_by_sku[sku][-horizon:]
        promo_calendar = {str(idx): 1.35 if flag else 1.0 for idx, flag in enumerate(promo_future)}
        holiday_calendar = {str(idx): 1.2 if flag else 1.0 for idx, flag in enumerate(holiday_future)}
        predicted = forecast_demand(
            history=train,
            horizon_days=horizon,
            season_period=7,
            promotion_calendar=promo_calendar,
            holiday_calendar=holiday_calendar,
        )
        sku_scores.append(mape(actual, predicted))

    avg_mape = round(sum(sku_scores) / len(sku_scores), 2) if sku_scores else 0.0
    return {"sample_skus": len(sku_scores), "horizon_days": horizon, "avg_mape": avg_mape}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate forecast accuracy on generated dataset")
    parser.add_argument("--sales", type=Path, default=Path("data/dataset/sales_history.csv"))
    parser.add_argument("--sample-skus", type=int, default=1000)
    parser.add_argument("--horizon", type=int, default=7)
    parser.add_argument("--report", type=Path, default=Path("docs/report_forecast_accuracy.md"))
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    result = evaluate(args.sales, args.sample_skus, args.horizon)
    report = [
        "# Forecast Accuracy Report",
        "",
        f"- Sample SKU: {result['sample_skus']}",
        f"- Horizon: {result['horizon_days']} days",
        f"- Average MAPE: {result['avg_mape']}%",
        f"- Target met (<15%): {'yes' if result['avg_mape'] < 15 else 'no'}",
    ]
    args.report.write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))
