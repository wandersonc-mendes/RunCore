import { useEffect, useRef, useState } from "react";
import { Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import {
  clearSession,
  createAthlete,
  createEvaluation,
  createTraining,
  deleteAthlete,
  deleteEvaluation,
  listAthletes,
  listEvaluations,
  getTraining,
  regenerateTraining,
  createTrainingSession,
  updateTrainingSession,
  getCurrentUser,
  hasSession,
  createInvitation,
  listInvitations,
  approveInvitation,
} from "./api";
import LoginScreen from "./LoginScreen";
import StudentPortal from "./StudentPortal";
import AthleteProfileView from "./AthleteProfileView";
import IptAssessmentView from "./IptAssessmentView";
import AppShell from "./layout/AppShell";
import SettingsPage from "./pages/SettingsPage";
import PlanningPage from "./pages/PlanningPage";
import WorkoutsPage from "./pages/WorkoutsPage";
import AgendaPage from "./pages/AgendaPage";
import EvaluationsPage from "./pages/EvaluationsPage";
import ReportsPage from "./pages/ReportsPage";
import CoachDashboardPage from "./pages/CoachDashboardPage";
import CoachProfilePage from "./pages/CoachProfilePage";
import StudentEvolutionPage from "./pages/StudentEvolutionPage";
import StudentAgendaPage from "./pages/StudentAgendaPage";
import AdminUsersPage from "./pages/AdminUsersPage";
import { adminPaths, coachPaths, studentPaths } from "./router/paths";
import "./App.css";

const emptyAthlete = { name: "", phone: "", email: "", goal: "", notes: "" };
const emptyEvaluation = {
  weight: "",
  height: "",
  max_hr: "",
  resting_hr: "",
  test_type: "",
  time: "",
  test_date: new Date().toISOString().slice(0, 10),
};

const weekdays = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"];

function asNumber(value) {
  return value === "" ? 0 : Number(value);
}

function formatTestTimeInput(value) {
  const digits = value.replace(/\D/g, "").slice(0, 6);
  return [digits.slice(0, 2), digits.slice(2, 4), digits.slice(4, 6)]
    .filter(Boolean)
    .join(":");
}

function formatPaceInput(value) {
  const digits = value.replace(/\D/g, "").slice(0, 4);
  if (digits.length <= 2) return digits;
  return `${digits.slice(0, 2)}:${digits.slice(2)}`;
}

function formatDate(value) {
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(value));
}

function formatTestDate(value) {
  return value ? new Intl.DateTimeFormat("pt-BR", { dateStyle: "short" }).format(new Date(`${value}T00:00:00`)) : "—";
}

function formatDuration(seconds) {
  const value = Math.round(seconds);
  const hours = Math.floor(value / 3600);
  const minutes = Math.floor((value % 3600) / 60);
  const remainder = value % 60;
  return [hours, minutes, remainder].map((part) => String(part).padStart(2, "0")).join(":");
}

function totalSessionDistance(session) {
  return session.steps.reduce(
    (total, step) => total + (step.distance * (step.repetitions || 1)),
    0,
  );
}

function stepTone(type = "") {
  const label = type.toLowerCase();
  if (label.includes("desaqueci")) return "cooldown";
  if (label.includes("aquecimento")) return "warmup";
  if (label.includes("descanso") || label.includes("recupera")) return "recovery";
  return "run";
}

function weekdayForDate(value) {
  if (!value) return "";
  return new Intl.DateTimeFormat("pt-BR", { weekday: "long" }).format(new Date(`${value}T12:00:00`));
}

function availableTrainingWeeks(startDate, targetDate) {
  if (!startDate || !targetDate) return null;

  const start = new Date(`${startDate}T00:00:00Z`);
  const target = new Date(`${targetDate}T00:00:00Z`);

  if (
    Number.isNaN(start.getTime())
    || Number.isNaN(target.getTime())
    || target < start
  ) {
    return null;
  }

  const dayInMilliseconds = 24 * 60 * 60 * 1000;
  const weekInMilliseconds = 7 * dayInMilliseconds;
  const inclusiveDuration =
    target.getTime() - start.getTime() + dayInMilliseconds;

  return Math.max(
    1,
    Math.ceil(inclusiveDuration / weekInMilliseconds),
  );
}

function BrandLogo() {
  return <span className="brand-logo"><img src="/logo-horizontal.png?v=2" alt="RunCore" /></span>;
}

function SessionAdjustment({
  value,
  onChange,
  onSave,
  onCancel,
  saving,
  athlete,
}) {
  const [openTypePicker, setOpenTypePicker] = useState(null);

  const stepTypes = [
    "Aquecimento",
    "Corrida",
    "Caminhada",
    "Recuperação",
    "Descanso",
    "Desaquecimento",
    "Outros",
  ];

  const frequentBlocks = [
    {
      label: "Aquecimento",
      type: "Aquecimento",
      distance: 2,
      distance_unit: "km",
      repetitions: 0,
      recovery: "",
      pace_min: "",
      pace_max: "",
      notes: "Corrida leve e mobilidade.",
    },
    {
      label: "Intervalado",
      type: "Corrida",
      distance: 400,
      distance_unit: "m",
      repetitions: 8,
      recovery: "200 m trote",
      pace_min: "",
      pace_max: "",
      notes: "Intervalado controlado.",
    },
    {
      label: "Ritmo",
      type: "Corrida",
      distance: 6,
      distance_unit: "km",
      repetitions: 0,
      recovery: "",
      pace_min: "",
      pace_max: "",
      notes: "Ritmo contínuo.",
    },
    {
      label: "Tempo Run",
      type: "Corrida",
      distance: 5,
      distance_unit: "km",
      repetitions: 0,
      recovery: "",
      pace_min: "",
      pace_max: "",
      notes: "Trecho sustentado próximo ao limiar.",
    },
    {
      label: "Fartlek",
      type: "Corrida",
      distance: 1,
      distance_unit: "km",
      repetitions: 6,
      recovery: "1 min leve",
      pace_min: "",
      pace_max: "",
      notes: "Alternar ritmo forte e leve.",
    },
    {
      label: "Longão",
      type: "Corrida",
      distance: 16,
      distance_unit: "km",
      repetitions: 0,
      recovery: "",
      pace_min: "",
      pace_max: "",
      notes: "Corrida longa em intensidade controlada.",
    },
    {
      label: "Desaquecimento",
      type: "Desaquecimento",
      distance: 1,
      distance_unit: "km",
      repetitions: 0,
      recovery: "",
      pace_min: "",
      pace_max: "",
      notes: "Corrida muito leve.",
    },
  ];

  function changeStep(index, field, nextValue) {
    onChange((session) => ({
      ...session,
      steps: session.steps.map((step, position) =>
        position === index
          ? { ...step, [field]: nextValue }
          : step
      ),
    }));
  }

  function addStep(preset = null) {
    const baseStep = preset || {
      type: "Corrida",
      distance: 1,
      distance_unit: "km",
      repetitions: 0,
      recovery: "",
      pace_min: "",
      pace_max: "",
      notes: "",
    };

    onChange((session) => ({
      ...session,
      steps: [
        ...session.steps,
        { ...baseStep },
      ],
    }));
  }

  function removeStep(index) {
    onChange((session) => ({
      ...session,
      steps: session.steps.filter(
        (_, position) => position !== index,
      ),
    }));
  }

  function stepDistanceKm(step) {
    const distance = Number(step.distance || 0);
    const repetitions = Math.max(
      Number(step.repetitions || 0),
      1,
    );
    const unit = step.distance_unit || (
      Number(step.repetitions || 0) > 0
        ? "m"
        : "km"
    );

    const total = distance * repetitions;

    return unit === "m"
      ? total / 1000
      : total;
  }

  function paceToSeconds(value) {
    if (!value || !String(value).includes(":")) {
      return null;
    }

    const [minutes, seconds] = String(value)
      .split(":")
      .map(Number);

    if (
      Number.isNaN(minutes)
      || Number.isNaN(seconds)
    ) {
      return null;
    }

    return minutes * 60 + seconds;
  }

  const totalDistance = value.steps.reduce(
    (total, step) =>
      total + stepDistanceKm(step),
    0,
  );

  const estimatedSeconds = value.steps.reduce(
    (total, step) => {
      const distance = stepDistanceKm(step);
      const minPace = paceToSeconds(step.pace_min);
      const maxPace = paceToSeconds(step.pace_max);
      const paces = [
        minPace,
        maxPace,
      ].filter(Boolean);

      if (paces.length === 0) {
        return total;
      }

      const averagePace = paces.reduce(
        (sum, pace) => sum + pace,
        0,
      ) / paces.length;

      return total + distance * averagePace;
    },
    0,
  );

  function formatDuration(seconds) {
    if (!seconds) {
      return "Não calculado";
    }

    const rounded = Math.round(seconds);
    const hours = Math.floor(rounded / 3600);
    const minutes = Math.floor(
      (rounded % 3600) / 60,
    );
    const remainder = rounded % 60;

    return [hours, minutes, remainder]
      .map((part) =>
        String(part).padStart(2, "0")
      )
      .join(":");
  }

  const estimatedLoad = value.steps.reduce(
    (total, step) => {
      const zoneMatch = String(
        value.zone || step.notes || "",
      ).match(/z\s*([1-5])/i);

      const zoneFactor = zoneMatch
        ? Number(zoneMatch[1])
        : 2;

      return total
        + stepDistanceKm(step) * zoneFactor;
    },
    0,
  );

  return (
    <form
      className="workout-editor-v2"
      onSubmit={onSave}
    >
      <header className="workout-editor-v2-header">
        <div>
          <p className="eyebrow">EDIÇÃO COMPLETA</p>
          <h2>Editar treino</h2>
        </div>

        <div>
          <button
            type="button"
            className="btn-ghost"
            onClick={onCancel}
            disabled={saving}
          >
            Cancelar
          </button>

          <button
            className="btn-primary"
            disabled={
              saving
              || value.steps.length === 0
            }
          >
            {saving ? "Salvando..." : "Salvar"}
          </button>
        </div>
      </header>

      <div className="workout-editor-v2-grid">
        <aside className="workout-editor-sidebar">
          <section className="workout-athlete-summary">
            <span className="workout-athlete-avatar">
              {(athlete?.name || "RC")
                .split(" ")
                .filter(Boolean)
                .slice(0, 2)
                .map((part) => part[0])
                .join("")
                .toUpperCase()}
            </span>

            <div>
              <strong>
                {athlete?.name || "Atleta"}
              </strong>
              <small>
                {athlete?.goal
                  || "Objetivo não informado"}
              </small>
            </div>
          </section>

          <label>
            Data do treino
            <input
              type="date"
              value={value.session_date || ""}
              onChange={(event) =>
                onChange((item) => ({
                  ...item,
                  session_date: event.target.value,
                }))
              }
            />
          </label>

          <label>
            Dia da semana
            <input
              readOnly
              value={
                weekdayForDate(value.session_date)
                || "Não definido"
              }
            />
          </label>

          <section className="workout-editor-summary-card">
            <h3>Resumo</h3>

            <div>
              <span>Distância total</span>
              <strong>
                {totalDistance.toLocaleString(
                  "pt-BR",
                  {
                    minimumFractionDigits: 1,
                    maximumFractionDigits: 2,
                  },
                )} km
              </strong>
            </div>

            <div>
              <span>Tempo estimado</span>
              <strong>
                {formatDuration(estimatedSeconds)}
              </strong>
            </div>

            <div>
              <span>Carga estimada</span>
              <strong>
                {estimatedLoad.toFixed(0)} pts
              </strong>
            </div>
          </section>
        </aside>

        <main className="workout-editor-main">
          <section className="workout-editor-session-fields">
            <label>
              Nome do treino
              <input
                required
                value={value.workout_name}
                onChange={(event) =>
                  onChange((item) => ({
                    ...item,
                    workout_name: event.target.value,
                  }))
                }
              />
            </label>

            <label>
              Zona geral
              <input
                value={value.zone}
                onChange={(event) =>
                  onChange((item) => ({
                    ...item,
                    zone: event.target.value,
                  }))
                }
              />
            </label>
          </section>

          <div className="workout-blocks-heading">
            <h3>Blocos do treino</h3>

            <button
              type="button"
              className="btn-ghost"
              onClick={() => addStep()}
            >
              + Adicionar bloco
            </button>
          </div>

          <div className="workout-block-list">
            {value.steps.map((step, index) => (
              <section
                className={`workout-block-card ${stepTone(step.type)}`}
                key={step.id || index}
              >
                <header>
                  <span>{index + 1}</span>

                  <strong>
                    {step.type || `Bloco ${index + 1}`}
                  </strong>

                  {value.steps.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeStep(index)}
                      aria-label={`Remover bloco ${index + 1}`}
                    >
                      ×
                    </button>
                  )}
                </header>

                <div className="workout-block-fields">
                  <label>
                    Tipo
                    <div className="step-type-picker">
                      <button
                        type="button"
                        onClick={() =>
                          setOpenTypePicker((current) =>
                            current === index
                              ? null
                              : index
                          )
                        }
                      >
                        {step.type}
                        <span>⌄</span>
                      </button>

                      {openTypePicker === index && (
                        <div className="step-type-menu">
                          {stepTypes.map((type) => (
                            <button
                              type="button"
                              className={
                                step.type === type
                                  ? "active"
                                  : ""
                              }
                              key={type}
                              onClick={() => {
                                changeStep(
                                  index,
                                  "type",
                                  type,
                                );
                                setOpenTypePicker(null);
                              }}
                            >
                              {type}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  </label>

                  <label>
                    Distância
                    <div className="distance-input">
                      <input
                        type="number"
                        step="0.1"
                        min="0"
                        value={step.distance}
                        onChange={(event) =>
                          changeStep(
                            index,
                            "distance",
                            event.target.value,
                          )
                        }
                      />

                      <select
                        value={
                          step.distance_unit
                          || (
                            step.repetitions
                              ? "m"
                              : "km"
                          )
                        }
                        onChange={(event) =>
                          changeStep(
                            index,
                            "distance_unit",
                            event.target.value,
                          )
                        }
                      >
                        <option value="km">km</option>
                        <option value="m">m</option>
                      </select>
                    </div>
                  </label>

                  <label>
                    Repetições
                    <input
                      type="number"
                      min="0"
                      value={step.repetitions}
                      onChange={(event) =>
                        changeStep(
                          index,
                          "repetitions",
                          event.target.value,
                        )
                      }
                    />
                  </label>

                  <label>
                    Recuperação
                    <input
                      value={step.recovery || ""}
                      placeholder="Ex.: 200 m trote"
                      onChange={(event) =>
                        changeStep(
                          index,
                          "recovery",
                          event.target.value,
                        )
                      }
                    />
                  </label>

                  <label>
                    Ritmo mínimo
                    <input
                      inputMode="numeric"
                      maxLength={5}
                      value={step.pace_min || ""}
                      placeholder="05:20"
                      onChange={(event) =>
                        changeStep(
                          index,
                          "pace_min",
                          formatPaceInput(
                            event.target.value,
                          ),
                        )
                      }
                    />
                  </label>

                  <label>
                    Ritmo máximo
                    <input
                      inputMode="numeric"
                      maxLength={5}
                      value={step.pace_max || ""}
                      placeholder="05:00"
                      onChange={(event) =>
                        changeStep(
                          index,
                          "pace_max",
                          formatPaceInput(
                            event.target.value,
                          ),
                        )
                      }
                    />
                  </label>
                </div>

                <label className="workout-block-notes">
                  Instrução do bloco
                  <textarea
                    value={step.notes || ""}
                    onChange={(event) =>
                      changeStep(
                        index,
                        "notes",
                        event.target.value,
                      )
                    }
                  />
                </label>
              </section>
            ))}
          </div>

          <label className="workout-general-notes">
            Orientação geral do treinador
            <textarea
              value={value.notes}
              onChange={(event) =>
                onChange((item) => ({
                  ...item,
                  notes: event.target.value,
                }))
              }
            />
          </label>
        </main>

        <aside className="workout-frequent-blocks">
          <h3>Blocos frequentes</h3>

          {frequentBlocks.map((block) => (
            <button
              type="button"
              key={block.label}
              onClick={() => addStep(block)}
            >
              <span>＋</span>
              {block.label}
            </button>
          ))}
        </aside>
      </div>
    </form>
  );
}


export default function App() {
  const location = useLocation();
  const navigate = useNavigate();
  const [athletes, setAthletes] = useState([]);
  const [currentUser, setCurrentUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);
  const masterInitialRedirectDone = useRef(false);
  const [search, setSearch] = useState("");
  const [athleteForm, setAthleteForm] = useState(emptyAthlete);
  const [evaluationForm, setEvaluationForm] = useState(emptyEvaluation);
  const [showForm, setShowForm] = useState(false);
  const [selectedAthlete, setSelectedAthlete] = useState(null);
  const [selectedWorkout, setSelectedWorkout] = useState(null);
  const [selectedView, setSelectedView] = useState("evaluations");
  const [evaluations, setEvaluations] = useState([]);
  const [training, setTraining] = useState(null);
  const [loading, setLoading] = useState(true);
  const [savingEvaluation, setSavingEvaluation] = useState(false);
  const [savingTraining, setSavingTraining] = useState(false);
  const [trainingForm, setTrainingForm] = useState({ name: "Planejamento Principal", objective: "", target_distance: "", start_date: new Date().toISOString().slice(0, 10), target_date: "", total_weeks: "8" });
  const [workoutEdit, setWorkoutEdit] = useState(null);
  const [error, setError] = useState(null);
  const [invitations, setInvitations] = useState({ pending: [], sent: [] });
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteLink, setInviteLink] = useState("");
  const [quickAction, setQuickAction] = useState(null);

  async function loadAthletes(currentSearch = search) {
    setLoading(true);
    setError(null);
    try {
      setAthletes(await listAthletes(currentSearch));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function loadEvaluations(athleteId) {
    setLoading(true);
    setError(null);
    try {
      setEvaluations(await listEvaluations(athleteId));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!trainingForm.target_date) {
      return;
    }

    const calculatedWeeks = availableTrainingWeeks(
      trainingForm.start_date,
      trainingForm.target_date,
    );

    setTrainingForm((current) => {
      const nextValue = calculatedWeeks
        ? String(calculatedWeeks)
        : "";

      if (current.total_weeks === nextValue) {
        return current;
      }

      return {
        ...current,
        total_weeks: nextValue,
      };
    });
  }, [
    trainingForm.start_date,
    trainingForm.target_date,
  ]);

  useEffect(() => {
    if (!hasSession()) { setAuthLoading(false); return; }
    getCurrentUser().then(setCurrentUser).catch(clearSession).finally(() => setAuthLoading(false));
  }, []);

  useEffect(() => {
    if (!currentUser) {
      masterInitialRedirectDone.current = false;
      return;
    }

    if (
      currentUser.role === "master"
      && !masterInitialRedirectDone.current
    ) {
      masterInitialRedirectDone.current = true;
      navigate(coachPaths.dashboard, { replace: true });
    }
  }, [currentUser, navigate]);

  useEffect(() => {
    if (["coach", "master"].includes(currentUser?.role)) { loadAthletes(""); loadInvitations(); }
  }, [currentUser]);

  useEffect(() => {
    if (
      ["coach", "master"].includes(currentUser?.role)
      && !location.pathname.startsWith("/treinador")
      && !location.pathname.startsWith("/administrativo")
    ) {
      navigate(coachPaths.dashboard, { replace: true });
    }
  }, [currentUser, location.pathname, navigate]);

  useEffect(() => {
    if (!["coach", "master"].includes(currentUser?.role)) return undefined;
    const refreshInvitations = () => loadInvitations();
    const interval = window.setInterval(refreshInvitations, 5000);
    window.addEventListener("focus", refreshInvitations);
    return () => { window.clearInterval(interval); window.removeEventListener("focus", refreshInvitations); };
  }, [currentUser]);


  useEffect(() => {
    closeWorkoutEditor();
  }, [location.pathname]);

  useEffect(() => {
    if (!selectedWorkout) {
      document.body.style.overflow = "";
      return undefined;
    }

    document.body.style.overflow = "hidden";

    function closeOnEscape(event) {
      if (event.key === "Escape") {
        closeWorkoutEditor();
      }
    }

    window.addEventListener("keydown", closeOnEscape);

    return () => {
      document.body.style.overflow = "";
      window.removeEventListener("keydown", closeOnEscape);
    };
  }, [selectedWorkout]);

  useEffect(() => {
    if (
      !["coach", "master"].includes(currentUser?.role)
      || athletes.length === 0
    ) {
      return;
    }

    const routeMatch = location.pathname.match(
      /^\/treinador\/atletas\/(\d+)(?:\/(planejamento|avaliacoes|ipt))?$/
    );

    if (!routeMatch) {
      const topLevelCoachPaths = new Set([
        coachPaths.dashboard,
        coachPaths.athletes,
        coachPaths.planning,
        coachPaths.workouts,
        coachPaths.calendar,
        coachPaths.evaluations,
        coachPaths.reports,
        coachPaths.settings,
        coachPaths.profile,
      ]);

      if (topLevelCoachPaths.has(location.pathname)) {
        setSelectedAthlete(null);
        setSelectedWorkout(null);
        setWorkoutEdit(null);
      }

      return;
    }

    const athleteId = Number(routeMatch[1]);
    const routeSection = routeMatch[2] || "profile";
    const viewSection = routeSection === "planejamento"
      ? "training"
      : routeSection === "avaliacoes"
        ? "evaluations"
        : routeSection;

    const athlete = athletes.find(
      (item) => item.id === athleteId,
    );

    if (!athlete) {
      navigate(coachPaths.athletes, { replace: true });
      return;
    }

    const requestedWorkoutId = new URLSearchParams(
      location.search,
    ).get("sessao");

    const hasPendingTemplate = Boolean(
      window.sessionStorage.getItem(
        "runcore.pending-workout-template",
      ),
    );

    const requestedWorkoutAlreadyReady = (
      requestedWorkoutId
      && selectedAthlete?.id === athlete.id
      && selectedView === viewSection
      && String(selectedWorkout?.id)
        === String(requestedWorkoutId)
      && workoutEdit
      && !hasPendingTemplate
    );

    if (requestedWorkoutAlreadyReady) {
      return;
    }

    if (
      selectedAthlete?.id === athlete.id
      && selectedView === viewSection
      && !requestedWorkoutId
    ) {
      return;
    }

    setSelectedAthlete(athlete);
    setSelectedView(viewSection);
    setSelectedWorkout(null);
    setError(null);

    if (viewSection === "evaluations") {
      setEvaluationForm(emptyEvaluation);
      loadEvaluations(athlete.id);
    }

    if (viewSection === "training") {
      setWorkoutEdit(null);
      setTrainingForm({
        name: "Planejamento Principal",
        objective: athlete.goal || "Preparação para prova",
        target_distance: "",
        start_date: new Date().toISOString().slice(0, 10),
        target_date: "",
        total_weeks: "8",
      });
      setLoading(true);
      getTraining(athlete.id)
        .then((loadedTraining) => {
          setTraining(loadedTraining);

          if (requestedWorkoutId) {
            const requestedWorkout = (
              loadedTraining?.sessions || []
            ).find(
              (session) =>
                String(session.id)
                === String(requestedWorkoutId),
            );

            if (requestedWorkout) {
              let preparedWorkout = {
                ...requestedWorkout,
                notes: requestedWorkout.notes || "",
                steps: (requestedWorkout.steps || []).map(
                  (step) => ({ ...step }),
                ),
              };

              try {
                const pending = JSON.parse(
                  window.sessionStorage.getItem(
                    "runcore.pending-workout-template",
                  ) || "null",
                );

                if (
                  pending
                  && String(pending.athleteId) === String(athlete.id)
                  && String(pending.sessionId) === String(requestedWorkout.id)
                ) {
                  const template = pending.template;

                  preparedWorkout = {
                    ...preparedWorkout,
                    workout_name: template.name,
                    zone: template.zone,
                    planned_distance: Number(template.estimatedDistance || 0),
                    repetitions: 0,
                    notes: [template.notes, template.objective]
                      .filter(Boolean)
                      .join("\n"),
                    steps: template.steps.map((step, index) => ({
                      id: `template-${Date.now()}-${index}`,
                      type: step.type,
                      distance: step.unit === "min"
                        ? 0
                        : Number(step.distance || 0),
                      distance_unit: step.unit === "m" ? "m" : "km",
                      repetitions: Number(step.repetitions || 0),
                      recovery: step.recovery || "",
                      pace_min: step.pace || "",
                      pace_max: step.pace || "",
                      notes: step.unit === "min"
                        ? `Duração: ${step.distance} min`
                        : "",
                    })),
                  };

                  window.sessionStorage.removeItem(
                    "runcore.pending-workout-template",
                  );
                }
              } catch {
                window.sessionStorage.removeItem(
                  "runcore.pending-workout-template",
                );
              }

              setSelectedWorkout(requestedWorkout);
              setWorkoutEdit(preparedWorkout);
            } else {
              setError("A sessão solicitada não foi encontrada.");
            }
          }
        })
        .catch((err) => setError(err.message))
        .finally(() => setLoading(false));
    }
  }, [
    athletes,
    currentUser,
    location.pathname,
    location.search,
    navigate,
    selectedAthlete,
    selectedView,
    selectedWorkout,
    workoutEdit,
  ]);

  async function loadInvitations() {
    try { setInvitations(await listInvitations()); } catch (err) { setError(err.message); }
  }

  async function handleCreateInvitation(event) {
    event.preventDefault();
    try {
      const invitation = await createInvitation({ email: inviteEmail });
      setInviteEmail("");
      setInviteLink(invitation.registration_url);
      loadInvitations();
    } catch (err) { setError(err.message); }
  }

  async function handleApproveInvitation(id) {
    try { await approveInvitation(id); await Promise.all([loadInvitations(), loadAthletes(search)]); } catch (err) { setError(err.message); }
  }

  function handleSearchSubmit(event) {
    event.preventDefault();
    loadAthletes(search);
  }

  async function handleCreateAthlete(event) {
    event.preventDefault();
    if (!athleteForm.name.trim()) return;
    try {
      await createAthlete({ ...athleteForm, active: true });
      setAthleteForm(emptyAthlete);
      setShowForm(false);
      loadAthletes(search);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleDeleteAthlete(id) {
    if (!window.confirm("Remover este atleta?")) return;
    try {
      await deleteAthlete(id);
      if (selectedAthlete?.id === id) setSelectedAthlete(null);
      loadAthletes(search);
    } catch (err) {
      setError(err.message);
    }
  }

  function openEvaluations(athlete) {
    setSelectedAthlete(athlete);
    setSelectedView("evaluations");
    setEvaluationForm(emptyEvaluation);
    setSelectedWorkout(null);
    navigate(
      coachPaths.athleteEvaluations(athlete.id),
    );
    loadEvaluations(athlete.id);
  }

  function openProfile(athlete) {
    setSelectedAthlete(athlete);
    setSelectedView("profile");
    navigate(
      coachPaths.athleteProfile(athlete.id),
    );
  }

  function openIpt(athlete) {
    setSelectedAthlete(athlete);
    setSelectedView("ipt");
    setSelectedWorkout(null);
    setError(null);
    navigate(
      coachPaths.athleteIpt(athlete.id),
    );
  }

  async function createSessionFromTemplate(
    athlete,
    sessionDate,
    template,
  ) {
    const createdSession = await createTrainingSession(
      athlete.id,
      {
        session_date: sessionDate,
        workout_name: template.name,
        zone: template.zone,
        planned_distance: Number(
          template.estimatedDistance || 0,
        ),
        repetitions: 0,
        notes: [
          template.notes,
          template.objective,
        ].filter(Boolean).join("\n"),
        steps: template.steps.map((step) => ({
          type: step.type,
          distance:
            step.unit === "min"
              ? 0
              : Number(step.distance || 0),
          distance_unit:
            step.unit === "m" ? "m" : "km",
          repetitions: Number(
            step.repetitions || 0,
          ),
          recovery: step.recovery || "",
          pace_min: step.pace || "",
          pace_max: step.pace || "",
          notes:
            step.unit === "min"
              ? `Duração: ${step.distance} min`
              : "",
        })),
      },
    );

    setTraining((current) => {
      if (!current) {
        return current;
      }

      return {
        ...current,
        sessions: [
          ...current.sessions,
          createdSession,
        ].sort((first, second) =>
          String(first.session_date || "")
            .localeCompare(
              String(second.session_date || ""),
            )
        ),
      };
    });

    openTraining(athlete, createdSession);
  }

  function applyWorkoutTemplate(
    athlete,
    session,
    template,
  ) {
    window.sessionStorage.setItem(
      "runcore.pending-workout-template",
      JSON.stringify({
        athleteId: athlete.id,
        sessionId: session.id,
        template,
      }),
    );

    openTraining(athlete, session);
  }

  async function openTraining(
    athlete,
    requestedWorkout = null,
  ) {
    setSelectedAthlete(athlete);
    setSelectedView("training");
    setSelectedWorkout(null);
    setWorkoutEdit(null);
    setError(null);

    const planningPath =
      coachPaths.athletePlanning(athlete.id);

    if (requestedWorkout?.id) {
      const freshWorkout = (
        training?.sessions || []
      ).find(
        (session) =>
          String(session.id)
          === String(requestedWorkout.id),
      ) || requestedWorkout;

      setSelectedWorkout(freshWorkout);
      setWorkoutEdit({
        ...freshWorkout,
        notes: freshWorkout.notes || "",
        steps: (freshWorkout.steps || []).map(
          (step) => ({ ...step }),
        ),
      });

      navigate(
        `${planningPath}?sessao=${freshWorkout.id}`,
      );
      return;
    }

    navigate(planningPath);

    setTrainingForm({
      name: "Planejamento Principal",
      objective:
        athlete.goal || "Preparação para prova",
      target_distance: "",
      start_date:
        new Date().toISOString().slice(0, 10),
      target_date: "",
      total_weeks: "8",
    });

    setLoading(true);

    try {
      setTraining(
        await getTraining(athlete.id),
      );
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateTraining(regenerate = false) {
    if (savingTraining) return;

    setSavingTraining(true);
    setError(null);
    try {
      const data = regenerate
        ? await regenerateTraining(selectedAthlete.id)
        : await createTraining(selectedAthlete.id, { ...trainingForm, target_distance: Number(trainingForm.target_distance), total_weeks: trainingForm.target_date ? null : Number(trainingForm.total_weeks) });
      setTraining(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setSavingTraining(false);
    }
  }

  function closeWorkoutEditor() {
    setSelectedWorkout(null);
    setWorkoutEdit(null);

    if (
      selectedAthlete
      && location.search.includes("sessao=")
    ) {
      navigate(
        coachPaths.athletePlanning(
          selectedAthlete.id,
        ),
        { replace: true },
      );
    }
  }

  async function handleUpdateWorkout(event) {
    event.preventDefault();

    if (!workoutEdit || savingTraining) {
      return;
    }

    const normalizedWorkout = {
      ...workoutEdit,
      planned_distance: Number(
        workoutEdit.planned_distance,
      ),
      repetitions: Number(
        workoutEdit.repetitions,
      ),
      steps: workoutEdit.steps.map((step) => ({
        ...step,
        distance: Number(
          step.distance,
        ),
        repetitions: Number(
          step.repetitions,
        ),
      })),
    };

    setSavingTraining(true);
    setError(null);

    try {
      await updateTrainingSession(
        selectedAthlete.id,
        workoutEdit.id,
        normalizedWorkout,
      );

      setTraining((current) => {
        if (!current) {
          return current;
        }

        return {
          ...current,
          sessions: current.sessions.map((session) => (
            session.id === normalizedWorkout.id
              ? {
                  ...session,
                  ...normalizedWorkout,
                }
              : session
          )),
        };
      });

      closeWorkoutEditor();
    } catch (err) {
      setError(
        err.message,
      );
    } finally {
      setSavingTraining(false);
    }
  }

  async function handleCreateEvaluation(event) {
    event.preventDefault();
    if (savingEvaluation) return;

    setSavingEvaluation(true);
    try {
      await createEvaluation(selectedAthlete.id, {
        weight: asNumber(evaluationForm.weight),
        height: asNumber(evaluationForm.height),
        max_hr: asNumber(evaluationForm.max_hr),
        resting_hr: asNumber(evaluationForm.resting_hr),
        test_type: evaluationForm.test_type,
        time: evaluationForm.time,
        test_date: evaluationForm.test_date,
      });
      setEvaluationForm(emptyEvaluation);
      loadEvaluations(selectedAthlete.id);
    } catch (err) {
      setError(err.message);
    } finally {
      setSavingEvaluation(false);
    }
  }

  async function handleDeleteEvaluation(evaluationId) {
    if (!window.confirm("Remover esta avaliação?")) return;
    try {
      await deleteEvaluation(selectedAthlete.id, evaluationId);
      loadEvaluations(selectedAthlete.id);
    } catch (err) {
      setError(err.message);
    }
  }

  if (authLoading) {
    return (
      <main
        className="app-bootstrap-loading"
        aria-label="Carregando RunCore"
      >
        <section className="app-bootstrap-loading-card">
          <img
            src="/logo-horizontal.png?v=2"
            alt="RunCore"
          />

          <span
            className="app-bootstrap-spinner"
            aria-hidden="true"
          />

          <p>Preparando seu painel...</p>
        </section>
      </main>
    );
  }
  if (!currentUser) return <LoginScreen onAuthenticated={setCurrentUser} />;
  if (currentUser.role === "admin") {
    const adminLogout = () => {
      clearSession();
      setCurrentUser(null);
    };

    return (
      <Routes>
        <Route element={<AppShell user={currentUser} onLogout={adminLogout} />}>
          <Route
            path={adminPaths.users}
            element={<AdminUsersPage currentUser={currentUser} />}
          />
          <Route
            path={adminPaths.settings}
            element={<SettingsPage user={currentUser} />}
          />
        </Route>
        <Route path="*" element={<Navigate to={adminPaths.users} replace />} />
      </Routes>
    );
  }

  if (currentUser.role === "student") {
    const studentLogout = () => {
      clearSession();
      setCurrentUser(null);
    };

    return (
      <Routes>
        <Route element={<AppShell user={currentUser} onLogout={studentLogout} />}>
          <Route path={studentPaths.dashboard} element={<StudentPortal user={currentUser} onLogout={studentLogout} view="dashboard" />} />
          <Route path={studentPaths.trainingPlan} element={<StudentPortal user={currentUser} onLogout={studentLogout} view="training" />} />
          <Route path={studentPaths.goals} element={<StudentPortal user={currentUser} onLogout={studentLogout} view="goals" />} />
          <Route path={studentPaths.activities} element={<StudentPortal user={currentUser} onLogout={studentLogout} view="activities" />} />
          <Route path={studentPaths.calculators} element={<StudentPortal user={currentUser} onLogout={studentLogout} view="calculators" />} />
          <Route path={studentPaths.profile} element={<StudentPortal user={currentUser} onLogout={studentLogout} view="profile" />} />
          <Route path={studentPaths.evolution} element={<StudentEvolutionPage />} />
          <Route path={studentPaths.calendar} element={<StudentAgendaPage />} />
          <Route path={studentPaths.settings} element={<SettingsPage user={currentUser} />} />
        </Route>
        <Route path="*" element={<Navigate to={studentPaths.dashboard} replace />} />
      </Routes>
    );
  }

  const coachLogout = () => {
    clearSession();
    setCurrentUser(null);
  };

  if (
    currentUser.role === "master"
    && location.pathname === adminPaths.users
  ) {
    return (
      <AppShell user={currentUser} onLogout={coachLogout}>
        <AdminUsersPage currentUser={currentUser} />
      </AppShell>
    );
  }









  if (
    !selectedAthlete
    && location.pathname === coachPaths.dashboard
  ) {
    return (
      <AppShell user={currentUser} onLogout={coachLogout}>
        <CoachDashboardPage
          user={currentUser}
          athletes={athletes}
          invitations={invitations}
          inviteEmail={inviteEmail}
          setInviteEmail={setInviteEmail}
          inviteLink={inviteLink}
          onCreateInvitation={handleCreateInvitation}
          onApproveInvitation={handleApproveInvitation}
          onOpenProfile={openProfile}
          onOpenTraining={openTraining}
          onOpenEvaluations={openEvaluations}
        />
      </AppShell>
    );
  }

  if (
    !selectedAthlete
    && location.pathname === coachPaths.reports
  ) {
    return (
      <AppShell user={currentUser} onLogout={coachLogout}>
        <ReportsPage
          athletes={athletes}
          onOpenPlanning={openTraining}
          onOpenEvaluations={openEvaluations}
        />
      </AppShell>
    );
  }

  if (
    !selectedAthlete
    && location.pathname === coachPaths.evaluations
  ) {
    return (
      <AppShell user={currentUser} onLogout={coachLogout}>
        <EvaluationsPage
          athletes={athletes}
          onOpenEvaluations={openEvaluations}
        />
      </AppShell>
    );
  }

  if (
    !selectedAthlete
    && location.pathname === coachPaths.calendar
  ) {
    return (
      <AppShell user={currentUser} onLogout={coachLogout}>
        <AgendaPage
          athletes={athletes}
          onOpenTraining={openTraining}
        />
      </AppShell>
    );
  }

  if (
    !selectedAthlete
    && location.pathname === coachPaths.workouts
  ) {
    return (
      <AppShell user={currentUser} onLogout={coachLogout}>
        <WorkoutsPage
          athletes={athletes}
          onApplyTemplate={applyWorkoutTemplate}
          onCreateFromTemplate={createSessionFromTemplate}
        />
      </AppShell>
    );
  }

  if (
    !selectedAthlete
    && location.pathname === coachPaths.planning
  ) {
    return (
      <AppShell user={currentUser} onLogout={coachLogout}>
        <PlanningPage
          athletes={athletes}
          loading={loading}
          error={error}
          onOpenPlanning={openTraining}
        />
      </AppShell>
    );
  }


  if (
    !selectedAthlete
    && location.pathname === coachPaths.profile
  ) {
    return (
      <AppShell user={currentUser} onLogout={coachLogout}>
        <CoachProfilePage user={currentUser} />
      </AppShell>
    );
  }

  if (
    !selectedAthlete
    && location.pathname === coachPaths.settings
  ) {
    return (
      <AppShell user={currentUser} onLogout={coachLogout}>
        <SettingsPage user={currentUser} />
      </AppShell>
    );
  }

  if (selectedAthlete && selectedView === "profile") {
    return (
      <AppShell user={currentUser} onLogout={coachLogout}>
        <div className="page routed-profile-page">
          <AthleteProfileView
            athlete={selectedAthlete}
            onClose={() => {
              setSelectedAthlete(null);
              navigate(coachPaths.athletes);
            }}
            onRemove={() =>
              handleDeleteAthlete(selectedAthlete.id)
            }
            onOpenTraining={openTraining}
            onOpenEvaluations={openEvaluations}
          />
        </div>
      </AppShell>
    );
  }

  if (selectedAthlete && selectedView === "ipt") {
    return (
      <AppShell user={currentUser} onLogout={coachLogout}>
        <div className="page routed-ipt-page">
          <IptAssessmentView
            athlete={selectedAthlete}
            onBack={() => {
              setSelectedAthlete(null);
              navigate(coachPaths.athletes);
            }}
            onEvaluations={() =>
              openEvaluations(selectedAthlete)
            }
            onTraining={() =>
              openTraining(selectedAthlete)
            }
          />
        </div>
      </AppShell>
    );
  }

  if (selectedAthlete && selectedView === "evaluations") {
    return (
      <AppShell user={currentUser} onLogout={coachLogout}>
        <div className="page routed-evaluations-page">
        <header className="topbar">
          <div className="brand">
            <BrandLogo />
            <div>
              <h1>Avaliações físicas e VDOT</h1>
              <p>Aluno: {selectedAthlete.name}</p>
            </div>
          </div>
          <div className="header-actions"><button className="btn-ghost" onClick={() => openIpt(selectedAthlete)}>IPT</button><button className="btn-ghost" onClick={() => openTraining(selectedAthlete)}>Planejamento</button><button className="btn-ghost" onClick={() => setSelectedAthlete(null)}>Voltar para atletas</button></div>
        </header>

        <main className="content">
          {error && <div className="alert">{error}</div>}

          <form className="card evaluation-form" onSubmit={handleCreateEvaluation}>
            <h2>Nova avaliação</h2>
            <div className="form-grid">
              <label>Peso (kg)<input type="number" min="0.1" step="0.1" required value={evaluationForm.weight} onChange={(e) => setEvaluationForm({ ...evaluationForm, weight: e.target.value })} /></label>
              <label>Altura (m)<input type="number" min="0.01" step="0.01" required value={evaluationForm.height} onChange={(e) => setEvaluationForm({ ...evaluationForm, height: e.target.value })} /></label>
              <label>FC máxima<input type="number" min="1" required value={evaluationForm.max_hr} onChange={(e) => setEvaluationForm({ ...evaluationForm, max_hr: e.target.value })} /></label>
              <label>FC repouso<input type="number" min="1" required value={evaluationForm.resting_hr} onChange={(e) => setEvaluationForm({ ...evaluationForm, resting_hr: e.target.value })} /></label>
              <label>Data do teste<input type="date" required value={evaluationForm.test_date} onChange={(e) => setEvaluationForm({ ...evaluationForm, test_date: e.target.value })} /></label>
              <label>Tipo de teste<select required value={evaluationForm.test_type} onChange={(e) => setEvaluationForm({ ...evaluationForm, test_type: e.target.value })}><option value="" disabled>Selecione</option><option value="3 km">3 km</option><option value="5 km">5 km</option><option value="10 km">10 km</option><option value="Meia maratona">Meia maratona</option><option value="Maratona">Maratona</option></select></label>              <label>Tempo do teste (HH:MM:SS)<input type="text" inputMode="numeric" placeholder="00:25:30" pattern="\d{2}:[0-5]\d:[0-5]\d" required value={evaluationForm.time} onChange={(e) => setEvaluationForm({ ...evaluationForm, time: formatTestTimeInput(e.target.value) })} /></label>
            </div>
            <button type="submit" className="btn-primary" disabled={savingEvaluation}>{savingEvaluation ? "Salvando..." : "Salvar avaliação"}</button>
          </form>

          {loading ? <p className="muted">Carregando...</p> : evaluations.length === 0 ? (
            <div className="empty-state"><p>Nenhuma avaliação registrada.</p></div>
          ) : (
            <table className="athletes-table">
              <thead><tr><th>Data</th><th>VDOT</th><th>Teste</th><th>Dados</th><th></th></tr></thead>
              <tbody>
                {evaluations.map((evaluation) => (
                  <tr key={evaluation.id}>
                    <td>{formatTestDate(evaluation.test_date)}</td>
                    <td className="name-cell">{evaluation.vdot.toFixed(1)}</td>
                    <td>{evaluation.test_type}</td>
                    <td className="muted">{evaluation.distance ? `${evaluation.distance / 1000} km em ${formatDuration(evaluation.time_seconds)}` : "Sem teste de corrida"}</td>
                    <td><button className="btn-link-danger" onClick={() => handleDeleteEvaluation(evaluation.id)}>Remover</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </main>
        </div>
      </AppShell>
    );
  }

  const requestedWorkoutId = new URLSearchParams(
    location.search,
  ).get("sessao");

  if (
    selectedAthlete
    && selectedView === "training"
    && requestedWorkoutId
  ) {
    return (
      <AppShell
        user={currentUser}
        onLogout={coachLogout}
      >
        <div className="dedicated-workout-editor-page">
          {selectedWorkout && workoutEdit ? (
            <SessionAdjustment
              key={workoutEdit.id}
              value={workoutEdit}
              onChange={setWorkoutEdit}
              onSave={handleUpdateWorkout}
              onCancel={closeWorkoutEditor}
              saving={savingTraining}
              athlete={selectedAthlete}
            />
          ) : error ? (
            <section className="dedicated-workout-loading">
              <div>
                <p className="eyebrow">NÃO FOI POSSÍVEL ABRIR</p>
                <h2>Erro ao carregar treino</h2>
                <p>{error}</p>
                <button
                  type="button"
                  className="btn-primary"
                  onClick={closeWorkoutEditor}
                >
                  Voltar ao planejamento
                </button>
              </div>
            </section>
          ) : (
            <section className="dedicated-workout-loading">
              <span
                className="dedicated-workout-spinner"
                aria-hidden="true"
              />
              <div>
                <p className="eyebrow">EDIÇÃO COMPLETA</p>
                <h2>Carregando treino</h2>
                <p>
                  Preparando os blocos e dados da sessão.
                </p>
              </div>
            </section>
          )}
        </div>
      </AppShell>
    );
  }

  if (selectedAthlete && selectedView === "training") {
    const sessionsByWeek = (training?.sessions || []).reduce((weeks, session) => {
      (weeks[session.week] ||= []).push(session);
      return weeks;
    }, {});

    return (
      <AppShell user={currentUser} onLogout={coachLogout}>
        <div className="page routed-training-page">
        <header className="topbar">
          <div className="brand"><BrandLogo /><div><h1>Planejamento de treino</h1><p>Aluno: {selectedAthlete.name}</p></div></div>
          <div className="header-actions"><button className="btn-ghost" onClick={() => openIpt(selectedAthlete)}>IPT</button><button className="btn-ghost" onClick={() => openEvaluations(selectedAthlete)}>Avaliações</button><button className="btn-ghost" onClick={() => setSelectedAthlete(null)}>Voltar para atletas</button></div>
        </header>
        <main className="content">
          {error && <div className="alert">{error}</div>}
          {loading ? <p className="muted">Carregando...</p> : !training ? (
            <section className="card training-config"><p className="eyebrow">NOVO MACROCICLO</p><h2>Monte o ciclo a partir da meta do aluno</h2><p className="muted">Use a data da prova para calcular as semanas disponíveis ou informe a duração do ciclo.</p><div className="form-grid"><label>Planejamento<input value={trainingForm.name} onChange={(event) => setTrainingForm((form) => ({ ...form, name: event.target.value }))} /></label><label>Objetivo principal<input required value={trainingForm.objective} onChange={(event) => setTrainingForm((form) => ({ ...form, objective: event.target.value }))} placeholder="Ex.: Meia Maratona de Vitória" /></label><label>Distância-alvo (km)<input required type="number" min="0.1" step="0.1" value={trainingForm.target_distance} onChange={(event) => setTrainingForm((form) => ({ ...form, target_distance: event.target.value }))} placeholder="21.1" /></label><label>Início do ciclo<input required type="date" value={trainingForm.start_date} onChange={(event) => setTrainingForm((form) => ({ ...form, start_date: event.target.value }))} /></label><label>Data da prova (opcional)<input type="date" value={trainingForm.target_date} onChange={(event) => setTrainingForm((form) => ({ ...form, target_date: event.target.value }))} /></label><label>Semanas disponíveis {trainingForm.target_date && <small>(calculadas entre o início e a prova)</small>}<input disabled={Boolean(trainingForm.target_date)} type="number" min="1" max="52" value={trainingForm.total_weeks} onChange={(event) => setTrainingForm((form) => ({ ...form, total_weeks: event.target.value }))} /></label></div><button className="btn-primary" disabled={savingTraining || !trainingForm.objective || !trainingForm.target_distance} onClick={() => handleCreateTraining()}>{savingTraining ? "Gerando ciclo..." : "Gerar macrociclo"}</button></section>
          ) : (
            <>
              <section className="card training-summary"><div><p className="eyebrow">MACROCICLO · FASE ATUAL: {training.current_phase}</p><h2>{training.name}</h2><p>Meta: {training.target_distance} km</p><small>Semana {training.current_week} de {training.total_weeks} · início {formatTestDate(training.start_date)}{training.target_date ? ` · prova ${formatTestDate(training.target_date)}` : ""}</small></div><button className="btn-ghost" disabled={savingTraining} onClick={() => handleCreateTraining(true)}>{savingTraining ? "Atualizando..." : "Atualizar planilha"}</button></section>
              {Object.entries(sessionsByWeek).map(([week, sessions]) => (
                <section key={week} className="week-section"><h2>Semana {week} <small>· {sessions[0]?.phase}</small></h2><div className="session-grid">{sessions.map((session) => <article className="card session-card" key={session.id}><span className="session-day">{weekdays[session.weekday]} · {formatTestDate(session.session_date)}</span><h3>{session.workout_name}</h3><p className="zone">{session.zone}</p><p>{session.repetitions ? `${session.repetitions} × ${session.planned_distance} m` : `${session.planned_distance.toFixed(1)} km`}</p><button
  className="btn-link open-workout"
  onClick={() =>
    openTraining(
      selectedAthlete,
      session,
    )
  }
>
  Abrir e ajustar
</button></article>)}</div></section>
              ))}
            </>
          )}
        </main>
        </div>
      </AppShell>
    );
  }

  const coachView =
    location.pathname === coachPaths.athletes
      ? "athletes"
      : "dashboard";

  return (
    <AppShell user={currentUser} onLogout={coachLogout}>
      <div
        className="page coach-routed-page"
        data-view={coachView}
      >
      <header className="topbar">
        <div className="brand">
          <BrandLogo />

          <div>
            <h1>RunCore</h1>
            <p>Painel do treinador</p>
          </div>
        </div>

        <div className="header-actions">
          <button
            className="btn-ghost"
            onClick={() => {
              clearSession();
              setCurrentUser(null);
            }}
          >
            Sair
          </button>

          <button
            className="btn-primary"
            onClick={() => setShowForm((value) => !value)}
          >
            {showForm ? "Cancelar" : "+ Novo atleta"}
          </button>
        </div>
      </header>

      {quickAction && (
        <div
          className="quick-action-overlay"
          role="dialog"
          aria-modal="true"
          aria-label="Escolher atleta"
        >
          <section className="quick-action-dialog">
            <div>
              <p className="eyebrow">ATALHO</p>

              <h2>
                {quickAction === "athletes"
                  ? "Abrir cadastro do atleta"
                  : quickAction === "evaluations"
                    ? "Abrir avaliações"
                    : "Abrir planejamento"}
              </h2>

              <p className="muted">
                Escolha o atleta que deseja acompanhar.
              </p>
            </div>

            <div className="quick-action-list">
              {athletes.length ? (
                athletes.map((athlete) => (
                  <button
                    type="button"
                    key={athlete.id}
                    onClick={() => {
                      setQuickAction(null);

                      if (quickAction === "athletes") {
                        openProfile(athlete);
                      } else if (quickAction === "evaluations") {
                        openEvaluations(athlete);
                      } else {
                        openTraining(athlete);
                      }
                    }}
                  >
                    <span>{athlete.name}</span>

                    <small>
                      {athlete.goal || "Sem objetivo informado"}
                    </small>
                  </button>
                ))
              ) : (
                <p className="muted">Nenhum atleta cadastrado.</p>
              )}
            </div>

            <button
              type="button"
              className="btn-ghost"
              onClick={() => setQuickAction(null)}
            >
              Cancelar
            </button>
          </section>
        </div>
      )}

      <main className="content">
        <section
          id="visao-geral"
          className="coach-hero"
        >
          <div>
            <p className="eyebrow">VISÃO GERAL</p>

            <h2>Olá, {currentUser.name}.</h2>

            <p>
              Organize seus atletas, acompanhe avaliações e mantenha
              cada plano em dia.
            </p>
          </div>

          <div className="hero-date">
            <span>RUNCORE</span>
            <strong>Assessoria em movimento</strong>
          </div>
        </section>

        <nav
          className="portal-menu coach-nav coach-nav-below"
          aria-label="Navegação do treinador"
        >
          <button
            type="button"
            onClick={() =>
              document
                .getElementById("visao-geral")
                ?.scrollIntoView({
                  behavior: "smooth",
                  block: "start",
                })
            }
          >
            Visão geral
          </button>

          <button
            type="button"
            onClick={() =>
              document
                .getElementById("convites")
                ?.scrollIntoView({
                  behavior: "smooth",
                  block: "start",
                })
            }
          >
            Convites e aprovações
          </button>

          <button
            type="button"
            onClick={() => setQuickAction("athletes")}
          >
            Atletas
          </button>

          <button
            type="button"
            onClick={() => setQuickAction("evaluations")}
          >
            Avaliações
          </button>

          <button
            type="button"
            onClick={() => setQuickAction("training")}
          >
            Planejamentos
          </button>
        </nav>

        <section
          id="convites"
          className="card invitations-card"
        >
          <div>
            <p className="eyebrow">NOVOS ALUNOS</p>

            <h2>Convites e aprovações</h2>

            <p className="muted">
              Envie o link, receba o pré-cadastro e aprove o aluno
              quando estiver pronto.
            </p>
          </div>

          <form
            className="invite-form"
            onSubmit={handleCreateInvitation}
          >
            <input
              type="email"
              value={inviteEmail}
              onChange={(event) =>
                setInviteEmail(event.target.value)
              }
              placeholder="E-mail do aluno (opcional)"
            />

            <button className="btn-primary">
              Gerar link de convite
            </button>
          </form>

          {inviteLink && (
            <div className="invite-link">
              <span>Link pronto para compartilhar</span>

              <input
                readOnly
                value={inviteLink}
                onFocus={(event) => event.target.select()}
              />

              <button
                type="button"
                className="btn-ghost"
                onClick={() =>
                  navigator.clipboard?.writeText(inviteLink)
                }
              >
                Copiar
              </button>
            </div>
          )}

          <div className="invitation-status-grid">
            <section className="pending-invitations">
              <div className="invitation-section-heading">
                <strong>Aguardando sua aprovação</strong>
                <span>{invitations.pending.length}</span>
              </div>

              {invitations.pending.length ? (
                invitations.pending.map((invitation) => (
                  <div
                    className="invitation-row"
                    key={invitation.id}
                  >
                    <div>
                      <strong>
                        {invitation.student_name || "Novo aluno"}
                      </strong>

                      <small>
                        {invitation.email ||
                          "E-mail informado no pré-cadastro"}
                        {" · "}
                        {formatDate(invitation.created_at)}
                      </small>
                    </div>

                    <div className="invitation-actions">
                      {invitation.athlete_id && (
                        <button
                          type="button"
                          className="btn-ghost"
                          onClick={() =>
                            openProfile({
                              id: invitation.athlete_id,
                              name:
                                invitation.student_name ||
                                "Novo aluno",
                            })
                          }
                        >
                          Ver cadastro
                        </button>
                      )}

                      <button
                        type="button"
                        className="btn-primary"
                        onClick={() =>
                          handleApproveInvitation(invitation.id)
                        }
                      >
                        Aprovar
                      </button>
                    </div>
                  </div>
                ))
              ) : (
                <p className="invitation-empty">
                  Nenhum aluno aguardando aprovação.
                </p>
              )}
            </section>

            <section className="sent-invitations">
              <div className="invitation-section-heading">
                <strong>Convites enviados</strong>
                <span>{invitations.sent.length}</span>
              </div>

              {invitations.sent.length ? (
                invitations.sent
                  .slice(0, 3)
                  .map((invitation) => (
                    <div
                      className="sent-invitation"
                      key={invitation.id}
                    >
                      <span>
                        {invitation.email ||
                          "Link sem e-mail definido"}
                      </span>

                      <small>
                        Enviado em{" "}
                        {formatDate(invitation.created_at)}
                      </small>
                    </div>
                  ))
              ) : (
                <p className="invitation-empty">
                  Nenhum convite pendente de uso.
                </p>
              )}
            </section>
          </div>
        </section>

        <section className="stat-grid">
          <article className="stat-card">
            <span className="stat-icon">●</span>

            <div>
              <span>Atletas ativos</span>

              <strong>
                {
                  athletes.filter(
                    (athlete) => athlete.active,
                  ).length
                }
              </strong>

              <small>em acompanhamento</small>
            </div>
          </article>

          <article className="stat-card">
            <span className="stat-icon stat-blue">↗</span>

            <div>
              <span>Total de atletas</span>
              <strong>{athletes.length}</strong>
              <small>cadastros na equipe</small>
            </div>
          </article>

          <article className="stat-card">
            <span className="stat-icon stat-amber">✓</span>

            <div>
              <span>Próximo passo</span>
              <strong>Avaliar</strong>
              <small>atualize o VDOT dos atletas</small>
            </div>
          </article>
        </section>

        <section
          id="atletas"
          className="section-heading athletes-section-heading"
        >
          <div>
            <p className="eyebrow">EQUIPE</p>
            <h2>Seus atletas</h2>
          </div>

          <div className="athletes-heading-actions">
            <span>{athletes.length} cadastrados</span>

            <button
              type="button"
              className="btn-primary"
              onClick={() =>
                setShowForm((value) => !value)
              }
            >
              {showForm ? "Cancelar" : "+ Novo atleta"}
            </button>
          </div>
        </section>

        <form
          className="search-row"
          onSubmit={handleSearchSubmit}
        >
          <input
            type="text"
            placeholder="Buscar por nome..."
            value={search}
            onChange={(event) =>
              setSearch(event.target.value)
            }
          />

          <button
            type="submit"
            className="btn-ghost"
          >
            Buscar
          </button>
        </form>

        {showForm && (
          <form
            className="card new-athlete-form"
            onSubmit={handleCreateAthlete}
          >
            <div className="form-grid">
              <label>
                Nome

                <input
                  required
                  value={athleteForm.name}
                  onChange={(event) =>
                    setAthleteForm({
                      ...athleteForm,
                      name: event.target.value,
                    })
                  }
                />
              </label>

              <label>
                Telefone

                <input
                  value={athleteForm.phone}
                  onChange={(event) =>
                    setAthleteForm({
                      ...athleteForm,
                      phone: event.target.value,
                    })
                  }
                />
              </label>

              <label>
                E-mail

                <input
                  type="email"
                  value={athleteForm.email}
                  onChange={(event) =>
                    setAthleteForm({
                      ...athleteForm,
                      email: event.target.value,
                    })
                  }
                />
              </label>

              <label>
                Objetivo

                <input
                  placeholder="Ex: Maratona, 10K..."
                  value={athleteForm.goal}
                  onChange={(event) =>
                    setAthleteForm({
                      ...athleteForm,
                      goal: event.target.value,
                    })
                  }
                />
              </label>
            </div>

            <label className="notes-label">
              Observações

              <textarea
                rows={2}
                value={athleteForm.notes}
                onChange={(event) =>
                  setAthleteForm({
                    ...athleteForm,
                    notes: event.target.value,
                  })
                }
              />
            </label>

            <button
              type="submit"
              className="btn-primary"
            >
              Salvar atleta
            </button>
          </form>
        )}

        {error && (
          <div className="alert">
            {error}
          </div>
        )}

        {loading ? (
          <p className="muted">Carregando...</p>
        ) : athletes.length === 0 ? (
          <div className="empty-state">
            <p>Nenhum atleta cadastrado ainda.</p>

            <p className="muted">
              Use "+ Novo atleta" para começar.
            </p>
          </div>
        ) : (
          <table className="athletes-table">
            <thead>
              <tr>
                <th>Nome</th>
                <th>Contato</th>
                <th>Objetivo</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>

            <tbody>
              {athletes.map((athlete) => (
                <tr key={athlete.id}>
                  <td className="name-cell">
                    <button
                      type="button"
                      className="btn-link athlete-name-link"
                      onClick={() => openProfile(athlete)}
                    >
                      {athlete.name}
                    </button>
                  </td>

                  <td className="muted">
                    {athlete.phone || "Não informado"}
                  </td>

                  <td>
                    {athlete.goal || "—"}
                  </td>

                  <td>
                    <span
                      className={`badge ${
                        athlete.active
                          ? "badge-active"
                          : "badge-inactive"
                      }`}
                    >
                      {athlete.active
                        ? "Ativo"
                        : "Inativo"}
                    </span>
                  </td>

                  <td className="table-actions">
                    <button
                      type="button"
                      className="btn-link"
                      onClick={() =>
                        openIpt(athlete)
                      }
                    >
                      IPT
                    </button>

                    <button
                      type="button"
                      className="btn-link"
                      onClick={() =>
                        openEvaluations(athlete)
                      }
                    >
                      Avaliações
                    </button>

                    <button
                      type="button"
                      className="btn-link"
                      onClick={() =>
                        openTraining(athlete)
                      }
                    >
                      Planejamento
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </main>
      </div>
    </AppShell>
  );
}
