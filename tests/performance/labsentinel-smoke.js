/**
 * Escenario inicial de carga (HU12) — LabSentinel
 *
 * Requisitos: stack levantado (`docker compose up`) y k6 instalado.
 *
 *   k6 run tests/performance/labsentinel-smoke.js
 *
 * Variables opcionales:
 *   BASE_URL=http://localhost:8080
 *   VUS=5
 *   DURATION=30s
 *
 * Este escenario golpea endpoints públicos de salud (sin cookie).
 * Es reproducible y demuestra que el gateway y los microservicios
 * responden bajo carga ligera. Las rutas autenticadas se validan con pytest.
 */

import http from "k6/http";
import { check, sleep } from "k6";

const BASE_URL = __ENV.BASE_URL || "http://localhost:8080";

export const options = {
  vus: Number(__ENV.VUS || 5),
  duration: __ENV.DURATION || "30s",
  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<800"],
    checks: ["rate>0.99"],
  },
};

const HEALTH_PATHS = [
  "/api/devices/health",
  "/api/telemetry/health",
  "/api/alerts-tickets/health",
  "/api/reports/health",
];

export default function () {
  for (const path of HEALTH_PATHS) {
    const response = http.get(`${BASE_URL}${path}`);
    check(response, {
      [`${path} status 200`]: (r) => r.status === 200,
      [`${path} body ok`]: (r) => {
        try {
          const body = r.json();
          return body && (body.status === "ok" || body.service);
        } catch (_) {
          return false;
        }
      },
    });
  }
  sleep(1);
}
