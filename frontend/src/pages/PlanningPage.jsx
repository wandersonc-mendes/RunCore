import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";

import {
  getTraining,
  updateTrainingSession,
} from "../api";
import { formatWorkoutSummary } from "../utils/workoutSummary";

import "./PlanningPage.css";


const WEEKDAYS = [
  "Seg",
  "Ter",
  "Qua",
  "Qui",
  "Sex",
  "Sáb",
  "Dom",
];


function startOfWeek(date) {
  const result = new Date(date);
  const weekday = result.getDay();
  const offset = weekday === 0 ? -6 : 1 - weekday;

  result.setDate(result.getDate() + offset);
  result.setHours(0, 0, 0, 0);

  return result;
}


function addDays(date, amount) {
  const result = new Date(date);
  result.setDate(result.getDate() + amount);
  return result;
}


function dateKey(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");

  return `${year}-${month}-${day}`;
}


function formatDay(date) {
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "2-digit",
  }).format(date);
}


function formatWeekRange(days) {
  const first = days[0];
  const last = days[6];

  const start = new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "short",
  }).format(first);

  const end = new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(last);

  return `${start} - ${end}`;
}


function sessionWeekdayIndex(session) {
  const configuredWeekday = Number(session?.weekday);

  if (
    Number.isInteger(configuredWeekday)
    && configuredWeekday >= 0
    && configuredWeekday <= 6
  ) {
    return configuredWeekday;
  }

  if (!session?.session_date) {
    return null;
  }

  const nativeWeekday = new Date(
    `${session.session_date}T12:00:00`,
  ).getDay();

  return nativeWeekday === 0
    ? 6
    : nativeWeekday - 1;
}


function initials(name = "") {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("") || "RC";
}


function sessionTone(session) {
  const value = [
    session?.workout_name,
    session?.zone,
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();

  if (
    value.includes("long")
    || value.includes("longo")
    || value.includes("longão")
  ) {
    return "long";
  }

  if (
    value.includes("interval")
    || value.includes("tiro")
    || value.includes("repetition")
  ) {
    return "interval";
  }

  if (
    value.includes("tempo")
    || value.includes("limiar")
    || value.includes("threshold")
  ) {
    return "tempo";
  }

  if (value.includes("progress")) {
    return "progressive";
  }

  if (
    value.includes("regener")
    || value.includes("recuper")
  ) {
    return "recovery";
  }

  return "easy";
}


function stepPayload(step) {
  return {
    type: step.type || "Corrida",
    prescription_type: step.prescription_type || "distance",
    intensity_type: step.intensity_type || "pace",
    distance: Number(step.distance || 0),
    distance_unit: step.distance_unit || "km",
    duration: Number(step.duration || 0),
    repetitions: Number(step.repetitions || 0),
    recovery: step.recovery || "",
    pace_min: step.pace_min || "",
    pace_max: step.pace_max || "",
    heart_rate_min: step.heart_rate_min || null,
    heart_rate_max: step.heart_rate_max || null,
    rpe_min: step.rpe_min || null,
    rpe_max: step.rpe_max || null,
    notes: step.notes || "",
  };
}


function sessionPayload(session, sessionDate) {
  return {
    session_date: sessionDate,
    workout_name: session.workout_name,
    zone: session.zone || "Easy",
    planned_distance: Number(session.planned_distance || 0),
    repetitions: Number(session.repetitions || 0),
    objective: session.objective || "",
    notes: session.notes || "",
    steps: (session.steps || []).map(stepPayload),
  };
}


export default function PlanningPage({
  athletes,
  loading,
  error,
  onOpenPlanning,
}) {
  const [searchParams, setSearchParams] = useSearchParams();

  const requestedAthleteId = searchParams.get("atleta") || "all";
  const requestedView = (
    searchParams.get("visao") === "macrociclo"
      ? "macrociclo"
      : "semana"
  );

  const [weekStart, setWeekStart] = useState(
    () => startOfWeek(new Date()),
  );
  const [records, setRecords] = useState([]);
  const [loadingTrainings, setLoadingTrainings] = useState(true);
  const [athleteFilter, setAthleteFilter] = useState(
    requestedAthleteId,
  );
  const [planningView, setPlanningView] = useState(
    requestedView,
  );
  const [goalFilter, setGoalFilter] = useState("all");
  const [draggingSessionId, setDraggingSessionId] = useState(null);
  const [dropTarget, setDropTarget] = useState("");
  const [movingSessionId, setMovingSessionId] = useState(null);
  const [moveError, setMoveError] = useState("");

  useEffect(() => {
    setAthleteFilter(requestedAthleteId);
    setPlanningView(requestedView);
  }, [requestedAthleteId, requestedView]);

  useEffect(() => {
    let active = true;

    async function loadTrainings() {
      setLoadingTrainings(true);

      const results = await Promise.allSettled(
        athletes.map(async (athlete) => ({
          athlete,
          training: await getTraining(athlete.id),
        })),
      );

      if (!active) {
        return;
      }

      setRecords(
        results
          .filter((result) => result.status === "fulfilled")
          .map((result) => result.value),
      );

      setLoadingTrainings(false);
    }

    loadTrainings();

    return () => {
      active = false;
    };
  }, [athletes]);

  const weekDays = useMemo(
    () => Array.from(
      { length: 7 },
      (_, index) => addDays(weekStart, index),
    ),
    [weekStart],
  );

  const goals = useMemo(
    () => Array.from(
      new Set(
        athletes
          .map((athlete) => athlete.goal?.trim())
          .filter(Boolean),
      ),
    ).sort((first, second) =>
      first.localeCompare(second, "pt-BR"),
    ),
    [athletes],
  );

  const visibleRecords = useMemo(
    () => records.filter(({ athlete }) => {
      const matchesAthlete =
        athleteFilter === "all"
        || String(athlete.id) === athleteFilter;

      const matchesGoal =
        goalFilter === "all"
        || athlete.goal === goalFilter;

      return athlete.active && matchesAthlete && matchesGoal;
    }),
    [
      athleteFilter,
      goalFilter,
      records,
    ],
  );

  const sessionsByAthleteAndDate = useMemo(() => {
    const result = new Map();

    visibleRecords.forEach(({ athlete, training }) => {
      const byDate = new Map();

      (training?.sessions || []).forEach((session) => {
        if (!session.session_date) {
          return;
        }

        const sessions = byDate.get(session.session_date) || [];
        sessions.push(session);
        byDate.set(session.session_date, sessions);
      });

      result.set(athlete.id, byDate);
    });

    return result;
  }, [visibleRecords]);

  const macrocycleRecord = (
    athleteFilter !== "all"
      ? visibleRecords[0] || null
      : null
  );

  const macrocycleWeeks = useMemo(() => {
    const training = macrocycleRecord?.training;

    if (!training) {
      return [];
    }

    const sessions = training.sessions || [];
    const configuredWeeks = Math.max(
      0,
      Number(training.total_weeks || 0),
    );

    let dateBasedWeeks = 0;

    if (training.start_date && training.target_date) {
      const start = new Date(
        `${training.start_date}T00:00:00`,
      );
      const target = new Date(
        `${training.target_date}T00:00:00`,
      );

      if (
        !Number.isNaN(start.getTime())
        && !Number.isNaN(target.getTime())
        && target >= start
      ) {
        const dayMs = 24 * 60 * 60 * 1000;
        const inclusiveDays = Math.floor(
          (target.getTime() - start.getTime()) / dayMs,
        ) + 1;

        dateBasedWeeks = Math.max(
          1,
          Math.ceil(inclusiveDays / 7),
        );
      }
    }

    const sessionWeeks = sessions.reduce(
      (highestWeek, session) =>
        Math.max(
          highestWeek,
          Number(session.week || 0),
        ),
      0,
    );

    const totalWeeks = Math.max(
      configuredWeeks,
      dateBasedWeeks,
      sessionWeeks,
    );

    if (totalWeeks < 1) {
      return [];
    }

    const grouped = new Map(
      Array.from(
        { length: totalWeeks },
        (_, index) => [index + 1, []],
      ),
    );

    sessions.forEach((session) => {
      const weekNumber = Number(session.week || 0);

      if (weekNumber < 1) {
        return;
      }

      if (!grouped.has(weekNumber)) {
        grouped.set(weekNumber, []);
      }

      grouped.get(weekNumber).push(session);
    });

    return Array.from(grouped.entries())
      .sort(([first], [second]) => first - second)
      .map(([week, weekSessions]) => ({
        week,
        sessions: [...weekSessions].sort(
          (first, second) =>
            String(first.session_date || "").localeCompare(
              String(second.session_date || ""),
            ),
        ),
      }));
  }, [macrocycleRecord]);

  function changePlanningView(nextView) {
    setPlanningView(nextView);

    const nextParams = new URLSearchParams(searchParams);
    nextParams.set("visao", nextView);

    if (athleteFilter !== "all") {
      nextParams.set("atleta", athleteFilter);
    } else {
      nextParams.delete("atleta");
    }

    setSearchParams(nextParams, { replace: true });
  }

  function changeAthleteFilter(nextAthleteId) {
    setAthleteFilter(nextAthleteId);

    const nextParams = new URLSearchParams(searchParams);

    if (nextAthleteId === "all") {
      nextParams.delete("atleta");

      if (planningView === "macrociclo") {
        setPlanningView("semana");
        nextParams.set("visao", "semana");
      }
    } else {
      nextParams.set("atleta", nextAthleteId);
    }

    setSearchParams(nextParams, { replace: true });
  }

  function updateSessionDateLocally(
    athleteId,
    sessionId,
    nextDate,
  ) {
    setRecords((current) =>
      current.map((record) => {
        if (record.athlete.id !== athleteId) {
          return record;
        }

        return {
          ...record,
          training: {
            ...record.training,
            sessions: (record.training?.sessions || []).map(
              (session) =>
                session.id === sessionId
                  ? {
                      ...session,
                      session_date: nextDate,
                      weekday: new Date(
                        `${nextDate}T12:00:00`,
                      ).getDay() === 0
                        ? 6
                        : new Date(
                            `${nextDate}T12:00:00`,
                          ).getDay() - 1,
                    }
                  : session,
            ),
          },
        };
      }),
    );
  }

  async function moveSession(
    athlete,
    session,
    nextDate,
  ) {
    if (
      movingSessionId
      || !session
      || session.session_date === nextDate
    ) {
      return;
    }

    const previousDate = session.session_date;

    setMoveError("");
    setMovingSessionId(session.id);
    updateSessionDateLocally(
      athlete.id,
      session.id,
      nextDate,
    );

    try {
      await updateTrainingSession(
        athlete.id,
        session.id,
        sessionPayload(session, nextDate),
      );
    } catch (moveFailure) {
      updateSessionDateLocally(
        athlete.id,
        session.id,
        previousDate,
      );
      setMoveError(
        moveFailure.message
        || "Não foi possível mover o treino.",
      );
    } finally {
      setMovingSessionId(null);
      setDraggingSessionId(null);
      setDropTarget("");
    }
  }

  const isLoading = loading || loadingTrainings;

  return (
    <section className="planning-page planning-week-page">
      <header className="planning-week-header">
        <div>
          <p className="eyebrow">PLANEJAMENTO</p>
          <h2>
            {planningView === "macrociclo"
              ? "Macrociclo completo"
              : "Planejamento semanal"}
          </h2>
          <p className="muted">
            {planningView === "macrociclo"
              ? (
                "Visualize todas as semanas e sessões "
                + "do ciclo do atleta."
              )
              : (
                "Arraste um treino para outro dia para "
                + "reorganizar a semana do atleta."
              )}
          </p>
        </div>

        <div className="planning-week-counter">
          <strong>{visibleRecords.length}</strong>
          <span>atletas exibidos</span>
        </div>
      </header>

      {(error || moveError) && (
        <div className="alert">
          {moveError || error}
        </div>
      )}

      <section className="planning-view-switcher">
        <button
          type="button"
          className={planningView === "semana" ? "active" : ""}
          onClick={() => changePlanningView("semana")}
        >
          Semana
        </button>

        <button
          type="button"
          className={planningView === "macrociclo" ? "active" : ""}
          disabled={athleteFilter === "all"}
          title={
            athleteFilter === "all"
              ? "Selecione um atleta para visualizar o macrociclo."
              : ""
          }
          onClick={() => changePlanningView("macrociclo")}
        >
          Macrociclo
        </button>
      </section>

      <section className="planning-week-toolbar">
        {planningView === "semana" && (
          <div className="week-navigation">
          <button
            type="button"
            aria-label="Semana anterior"
            onClick={() =>
              setWeekStart((current) => addDays(current, -7))
            }
          >
            ‹
          </button>

          <button
            type="button"
            className="today-button"
            onClick={() =>
              setWeekStart(startOfWeek(new Date()))
            }
          >
            Hoje
          </button>

          <button
            type="button"
            aria-label="Próxima semana"
            onClick={() =>
              setWeekStart((current) => addDays(current, 7))
            }
          >
            ›
          </button>

          <strong>{formatWeekRange(weekDays)}</strong>
          </div>
        )}

        <div className="planning-week-filters">
          <label>
            <span>Objetivo</span>
            <select
              value={goalFilter}
              onChange={(event) =>
                setGoalFilter(event.target.value)
              }
            >
              <option value="all">Todos</option>
              {goals.map((goal) => (
                <option value={goal} key={goal}>
                  {goal}
                </option>
              ))}
            </select>
          </label>

          <label>
            <span>Atleta</span>
            <select
              value={athleteFilter}
              onChange={(event) =>
                changeAthleteFilter(
                  event.target.value,
                )
              }
            >
              <option value="all">Todos</option>
              {athletes
                .filter((athlete) => athlete.active)
                .map((athlete) => (
                  <option
                    key={athlete.id}
                    value={athlete.id}
                  >
                    {athlete.name}
                  </option>
                ))}
            </select>
          </label>
        </div>
      </section>

      {isLoading ? (
        <section className="planning-empty">
          <h3>Carregando planejamento</h3>
          <p>Buscando os planejamentos dos atletas.</p>
        </section>
      ) : visibleRecords.length === 0 ? (
        <section className="planning-empty">
          <h3>Nenhum atleta encontrado</h3>
          <p>
            Ajuste os filtros para visualizar
            outros planejamentos.
          </p>
        </section>
      ) : planningView === "macrociclo" ? (
        athleteFilter === "all" ? (
          <section className="planning-empty">
            <h3>Selecione um atleta</h3>
            <p>
              O macrociclo completo é exibido
              individualmente por atleta.
            </p>
          </section>
        ) : macrocycleWeeks.length === 0 ? (
          <section className="planning-empty">
            <h3>Macrociclo sem sessões</h3>
            <p>
              Este atleta ainda não possui treinos
              distribuídos no ciclo.
            </p>
          </section>
        ) : (
          <section className="planning-macrocycle">
            <header className="planning-macrocycle-summary">
              <div>
                <span className="planning-avatar">
                  {initials(macrocycleRecord.athlete.name)}
                </span>
                <div>
                  <strong>{macrocycleRecord.athlete.name}</strong>
                  <small>
                    {macrocycleRecord.training?.objective
                      || macrocycleRecord.athlete.goal
                      || "Sem objetivo"}
                  </small>
                </div>
              </div>

              <div>
                <strong>{macrocycleWeeks.length}</strong>
                <span>semanas no ciclo</span>
              </div>
            </header>

            <div className="planning-macrocycle-weeks">
              {macrocycleWeeks.map(({ week, sessions }) => (
                <article
                  className="planning-macro-week"
                  key={week}
                >
                  <header>
                    <div>
                      <span>SEMANA</span>
                      <strong>{week || "—"}</strong>
                    </div>
                    <small>
                      {sessions.length} {
                        sessions.length === 1
                          ? "sessão"
                          : "sessões"
                      }
                    </small>
                  </header>

                  <div className="planning-macro-days">
                    {WEEKDAYS.map((weekday, weekdayIndex) => {
                      const daySessions = sessions.filter(
                        (session) =>
                          sessionWeekdayIndex(session)
                          === weekdayIndex,
                      );

                      return (
                        <div
                          className="planning-macro-day"
                          key={`${week}-${weekday}`}
                        >
                          <span>{weekday}</span>

                          {daySessions.length === 0 ? (
                            <small className="planning-macro-rest">
                              Livre
                            </small>
                          ) : (
                            daySessions.map((session) => (
                              <button
                                type="button"
                                className={
                                  `planning-session-card ${sessionTone(session)}`
                                }
                                key={session.id}
                                onClick={() =>
                                  onOpenPlanning(
                                    macrocycleRecord.athlete,
                                    session,
                                  )
                                }
                              >
                                <strong>
                                  {session.workout_name}
                                </strong>
                                <span>
                                  {formatWorkoutSummary(session)}
                                </span>
                                <small>
                                  {session.session_date
                                    ? formatDay(
                                        new Date(
                                          `${session.session_date}T12:00:00`,
                                        ),
                                      )
                                    : (
                                      session.zone || "Treino"
                                    )}
                                </small>
                              </button>
                            ))
                          )}
                        </div>
                      );
                    })}
                  </div>
                </article>
              ))}
            </div>
          </section>
        )
      ) : (
        <div className="planning-week-scroll">
          <div className="planning-week-grid">
            <div className="planning-grid-corner">
              Atleta
            </div>

            {weekDays.map((day, index) => (
              <div
                className="planning-day-heading"
                key={dateKey(day)}
              >
                <strong>{WEEKDAYS[index]}</strong>
                <span>{formatDay(day)}</span>
              </div>
            ))}

            {visibleRecords.map(({ athlete, training }) => {
              const athleteSessions =
                sessionsByAthleteAndDate.get(athlete.id)
                || new Map();

              return [
                <button
                  type="button"
                  className="planning-athlete-cell"
                  key={`athlete-${athlete.id}`}
                  onClick={() => onOpenPlanning(athlete)}
                >
                  <span className="planning-avatar">
                    {initials(athlete.name)}
                  </span>

                  <span>
                    <strong>{athlete.name}</strong>
                    <small>
                      {training?.objective
                        || athlete.goal
                        || "Sem objetivo"}
                    </small>
                  </span>
                </button>,

                ...weekDays.map((day) => {
                  const key = dateKey(day);
                  const sessions = athleteSessions.get(key) || [];
                  const targetKey = `${athlete.id}-${key}`;
                  const isTarget = dropTarget === targetKey;

                  return (
                    <div
                      className={
                        `planning-session-cell planning-drop-cell ${
                          sessions.length ? "has-sessions" : "empty"
                        } ${isTarget ? "drop-target" : ""}`
                      }
                      key={targetKey}
                      onDragOver={(event) => {
                        event.preventDefault();
                        event.dataTransfer.dropEffect = "move";
                        setDropTarget(targetKey);
                      }}
                      onDragLeave={(event) => {
                        if (
                          !event.currentTarget.contains(
                            event.relatedTarget,
                          )
                        ) {
                          setDropTarget("");
                        }
                      }}
                      onDrop={(event) => {
                        event.preventDefault();

                        const sessionId = Number(
                          event.dataTransfer.getData(
                            "application/x-runcore-session",
                          ) || draggingSessionId,
                        );

                        const session = (
                          training?.sessions || []
                        ).find(
                          (item) => item.id === sessionId,
                        );

                        moveSession(
                          athlete,
                          session,
                          key,
                        );
                      }}
                    >
                      {sessions.map((session) => (
                        <button
                          type="button"
                          draggable={!movingSessionId}
                          className={
                            `planning-session-card ${sessionTone(session)} ${
                              draggingSessionId === session.id
                                ? "is-dragging"
                                : ""
                            } ${
                              movingSessionId === session.id
                                ? "is-saving"
                                : ""
                            }`
                          }
                          key={session.id}
                          onDragStart={(event) => {
                            setDraggingSessionId(session.id);
                            event.dataTransfer.effectAllowed = "move";
                            event.dataTransfer.setData(
                              "application/x-runcore-session",
                              String(session.id),
                            );
                            event.dataTransfer.setData(
                              "text/plain",
                              String(session.id),
                            );
                          }}
                          onDragEnd={() => {
                            setDraggingSessionId(null);
                            setDropTarget("");
                          }}
                          onClick={() => {
                            if (!draggingSessionId) {
                              onOpenPlanning(
                                athlete,
                                session,
                              );
                            }
                          }}
                        >
                          <strong>{session.workout_name}</strong>
                          <span>{formatWorkoutSummary(session)}</span>
                          <small>{session.zone || "Treino"}</small>
                        </button>
                      ))}

                      <button
                        type="button"
                        className="planning-add-session"
                        onClick={() =>
                          onOpenPlanning(athlete, null)
                        }
                      >
                        <span className="empty-plus">＋</span>
                        <small>Adicionar</small>
                      </button>
                    </div>
                  );
                }),
              ];
            })}
          </div>
        </div>
      )}

      {planningView === "semana" && (
        <footer className="planning-week-legend">
          <span><b className="easy" />Fácil</span>
          <span><b className="interval" />Intervalado</span>
          <span><b className="tempo" />Tempo/Limiar</span>
          <span><b className="long" />Longo</span>
          <span><b className="recovery" />Regenerativo</span>
          <span><b className="progressive" />Progressivo</span>
        </footer>
      )}
    </section>
  );
}
