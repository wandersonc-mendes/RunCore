import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { clearSession, connectStrava, createGoal, deleteGoal, getActivityFeedback, getStravaActivityDetails, getStravaStatus, getStudentTraining, listGoals, listStravaActivities, saveActivityFeedback, syncStravaActivities } from "./api";
import ProfilePanel from "./ProfilePanel";
import { studentPaths } from "./router/paths";
import { formatWorkoutSummary } from "./utils/workoutSummary";

function formatDuration(seconds = 0) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainder = seconds % 60;
  return [hours, minutes, remainder].map((part) => String(part).padStart(2, "0")).join(":");
}

function formatPace(speed) {
  if (!speed) return "—";
  const seconds = Math.round(1000 / speed);
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}/km`;
}

function stepDistance(step) {
  return `${Number(step.distance).toFixed(step.distance_unit === "m" ? 0 : 1)} ${step.distance_unit || (step.repetitions ? "m" : "km")}`;
}

function stepTone(type = "") {
  const label = type.toLowerCase();
  if (label.includes("desaqueci")) return "cooldown";
  if (label.includes("aquecimento")) return "warmup";
  if (label.includes("descanso") || label.includes("recupera")) return "recovery";
  return "run";
}

function paceToSeconds(value) {
  const match = String(value || "").match(/^(\d{1,2}):(\d{2})$/);
  return match ? (Number(match[1]) * 60) + Number(match[2]) : null;
}

function plannedDistanceKm(step) {
  return Number(step.distance || 0) * ((step.distance_unit || (step.repetitions ? "m" : "km")) === "m" ? 0.001 : 1);
}

function statusForRange(value, low, high, fasterIsHigher = false) {
  if (!Number.isFinite(value) || !Number.isFinite(low) || !Number.isFinite(high)) return "unknown";
  const minimum = Math.min(low, high), maximum = Math.max(low, high);
  if (value >= minimum && value <= maximum) return "inside";
  if (fasterIsHigher) return value > maximum ? "above" : "below";
  return value < minimum ? "above" : "below";
}

function statusLabel(status, metric = "pace") {
  if (status === "inside") return "Dentro do planejado";
  if (status === "above") return metric === "pace" ? "Mais rápido que o planejado" : "Acima do planejado";
  if (status === "below") return metric === "pace" ? "Mais lento que o planejado" : "Abaixo do planejado";
  return "Sem referência suficiente";
}

function sessionForActivity(training, activity) {
  if (!training?.sessions || !activity?.start_at) return null;
  const date = new Date(activity.start_at).toISOString().slice(0, 10);
  return training.sessions.find((session) => session.session_date === date) || null;
}

function analyseActivity(training, activity, details) {
  const session = sessionForActivity(training, activity);
  if (!session) return null;
  const expectedSteps = session.steps.flatMap((step) => Array.from({ length: Math.max(1, Number(step.repetitions || 1)) }, () => ({ ...step, repetitions: 0 })));
  const plannedDistance = expectedSteps.reduce((total, step) => total + plannedDistanceKm(step), 0);
  const distanceStatus = statusForRange(activity.distance, plannedDistance * .92, plannedDistance * 1.08, true);
  const laps = details?.laps || [];
  const aligned = expectedSteps.length > 0 && laps.length >= expectedSteps.length;
  const blocks = aligned ? expectedSteps.map((step, index) => {
    const lap = laps[index];
    const expectedPaces = [paceToSeconds(step.pace_min), paceToSeconds(step.pace_max)].filter(Number.isFinite);
    const actualPace = lap.average_speed ? Math.round(1000 / lap.average_speed) : null;
    const paceStatus = expectedPaces.length === 2 ? statusForRange(actualPace, expectedPaces[0], expectedPaces[1]) : "unknown";
    const expectedDistance = plannedDistanceKm(step);
    const tolerance = Math.max(.05, expectedDistance * .16);
    const blockDistanceStatus = statusForRange(lap.distance, expectedDistance - tolerance, expectedDistance + tolerance, true);
    return { step, lap, paceStatus, distanceStatus: blockDistanceStatus, expectedDistance };
  }) : [];
  const inside = blocks.filter((block) => block.paceStatus === "inside" && block.distanceStatus === "inside").length;
  return { session, plannedDistance, distanceStatus, blocks, aligned, inside };
}

function WorkoutChart({ steps = [] }) {
  const chartWeight = (step) => Math.max(1, Math.sqrt(Number(step.distance || 0) * ((step.distance_unit || "km") === "km" ? 1000 : 1)));
  const paceSeconds = (value) => {
    const match = String(value || "").match(/^(\d{1,2}):(\d{2})$/);
    return match ? (Number(match[1]) * 60) + Number(match[2]) : null;
  };
  const weightedSteps = [];
  for (let index = 0; index < steps.length; index += 1) {
    const step = steps[index];
    const next = steps[index + 1];
    const repetitions = Math.max(1, Number(step.repetitions || 1));
    const nextIsRecovery = next && (stepTone(next.type) === "recovery");
    if (repetitions > 1 && nextIsRecovery) {
      for (let repetition = 0; repetition < repetitions; repetition += 1) {
        weightedSteps.push({ ...step, repetitions: 0, weight: chartWeight(step), chartKey: `${step.order}-run-${repetition}` });
        weightedSteps.push({ ...next, repetitions: 0, weight: chartWeight(next), chartKey: `${next.order}-recovery-${repetition}` });
      }
      index += 1;
    } else if (repetitions > 1) {
      for (let repetition = 0; repetition < repetitions; repetition += 1) weightedSteps.push({ ...step, repetitions: 0, weight: chartWeight(step), chartKey: `${step.order}-${repetition}` });
    } else {
      weightedSteps.push({ ...step, weight: chartWeight(step), chartKey: `${step.order}-single` });
    }
  }
  const pacedSegments = weightedSteps.map((step) => {
    const values = [paceSeconds(step.pace_min), paceSeconds(step.pace_max)].filter(Number.isFinite);
    return values.length ? values.reduce((total, value) => total + value, 0) / values.length : null;
  }).filter(Number.isFinite);
  const slowest = Math.max(...pacedSegments, 1);
  const fastest = Math.min(...pacedSegments, slowest);
  const chartHeight = (step) => {
    const values = [paceSeconds(step.pace_min), paceSeconds(step.pace_max)].filter(Number.isFinite);
    if (values.length) {
      const average = values.reduce((total, value) => total + value, 0) / values.length;
      const intensity = slowest === fastest ? .72 : (slowest - average) / (slowest - fastest);
      return `${54 + (intensity * 36)}%`;
    }
    if (stepTone(step.type) === "recovery") return "44%";
    if (stepTone(step.type) === "warmup" || stepTone(step.type) === "cooldown") return "56%";
    return "68%";
  };
  return <section className="workout-chart" aria-label="Gráfico da estrutura do treino">
    <div className="workout-chart-bars">{weightedSteps.map((step) => <div key={step.chartKey} className={`chart-segment ${stepTone(step.type)}`} style={{ flexGrow: step.weight, height: chartHeight(step) }} title={`${step.type}: ${stepDistance(step)} `}><span>{weightedSteps.length <= 7 ? step.type : ""}</span></div>)}</div>
    <div className="workout-chart-legend"><span className="warmup">Aquecimento</span><span className="run">Corrida</span><span className="recovery">Recuperação</span><span className="cooldown">Desaquecimento</span></div>
  </section>;
}

function activityMetric(activity) {
  if (!activity.distance || !activity.moving_time) return "Sem dados de distância";
  if (activity.sport_type === "Run") return `Pace médio: ${formatPace(activity.distance * 1000 / activity.moving_time)}`;
  return `Velocidade média: ${(activity.distance / (activity.moving_time / 3600)).toFixed(1)} km/h`;
}


function localDateKey(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function dateFromKey(value) {
  if (!value) return null;
  const date = new Date(`${value}T12:00:00`);
  return Number.isNaN(date.getTime()) ? null : date;
}

function StudentTrainingDonut({ completed, proposed, extra }) {
  const total = completed + proposed + extra;
  const completedEnd = total ? completed / total * 100 : 0;
  const proposedEnd = total ? completedEnd + proposed / total * 100 : 0;

  return (
    <div className="student-training-donut-wrap">
      <div
        className="student-training-donut"
        style={{
          background: total
            ? `conic-gradient(#19865f 0 ${completedEnd}%, #1598c8 ${completedEnd}% ${proposedEnd}%, #f29a1f ${proposedEnd}% 100%)`
            : "conic-gradient(#dfe7e3 0 100%)",
        }}
      >
        <div><strong>{total}</strong><span>treinos no mês</span></div>
      </div>
      <div className="student-training-donut-legend">
        <span className="completed"><i />Feitos<strong>{completed}</strong></span>
        <span className="proposed"><i />Propostos<strong>{proposed}</strong></span>
        <span className="extra"><i />Feitos avulsos<strong>{extra}</strong></span>
      </div>
    </div>
  );
}


export default function StudentPortal({ user, onLogout, view = "dashboard" }) {
  const navigate = useNavigate();
  const [strava, setStrava] = useState(null);
  const [error, setError] = useState("");
  const [activities, setActivities] = useState([]);
  const [syncing, setSyncing] = useState(false);
  const [expandedActivity, setExpandedActivity] = useState(null);
  const [activityDetails, setActivityDetails] = useState({});
  const [activityFeedbacks, setActivityFeedbacks] = useState({});
  const [feedbackForms, setFeedbackForms] = useState({});
  const [savingFeedback, setSavingFeedback] = useState(null);
  const [loadingActivity, setLoadingActivity] = useState(null);
  const [training, setTraining] = useState(null);
  const [showActivities, setShowActivities] = useState(false);
  const [calculator, setCalculator] = useState(null);
  const [pace, setPace] = useState("05:00");
  const [distance, setDistance] = useState("10");
  const [goals, setGoals] = useState([]);
  const [goalForm, setGoalForm] = useState({ name: "", distance: "", target_date: "", priority: "Principal" });
  const [savingGoal, setSavingGoal] = useState(false);
  const [showProfile, setShowProfile] = useState(false);
  const [selectedSession, setSelectedSession] = useState(null);

  useEffect(() => {
    function loadStatus() {
      getStravaStatus()
        .then((status) => {
          setStrava(status);
          if (status.connected) listStravaActivities().then(setActivities).catch(() => {});
        })
        .catch((err) => setError(err.message));
      getStudentTraining().then(setTraining).catch(() => {});
      listGoals().then(setGoals).catch(() => {});
    }

    loadStatus();
    const interval = window.setInterval(loadStatus, 10000);
    window.addEventListener("focus", loadStatus);
    return () => {
      window.clearInterval(interval);
      window.removeEventListener("focus", loadStatus);
    };
  }, []);

  async function sync() {
    setSyncing(true);
    setError("");
    try {
      const result = await syncStravaActivities();
      setActivities(result.activities);
      setActivityDetails({});
    } catch (err) {
      setError(err.message);
    } finally {
      setSyncing(false);
    }
  }

  async function toggleActivity(activityId) {
    if (expandedActivity === activityId) {
      setExpandedActivity(null);
      return;
    }
    setExpandedActivity(activityId);
    if (activityDetails[activityId]) return;

    setLoadingActivity(activityId);
    try {
      const [details, feedback] = await Promise.all([getStravaActivityDetails(activityId), getActivityFeedback(activityId)]);
      setActivityDetails((current) => ({ ...current, [activityId]: details }));
      if (feedback) {
        setActivityFeedbacks((current) => ({ ...current, [activityId]: feedback }));
        setFeedbackForms((current) => ({ ...current, [activityId]: feedback }));
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingActivity(null);
    }
  }

  async function saveGoal(event) {
    event.preventDefault();
    setSavingGoal(true);
    setError("");
    try {
      const goal = await createGoal({ ...goalForm, distance: Number(goalForm.distance) });
      setGoals((current) => [...current, goal].sort((a, b) => a.target_date.localeCompare(b.target_date)));
      setGoalForm({ name: "", distance: "", target_date: "", priority: "Principal" });
    } catch (err) {
      setError(err.message);
    } finally {
      setSavingGoal(false);
    }
  }

  async function removeGoal(goalId) {
    try {
      await deleteGoal(goalId);
      setGoals((current) => current.filter((goal) => goal.id !== goalId));
    } catch (err) {
      setError(err.message);
    }
  }

  function feedbackFor(activityId) {
    return feedbackForms[activityId] || activityFeedbacks[activityId] || { perceived_effort: 5, feeling: "bem", pain: "", sleep_quality: "", pre_fatigue: "", notes: "" };
  }

  async function saveFeedback(activityId) {
    const form = feedbackFor(activityId);
    setSavingFeedback(activityId);
    setError("");
    try {
      const feedback = await saveActivityFeedback(activityId, {
        ...form,
        perceived_effort: Number(form.perceived_effort),
        sleep_quality: form.sleep_quality === "" ? null : Number(form.sleep_quality),
        pre_fatigue: form.pre_fatigue === "" ? null : Number(form.pre_fatigue),
      });
      setActivityFeedbacks((current) => ({ ...current, [activityId]: feedback }));
      setFeedbackForms((current) => ({ ...current, [activityId]: feedback }));
    } catch (err) { setError(err.message); } finally { setSavingFeedback(null); }
  }

  function changeFeedback(activityId, field, value) {
    setFeedbackForms((current) => ({ ...current, [activityId]: { ...feedbackFor(activityId), [field]: value } }));
  }

  const runs = activities.filter((activity) => activity.sport_type === "Run");
  const runDistance = runs.reduce((total, activity) => total + activity.distance, 0);
  const runTime = runs.reduce((total, activity) => total + activity.moving_time, 0);
  const currentWeekSessions = training?.sessions?.filter((session) => session.week === training.current_week) || [];
  const weekdays = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"];
  const paceParts = pace.split(":").map(Number);
  const paceSeconds = paceParts.length === 2 && paceParts.every(Number.isFinite) ? paceParts[0] * 60 + paceParts[1] : 0;
  const calculatorDistance = Number(distance) || 0;
  const velocity = paceSeconds ? 3600 / paceSeconds : 0;
  const predictedTime = paceSeconds * calculatorDistance;

  const goalsPageSummary = (() => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const sortedGoals = [...goals].sort(
      (first, second) =>
        first.target_date.localeCompare(second.target_date),
    );

    const futureGoals = sortedGoals.filter((goal) => {
      const date = dateFromKey(goal.target_date);
      return date && date >= today;
    });

    const pastGoals = sortedGoals
      .filter((goal) => {
        const date = dateFromKey(goal.target_date);
        return date && date < today;
      })
      .reverse();

    const mainGoal = futureGoals.find(
      (goal) => goal.priority === "Principal",
    ) || futureGoals[0] || null;

    return {
      futureGoals,
      pastGoals,
      mainGoal,
    };
  })();


  const trainingPageSummary = (() => {
    const sessions = currentWeekSessions;
    const volume = sessions.reduce(
      (total, session) => total + (session.steps || []).reduce(
        (sessionTotal, step) => sessionTotal
          + plannedDistanceKm(step)
          * Math.max(1, Number(step.repetitions || 1)),
        0,
      ),
      0,
    );

    const zones = [
      ...new Set(
        sessions
          .map((session) => session.zone)
          .filter(Boolean),
      ),
    ];

    return {
      sessions: sessions.length,
      volume,
      zones,
      phase:
        sessions.find((session) => session.phase)?.phase
        || training?.phase
        || "Fase não informada",
      objective:
        training?.goal
        || training?.objective
        || training?.name
        || "Evolução consistente",
    };
  })();


  const dashboardSummary = (() => {
    const now = new Date();
    const thirtyDaysAgo = new Date(now);
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
    const currentMonth = now.getMonth();
    const currentYear = now.getFullYear();

    const monthRuns = runs.filter((activity) => {
      const date = new Date(activity.start_at);
      return !Number.isNaN(date.getTime())
        && date.getMonth() === currentMonth
        && date.getFullYear() === currentYear;
    });

    const recentDistance = runs.reduce((total, activity) => {
      const date = new Date(activity.start_at);
      return !Number.isNaN(date.getTime()) && date >= thirtyDaysAgo && date <= now
        ? total + Number(activity.distance || 0)
        : total;
    }, 0);

    const monthSessions = (training?.sessions || []).filter((session) => {
      const date = dateFromKey(session.session_date);
      return date && date.getMonth() === currentMonth && date.getFullYear() === currentYear;
    });

    const activityDates = new Set(monthRuns.map((activity) => localDateKey(activity.start_at)));
    const plannedDates = new Set(monthSessions.map((session) => session.session_date).filter(Boolean));
    const completed = monthSessions.filter((session) => activityDates.has(session.session_date)).length;
    const proposed = monthSessions.filter((session) => !activityDates.has(session.session_date)).length;
    const extra = monthRuns.filter((activity) => !plannedDates.has(localDateKey(activity.start_at))).length;

    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const upcomingGoals = [...goals]
      .filter((goal) => {
        const date = dateFromKey(goal.target_date);
        return date && date >= today;
      })
      .sort((a, b) => a.target_date.localeCompare(b.target_date))
      .slice(0, 3);

    const upcomingSessions = [...(training?.sessions || [])]
      .filter((session) => {
        const date = dateFromKey(session.session_date);
        return date && date >= today;
      })
      .sort((a, b) => a.session_date.localeCompare(b.session_date));

    const nextSession = upcomingSessions[0] || null;

    const weekDistance = currentWeekSessions.reduce(
      (total, session) => total + (session.steps || []).reduce(
        (sessionTotal, step) => sessionTotal
          + plannedDistanceKm(step)
          * Math.max(1, Number(step.repetitions || 1)),
        0,
      ),
      0,
    );

    const weekCompleted = currentWeekSessions.filter(
      (session) => activityDates.has(session.session_date),
    ).length;

    return {
      recentDistance,
      completed,
      proposed,
      extra,
      upcomingGoals,
      nextSession,
      weekDistance,
      weekCompleted,
      weekTotal: currentWeekSessions.length,
      latestActivity: [...activities]
        .sort((a, b) => {
          const dateA = new Date(a.start_at || 0).getTime();
          const dateB = new Date(b.start_at || 0).getTime();
          return dateB - dateA;
        })[0] || null,
    };
  })();

  useEffect(() => {
    if (view === "activities") {
      setShowActivities(true);
    } else {
      setExpandedActivity(null);
    }

    if (view === "calculators") {
      setCalculator((current) => current || "pace");
    }

    if (view !== "training") {
      setSelectedSession(null);
    }
  }, [view]);

  if (showProfile || view === "profile") {
    return (
      <ProfilePanel
        onClose={() => setShowProfile(false)}
      />
    );
  }

  return (
    <main className="student-page routed-student-page" data-view={view}>
      <section className="student-content">
                {view === "dashboard" && (
          <>
            <section className="student-dashboard-hero">
              <div>
                <p className="eyebrow">VISÃO GERAL</p>
                <h2>Olá, {user.name}.</h2>
                <p>Acompanhe sua semana de treino, suas atividades e sua evolução em um único lugar.</p>
              </div>
              <div className="student-dashboard-hero-brand">
                <span>RUNCORE</span>
                <strong>Seu treinamento em movimento</strong>
              </div>
            </section>

            <section className="student-dashboard-priority">
              <article className="student-next-session-card">
                <header>
                  <div>
                    <span>Próximo treino</span>
                    <h3>
                      {dashboardSummary.nextSession
                        ? dashboardSummary.nextSession.workout_name
                        : "Nenhum treino futuro"}
                    </h3>
                  </div>

                  <button
                    type="button"
                    className="btn-ghost"
                    onClick={() => navigate(studentPaths.training)}
                  >
                    Ver planilha
                  </button>
                </header>

                {dashboardSummary.nextSession ? (
                  <div className="student-next-session-content">
                    <time>
                      {new Intl.DateTimeFormat("pt-BR", {
                        weekday: "long",
                        day: "2-digit",
                        month: "short",
                      }).format(
                        dateFromKey(
                          dashboardSummary.nextSession.session_date,
                        ),
                      )}
                    </time>

                    <strong>
                      {dashboardSummary.nextSession.zone
                        || "Treino programado"}
                    </strong>

                    <p>
                      {formatWorkoutSummary(
                        dashboardSummary.nextSession,
                      )}
                    </p>
                  </div>
                ) : (
                  <p className="muted">
                    A próxima sessão aparecerá quando houver
                    um treino futuro na planilha.
                  </p>
                )}
              </article>

              <article className="student-week-summary-card">
                <span>Semana atual</span>
                <h3>Resumo do planejamento</h3>

                <div className="student-week-summary-metrics">
                  <div>
                    <strong>
                      {dashboardSummary.weekCompleted}
                      /{dashboardSummary.weekTotal}
                    </strong>
                    <small>treinos concluídos</small>
                  </div>

                  <div>
                    <strong>
                      {dashboardSummary.weekDistance.toLocaleString(
                        "pt-BR",
                        {
                          minimumFractionDigits: 1,
                          maximumFractionDigits: 1,
                        },
                      )} km
                    </strong>
                    <small>volume planejado</small>
                  </div>
                </div>
              </article>
            </section>

            <section className="student-dashboard-secondary">
              <article className="student-latest-activity-card">
                <header>
                  <div>
                    <span>Última atividade</span>
                    <h3>
                      {dashboardSummary.latestActivity
                        ? dashboardSummary.latestActivity.name
                        : "Nenhuma atividade importada"}
                    </h3>
                  </div>

                  <button
                    type="button"
                    className="btn-ghost"
                    onClick={() => navigate(studentPaths.activities)}
                  >
                    Ver atividades
                  </button>
                </header>

                {dashboardSummary.latestActivity ? (
                  <div className="student-latest-activity-metrics">
                    <div>
                      <strong>
                        {Number(
                          dashboardSummary.latestActivity.distance || 0,
                        ).toLocaleString("pt-BR", {
                          minimumFractionDigits: 1,
                          maximumFractionDigits: 2,
                        })} km
                      </strong>
                      <small>distância</small>
                    </div>

                    <div>
                      <strong>
                        {formatDuration(
                          dashboardSummary.latestActivity.moving_time,
                        )}
                      </strong>
                      <small>tempo em movimento</small>
                    </div>

                    <div>
                      <strong>
                        {activityMetric(
                          dashboardSummary.latestActivity,
                        ).replace("Pace médio: ", "")}
                      </strong>
                      <small>
                        {dashboardSummary.latestActivity.sport_type === "Run"
                          ? "pace médio"
                          : "velocidade média"}
                      </small>
                    </div>
                  </div>
                ) : (
                  <p className="muted">
                    Conecte e sincronize o Strava para visualizar
                    aqui um resumo da atividade mais recente.
                  </p>
                )}
              </article>

              <article className="student-quick-actions-card">
                <span>Acesso rápido</span>
                <h3>Próximas ações</h3>

                <div className="student-quick-actions">
                  <button
                    type="button"
                    onClick={() => navigate(studentPaths.training)}
                  >
                    <strong>Minha planilha</strong>
                    <small>Consultar treinos</small>
                  </button>

                  <button
                    type="button"
                    onClick={() => navigate(studentPaths.goals)}
                  >
                    <strong>Metas e provas</strong>
                    <small>Organizar objetivos</small>
                  </button>

                  <button
                    type="button"
                    onClick={() => navigate(studentPaths.activities)}
                  >
                    <strong>Atividades</strong>
                    <small>Revisar execuções</small>
                  </button>

                  <button
                    type="button"
                    onClick={() => navigate(studentPaths.calculators)}
                  >
                    <strong>Calculadoras</strong>
                    <small>Calcular ritmo e tempo</small>
                  </button>
                </div>
              </article>
            </section>

            <section className="student-dashboard-overview">
              <div className="student-dashboard-overview-main">
                <article className="student-month-distance-card">
                  <div className="student-dashboard-icon">KM</div>
                  <div>
                    <span>Quilometragem recente</span>
                    <strong>{dashboardSummary.recentDistance.toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 })} km</strong>
                    <small>percorridos nos últimos 30 dias</small>
                  </div>
                </article>

                <article className="student-race-calendar-card">
                  <header>
                    <div><span>Calendário pessoal</span><h3>Próximas provas</h3></div>
                    <button
                      type="button"
                      className="btn-ghost"
                      onClick={() => navigate(studentPaths.goals)}
                    >
                      Gerenciar
                    </button>
                  </header>
                  {dashboardSummary.upcomingGoals.length ? (
                    <div className="student-race-calendar-list">
                      {dashboardSummary.upcomingGoals.map((goal) => {
                        const raceDate = dateFromKey(goal.target_date);
                        return (
                          <article key={goal.id}>
                            <time><strong>{String(raceDate.getDate()).padStart(2, "0")}</strong><span>{new Intl.DateTimeFormat("pt-BR", { month: "short" }).format(raceDate)}</span></time>
                            <div><strong>{goal.name}</strong><span>{Number(goal.distance).toLocaleString("pt-BR", { maximumFractionDigits: 2 })} km · {goal.priority}</span></div>
                          </article>
                        );
                      })}
                    </div>
                  ) : <p className="muted">Nenhuma prova futura cadastrada.</p>}
                </article>
              </div>

              <article className="student-training-status-card">
                <header><div><span>Situação dos treinos</span><h3>Mês atual</h3></div></header>
                <StudentTrainingDonut completed={dashboardSummary.completed} proposed={dashboardSummary.proposed} extra={dashboardSummary.extra} />
              </article>
            </section>
          </>
        )}
        {view === "goals" && (
          <section id="metas" className="student-goals-page">
            <header className="student-goals-heading">
              <div>
                <p className="eyebrow">METAS E PROVAS</p>
                <h2>Objetivos do seu ciclo</h2>
                <p className="muted">
                  Acompanhe a prova principal, organize os próximos
                  compromissos e mantenha o histórico separado.
                </p>
              </div>

              <span className="student-goals-total">
                {goalsPageSummary.futureGoals.length} {
                  goalsPageSummary.futureGoals.length === 1
                    ? "prova futura"
                    : "provas futuras"
                }
              </span>
            </header>

            {goalsPageSummary.mainGoal ? (() => {
              const mainDate = dateFromKey(
                goalsPageSummary.mainGoal.target_date,
              );
              const days = Math.ceil(
                (mainDate - new Date().setHours(0, 0, 0, 0))
                / 86400000,
              );

              return (
                <article className="student-main-goal-card">
                  <div>
                    <span>Objetivo principal</span>
                    <h3>{goalsPageSummary.mainGoal.name}</h3>
                    <p>
                      {Number(
                        goalsPageSummary.mainGoal.distance,
                      ).toLocaleString("pt-BR", {
                        maximumFractionDigits: 2,
                      })} km · {
                        new Intl.DateTimeFormat("pt-BR", {
                          day: "2-digit",
                          month: "long",
                          year: "numeric",
                        }).format(mainDate)
                      }
                    </p>
                  </div>

                  <div className="student-main-goal-countdown">
                    <strong>{Math.max(0, days)}</strong>
                    <span>
                      {days === 1 ? "dia restante" : "dias restantes"}
                    </span>
                  </div>
                </article>
              );
            })() : (
              <section className="student-goals-empty-main">
                <h3>Nenhum objetivo futuro cadastrado</h3>
                <p>
                  Use o formulário abaixo para registrar sua próxima
                  prova ou meta esportiva.
                </p>
              </section>
            )}

            <section className="student-goals-content">
              <div className="student-goals-list-column">
                <section className="student-goals-section">
                  <header>
                    <div>
                      <span>Planejamento futuro</span>
                      <h3>Próximas provas</h3>
                    </div>
                  </header>

                  {goalsPageSummary.futureGoals.length ? (
                    <div className="student-goals-list">
                      {goalsPageSummary.futureGoals.map((goal) => {
                        const goalDate = dateFromKey(goal.target_date);
                        const days = Math.ceil(
                          (goalDate - new Date().setHours(0, 0, 0, 0))
                          / 86400000,
                        );

                        return (
                          <article key={goal.id}>
                            <time>
                              <strong>
                                {String(goalDate.getDate()).padStart(2, "0")}
                              </strong>
                              <span>
                                {new Intl.DateTimeFormat("pt-BR", {
                                  month: "short",
                                }).format(goalDate)}
                              </span>
                            </time>

                            <div>
                              <div className="student-goal-name-row">
                                <strong>{goal.name}</strong>
                                <span>{goal.priority}</span>
                              </div>
                              <small>
                                {Number(goal.distance).toLocaleString(
                                  "pt-BR",
                                  { maximumFractionDigits: 2 },
                                )} km · faltam {Math.max(0, days)} dias
                              </small>
                            </div>

                            <button
                              type="button"
                              className="btn-ghost"
                              onClick={() => removeGoal(goal.id)}
                            >
                              Remover
                            </button>
                          </article>
                        );
                      })}
                    </div>
                  ) : (
                    <p className="muted">
                      Nenhuma prova futura cadastrada.
                    </p>
                  )}
                </section>

                {goalsPageSummary.pastGoals.length > 0 && (
                  <section className="student-goals-section">
                    <header>
                      <div>
                        <span>Registro anterior</span>
                        <h3>Histórico</h3>
                      </div>
                    </header>

                    <div className="student-goals-history">
                      {goalsPageSummary.pastGoals.map((goal) => (
                        <article key={goal.id}>
                          <div>
                            <strong>{goal.name}</strong>
                            <small>
                              {Number(goal.distance).toLocaleString(
                                "pt-BR",
                                { maximumFractionDigits: 2 },
                              )} km · {
                                new Intl.DateTimeFormat("pt-BR").format(
                                  dateFromKey(goal.target_date),
                                )
                              }
                            </small>
                          </div>

                          <button
                            type="button"
                            className="btn-ghost"
                            onClick={() => removeGoal(goal.id)}
                          >
                            Remover
                          </button>
                        </article>
                      ))}
                    </div>
                  </section>
                )}
              </div>

              <aside className="student-goal-form-card">
                <div>
                  <span>Novo compromisso</span>
                  <h3>Adicionar meta ou prova</h3>
                  <p>
                    O cadastro é responsabilidade do atleta e pode
                    ser atualizado conforme o calendário esportivo.
                  </p>
                </div>

                <form className="goal-form" onSubmit={saveGoal}>
                  <label>
                    Nome
                    <input
                      required
                      value={goalForm.name}
                      onChange={(event) =>
                        setGoalForm((current) => ({
                          ...current,
                          name: event.target.value,
                        }))
                      }
                      placeholder="Ex.: Maratona de Vitória"
                    />
                  </label>

                  <label>
                    Distância
                    <input
                      required
                      type="number"
                      min="0.1"
                      step="0.1"
                      value={goalForm.distance}
                      onChange={(event) =>
                        setGoalForm((current) => ({
                          ...current,
                          distance: event.target.value,
                        }))
                      }
                      placeholder="Distância em km"
                    />
                  </label>

                  <label>
                    Data
                    <input
                      required
                      type="date"
                      value={goalForm.target_date}
                      onChange={(event) =>
                        setGoalForm((current) => ({
                          ...current,
                          target_date: event.target.value,
                        }))
                      }
                    />
                  </label>

                  <label>
                    Prioridade
                    <select
                      value={goalForm.priority}
                      onChange={(event) =>
                        setGoalForm((current) => ({
                          ...current,
                          priority: event.target.value,
                        }))
                      }
                    >
                      <option>Principal</option>
                      <option>Secundária</option>
                    </select>
                  </label>

                  <button
                    className="btn-primary"
                    disabled={savingGoal}
                  >
                    {savingGoal ? "Salvando..." : "Adicionar"}
                  </button>
                </form>
              </aside>
            </section>
          </section>
        )}

        {view === "calculators" && calculator && (
          <section className="calculator-card">
          <div><p className="eyebrow">CALCULADORA</p><h3>{calculator === "pace" ? "Pace e velocidade" : "Previsão de tempo final"}</h3><div className="calculator-tabs"><button className={calculator === "pace" ? "active" : ""} onClick={() => setCalculator("pace")}>Pace</button><button className={calculator === "prediction" ? "active" : ""} onClick={() => setCalculator("prediction")}>Previsão</button></div></div>
          <label>Pace (min/km)<input value={pace} onChange={(event) => setPace(event.target.value)} placeholder="05:00" /></label>
          {calculator === "prediction" && <label>Distância (km)<input type="number" min="0" step="0.1" value={distance} onChange={(event) => setDistance(event.target.value)} /></label>}
          <strong>{calculator === "pace" ? `${velocity.toFixed(2)} km/h` : formatDuration(predictedTime)}</strong>
          <button
            className="btn-ghost"
            onClick={() => setCalculator("pace")}
          >
            Limpar
          </button>
          </section>
        )}

        {view === "activities" && (
          <>
            <article className="connection-card">
          <div><span className="connection-logo">S</span><div><h3>Strava</h3><p>{strava?.connected ? "Conta conectada. Sincronize suas atividades quando quiser." : "Conecte sua conta para importar suas atividades."}</p></div></div>
          {strava?.connected ? <button className="btn-primary" disabled={syncing} onClick={sync}>{syncing ? "Sincronizando..." : "Sincronizar atividades"}</button> : <button className="btn-primary" disabled={!strava?.configured} onClick={() => connectStrava().catch((err) => setError(err.message))}>{strava ? "Conectar Strava" : "Verificando..."}</button>}
        </article>
        {strava && !strava.configured && <p className="muted">A integração Strava ainda está sendo configurada pelo treinador.</p>}
        {error && <div className="alert">{error}</div>}
        {strava?.connected && activities.length > 0 && <section id="resumo" className="student-stats" aria-label="Resumo das atividades importadas">
          <article><span>Atividades</span><strong>{activities.length}</strong><small>importadas</small></article>
          <article><span>Corridas</span><strong>{runs.length}</strong><small>registradas</small></article>
          <article><span>Quilometragem</span><strong>{runDistance.toFixed(1)} km</strong><small>em corridas</small></article>
          <article><span>Tempo correndo</span><strong>{formatDuration(runTime)}</strong><small>em movimento</small></article>
        </section>}
        {strava?.connected && <article id="activities" className={`activity-card ${showActivities ? "is-open" : "is-collapsed"}`}>
          <div className="activity-card-heading"><h3>Atividades recentes</h3><button className="btn-ghost activity-collapse" onClick={() => setShowActivities((current) => !current)}>{showActivities ? "Recolher" : "Ver atividades"}</button></div>
          {activities.length === 0 ? <p className="muted">Nenhuma atividade importada ainda. Clique em “Sincronizar atividades”.</p> : <div className="activity-list">
            {activities.map((activity) => {
              const expanded = expandedActivity === activity.id;
              const details = activityDetails[activity.id];
              const analysis = analyseActivity(training, activity, details);
              return <article className={`activity-row ${expanded ? "expanded" : ""}`} key={activity.id}>
                <button className="activity-toggle" onClick={() => toggleActivity(activity.id)}>
                  <div><strong>{activity.name}</strong><span>{activity.sport_type} · {activity.distance.toFixed(2)} km · {Math.floor(activity.moving_time / 60)} min</span></div><b>{expanded ? "−" : "+"}</b>
                </button>
                {expanded && <section className="activity-details">
                  {loadingActivity === activity.id ? <p className="muted">Carregando detalhes do Strava…</p> : <>
                    <div><span>Distância</span><strong>{activity.distance.toFixed(2)} km</strong></div>
                    <div><span>Tempo em movimento</span><strong>{formatDuration(activity.moving_time)}</strong></div>
                    <div><span>{activity.sport_type === "Run" ? "Pace médio" : "Velocidade média"}</span><strong>{activityMetric(activity).replace(/^(Pace médio: |Velocidade média: )/, "")}</strong></div>
                    <div><span>Elevação</span><strong>{details?.total_elevation_gain == null ? "Não informada" : `${Math.round(details.total_elevation_gain)} m`}</strong></div>
                    <div><span>FC média</span><strong>{details?.average_heartrate ? `${Math.round(details.average_heartrate)} bpm` : "Não informada"}</strong></div>
                    <div><span>FC máxima</span><strong>{details?.max_heartrate ? `${Math.round(details.max_heartrate)} bpm` : "Não informada"}</strong></div>
                    <div><span>Cadência média</span><strong>{details?.average_cadence ? `${Math.round(details.average_cadence)} spm` : "Não informada"}</strong></div>
                    <div><span>Data</span><strong>{activity.start_at ? new Intl.DateTimeFormat("pt-BR", { dateStyle: "medium" }).format(new Date(activity.start_at)) : "Não informada"}</strong></div>
                    {analysis && <section className="adherence-card"><div className="adherence-heading"><div><span>ADERÊNCIA AO TREINO</span><strong>{analysis.session.workout_name}</strong></div><b className={`adherence-status ${analysis.distanceStatus}`}>{statusLabel(analysis.distanceStatus, "distance")}</b></div><p>Planejado: {analysis.plannedDistance.toFixed(2)} km · Executado: {activity.distance.toFixed(2)} km</p>{analysis.aligned ? <><strong className="adherence-result">{analysis.inside} de {analysis.blocks.length} blocos dentro do planejado</strong><div className="adherence-blocks">{analysis.blocks.map((block, index) => <div className="adherence-block" key={`${block.step.order}-${index}`}><span>{block.step.type} {index + 1}</span><div><b className={`adherence-dot ${block.paceStatus}`} title={statusLabel(block.paceStatus)}></b><strong>{formatPace(block.lap.average_speed)}</strong><small>{block.lap.distance.toFixed(2)} km · alvo {block.expectedDistance.toFixed(2)} km</small></div><em className={block.paceStatus}>{statusLabel(block.paceStatus)}</em></div>)}</div></> : <p className="muted">As voltas importadas não correspondem diretamente às etapas do plano; por enquanto, a comparação está disponível para a sessão como um todo.</p>}</section>}
                    {details?.laps?.length > 0 && <div className="laps"><strong>Parciais</strong>{details.laps.map((lap) => <div className="lap" key={lap.number}><div className="lap-main"><strong>Volta {lap.number} — {formatDuration(lap.moving_time)}</strong><span>{lap.distance.toFixed(2)} km · {formatPace(lap.average_speed)}</span></div><small>{lap.average_heartrate ? `${Math.round(lap.average_heartrate)} bpm` : "FC não informada"} · {lap.elevation_gain == null ? "elevação não informada" : `${Math.round(lap.elevation_gain)} m`}</small></div>)}</div>}
                    <section className="training-feedback">
                      <div className="feedback-heading"><div><span>SEU RELATO</span><h4>Como foi este treino?</h4></div>{activityFeedbacks[activity.id] && <b>Registrado</b>}</div>
                      <p>Seu feedback complementa os dados do relógio e alimenta a carga de treinamento.</p>
                      <div className="feedback-fields">
                        <label>PSE (1 a 10)<select value={feedbackFor(activity.id).perceived_effort} onChange={(event) => changeFeedback(activity.id, "perceived_effort", event.target.value)}>{Array.from({ length: 10 }, (_, index) => <option key={index + 1} value={index + 1}>{index + 1}</option>)}</select></label>
                        <label>Como se sentiu?<select value={feedbackFor(activity.id).feeling} onChange={(event) => changeFeedback(activity.id, "feeling", event.target.value)}><option value="otimo">Ótimo</option><option value="bem">Bem</option><option value="pesado">Pesado</option><option value="muito_dificil">Muito difícil</option></select></label>
                        <label>Sono (1 a 5)<select value={feedbackFor(activity.id).sleep_quality} onChange={(event) => changeFeedback(activity.id, "sleep_quality", event.target.value)}><option value="">Não informar</option>{[1, 2, 3, 4, 5].map((value) => <option key={value} value={value}>{value}</option>)}</select></label>
                        <label>Fadiga antes (1 a 5)<select value={feedbackFor(activity.id).pre_fatigue} onChange={(event) => changeFeedback(activity.id, "pre_fatigue", event.target.value)}><option value="">Não informar</option>{[1, 2, 3, 4, 5].map((value) => <option key={value} value={value}>{value}</option>)}</select></label>
                      </div>
                      <label>Houve dor ou desconforto?<input value={feedbackFor(activity.id).pain} onChange={(event) => changeFeedback(activity.id, "pain", event.target.value)} placeholder="Ex.: panturrilha direita leve" /></label>
                      <label>Comentário do aluno<textarea rows="2" value={feedbackFor(activity.id).notes} onChange={(event) => changeFeedback(activity.id, "notes", event.target.value)} placeholder="Conte ao treinador como o treino aconteceu." /></label>
                      <button type="button" className="btn-primary" disabled={savingFeedback === activity.id} onClick={() => saveFeedback(activity.id)}>{savingFeedback === activity.id ? "Salvando..." : "Salvar feedback"}</button>
                    </section>
                  </>}
                </section>}
              </article>;
            })}
          </div>}
        </article>}
          </>
        )}

        {view === "training" && (
          <>
            <section className="student-training-page-heading">
              <div>
                <p className="eyebrow">MINHA PLANILHA</p>
                <h2>Estrutura e execução dos treinos</h2>
                <p className="muted">
                  Consulte o objetivo da semana, o volume previsto
                  e as orientações técnicas de cada sessão.
                </p>
              </div>

              <button
                type="button"
                className="btn-ghost"
                onClick={() => navigate(studentPaths.calendar)}
              >
                Ver Agenda
              </button>
            </section>

            {training && (
              <section className="student-training-page-summary">
                <article>
                  <span>Semana atual</span>
                  <strong>{training.current_week || 1}</strong>
                  <small>{trainingPageSummary.phase}</small>
                </article>

                <article>
                  <span>Sessões previstas</span>
                  <strong>{trainingPageSummary.sessions}</strong>
                  <small>treinos estruturados</small>
                </article>

                <article>
                  <span>Volume planejado</span>
                  <strong>
                    {trainingPageSummary.volume.toLocaleString(
                      "pt-BR",
                      {
                        minimumFractionDigits: 1,
                        maximumFractionDigits: 1,
                      },
                    )} km
                  </strong>
                  <small>na semana atual</small>
                </article>

                <article className="student-training-objective-card">
                  <span>Objetivo do ciclo</span>
                  <strong>{trainingPageSummary.objective}</strong>
                  <small>
                    {trainingPageSummary.zones.length
                      ? `Zonas trabalhadas: ${
                        trainingPageSummary.zones.join(", ")
                      }`
                      : "As zonas aparecerão conforme o planejamento."}
                  </small>
                </article>
              </section>
            )}

            {training ? <article id="planilha" className="student-plan">
          <div className="student-plan-heading">
            <div className="student-plan-title-block">
              <div className="student-plan-kicker">
                <p className="eyebrow">
                  SUA PLANILHA · {training.current_phase}
                </p>

                <span>
                  Semana {training.current_week} de {training.total_weeks}
                </span>
              </div>

              <div className="student-plan-name-row">
                <h3>{training.name}</h3>

                <strong>
                  Meta: {
                    goals.find(
                      (goal) =>
                        goal.priority === "Principal"
                        && goal.target_date
                        && new Date(`${goal.target_date}T23:59:59`)
                          >= new Date(),
                    )?.name
                    || training.objective
                    || `${training.target_distance.toFixed(1)} km`
                  }
                </strong>
              </div>
            </div>
          </div>

          <div className="student-sessions">
            {currentWeekSessions.map((session) => (
              <article key={session.id}>
                <span>{weekdays[session.weekday] || "Treino"}</span>
                <strong>{session.workout_name}</strong>
                <small>{session.zone}</small>
                <b>
                  {formatWorkoutSummary(session)}
                </b>
                <p>
                  {session.steps?.[0]?.notes
                    || "Confira os detalhes do treino com seu treinador."}
                </p>
                <button
                  className="btn-link"
                  onClick={() => setSelectedSession(session)}
                >
                  Ver estrutura e benefícios
                </button>
              </article>
            ))}
          </div>
        </article> : <article id="planilha" className="student-empty"><h3>Planilha</h3><p>Seu plano e a execução dos treinos aparecerão aqui após o vínculo com seu treinador.</p></article>}
          </>
        )}
      </section>
      {view === "training" && selectedSession && <div className="student-session-modal-backdrop" role="presentation" onMouseDown={() => setSelectedSession(null)}><section className="student-session-modal" role="dialog" aria-modal="true" aria-labelledby="student-session-title" onMouseDown={(event) => event.stopPropagation()}><header><div><span>{weekdays[selectedSession.weekday] || "Treino"} · Semana {selectedSession.week}</span><h3 id="student-session-title">{selectedSession.workout_name}</h3><p>{selectedSession.zone} · {formatWorkoutSummary(selectedSession)}</p></div><button className="modal-close" onClick={() => setSelectedSession(null)} aria-label="Fechar">×</button></header><WorkoutChart steps={selectedSession.steps} /><section><h4>Como executar</h4><ol>{selectedSession.steps?.map((step) => <li className={`workout-step ${stepTone(step.type)}`} key={step.order}><strong>{step.type}</strong><span>{step.repetitions ? `${step.repetitions} × ${stepDistance(step)}` : stepDistance(step)} · {step.pace_min}–{step.pace_max}/km{step.recovery ? ` · recuperação: ${step.recovery}` : ""}</span><small>{step.notes}</small></li>)}</ol></section><section className="student-adaptations"><h4>Benefícios e adaptações</h4><ul>{selectedSession.adaptations?.map((adaptation) => <li key={adaptation}>{adaptation}</li>)}</ul></section><footer><button className="btn-ghost" onClick={() => setSelectedSession(null)}>Fechar</button></footer></section></div>}
    </main>
  );
}
