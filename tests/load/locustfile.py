from locust import HttpUser, between, task


class SmartStockUser(HttpUser):
    wait_time = between(0.1, 0.8)

    @task(3)
    def health(self):
        self.client.get("/health")

    @task(2)
    def services_health(self):
        self.client.get("/services/health")

    @task(1)
    def trigger_recalculate(self):
        payload = {
            "warehouse_id": "WH-001",
            "sku_histories": {
                "SKU-1": [11, 12, 10, 13, 12, 14, 15],
                "SKU-2": [21, 22, 20, 24, 23, 22, 25],
            },
            "current_stock": {"SKU-1": 30, "SKU-2": 20},
        }
        self.client.post("/workflow/recalculate", json=payload)
