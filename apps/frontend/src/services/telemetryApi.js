const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

async function request(path) {
  const response = await fetch(`${API_BASE_URL}/telemetry${path}`, {
    credentials: "include",
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(
      data.detail ?? "No se pudo consultar el historial de lecturas.",
    );
  }

  return data;
}

export function getTelemetryHistory({
  deviceId,
  startAt,
  endAt,
  metricCode = "",
  limit = 10,
  offset = 0,
}) {
  const params = new URLSearchParams({
    device_id: deviceId,
    start_at: startAt,
    end_at: endAt,
    limit: String(limit),
    offset: String(offset),
  });

  if (metricCode) {
    params.set("metric_code", metricCode);
  }

  return request(`/readings/history?${params.toString()}`);
}