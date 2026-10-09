const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}/alerts-tickets${path}`, { credentials: "include", ...options });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = Array.isArray(data.detail) ? "Revisa los datos del formulario." : data.detail;
    const error = new Error(detail ?? "No se pudo completar la operación.");
    error.status = response.status;
    throw error;
  }
  return data;
}

export function listMyTickets(filters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") params.set(key, value);
  });
  const query = params.toString();
  return request(`/tickets/mine${query ? `?${query}` : ""}`);
}

export const getTicket = (id) => request(`/tickets/${id}`);

export function createTicket({ deviceId, category, description, attachment }) {
  const formData = new FormData();
  formData.append("device_id", deviceId);
  formData.append("category", category);
  formData.append("description", description);
  if (attachment) formData.append("attachment", attachment);
  return request("/tickets", { method: "POST", body: formData });
}
