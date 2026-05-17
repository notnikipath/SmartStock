# Demo Video Script (7-10 min)

## Scene 1. Intro (0:00-0:45)

- Problem: overstock, stockout, spoilage.
- Goal: full inventory lifecycle automation.

## Scene 2. Architecture (0:45-2:00)

- Show microservices map from `docs/architecture.md`.
- Explain operational/analytical stores and queue.

## Scene 3. Live workflow (2:00-5:30)

1. Open `http://localhost:8000/docs`.
2. Call `POST /workflow/new-shipment`.
3. Show:
   - movement registration,
   - forecast values,
   - reorder recommendations,
   - notification trigger.
4. Open `inventory-service` and check `/stock/WH-001/{sku}`.
5. Open `storage-service` and check `/logs/operation`.

## Scene 4. Analytics and dashboards (5:30-7:00)

- Open frontend `http://localhost:5173`.
- Switch RU/EN and roles.
- Show KPI cards and service health panel.

## Scene 5. Accuracy and performance (7:00-8:30)

- Show `docs/report_forecast_accuracy.md`.
- Mention load scripts in `tests/load`.
- Mention target for 10k SKU recommendation under 10 sec.

## Scene 6. Conclusion (8:30-9:00)

- Recap optional enhancements and roadmap:
  - production ML models (Prophet/LightGBM),
  - mobile warehouse app,
  - deeper marketplace integrations.
