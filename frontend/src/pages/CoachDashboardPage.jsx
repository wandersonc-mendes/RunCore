import { useEffect, useMemo, useState } from "react";

import {
  getTraining,
  listEvaluations,
} from "../api";

import "./CoachDashboardPage.css";

const BRAZIL_TIME_ZONE = "America/Sao_Paulo";


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


function formatDashboardDate() {
  const value = new Intl.DateTimeFormat("pt-BR", {
    weekday: "long",
    day: "2-digit",
    month: "long",
    year: "numeric",
    timeZone: BRAZIL_TIME_ZONE,
  }).format(new Date());

  return value.charAt(0).toUpperCase() + value.slice(1);
}


function getGreeting() {
  const hour = Number(
    new Intl.DateTimeFormat("pt-BR", {
      hour: "2-digit",
      hourCycle: "h23",
      timeZone: BRAZIL_TIME_ZONE,
    }).formatToParts(new Date()).find((part) => part.type === "hour")?.value,
  );

  if (hour >= 5 && hour < 12) {
    return { message: "Bom dia", icon: "☀️" };
  }

  if (hour >= 12 && hour < 18) {
    return { message: "Boa tarde", icon: "🌤️" };
  }

  return { message: "Boa noite", icon: "🌙" };
}


function formatDate(value) {
  if (!value) return "Sem data";

  return new Intl.DateTimeFormat("pt-BR").format(
    new Date(`${value}T12:00:00`),
  );
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
  const [inviteCopyStatus, setInviteCopyStatus] = useState("");

  async function copyInvitationLink() {
    setInviteCopyStatus("");

    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(inviteLink);
      } else {
        const temporaryInput = document.createElement("textarea");
        temporaryInput.value = inviteLink;
        temporaryInput.setAttribute("readonly", "");
        temporaryInput.style.position = "fixed";
        temporaryInput.style.opacity = "0";
        document.body.appendChild(temporaryInput);
        temporaryInput.select();

        const copied = document.execCommand("copy");
        document.body.removeChild(temporaryInput);

        if (!copied) {
          throw new Error("Falha ao copiar.");
        }
      }

      setInviteCopyStatus("copied");

      window.setTimeout(() => {
        setInviteCopyStatus("");
      }, 2500);
    } catch {
      setInviteCopyStatus("error");
    }
  }


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

    const sessions = records.flatMap(({ athlete, training }) =>
      (training?.sessions || []).map((session) => ({
        ...session,
        athlete,
      })),
    );

    const weekSessions = sessions.filter((session) => {
      if (!session.session_date) return false;

      const sessionDate = new Date(
        `${session.session_date}T12:00:00`,
      );

      return sessionDate >= weekStart && sessionDate <= weekEnd;
    });

    const completedSessions = weekSessions.filter(
      (session) => session.completed,
    );

    const pendingSessions = weekSessions.filter(
      (session) => !session.completed,
    );

    const activeAthletes = athletes.filter(
      (athlete) => athlete.active,
    );

    const pendingEvaluations = records.filter(
      ({ athlete, evaluations }) =>
        athlete.active && evaluations.length === 0,
    );

    const inactiveAthletes = athletes.filter(
      (athlete) => !athlete.active,
    );

    const weeklyVolume = weekSessions.reduce(
      (total, session) =>
        total + Number(session.planned_distance || 0),
      0,
    );

    const todaySessions = weekSessions.filter(
      (session) => session.session_date === today,
    );

    const attentionItems = [];

    if (pendingEvaluations.length > 0) {
      attentionItems.push({
        id: "evaluations",
        icon: "●",
        tone: "orange",
        title: `${pendingEvaluations.length} atleta(s) sem avaliação`,
        detail: "Avaliação necessária para prescrição individualizada",
        action: () =>
          onOpenEvaluations(pendingEvaluations[0].athlete),
      });
    }

    if (invitations.pending.length > 0) {
      attentionItems.push({
        id: "invitations",
        icon: "⚑",
        tone: "purple",
        title: `${invitations.pending.length} convite(s) aguardando aprovação`,
        detail: "Há cadastros pendentes de análise",
      });
    }

    if (inactiveAthletes.length > 0) {
      attentionItems.push({
        id: "inactive",
        icon: "!",
        tone: "red",
        title: `${inactiveAthletes.length} atleta(s) inativo(s)`,
        detail: "Revise a situação cadastral dos atletas",
      });
    }

    if (todaySessions.length === 0) {
      attentionItems.push({
        id: "today",
        icon: "↻",
        tone: "blue",
        title: "Nenhum treino programado para hoje",
        detail: "Confira o planejamento semanal dos atletas",
      });
    }

    return {
      activeAthletes,
      weekSessions,
      completedSessions,
      pendingSessions,
      weeklyVolume,
      averageVolume:
        activeAthletes.length > 0
          ? weeklyVolume / activeAthletes.length
          : 0,
      attentionItems,
    };
  }, [
    athletes,
    invitations.pending.length,
    onOpenEvaluations,
    records,
  ]);

  const totalSessions = dashboard.weekSessions.length;
  const completedPercent =
    totalSessions > 0
      ? (dashboard.completedSessions.length / totalSessions) * 100
      : 0;

  const firstActiveAthlete = dashboard.activeAthletes[0];
  const greeting = getGreeting();

  return (
    <section className="coach-dashboard-page dashboard-v2">
      <header className="dashboard-v2-header">
        <div>
          <h2>
            {greeting.message},{" "}
            {user?.name?.split(" ")[0] || "Treinador"}!{" "}
            <span aria-hidden="true">{greeting.icon}</span>
          </h2>
          <p>{formatDashboardDate()}</p>
        </div>

        <button
          type="button"
          className="dashboard-plan-week"
          disabled={!firstActiveAthlete}
          onClick={() => {
            if (firstActiveAthlete) {
              onOpenTraining(firstActiveAthlete);
            }
          }}
        >
          <span aria-hidden="true">＋</span>
          Planejar semana
        </button>
      </header>

      {error && <div className="alert">{error}</div>}

      <section className="dashboard-v2-metrics">
        <article className="metric-blue">
          <span className="metric-icon">♟</span>
          <strong>{dashboard.activeAthletes.length}</strong>
          <p>Atletas ativos</p>
        </article>

        <article className="metric-purple">
          <span className="metric-icon">▣</span>
          <strong>{dashboard.weekSessions.length}</strong>
          <p>Treinos programados</p>
        </article>

        <article className="metric-green">
          <span className="metric-icon">✓</span>
          <strong>{dashboard.completedSessions.length}</strong>
          <p>Concluídos esta semana</p>
        </article>

        <article className="metric-orange">
          <span className="metric-icon">◷</span>
          <strong>{dashboard.pendingSessions.length}</strong>
          <p>Pendentes esta semana</p>
        </article>

        <article className="metric-red">
          <span className="metric-icon">×</span>
          <strong>{invitations.pending.length}</strong>
          <p>Convites pendentes</p>
        </article>
      </section>

      <section
        id="convites"
        className="dashboard-invitations"
      >
        <header>
          <div>
            <span>NOVOS ALUNOS</span>
            <h3>Convites e aprovações</h3>
            <p>
              Gere um link para o pré-cadastro e aprove os alunos
              que concluírem o envio das informações.
            </p>
          </div>

          <strong>
            {invitations.pending.length} aguardando aprovação
          </strong>
        </header>

        <form
          className="dashboard-invite-form"
          onSubmit={onCreateInvitation}
        >
          <label>
            E-mail do aluno
            <input
              type="email"
              value={inviteEmail}
              onChange={(event) =>
                setInviteEmail(event.target.value)
              }
              placeholder="Opcional"
            />
          </label>

          <button type="submit" className="btn-primary">
            Gerar link de convite
          </button>
        </form>

        {inviteLink && (
          <div className="dashboard-invite-link">
            <div>
              <span>Link pronto para compartilhar</span>
              <input
                readOnly
                value={inviteLink}
                onFocus={(event) => event.target.select()}
              />
            </div>

            <div className="dashboard-copy-feedback">
              <button
                type="button"
                className="btn-ghost"
                onClick={copyInvitationLink}
              >
                {inviteCopyStatus === "copied"
                  ? "Link copiado"
                  : "Copiar"}
              </button>

              {inviteCopyStatus === "copied" && (
                <small role="status">
                  Copiado para a área de transferência.
                </small>
              )}

              {inviteCopyStatus === "error" && (
                <small role="alert" className="is-error">
                  Não foi possível copiar. Selecione o link manualmente.
                </small>
              )}
            </div>
          </div>
        )}

        <div className="dashboard-invitation-columns">
          <section>
            <header>
              <strong>Aguardando aprovação</strong>
              <span>{invitations.pending.length}</span>
            </header>

            {invitations.pending.length ? (
              <div className="dashboard-invitation-list">
                {invitations.pending.map((invitation) => (
                  <article key={invitation.id}>
                    <div>
                      <strong>
                        {invitation.student_name || "Novo aluno"}
                      </strong>
                      <small>
                        {invitation.email
                          || "E-mail informado no pré-cadastro"}
                      </small>
                    </div>

                    <div className="dashboard-invitation-actions">
                      {invitation.athlete_id && onOpenProfile && (
                        <button
                          type="button"
                          className="btn-ghost"
                          onClick={() =>
                            onOpenProfile({
                              id: invitation.athlete_id,
                              name:
                                invitation.student_name
                                || "Novo aluno",
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
                          onApproveInvitation(invitation.id)
                        }
                      >
                        Aprovar
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <p className="dashboard-invitation-empty">
                Nenhum aluno aguardando aprovação.
              </p>
            )}
          </section>

          <section>
            <header>
              <strong>Convites enviados</strong>
              <span>{invitations.sent.length}</span>
            </header>

            {invitations.sent.length ? (
              <div className="dashboard-invitation-list sent">
                {invitations.sent.slice(0, 5).map((invitation) => (
                  <article key={invitation.id}>
                    <div>
                      <strong>
                        {invitation.email
                          || "Link sem e-mail definido"}
                      </strong>
                      <small>
                        Aguardando utilização do convite
                      </small>
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <p className="dashboard-invitation-empty">
                Nenhum convite pendente de uso.
              </p>
            )}
          </section>
        </div>
      </section>

      <section className="dashboard-v2-content">
        <article className="dashboard-v2-panel attention-panel">
          <header>
            <h3>Atenções</h3>
          </header>

          {loading ? (
            <p className="dashboard-v2-empty">Carregando alertas...</p>
          ) : dashboard.attentionItems.length === 0 ? (
            <p className="dashboard-v2-empty">Nenhuma atenção pendente.</p>
          ) : (
            <div className="attention-list">
              {dashboard.attentionItems.slice(0, 4).map((item) => (
                <button
                  type="button"
                  key={item.id}
                  className={`attention-item ${item.tone}`}
                  onClick={item.action}
                  disabled={!item.action}
                >
                  <span className="attention-icon">{item.icon}</span>
                  <span className="attention-copy">
                    <strong>{item.title}</strong>
                    <small>{item.detail}</small>
                  </span>
                  <span aria-hidden="true">›</span>
                </button>
              ))}
            </div>
          )}
        </article>

        <article className="dashboard-v2-panel weekly-summary-panel">
          <header>
            <h3>Resumo da semana</h3>
          </header>

          <div className="weekly-summary-main">
            <div
              className="weekly-donut"
              style={{ "--completed": `${completedPercent}%` }}
            >
              <div>
                <strong>{totalSessions}</strong>
                <span>treinos</span>
              </div>
            </div>

            <div className="weekly-summary-legend">
              <div>
                <span className="legend-dot completed" />
                <strong>{dashboard.completedSessions.length}</strong>
                <small>Concluídos</small>
              </div>

              <div>
                <span className="legend-dot pending" />
                <strong>{dashboard.pendingSessions.length}</strong>
                <small>Pendentes</small>
              </div>

              <div>
                <span className="legend-dot invitation" />
                <strong>{invitations.pending.length}</strong>
                <small>Convites</small>
              </div>
            </div>
          </div>

          <footer className="weekly-summary-footer">
            <div>
              <span>Volume da semana</span>
              <strong>
                {dashboard.weeklyVolume.toLocaleString("pt-BR", {
                  minimumFractionDigits: 1,
                  maximumFractionDigits: 1,
                })} km
              </strong>
              <small>
                Planejado de{" "}
                {formatDate(dashboard.weekSessions[0]?.session_date)}
              </small>
            </div>

            <div>
              <span>Média por atleta</span>
              <strong>
                {dashboard.averageVolume.toLocaleString("pt-BR", {
                  minimumFractionDigits: 1,
                  maximumFractionDigits: 1,
                })} km
              </strong>
              <small>
                {dashboard.activeAthletes.length} atleta(s) ativo(s)
              </small>
            </div>
          </footer>
        </article>
      </section>
    </section>
  );
}
