import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  vus: 100,
  duration: "1m",
  thresholds: {
    http_req_duration: ["p(95)<500"],
    http_req_failed: ["rate<0.01"],
  },
};

export default function () {
  const payload = JSON.stringify({
    warehouse_id: "WH-001",
    movement_type: "arrival",
    policy: "fifo",
    actor_id: "load-agent",
    actor_role: "warehouse_worker",
    items: [{ sku: "SKU-LOAD", quantity: 1, batch_id: `B-${__VU}-${__ITER}` }],
  });
  const params = { headers: { "Content-Type": "application/json" } };
  const res = http.post("http://localhost:8001/movements/register", payload, params);
  check(res, { "status is 200": (r) => r.status === 200 });
  sleep(0.2);
}
