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
export const getTelemetrySummary = () => request("/dashboard/telemetry-summary");
export const getDeviceTelemetry = ({ period = "24h", resolution = "5m" } = {}) => request(`/dashboard/device-telemetry?period=${period}&resolution=${resolution}`);


function buildReportParams({
  startDate,
  endDate,
  deviceId,
  status,
  severity,
  category,
} = {}) {
  const params = new URLSearchParams();

  if (startDate) params.set("start_date", startDate);
  if (endDate) params.set("end_date", endDate);
  if (deviceId) params.set("device_id", deviceId);
  if (status) params.set("status", status);
  if (severity) params.set("severity", severity);
  if (category) params.set("category", category);

  return params;
}

export const getDeviceReport = ({
  startDate,
  endDate,
  deviceId,
  status,
} = {}) => {
  const params = buildReportParams({ startDate, endDate, deviceId });
  if (status) params.set("device_status", status);

  return request(`/dashboard/reports/devices?${params.toString()}`);
};

export const getAlertReport = ({
  startDate,
  endDate,
  deviceId,
  severity,
  status,
} = {}) => {
  const params = buildReportParams({ startDate, endDate, deviceId, severity });
  if (status) params.set("alert_status", status);

  return request(`/dashboard/reports/alerts?${params.toString()}`);
};

export const getTicketReport = ({
  startDate,
  endDate,
  deviceId,
  status,
  category,
} = {}) => {
  const params = buildReportParams({ startDate, endDate, deviceId, category });
  if (status) params.set("ticket_status", status);

  return request(`/dashboard/reports/tickets?${params.toString()}`);
};
