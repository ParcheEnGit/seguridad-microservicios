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

export async function uploadDevicePhoto(id, photo) {
  const formData = new FormData();
  formData.append("photo", photo);
  const response = await fetch(`${API_BASE_URL}/devices/devices/${id}/photos`, {
    method: "POST",
    credentials: "include",
    body: formData,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail ?? "No se pudo subir la fotografía.");
  return data;
}

export async function deleteDevicePhoto(deviceId, photoId) {
  const response = await fetch(`${API_BASE_URL}/devices/devices/${deviceId}/photos/${photoId}`, {
    method: "DELETE",
    credentials: "include",
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail ?? "No se pudo eliminar la fotografía.");
  }
}
