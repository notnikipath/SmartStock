# SmartStock

Интеллектуальная распределенная система прогнозирования и оптимизации запасов.

## Что реализовано

- Микросервисная архитектура (9 сервисов + frontend + infra).
- Полный цикл: `учёт -> прогноз -> оптимизация -> отчёт/уведомление`.
- Поддержка категорий:
  - продукты питания,
  - товары повседневного спроса,
  - электроника,
  - сырье и материалы,
  - медикаменты.
- Правила FIFO/FEFO, safety stock, reorder point.
- Ролевой доступ (кладовщик, логист, аналитик, админ), аудит действий.
- Шифрование чувствительных полей в storage.
- RU/EN интерфейс и мультиязычные данные.

## Выбранные опциональные улучшения

1. Динамическое ценообразование (A1).
2. Автоматическое выявление аномалий спроса (A3).
3. Интеграция с GPS/ГЛОНАСС (B1, endpoint connector).
4. Интеграция с 1С (B3, endpoint connector).
5. Параллельная обработка потоков сканеров (C1).
6. Кэширование часто запрашиваемых остатков (C2, Redis-ready).
7. Настраиваемые дашборды под роль (D2).

## Структура проекта

```text
6_task_smartstock/
├── api-gateway/
├── inventory-service/
├── forecast-service/
├── optimization-service/
├── placement-service/
├── analytics-service/
├── integration-service/
├── notification-service/
├── storage-service/
├── frontend/
├── shared/
├── data/dataset/
├── docs/
├── tests/
├── scripts/
└── docker-compose.yml
```

## Быстрый старт

```bash
docker compose up --build -d
```

Проверка:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/services/health
```

Swagger:

- Gateway: `http://localhost:8000/docs`
- Inventory: `http://localhost:8001/docs`
- Forecast: `http://localhost:8002/docs`
- Optimization: `http://localhost:8003/docs`
- Placement: `http://localhost:8004/docs`
- Analytics: `http://localhost:8005/docs`
- Integration: `http://localhost:8006/docs`
- Notification: `http://localhost:8007/docs`
- Storage: `http://localhost:8008/docs`

Frontend:

- `http://localhost:5173`

## Датасет 10 000+ SKU

Генерация:

```bash
python scripts/generate_dataset.py --skus 10000 --days 180 --output data/dataset
```

Создаёт:

- `data/dataset/products.csv`
- `data/dataset/sales_history.csv`
- `data/dataset/stock_snapshot.csv`

## Тесты

```bash
pip install -r requirements-dev.txt
pytest -q
```

Нагрузочные:

- Locust: `tests/load/locustfile.py`
- k6: `tests/load/k6_inventory.js`

## CI/CD

- GitHub Actions: `.github/workflows/ci.yml`
- Проверки: lint + unit/integration + docker compose config.

## Документация

- Архитектура: `docs/architecture.md`
- API: `docs/api.md`
- Развёртывание: `docs/deployment.md`
- Алгоритмы: `docs/algorithms.md`
- Отчёт по точности: `docs/report_forecast_accuracy.md`
- Презентация: `docs/presentation_outline.md`
- Отчёт проекта: `docs/project_report.md`
- Сценарий демо-видео: `docs/demo_video_script.md`

## Пример бизнес-пайплайна

- Endpoint `POST /workflow/new-shipment` в API Gateway реализует:
  1. фиксацию движения товаров,
  2. пересчёт прогноза,
  3. расчёт рекомендаций закупки,
  4. уведомление менеджера,
  5. аудит/логирование операции.
