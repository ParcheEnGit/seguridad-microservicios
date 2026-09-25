const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}/devices${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(options.headers ?? {}) },
    ...options,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail ?? "No se pudo completar la operación.");
  return data;
}

export function listDevices(filters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") params.set(key, value);
  });
  const query = params.toString();
  return request(`/devices${query ? `?${query}` : ""}`);
}
export const createDevice = (payload) => request("/devices", { method: "POST", body: JSON.stringify(payload) });
export const updateDevice = (id, payload) => request(`/devices/${id}`, { method: "PATCH", body: JSON.stringify(payload) });
export const deactivateDevice = (id) => request(`/devices/${id}/deactivate`, { method: "PATCH", body: JSON.stringify({ status: "inactivo" }) });
export const replaceThresholds = (id, thresholds) => request(`/devices/${id}/thresholds`, { method: "PUT", body: JSON.stringify(thresholds) });
