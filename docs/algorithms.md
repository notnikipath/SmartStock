# Forecasting and Optimization Algorithms

## 1) Demand forecasting

Current baseline model in `shared/smartstock_common/forecasting.py`:

- Seasonal window (default 7 days).
- Trend component as difference between last and previous seasonal windows.
- Multipliers for promo and holiday calendars.
- Optional manual multiplier from analyst.

Formula (per day `d`):

`forecast[d] = max(0, seasonal[d] + trend * (d / season_period)) * promo[d] * holiday[d] * manual`

## 2) Anomaly detection

- Z-score over historical demand.
- Index is marked anomalous when `|z| >= 3.0`.
- Used to signal outliers (promotions, data glitches, incidents).

## 3) Inventory rotation rules

- `FIFO`: consume by earliest `received_at`.
- `FEFO`: consume by earliest `expiry_date`, fallback to `received_at`.

Implemented in `shared/smartstock_common/inventory.py`.

## 4) Reorder and safety stock

- Safety stock:
  - `SS = Z * sigma_demand * sqrt(lead_time_days)`
- Reorder point:
  - `ROP = avg_daily_demand * lead_time_days + SS`
- Recommendation quantity:
  - `max(min_order_qty, near_term_demand + SS - current_stock)`

Implemented in `shared/smartstock_common/optimization.py`.

## 5) Dynamic pricing (optional feature)

- Inputs: base price, stock coverage in days, demand score.
- Low cover + high demand increases price within configured max markup.
- High cover + weak demand applies markdown with margin floor.

## 6) Placement optimization

- Zone scoring by:
  - temperature compatibility,
  - turnover class (A/B/C),
  - capacity constraints (weight/volume),
  - security requirements,
  - medical support flags.

Implemented in `shared/smartstock_common/warehouse.py`.
