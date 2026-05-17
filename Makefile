.PHONY: up down lint test dataset

up:
	docker compose up --build -d

down:
	docker compose down

lint:
	ruff check .

test:
	pytest -q

dataset:
	python scripts/generate_dataset.py --skus 10000 --days 180 --output data/dataset
