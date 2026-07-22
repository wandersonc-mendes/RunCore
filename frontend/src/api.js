// Em desenvolvimento, o Vite encaminha /api para o backend local. Em produção,
// VITE_API_URL pode apontar para uma API hospedada separadamente.
const API_URL = import.meta.env.VITE_API_URL || "";

async function request(path, options = {}) {
  const token = localStorage.getItem("runcore_token");
  const response = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
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

export function login(data) { return request("/api/auth/login", { method: "POST", body: JSON.stringify(data) }); }
export function register(data) { return request("/api/auth/register", { method: "POST", body: JSON.stringify(data) }); }
export function getCurrentUser() { return request("/api/auth/me"); }
export function saveSession(session) { localStorage.setItem("runcore_token", session.token); }
export function clearSession() { localStorage.removeItem("runcore_token"); }
export function hasSession() { return Boolean(localStorage.getItem("runcore_token")); }
export function getStravaStatus() { return request("/api/integrations/strava/status"); }
export async function connectStrava() { const data = await request("/api/integrations/strava/connect"); window.location.assign(data.authorization_url); }
export function listStravaActivities() { return request("/api/integrations/strava/activities"); }
export function getStravaActivityDetails(activityId) { return request(`/api/integrations/strava/activities/${activityId}/details`); }
export function getActivityFeedback(activityId) { return request(`/api/integrations/strava/activities/${activityId}/feedback`); }
export function saveActivityFeedback(activityId, data) { return request(`/api/integrations/strava/activities/${activityId}/feedback`, { method: "PUT", body: JSON.stringify(data) }); }
export function syncStravaActivities() { return request("/api/integrations/strava/sync", { method: "POST" }); }
export function getAthleteTrainingLoad(athleteId) { return request(`/api/integrations/athletes/${athleteId}/training-load`); }
export function getStudentTraining() { return request("/api/student/training"); }
export function listGoals() { return request("/api/goals"); }
export function createGoal(data) { return request("/api/goals", { method: "POST", body: JSON.stringify(data) }); }
export function deleteGoal(id) { return request(`/api/goals/${id}`, { method: "DELETE" }); }
export function createInvitation(data = {}) { return request("/api/coach/invitations", { method: "POST", body: JSON.stringify(data) }); }
export function listInvitations() { return request("/api/coach/invitations"); }
export function approveInvitation(id) { return request(`/api/coach/invitations/${id}/approve`, { method: "POST" }); }
export function getStudentProfile() { return request("/api/student/profile"); }
export function saveStudentProfile(data) { return request("/api/student/profile", { method: "PUT", body: JSON.stringify(data) }); }
export function getAthleteProfile(athleteId) { return request(`/api/student/profile/athletes/${athleteId}`); }

export function listEvaluations(athleteId) {
  return request(`/api/athletes/${athleteId}/evaluations`);
}

export function createEvaluation(athleteId, data) {
  return request(`/api/athletes/${athleteId}/evaluations`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function deleteEvaluation(athleteId, evaluationId) {
  return request(`/api/athletes/${athleteId}/evaluations/${evaluationId}`, {
    method: "DELETE",
  });
}

export function getTraining(athleteId) {
  return request(`/api/athletes/${athleteId}/training`);
}

export function createTraining(athleteId, data) {
  return request(`/api/athletes/${athleteId}/training`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function regenerateTraining(athleteId) {
  return request(`/api/athletes/${athleteId}/training/regenerate`, {
    method: "POST",
  });
}

export function updateTrainingSession(athleteId, sessionId, data) {
  return request(`/api/athletes/${athleteId}/training/sessions/${sessionId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}
