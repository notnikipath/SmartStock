# Deployment Guide

## Prerequisites

- Docker 24+
- Docker Compose v2+
- (Optional) Python 3.11+ for local tests/scripts

## Local run

1. Go to project root `6_task_smartstock`.
2. Verify env file:
   - `.env` is included for local launch.
   - Adjust secrets before production.
3. Start stack:

```bash
docker compose up --build -d
```

4. Verify:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/services/health
```

5. Stop:

```bash
docker compose down
```

## Dataset generation

```bash
python scripts/generate_dataset.py --skus 10000 --days 180 --output data/dataset
```

## Accuracy evaluation

```bash
python scripts/evaluate_forecast.py --sales data/dataset/sales_history.csv
```

## Production recommendations

- Use managed PostgreSQL/ClickHouse/Redis/RabbitMQ and external object storage.
- Replace static encryption key with KMS-backed secret.
- Add OIDC/JWT auth in API Gateway.
- Add autoscaling for forecast and optimization services.
- Set separate queues for high-priority alerts and batch recalculation jobs.
