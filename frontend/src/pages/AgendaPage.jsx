import { useEffect, useMemo, useState } from "react";

import { getTraining } from "../api";
import "./AgendaPage.css";


function formatDate(value) {
  if (!value) {
    return "Data não informada";
  }

  return new Intl.DateTimeFormat("pt-BR", {
    weekday: "short",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(new Date(`${value}T12:00:00`));
}


function formatSessionDistance(session) {
  const repetitions = Number(session.repetitions || 0);
  const distance = Number(session.planned_distance || 0);

  if (repetitions > 0) {
    return `${repetitions} × ${distance} m`;
  }

  return `${distance.toFixed(1)} km`;
}


export default function AgendaPage({
  athletes,
  onOpenTraining,
}) {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function loadAgenda() {
      setLoading(true);
      setError("");

      try {
        const results = await Promise.allSettled(
          athletes.map(async (athlete) => {
            const training = await getTraining(athlete.id);

            return (training?.sessions || []).map(
              (session) => ({
                ...session,
                athlete,
              }),
            );
          }),
        );

        if (!active) {
          return;
        }

        const loadedSessions = results
          .filter((result) => result.status === "fulfilled")
          .flatMap((result) => result.value)
          .filter((session) => session.session_date)
          .sort((first, second) =>
            first.session_date.localeCompare(
              second.session_date,
            ),
          );

        setSessions(loadedSessions);
      } catch (err) {
        if (active) {
          setError(
            err?.message
            || "Não foi possível carregar a agenda.",
          );
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    loadAgenda();

    return () => {
      active = false;
    };
  }, [athletes]);

  const today = new Date().toISOString().slice(0, 10);

  const upcomingSessions = useMemo(
    () => sessions.filter(
      (session) => session.session_date >= today,
    ),
    [sessions, today],
  );

  const groupedSessions = useMemo(
    () => upcomingSessions.reduce(
      (groups, session) => {
        const date = session.session_date;

        if (!groups[date]) {
          groups[date] = [];
        }

        groups[date].push(session);
        return groups;
      },
      {},
    ),
    [upcomingSessions],
  );

  return (
    <section className="agenda-page">
      <header className="agenda-heading">
        <div>
          <p className="eyebrow">AGENDA</p>
          <h2>Próximos treinos</h2>
          <p className="muted">
            Sessões futuras organizadas por data
            para todos os atletas.
          </p>
        </div>

        <div className="agenda-summary">
          <strong>{upcomingSessions.length}</strong>
          <span>sessões futuras</span>
        </div>
      </header>

      {error && (
        <div className="alert">
          {error}
        </div>
      )}

      {loading ? (
        <p className="muted">
          Carregando agenda...
        </p>
      ) : upcomingSessions.length === 0 ? (
        <section className="agenda-empty">
          <h3>Nenhum treino futuro encontrado</h3>
          <p>
            Gere ou atualize o planejamento
            dos atletas para preencher a agenda.
          </p>
        </section>
      ) : (
        <div className="agenda-days">
          {Object.entries(groupedSessions).map(
            ([date, dateSessions]) => (
              <section
                className="agenda-day"
                key={date}
              >
                <header>
                  <div>
                    <span>{formatDate(date)}</span>
                    <strong>
                      {dateSessions.length} treino(s)
                    </strong>
                  </div>
                </header>

                <div className="agenda-session-list">
                  {dateSessions.map((session) => (
                    <article
                      className="agenda-session"
                      key={`${session.athlete.id}-${session.id}`}
                    >
                      <div className="agenda-session-main">
                        <span className="agenda-athlete-avatar">
                          {session.athlete.name
                            .split(" ")
                            .filter(Boolean)
                            .slice(0, 2)
                            .map((part) => part[0])
                            .join("")
                            .toUpperCase()}
                        </span>

                        <div>
                          <strong>
                            {session.athlete.name}
                          </strong>
                          <h3>
                            {session.workout_name}
                          </h3>
                          <p>
                            {session.phase}
                            {session.zone
                              ? ` · ${session.zone}`
                              : ""}
                          </p>
                        </div>
                      </div>

                      <div className="agenda-session-meta">
                        <span>
                          {formatSessionDistance(session)}
                        </span>

                        <button
                          type="button"
                          className="btn-ghost"
                          onClick={() =>
                            onOpenTraining(
                              session.athlete,
                            )
                          }
                        >
                          Abrir planejamento
                        </button>
                      </div>
                    </article>
                  ))}
                </div>
              </section>
            ),
          )}
        </div>
      )}
    </section>
  );
}
