const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Erro ${response.status}`);
  }

  if (response.status === 204) return null;
  return response.json();
}

export function listAthletes(search) {
  const query = search ? `?search=${encodeURIComponent(search)}` : "";
  return request(`/api/athletes${query}`);
}

export function createAthlete(data) {
  return request("/api/athletes", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function deleteAthlete(id) {
  return request(`/api/athletes/${id}`, { method: "DELETE" });
}
