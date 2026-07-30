import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { getStudentTraining } from "../api";
import { studentPaths } from "../router/paths";
import { formatWorkoutSummary } from "../utils/workoutSummary";
import "./StudentAgendaPage.css";


function dateFromKey(value) {
  if (!value) return null;

  const date = new Date(`${value}T12:00:00`);
  return Number.isNaN(date.getTime()) ? null : date;
}


function localDateKey(date = new Date()) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");

  return `${year}-${month}-${day}`;
}


function formatDate(value) {
  const date = dateFromKey(value);

  if (!date) return "Sem data";

  return new Intl.DateTimeFormat("pt-BR", {
    weekday: "short",
    day: "2-digit",
    month: "short",
  }).format(date);
}


function relativeDateLabel(value) {
  const date = dateFromKey(value);

  if (!date) return "";

  const today = dateFromKey(localDateKey());
  const difference = Math.round(
    (date.getTime() - today.getTime()) / 86400000,
  );

  if (difference === 0) return "Hoje";
  if (difference === 1) return "Amanhã";
  if (difference > 1 && difference <= 7) {
    return `Em ${difference} dias`;
  }

  return "";
}


export default function StudentAgendaPage() {
  const navigate = useNavigate();
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
    const today = localDateKey();

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

  const agendaSummary = useMemo(() => {
    const today = localDateKey();
    const sevenDaysLater = new Date();

    sevenDaysLater.setDate(sevenDaysLater.getDate() + 7);

    const sevenDaysKey = localDateKey(sevenDaysLater);
    const todaySessions = sessions.filter(
      (session) => session.session_date === today,
    );
    const nextSevenDays = sessions.filter(
      (session) => session.session_date <= sevenDaysKey,
    );

    return {
      todaySessions,
      nextSevenDays,
      nextSession: sessions[0] || null,
    };
  }, [sessions]);

  return (
    <section className="student-agenda-page">
      <header className="student-agenda-heading">
        <div>
          <p className="eyebrow">AGENDA</p>
          <h2>Seus próximos compromissos</h2>
          <p className="muted">
            Consulte quando cada treino acontecer. Os detalhes
            de execução permanecem em Minha planilha.
          </p>
        </div>

        <button
          type="button"
          className="btn-ghost"
          onClick={() => navigate(studentPaths.trainingPlan)}
        >
          Abrir Minha planilha
        </button>
      </header>

      <section className="student-agenda-overview">
        <article>
          <span>Hoje</span>
          <strong>{agendaSummary.todaySessions.length}</strong>
          <small>
            {agendaSummary.todaySessions.length === 1
              ? "sessão programada"
              : "sessões programadas"}
          </small>
        </article>

        <article>
          <span>Próximos 7 dias</span>
          <strong>{agendaSummary.nextSevenDays.length}</strong>
          <small>compromissos de treino</small>
        </article>

        <article className="student-agenda-next-summary">
          <span>Próxima sessão</span>
          <strong>
            {agendaSummary.nextSession
              ? agendaSummary.nextSession.workout_name
              : "Nenhuma sessão futura"}
          </strong>
          <small>
            {agendaSummary.nextSession
              ? `${formatDate(
                agendaSummary.nextSession.session_date,
              )} · ${formatWorkoutSummary(
                agendaSummary.nextSession,
              )}`
              : "A agenda será atualizada pelo treinador."}
          </small>
        </article>
      </section>

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
                  <div>
                    <strong>Semana {week}</strong>
                    <small>
                      {weekSessions.length} {
                        weekSessions.length === 1
                          ? "sessão"
                          : "sessões"
                      }
                    </small>
                  </div>

                  <span>
                    {weekSessions[0]?.phase || ""}
                  </span>
                </header>

                <div>
                  {weekSessions.map((session) => {
                    const relativeLabel = relativeDateLabel(
                      session.session_date,
                    );

                    return (
                      <article
                        className={
                          relativeLabel === "Hoje"
                            ? "is-today"
                            : ""
                        }
                        key={session.id}
                      >
                        <div className="student-agenda-date">
                          {relativeLabel && (
                            <span>{relativeLabel}</span>
                          )}
                          <strong>
                            {formatDate(
                              session.session_date,
                            )}
                          </strong>
                        </div>

                        <div className="student-agenda-session-main">
                          <h3>{session.workout_name}</h3>
                          <p>
                            {session.zone
                              || "Zona não informada"}
                          </p>
                        </div>

                        <div className="student-agenda-session-meta">
                          <strong>
                            {formatWorkoutSummary(session)}
                          </strong>
                          <button
                            type="button"
                            onClick={() =>
                              navigate(studentPaths.trainingPlan)
                            }
                          >
                            Ver execução
                          </button>
                        </div>
                      </article>
                    );
                  })}
                </div>
              </section>
            ),
          )}
        </div>
      )}
    </section>
  );
}
