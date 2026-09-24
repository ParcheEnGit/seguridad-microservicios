const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

async function requestJson(path) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "GET",
    credentials: "include",
    headers: {
      Accept: "application/json",
    },
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(
      data.detail ?? `Error al consultar ${path}: ${response.status}`,
    );
  }

  return data;
}

export async function fetchAlerts() {
  return requestJson("/alerts-tickets/alerts");
}