// Em desenvolvimento, o Vite encaminha /api para o backend local.
// Em produção, VITE_API_URL pode apontar para uma API hospedada separadamente.
const API_URL = import.meta.env.VITE_API_URL || "";

function formatValidationError(detail) {
  if (!Array.isArray(detail)) {
    return null;
  }

  return detail
    .map((error) => {
      const location = Array.isArray(error.loc)
        ? error.loc.filter((item) => item !== "body").join(".")
        : "";

      const message = error.msg || "Valor inválido";

      return location
        ? `${location}: ${message}`
        : message;
    })
    .join(" | ");
}

function extractErrorMessage(body, status) {
  if (!body) {
    return `Erro ${status}`;
  }

  if (typeof body.detail === "string") {
    return body.detail;
  }

  const validationMessage = formatValidationError(body.detail);

  if (validationMessage) {
    return validationMessage;
  }

  if (typeof body.message === "string") {
    return body.message;
  }

  if (typeof body.error === "string") {
    return body.error;
  }

  return `Erro ${status}`;
}

async function request(path, options = {}) {
  const token = localStorage.getItem("runcore_token");
  const controller = new AbortController();
  const timeoutMilliseconds = options.timeout ?? 20000;
  const timeoutId = window.setTimeout(
    () => controller.abort(),
    timeoutMilliseconds,
  );

  let response;

  try {
    response = await fetch(`${API_URL}${path}`, {
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        ...(token
          ? {
              Authorization: `Bearer ${token}`,
            }
          : {}),
        ...(options.headers || {}),
      },
      ...options,
    });
  } catch (error) {
    if (error?.name === "AbortError") {
      throw new Error(
        "A API demorou mais de 20 segundos para salvar. "
        + "A operação foi interrompida para evitar que a tela fique travada.",
      );
    }

    throw new Error(
      "Não foi possível conectar à API. Verifique sua conexão e tente novamente.",
      {
        cause: error,
      },
    );
  } finally {
    window.clearTimeout(
      timeoutId,
    );
  }

  if (!response.ok) {
    const body = await response
      .json()
      .catch(() => null);

    throw new Error(
      extractErrorMessage(
        body,
        response.status,
      ),
    );
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export function listAthletes(search) {
  const query = search
    ? `?search=${encodeURIComponent(search)}`
    : "";

  return request(`/api/athletes${query}`);
}

export function createAthlete(data) {
  return request("/api/athletes", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function deleteAthlete(id) {
  return request(`/api/athletes/${id}`, {
    method: "DELETE",
  });
}

export function login(data) {
  return request("/api/auth/login", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function register(data) {
  return request("/api/auth/register", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function forgotPassword(data) {
  return request("/api/auth/forgot-password", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function resetPassword(data) {
  return request("/api/auth/reset-password", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function getCurrentUser() {
  return request("/api/auth/me");
}

export function listManagedUsers() {
  return request("/api/admin/users");
}

export function createManagedUser(data) {
  return request("/api/admin/users", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function createCoach(data) {
  return request("/api/admin/users/coaches", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateManagedUser(userId, data) {
  return request(`/api/admin/users/${userId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}


export function deleteManagedStudent(userId) {
  return request(`/api/admin/users/${userId}/student`, {
    method: "DELETE",
  });
}

export function saveSession(session) {
  localStorage.setItem(
    "runcore_token",
    session.token,
  );
}

export function clearSession() {
  localStorage.removeItem("runcore_token");
}

export function hasSession() {
  return Boolean(
    localStorage.getItem("runcore_token"),
  );
}

export function getStravaStatus() {
  return request(
    "/api/integrations/strava/status",
  );
}

export async function connectStrava() {
  const data = await request(
    "/api/integrations/strava/connect",
  );

  window.location.assign(
    data.authorization_url,
  );
}

export function listStravaActivities() {
  return request(
    "/api/integrations/strava/activities",
  );
}

export function getStravaActivityDetails(activityId) {
  return request(
    `/api/integrations/strava/activities/${activityId}/details`,
  );
}

export function getActivityFeedback(activityId) {
  return request(
    `/api/integrations/strava/activities/${activityId}/feedback`,
  );
}

export function saveActivityFeedback(
  activityId,
  data,
) {
  return request(
    `/api/integrations/strava/activities/${activityId}/feedback`,
    {
      method: "PUT",
      body: JSON.stringify(data),
    },
  );
}

export function syncStravaActivities() {
  return request(
    "/api/integrations/strava/sync",
    {
      method: "POST",
      timeout: 60000,
    },
  );
}

export function getAthleteTrainingLoad(athleteId) {
  return request(
    `/api/integrations/athletes/${athleteId}/training-load`,
  );
}

export function getStudentTraining() {
  return request("/api/student/training");
}

export function listGoals() {
  return request("/api/goals");
}

export function createGoal(data) {
  return request("/api/goals", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function deleteGoal(id) {
  return request(`/api/goals/${id}`, {
    method: "DELETE",
  });
}

export function createInvitation(data = {}) {
  return request(
    "/api/coach/invitations",
    {
      method: "POST",
      body: JSON.stringify(data),
    },
  );
}

export function listInvitations() {
  return request(
    "/api/coach/invitations",
  );
}

export function approveInvitation(id) {
  return request(
    `/api/coach/invitations/${id}/approve`,
    {
      method: "POST",
    },
  );
}

export function getStudentProfile() {
  return request(
    "/api/student/profile",
  );
}

export function saveStudentProfile(data) {
  return request(
    "/api/student/profile",
    {
      method: "PUT",
      body: JSON.stringify(data),
    },
  );
}

export function getAthleteProfile(athleteId) {
  return request(
    `/api/student/profile/athletes/${athleteId}`,
  );
}

export function listStudentEvaluations() {
  return request(
    "/api/student/evaluations",
  );
}


export function listEvaluations(athleteId) {
  return request(
    `/api/athletes/${athleteId}/evaluations`,
  );
}

export function createEvaluation(
  athleteId,
  data,
) {
  return request(
    `/api/athletes/${athleteId}/evaluations`,
    {
      method: "POST",
      body: JSON.stringify(data),
    },
  );
}

export function deleteEvaluation(
  athleteId,
  evaluationId,
) {
  return request(
    `/api/evaluations/${evaluationId}`,
    {
      method: "DELETE",
    },
  );
}

export function getTraining(athleteId) {
  return request(
    `/api/athletes/${athleteId}/training`,
  );
}

export function createTraining(
  athleteId,
  data,
) {
  return request(
    `/api/athletes/${athleteId}/training`,
    {
      method: "POST",
      body: JSON.stringify(data),
    },
  );
}

export function regenerateTraining(athleteId) {
  return request(
    `/api/athletes/${athleteId}/training/regenerate`,
    {
      method: "POST",
    },
  );
}

export function createTrainingSession(
  athleteId,
  data,
) {
  return request(
    `/api/athletes/${athleteId}/training/sessions`,
    {
      method: "POST",
      body: JSON.stringify(data),
    },
  );
}


export function updateTrainingSession(
  athleteId,
  sessionId,
  data,
) {
  return request(
    `/api/athletes/${athleteId}/training/sessions/${sessionId}`,
    {
      method: "PATCH",
      body: JSON.stringify(data),
    },
  );
}

export function listIptProtocols() {
  return request("/api/ipt/protocols");
}

export function listIptAssessments(athleteId) {
  return request(
    `/api/athletes/${athleteId}/ipt-assessments`,
  );
}

export function createIptAssessment(
  athleteId,
  data,
) {
  return request(
    `/api/athletes/${athleteId}/ipt-assessments`,
    {
      method: "POST",
      body: JSON.stringify(data),
    },
  );
}

export function deleteIptAssessment(assessmentId) {
  return request(
    `/api/ipt-assessments/${assessmentId}`,
    {
      method: "DELETE",
    },
  );
}
