import { useEffect, useMemo, useState } from "react";

import {
  getTraining,
  listEvaluations,
} from "../api";

import "./CoachDashboardPage.css";


const WEEKDAYS = [
  "Seg",
  "Ter",
  "Qua",
  "Qui",
  "Sex",
  "Sáb",
  "Dom",
];


function initials(name = "") {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("") || "RC";
}


function dateKey(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");

  return `${year}-${month}-${day}`;
}


function startOfWeek(date) {
  const result = new Date(date);
  const weekday = result.getDay();
  const offset = weekday === 0 ? -6 : 1 - weekday;

  result.setDate(result.getDate() + offset);
  result.setHours(0, 0, 0, 0);

  return result;
}


function endOfWeek(date) {
  const result = startOfWeek(date);
  result.setDate(result.getDate() + 6);
  result.setHours(23, 59, 59, 999);

  return result;
}


function formatToday() {
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  }).format(new Date());
}


function formatSessionDistance(session) {
  const repetitions = Number(
    session.repetitions || 0,
  );

  const distance = Number(
    session.planned_distance || 0,
  );

  if (repetitions > 0) {
    return `${repetitions} × ${distance} m`;
  }

  return `${distance.toFixed(1)} km`;
}


export default function CoachDashboardPage({
  user,
  athletes,
  invitations,
  inviteEmail,
  setInviteEmail,
  inviteLink,
  onCreateInvitation,
  onApproveInvitation,
  onOpenProfile,
  onOpenTraining,
  onOpenEvaluations,
}) {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function loadDashboard() {
      setLoading(true);
      setError("");

      try {
        const results = await Promise.allSettled(
          athletes.map(async (athlete) => {
            const [training, evaluations] = await Promise.all([
              getTraining(athlete.id),
              listEvaluations(athlete.id),
            ]);

            return {
              athlete,
              training,
              evaluations: evaluations || [],
            };
          }),
        );

        if (!active) return;

        setRecords(
          results
            .filter((result) => result.status === "fulfilled")
            .map((result) => result.value),
        );
      } catch (err) {
        if (active) {
          setError(
            err?.message
            || "Não foi possível carregar o dashboard.",
          );
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    loadDashboard();

    return () => {
      active = false;
    };
  }, [athletes]);

  const dashboard = useMemo(() => {
    const now = new Date();
    const today = dateKey(now);
    const weekStart = startOfWeek(now);
    const weekEnd = endOfWeek(now);

    const sessions = records.flatMap(
      ({ athlete, training }) =>
        (training?.sessions || []).map((session) => ({
          ...session,
          athlete,
        })),
    );

    const weekSessions = sessions.filter((session) => {
      if (!session.session_date) return false;

      const date = new Date(`${session.session_date}T12:00:00`);
      return date >= weekStart && date <= weekEnd;
    });

    const todaySessions = sessions
      .filter((session) => session.session_date === today)
      .sort((first, second) =>
        first.athlete.name.localeCompare(
          second.athlete.name,
          "pt-BR",
        ),
      );

    const weeklyTotals = Array.from({ length: 7 }, () => 0);

    weekSessions.forEach((session) => {
      const date = new Date(`${session.session_date}T12:00:00`);
      const day = date.getDay();
      const index = day === 0 ? 6 : day - 1;
      weeklyTotals[index] += 1;
    });

    const pendingEvaluations = records.filter(
      ({ athlete, evaluations }) =>
        athlete.active && evaluations.length === 0,
    );

    return {
      activeAthletes: athletes.filter(
        (athlete) => athlete.active,
      ).length,
      weekSessions,
      todaySessions,
      weeklyTotals,
      pendingEvaluations,
    };
  }, [athletes, records]);

  const maxWeekly = Math.max(...dashboard.weeklyTotals, 1);

  return (
    <section className="coach-dashboard-page">
      <header className="coach-dashboard-welcome">
        <div>
          <h2>Olá, {user?.name?.split(" ")[0] || "Treinador"}</h2>
          <p>
            Bem-vindo ao seu painel. Veja o resumo operacional
            da sua assessoria.
          </p>
        </div>

        <div className="coach-dashboard-date">
          <span aria-hidden="true">▣</span>
          <strong>{formatToday()}</strong>
        </div>
      </header>

      {error && <div className="alert">{error}</div>}

      <section className="coach-dashboard-metrics">
        <article>
          <div>
            <span>Atletas ativos</span>
            <strong>{dashboard.activeAthletes}</strong>
            <small>{athletes.length} cadastrados</small>
          </div>
          <b aria-hidden="true">♙</b>
        </article>

        <article>
          <div>
            <span>Treinos esta semana</span>
            <strong>{dashboard.weekSessions.length}</strong>
            <small>sessões programadas</small>
          </div>
          <b aria-hidden="true">↗</b>
        </article>

        <article>
          <div>
            <span>Avaliações pendentes</span>
            <strong>
              {dashboard.pendingEvaluations.length}
            </strong>
            <small>atletas sem avaliação</small>
          </div>
          <b aria-hidden="true">✓</b>
        </article>

        <article>
          <div>
            <span>Convites pendentes</span>
            <strong>{invitations.pending.length}</strong>
            <small>aguardando aprovação</small>
          </div>
          <b aria-hidden="true">⚑</b>
        </article>
      </section>

      <section className="coach-dashboard-main-grid">
        <article className="coach-dashboard-card today-card">
          <header>
            <div>
              <h3>Próximos treinos de hoje</h3>
              <p>{dashboard.todaySessions.length} sessão(ões)</p>
            </div>
          </header>

          {loading ? (
            <p className="coach-dashboard-empty">
              Carregando treinos...
            </p>
          ) : dashboard.todaySessions.length === 0 ? (
            <p className="coach-dashboard-empty">
              Nenhum treino programado para hoje.
            </p>
          ) : (
            <div className="today-training-list">
              {dashboard.todaySessions
                .slice(0, 6)
                .map((session) => (
                  <button
                    type="button"
                    key={`${session.athlete.id}-${session.id}`}
                    onClick={() =>
                      onOpenTraining(session.athlete)
                    }
                  >
                    <span className="dashboard-athlete-avatar">
                      {initials(session.athlete.name)}
                    </span>

                    <span className="today-training-main">
                      <strong>{session.athlete.name}</strong>
                      <small>
                        {session.workout_name}
                        {" · "}
                        {formatSessionDistance(session)}
                      </small>
                    </span>

                    <span className="today-training-zone">
                      {session.zone || "Treino"}
                    </span>

                    <span aria-hidden="true">›</span>
                  </button>
                ))}
            </div>
          )}
        </article>

        <article className="coach-dashboard-card weekly-card">
          <header>
            <div>
              <h3>Resumo semanal</h3>
              <p>Quantidade de sessões por dia</p>
            </div>
          </header>

          <div className="weekly-chart">
            {dashboard.weeklyTotals.map((total, index) => (
              <div className="weekly-chart-column" key={WEEKDAYS[index]}>
                <div className="weekly-chart-value">
                  <span>{total}</span>
                  <b
                    style={{
                      height: `${Math.max(
                        total ? 20 : 3,
                        (total / maxWeekly) * 100,
                      )}%`,
                    }}
                  />
                </div>
                <small>{WEEKDAYS[index]}</small>
              </div>
            ))}
          </div>
        </article>
      </section>

      <section className="coach-dashboard-secondary-grid">
        <article className="coach-dashboard-card pending-card">
          <header>
            <div>
              <h3>Avaliações pendentes</h3>
              <p>Atletas ativos ainda sem registro</p>
            </div>

            <button
              type="button"
              className="dashboard-link-button"
              onClick={() => {
                const first =
                  dashboard.pendingEvaluations[0]?.athlete;

                if (first) onOpenEvaluations(first);
              }}
              disabled={
                dashboard.pendingEvaluations.length === 0
              }
            >
              Abrir
            </button>
          </header>

          {dashboard.pendingEvaluations.length === 0 ? (
            <p className="coach-dashboard-empty">
              Todos os atletas ativos possuem avaliação.
            </p>
          ) : (
            <div className="pending-athlete-list">
              {dashboard.pendingEvaluations
                .slice(0, 4)
                .map(({ athlete }) => (
                  <button
                    type="button"
                    key={athlete.id}
                    onClick={() =>
                      onOpenEvaluations(athlete)
                    }
                  >
                    <span className="dashboard-athlete-avatar">
                      {initials(athlete.name)}
                    </span>
                    <span>
                      <strong>{athlete.name}</strong>
                      <small>
                        {athlete.goal
                          || "Sem objetivo informado"}
                      </small>
                    </span>
                    <b>+</b>
                  </button>
                ))}
            </div>
          )}
        </article>

        <article className="coach-dashboard-card invitations-compact">
          <header>
            <div>
              <h3>Convites e aprovações</h3>
              <p>Cadastre novos atletas por convite</p>
            </div>
          </header>

          <form onSubmit={onCreateInvitation}>
            <input
              type="email"
              value={inviteEmail}
              onChange={(event) =>
                setInviteEmail(event.target.value)
              }
              placeholder="E-mail do aluno (opcional)"
            />
            <button className="btn-primary">
              Gerar convite
            </button>
          </form>

          {inviteLink && (
            <div className="dashboard-invite-link">
              <input
                readOnly
                value={inviteLink}
                onFocus={(event) =>
                  event.target.select()
                }
              />
              <button
                type="button"
                className="btn-ghost"
                onClick={() =>
                  navigator.clipboard?.writeText(
                    inviteLink,
                  )
                }
              >
                Copiar
              </button>
            </div>
          )}

          <div className="dashboard-pending-invitations">
            {invitations.pending.length === 0 ? (
              <p className="coach-dashboard-empty">
                Nenhum aluno aguardando aprovação.
              </p>
            ) : (
              invitations.pending.slice(0, 3).map(
                (invitation) => (
                  <div key={invitation.id}>
                    <button
                      type="button"
                      className="pending-invitation-profile"
                      onClick={() => {
                        if (invitation.athlete_id) {
                          onOpenProfile({
                            id: invitation.athlete_id,
                            name:
                              invitation.student_name
                              || "Novo aluno",
                          });
                        }
                      }}
                    >
                      <strong>
                        {invitation.student_name
                          || "Novo aluno"}
                      </strong>
                      <small>
                        {invitation.email
                          || "Cadastro por link"}
                      </small>
                    </button>

                    <button
                      type="button"
                      className="btn-primary"
                      onClick={() =>
                        onApproveInvitation(
                          invitation.id,
                        )
                      }
                    >
                      Aprovar
                    </button>
                  </div>
                ),
              )
            )}
          </div>
        </article>
      </section>
    </section>
  );
}
