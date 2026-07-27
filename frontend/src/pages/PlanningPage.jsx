import { useEffect, useMemo, useState } from "react";

import {
  getTraining,
} from "../api";

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


function formatDistance(session) {
  const repetitions = Number(session?.repetitions || 0);
  const distance = Number(session?.planned_distance || 0);

  if (repetitions > 0) {
    return `${repetitions} × ${distance} m`;
  }

  return `${distance.toFixed(1)} km`;
}


export default function PlanningPage({
  athletes,
  loading,
  error,
  onOpenPlanning,
}) {
  const [weekStart, setWeekStart] = useState(
    () => startOfWeek(new Date()),
  );
  const [records, setRecords] = useState([]);
  const [loadingTrainings, setLoadingTrainings] = useState(true);
  const [athleteFilter, setAthleteFilter] = useState("all");
  const [goalFilter, setGoalFilter] = useState("all");

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
        if (session.session_date) {
          byDate.set(session.session_date, session);
        }
      });

      result.set(athlete.id, byDate);
    });

    return result;
  }, [visibleRecords]);

  const isLoading = loading || loadingTrainings;

  return (
    <section className="planning-page planning-week-page">
      <header className="planning-week-header">
        <div>
          <p className="eyebrow">PLANEJAMENTO</p>
          <h2>Planejamento semanal</h2>
          <p className="muted">
            Visualize os treinos de todos os atletas
            em uma única semana.
          </p>
        </div>

        <div className="planning-week-counter">
          <strong>{visibleRecords.length}</strong>
          <span>atletas exibidos</span>
        </div>
      </header>

      {error && (
        <div className="alert">
          {error}
        </div>
      )}

      <section className="planning-week-toolbar">
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
                setAthleteFilter(event.target.value)
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
          <h3>Carregando semana</h3>
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
                  const session = athleteSessions.get(key);

                  return (
                    <button
                      type="button"
                      className={
                        session
                          ? `planning-session-cell ${sessionTone(session)}`
                          : "planning-session-cell empty"
                      }
                      key={`${athlete.id}-${key}`}
                      onClick={() => onOpenPlanning(athlete)}
                    >
                      {session ? (
                        <>
                          <strong>{session.workout_name}</strong>
                          <span>{formatDistance(session)}</span>
                          <small>{session.zone || "Treino"}</small>
                        </>
                      ) : (
                        <>
                          <span className="empty-plus">＋</span>
                          <small>Adicionar</small>
                        </>
                      )}
                    </button>
                  );
                }),
              ];
            })}
          </div>
        </div>
      )}

      <footer className="planning-week-legend">
        <span><b className="easy" />Fácil</span>
        <span><b className="interval" />Intervalado</span>
        <span><b className="tempo" />Tempo/Limiar</span>
        <span><b className="long" />Longo</span>
        <span><b className="recovery" />Regenerativo</span>
        <span><b className="progressive" />Progressivo</span>
      </footer>
    </section>
  );
}
