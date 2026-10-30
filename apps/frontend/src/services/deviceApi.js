const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

const FIELD_LABELS = {
  device_code: "Código único",
  name: "Nombre del dispositivo",
  device_type: "Tipo de dispositivo",
  location: "Laboratorio o ubicación",
  metric_code: "Métrica",
  unit: "Unidad",
  min_value: "Mínimo",
  max_value: "Máximo",
};

function formatValidationError(detail) {
  if (typeof detail === "string") return detail;
  if (!Array.isArray(detail)) return "No se pudo completar la operación.";
  return detail.map((issue) => {
    const location = Array.isArray(issue.loc) ? issue.loc : [];
    const thresholdPosition = location.indexOf("thresholds");
    const listIndex = location.find((part) => Number.isInteger(part));
    const threshold = thresholdPosition >= 0 && Number.isInteger(location[thresholdPosition + 1])
      ? `Umbral ${location[thresholdPosition + 1] + 1}`
      : Number.isInteger(listIndex)
        ? `Umbral ${listIndex + 1}`
        : "";
    const field = FIELD_LABELS[location.at(-1)] ?? "Dato";
    const message = String(issue.msg ?? "valor no válido").replace(/^Value error,\s*/i, "");
    return `${[threshold, field].filter(Boolean).join(" · ")}: ${message}.`;
  }).join(" ");
}

function requestError(response, detail, fallback) {
  const error = new Error(formatValidationError(detail) || fallback);
  error.status = response.status;
  return error;
}

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}/devices${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(options.headers ?? {}) },
    ...options,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw requestError(response, data.detail, "No se pudo completar la operación.");
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
  if (!response.ok) throw requestError(response, data.detail, "No se pudo subir la fotografía.");
  return data;
}

export async function deleteDevicePhoto(deviceId, photoId) {
  const response = await fetch(`${API_BASE_URL}/devices/devices/${deviceId}/photos/${photoId}`, {
    method: "DELETE",
    credentials: "include",
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw requestError(response, data.detail, "No se pudo eliminar la fotografía.");
  }
}
