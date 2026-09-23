const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

function extractErrorMessage(data) {
  if (typeof data.detail === "string") {
    return data.detail;
  }
  if (Array.isArray(data.detail) && data.detail.length > 0) {
    return data.detail[0]?.msg ?? "No se pudo completar la solicitud.";
  }
  if (typeof data.message === "string") {
    return data.message;
  }
  return "No se pudo completar la solicitud.";
}

async function parseJsonResponse(response) {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(extractErrorMessage(data));
  }
  return data;
}

export async function loginWithGoogle(credential) {
  const response = await fetch(`${API_BASE_URL}/auth/google`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ credential }),
  });

  return parseJsonResponse(response);
}

export async function loginWithPassword(email, password) {
  const response = await fetch(`${API_BASE_URL}/auth/password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ email, password }),
  });

  return parseJsonResponse(response);
}

export async function fetchCurrentUser() {
  let response;

  try {
    response = await fetch(`${API_BASE_URL}/auth/me`, {
      method: "GET",
      credentials: "include",
    });
  } catch {
    throw new Error("No se pudo conectar con el servicio de autenticación.");
  }

  if (response.status === 401) {
    return null;
  }

  if (response.status === 502 || response.status === 503) {
    return null;
  }

  return parseJsonResponse(response);
}

export async function logout() {
  const response = await fetch(`${API_BASE_URL}/auth/logout`, {
    method: "POST",
    credentials: "include",
  });

  return parseJsonResponse(response);
}
