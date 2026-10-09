const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}/alerts-tickets${path}`, {
    credentials: "include",
    ...options,
    headers: {
      Accept: "application/json",
      ...options.headers,
    },
  });
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const error = new Error(data.detail ?? `Error de solicitud: ${response.status}`);
    error.status = response.status;
    throw error;
  }
  return data;
}

export function fetchManagedAlerts(filters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.set(key, value);
  });
  const query = params.toString();
  return request(`/alerts${query ? `?${query}` : ""}`);
}

export function fetchAlertDetail(alertId) {
  return request(`/alerts/${alertId}`);
}

export function setAlertStatus(alertId, status) {
  return request(`/alerts/${alertId}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
}
