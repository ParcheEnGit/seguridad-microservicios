const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

async function request(path) {
  const response = await fetch(`${API_BASE_URL}/reports${path}`, { credentials: "include" });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(typeof data.detail === "string" ? data.detail : "No se pudo cargar la información.");
    error.status = response.status;
    throw error;
  }
  return data;
}

export const getAdminSummary = () => request("/dashboard/admin-summary");
