# API Documentation

## OpenAPI / Swagger URLs

- API Gateway: `http://localhost:8000/docs`
- Inventory: `http://localhost:8001/docs`
- Forecast: `http://localhost:8002/docs`
- Optimization: `http://localhost:8003/docs`
- Placement: `http://localhost:8004/docs`
- Analytics: `http://localhost:8005/docs`
- Integration: `http://localhost:8006/docs`
- Notification: `http://localhost:8007/docs`
- Storage: `http://localhost:8008/docs`

## Key endpoints by module

### API Gateway

- `GET /health`
- `GET /services/health`
- `POST /workflow/new-shipment`
- `POST /workflow/recalculate`

### Inventory Service

- `POST /movements/register`
- `GET /stock/{warehouse_id}/{sku}`
- `GET /stock/critical/{warehouse_id}`
- `GET /stock/expiring/{warehouse_id}`
- `POST /scanner/ingest`
- `GET /audit`

### Forecast Service

- `POST /forecast/predict`
- `POST /forecast/bulk`
- `POST /forecast/manual-adjustment`
- `GET /forecast/{warehouse_id}/{sku}`
- `POST /forecast/accuracy`
- `GET /anomalies/{warehouse_id}/{sku}`

### Optimization Service

- `PUT /policy`
- `GET /policy/{warehouse_id}/{sku}`
- `POST /recommendation`
- `POST /recommendation/bulk`
- `POST /dynamic-price`

### Placement Service

- `POST /placement/recommend`
- `POST /placement/assign`
- `PUT /warehouse/zones`
- `GET /warehouse/map/{warehouse_id}`

### Analytics Service

- `POST /kpi/calculate`
- `GET /dashboards/{role}`
- `PUT /dashboards`
- `GET /reports/turnover/{warehouse_id}`
- `GET /reports/spoilage/{warehouse_id}`

### Integration Service

- `GET /connectors`
- `POST /sync/{connector}`
- `POST /webhooks`
- `GET /jobs`

### Notification Service

- `POST /notify/send`
- `POST /notify/stock-alert`
- `GET /notify/history`

### Storage Service

- `POST /logs/operation`
- `GET /logs/operation`
- `POST /documents/metadata`
- `GET /documents/metadata`
