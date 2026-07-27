import { useEffect, useMemo, useState } from "react";

import {
  getTraining,
  listEvaluations,
} from "../api";

import "./CoachDashboardPage.css";


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
  }).format(new Date());

  return value.charAt(0).toUpperCase() + value.slice(1);
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

  return (
    <section className="coach-dashboard-page dashboard-v2">
      <header className="dashboard-v2-header">
        <div>
          <h2>
            Bom dia, {user?.name?.split(" ")[0] || "Treinador"}!{" "}
            <span aria-hidden="true">☀</span>
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
