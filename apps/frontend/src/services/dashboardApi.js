const DEVICE_API_URL = "/api/devices";
const ALERT_API_URL = "/api/alerts-tickets";

async function requestJson(url) {
  const response = await fetch(url, {
    method: "GET",
    credentials: "include",
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`Error al consultar ${url}: ${response.status}`);
  }

  return response.json();
}

export async function fetchDevices() {
  return requestJson(`${DEVICE_API_URL}/`);
}

export async function fetchAlerts() {
  return requestJson(`${ALERT_API_URL}/alerts`);
}