/**
 * Prueba de carga autenticada — LabSentinel
 *
 * Recorre las consultas principales de un administrador a través del gateway:
 * sesión, dispositivos, alertas, historial de lecturas y resumen administrativo.
 * Cada usuario virtual espera 1 s entre recorridos (tiempo de lectura).
 *
 * Requisitos: stack levantado y una cookie de sesión válida de administrador.
 * La cookie se pasa por variable de entorno y nunca se guarda en el repositorio.
 *
 *   docker run --rm -i -e BASE_URL=https://host.docker.internal:8080 -e INSECURE_TLS=true \
 *     -e SESSION_COOKIE=<valor> -e VUS=10 -e DEVICE_ID=<uuid> \
 *     grafana/k6:1.3.0 run - < tests/performance/labsentinel-load.js
 *
 * Variables:
 *   BASE_URL        URL del gateway (por defecto https://localhost:8080)
 *   INSECURE_TLS    true para aceptar el certificado de la CA local de desarrollo
 *                   (necesario si se accede por un nombre distinto de localhost)
 *   SESSION_COOKIE  valor de labsentinel_session de un administrador
 *   DEVICE_ID       dispositivo para consultar el historial de lecturas
 *   VUS             usuarios virtuales en la meseta (por defecto 10)
 *   HOLD            duración de la meseta (por defecto 60s)
 *   SUMMARY_JSON    true para imprimir el resumen en JSON en lugar del texto de k6
 */

import http from "k6/http";
import { check, group, sleep } from "k6";
import { textSummary } from "https://jslib.k6.io/k6-summary/0.0.2/index.js";

const BASE_URL = __ENV.BASE_URL || "https://localhost:8080";
const VUS = Number(__ENV.VUS || 10);
const HOLD = __ENV.HOLD || "60s";
const DEVICE_ID = __ENV.DEVICE_ID || "";

export const options = {
  insecureSkipTLSVerify: __ENV.INSECURE_TLS === "true",
  scenarios: {
    carga: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: "10s", target: VUS },
        { duration: HOLD, target: VUS },
        { duration: "10s", target: 0 },
      ],
      gracefulRampDown: "5s",
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<800"],
    checks: ["rate>0.99"],
    // Submétricas por endpoint para comparar latencias en el análisis.
    "http_req_duration{endpoint:sesion}": ["p(95)<800"],
    "http_req_duration{endpoint:dispositivos}": ["p(95)<800"],
    "http_req_duration{endpoint:alertas}": ["p(95)<800"],
    "http_req_duration{endpoint:historial}": ["p(95)<800"],
    "http_req_duration{endpoint:resumen_admin}": ["p(95)<800"],
  },
  summaryTrendStats: ["avg", "min", "med", "p(90)", "p(95)", "max"],
};

const params = (name) => ({
  headers: { Cookie: `labsentinel_session=${__ENV.SESSION_COOKIE}` },
  tags: { endpoint: name },
});

function last24h() {
  const end = new Date();
  const start = new Date(end.getTime() - 24 * 60 * 60 * 1000);
  return `start_at=${start.toISOString()}&end_at=${end.toISOString()}`;
}

const ENDPOINTS = [
  ["sesion", () => "/api/auth/me"],
  ["dispositivos", () => "/api/devices/devices"],
  ["alertas", () => "/api/alerts-tickets/alerts"],
  ["historial", () => `/api/telemetry/readings/history?device_id=${DEVICE_ID}&${last24h()}`],
  ["resumen_admin", () => "/api/reports/dashboard/admin-summary"],
];

export default function () {
  for (const [name, path] of ENDPOINTS) {
    group(name, () => {
      const res = http.get(`${BASE_URL}${path()}`, params(name));
      check(res, { [`${name} 200`]: (r) => r.status === 200 });
    });
  }
  sleep(1);
}

// Resumen legible por defecto; SUMMARY_JSON=true lo emite en JSON para procesarlo.
export function handleSummary(data) {
  if (__ENV.SUMMARY_JSON === "true") {
    return { stdout: JSON.stringify(data) };
  }
  return { stdout: textSummary(data, { indent: " ", enableColors: false }) };
}
