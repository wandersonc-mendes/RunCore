import { useEffect, useMemo, useState } from "react";

import { getStudentTraining } from "../api";
import "./StudentAgendaPage.css";


function formatDate(value) {
  if (!value) return "Sem data";

  return new Intl.DateTimeFormat("pt-BR", {
    weekday: "short",
    day: "2-digit",
    month: "2-digit",
  }).format(new Date(`${value}T12:00:00`));
}


export default function StudentAgendaPage() {
  const [training, setTraining] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function loadTraining() {
      setLoading(true);
      setError("");

      try {
        const result = await getStudentTraining();

        if (active) {
          setTraining(result);
        }
      } catch (err) {
        if (active) {
          setError(
            err?.message
            || "Não foi possível carregar sua agenda.",
          );
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    loadTraining();

    return () => {
      active = false;
    };
  }, []);

  const sessions = useMemo(() => {
    const today = new Date().toISOString().slice(0, 10);

    return (training?.sessions || [])
      .filter(
        (session) =>
          session.session_date
          && session.session_date >= today,
      )
      .sort((first, second) =>
        first.session_date.localeCompare(
          second.session_date,
        ),
      );
  }, [training]);

  const grouped = useMemo(
    () => sessions.reduce((result, session) => {
      const week = session.week || 1;

      if (!result[week]) {
        result[week] = [];
      }

      result[week].push(session);
      return result;
    }, {}),
    [sessions],
  );

  return (
    <section className="student-agenda-page">
      <header className="student-agenda-heading">
        <div>
          <p className="eyebrow">AGENDA</p>
          <h2>Agenda do atleta</h2>
          <p className="muted">
            Seus próximos treinos organizados
            por semana e data.
          </p>
        </div>

        <div className="student-agenda-summary">
          <strong>{sessions.length}</strong>
          <span>sessões futuras</span>
        </div>
      </header>

      {error && <div className="alert">{error}</div>}

      {loading ? (
        <p className="muted">
          Carregando agenda...
        </p>
      ) : sessions.length === 0 ? (
        <section className="student-agenda-empty">
          <h3>Nenhum treino futuro encontrado</h3>
          <p>
            Sua agenda será preenchida quando o treinador
            publicar ou atualizar o planejamento.
          </p>
        </section>
      ) : (
        <div className="student-agenda-weeks">
          {Object.entries(grouped).map(
            ([week, weekSessions]) => (
              <section
                className="student-agenda-week"
                key={week}
              >
                <header>
                  <strong>Semana {week}</strong>
                  <span>
                    {weekSessions[0]?.phase || ""}
                  </span>
                </header>

                <div>
                  {weekSessions.map((session) => (
                    <article key={session.id}>
                      <div className="student-agenda-date">
                        <strong>
                          {formatDate(
                            session.session_date,
                          )}
                        </strong>
                      </div>

                      <div className="student-agenda-session-main">
                        <h3>{session.workout_name}</h3>
                        <p>
                          {session.zone || "Zona não informada"}
                        </p>
                      </div>

                      <span className="student-agenda-distance">
                        {Number(
                          session.planned_distance || 0,
                        ).toFixed(1)} km
                      </span>
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
