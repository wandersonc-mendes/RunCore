import { useEffect, useMemo, useState } from "react";

import {
  getAthleteAnalytics,
  getAthleteProfile,
  getAthleteTrainingLoad,
  getTraining,
} from "./api";


const questions = [
  "Supervisão médica por problema cardíaco",
  "Dor no peito durante atividade",
  "Dor no peito no último mês",
  "Desmaio ou tontura",
  "Problema ósseo ou articular",
  "Medicação para pressão ou coração",
  "Outro motivo médico para evitar exercício",
];


function Item({ label, value }) {
  return (
    <div className="viewer-item">
      <span>{label}</span>
      <strong>{value || "Não informado"}</strong>
    </div>
  );
}


function dateValue(value) {
  if (!value) return null;

  const result = new Date(`${value}T12:00:00`);

  return Number.isNaN(result.getTime())
    ? null
    : result;
}


function dateKey(date) {
  const year = date.getFullYear();
  const month = String(
    date.getMonth() + 1,
  ).padStart(2, "0");
  const day = String(
    date.getDate(),
  ).padStart(2, "0");

  return `${year}-${month}-${day}`;
}


function startOfWeek(date) {
  const result = new Date(date);
  const weekday = result.getDay();
  const offset = weekday === 0
    ? -6
    : 1 - weekday;

  result.setDate(result.getDate() + offset);
  result.setHours(0, 0, 0, 0);

  return result;
}


function addDays(date, amount) {
  const result = new Date(date);
  result.setDate(result.getDate() + amount);
  return result;
}


function formatDate(value) {
  const date = dateValue(value);

  if (!date) return "Sem data";

  return new Intl.DateTimeFormat(
    "pt-BR",
    {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    },
  ).format(date);
}


function formatWeekday(value) {
  const date = dateValue(value);

  if (!date) return "";

  const label = new Intl.DateTimeFormat(
    "pt-BR",
    { weekday: "long" },
  ).format(date);

  return label.charAt(0).toUpperCase()
    + label.slice(1);
}


function formatAnalyticsDuration(seconds) {
  const total = Math.max(
    0,
    Math.round(Number(seconds || 0)),
  );
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor(
    (total % 3600) / 60,
  );
  const remainder = total % 60;

  return [
    hours,
    minutes,
    remainder,
  ]
    .map((part) =>
      String(part).padStart(2, "0")
    )
    .join(":");
}


function formatPercentDelta(value) {
  if (value === null || value === undefined) {
    return "—";
  }

  const number = Number(value);

  if (Number.isNaN(number)) {
    return "—";
  }

  const prefix = number > 0 ? "+" : "";

  return `${prefix}${number.toLocaleString(
    "pt-BR",
    {
      minimumFractionDigits: 0,
      maximumFractionDigits: 1,
    },
  )}%`;
}


function initials(name = "") {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) =>
      part[0]?.toUpperCase()
    )
    .join("") || "RC";
}


function stepDistanceKm(step) {
  const distance = Number(step?.distance || 0);
  const repetitions = Math.max(
    Number(step?.repetitions || 0),
    1,
  );

  const unit = step?.distance_unit || (
    Number(step?.repetitions || 0) > 0
      ? "m"
      : "km"
  );

  const total = distance * repetitions;

  return unit === "m"
    ? total / 1000
    : total;
}


function sessionDistanceKm(session) {
  if (session?.steps?.length) {
    return session.steps.reduce(
      (total, step) =>
        total + stepDistanceKm(step),
      0,
    );
  }

  const distance = Number(
    session?.planned_distance || 0,
  );

  const repetitions = Number(
    session?.repetitions || 0,
  );

  return repetitions > 0
    ? distance * repetitions / 1000
    : distance;
}


function formatDistance(session) {
  return `${sessionDistanceKm(session).toLocaleString(
    "pt-BR",
    {
      minimumFractionDigits: 1,
      maximumFractionDigits: 2,
    },
  )} km`;
}


function LoadChart({ points = [], metrics }) {
  if (!points.length) {
    return (
      <p className="muted">
        Ainda não há feedbacks suficientes para calcular a carga.
      </p>
    );
  }

  const values = points.flatMap(
    (point) => [
      point.fitness,
      point.fatigue,
      point.form,
    ],
  );

  const min = Math.min(...values, 0);
  const max = Math.max(...values, 1);
  const range = Math.max(max - min, 1);

  const line = (field) =>
    points.map((point, index) =>
      `${(
        index / Math.max(points.length - 1, 1)
      ) * 100},${
        100 - (
          (point[field] - min) / range
        ) * 100
      }`
    ).join(" ");

  return (
    <div className="load-chart">
      <svg
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
      >
        <line
          x1="0"
          y1={
            100 - ((0 - min) / range) * 100
          }
          x2="100"
          y2={
            100 - ((0 - min) / range) * 100
          }
          className="load-zero"
        />
        <polyline
          points={line("fitness")}
          className="load-fitness"
        />
        <polyline
          points={line("fatigue")}
          className="load-fatigue"
        />
        <polyline
          points={line("form")}
          className="load-form"
        />
      </svg>

      <div className="load-legend">
        <span className="fitness">Fitness</span>
        <span className="fatigue">Fadiga</span>
        <span className="form">Forma</span>

        {metrics && (
          <div className="load-chart-meta">
            <span title="Monotonia">
              MON {metrics.monotony || "—"}
            </span>
            <span title="Strain">
              STR {metrics.strain || "—"}
            </span>
            <span title="Feedbacks recebidos">
              FB {metrics.feedbackCount}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}


export default function AthleteProfileView({
  athlete,
  onClose,
  onRemove,
  onOpenTraining,
  onOpenEvaluations,
}) {
  const [profile, setProfile] = useState(null);
  const [trainingPlan, setTrainingPlan] = useState(null);
  const [load, setLoad] = useState(null);
  const [loadError, setLoadError] = useState("");
  const [analytics, setAnalytics] = useState(null);
  const [analyticsError, setAnalyticsError] = useState("");
  const [tab, setTab] = useState("summary");

  useEffect(() => {
    let active = true;

    Promise.allSettled([
      getAthleteProfile(athlete.id),
      getTraining(athlete.id),
      getAthleteTrainingLoad(athlete.id),
      getAthleteAnalytics(athlete.id),
    ]).then((results) => {
      if (!active) return;

      const [
        profileResult,
        trainingResult,
        loadResult,
        analyticsResult,
      ] = results;

      setProfile(
        profileResult.status === "fulfilled"
          ? profileResult.value
          : {
              personal: {},
              parq: {},
              training: {},
            },
      );

      setTrainingPlan(
        trainingResult.status === "fulfilled"
          ? trainingResult.value
          : null,
      );

      if (loadResult.status === "fulfilled") {
        setLoad(loadResult.value);
        setLoadError("");
      } else {
        setLoad(null);
        setLoadError(
          loadResult.reason?.message || "",
        );
      }

      if (analyticsResult.status === "fulfilled") {
        setAnalytics(analyticsResult.value);
        setAnalyticsError("");
      } else {
        setAnalytics(null);
        setAnalyticsError(
          analyticsResult.reason?.message || "",
        );
      }
    });

    return () => {
      active = false;
    };
  }, [athlete.id]);

  const summary = useMemo(() => {
    const sessions = [
      ...(trainingPlan?.sessions || []),
    ].filter(
      (session) => session.session_date,
    );

    sessions.sort(
      (first, second) =>
        dateValue(first.session_date)
        - dateValue(second.session_date),
    );

    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const completed = sessions.filter(
      (session) =>
        session.completed
        && dateValue(session.session_date) <= today,
    );

    const future = sessions.filter(
      (session) =>
        !session.completed
        && dateValue(session.session_date) >= today,
    );

    const lastWorkout = completed.at(-1) || null;
    const nextWorkout = future[0] || null;

    const weekStart = startOfWeek(today);
    const weekEnd = addDays(weekStart, 6);

    const weekSessions = sessions.filter(
      (session) => {
        const date = dateValue(session.session_date);

        return (
          date >= weekStart
          && date <= weekEnd
        );
      },
    );

    const weeklyVolume = weekSessions.reduce(
      (total, session) =>
        total + sessionDistanceKm(session),
      0,
    );

    const fourWeekStart = addDays(weekStart, -21);
    const fourWeekSessions = sessions.filter(
      (session) => {
        const date = dateValue(session.session_date);

        return (
          date >= fourWeekStart
          && date <= weekEnd
        );
      },
    );

    const fourWeekVolume = fourWeekSessions.reduce(
      (total, session) =>
        total + sessionDistanceKm(session),
      0,
    );

    let daysWithoutTraining = null;

    if (lastWorkout) {
      const lastDate = dateValue(
        lastWorkout.session_date,
      );

      daysWithoutTraining = Math.max(
        0,
        Math.floor(
          (
            today.getTime()
            - lastDate.getTime()
          ) / 86400000,
        ),
      );
    }

    return {
      sessions,
      lastWorkout,
      nextWorkout,
      weeklyVolume,
      averageVolume: fourWeekVolume / 4,
      daysWithoutTraining,
    };
  }, [trainingPlan]);

  if (!profile) {
    return (
      <main className="athlete-overview-page">
        <p className="muted">Carregando atleta...</p>
      </main>
    );
  }

  const personal = profile.personal || {};
  const parq = profile.parq || {};
  const training = profile.training || {};
  const currentLoad = load?.points?.at(-1);
  const latestAnalyticsWeek = analytics?.weekly?.at(-1) || null;
  const dataCoverage = Number(
    analytics?.data_quality?.overall_coverage_percent || 0,
  );
  const periodComparison = analytics?.period_comparison || null;
  const currentPeriod = periodComparison?.current || {};
  const previousPeriod = periodComparison?.previous || {};
  const periodDelta = periodComparison?.delta || {};
  const paceBaselines = analytics?.pace_baselines || [];
  const qualityFields = Object.entries(
    analytics?.data_quality?.fields || {},
  );
  const analysisAvailability = Object.entries(
    analytics?.analysis_availability || {},
  );
  const calculationContext = (
    analytics?.calculation_context || {}
  );
  const weeklyEvolution = analytics?.weekly || [];

  const goal = (
    trainingPlan?.objective
    || training.goal
    || personal.goal
    || athlete.goal
    || "Objetivo não informado"
  );

  const targetDate = trainingPlan?.target_date;

  return (
    <main className="athlete-overview-page">
      <header className="athlete-overview-header">
        <button
          type="button"
          className="athlete-overview-back"
          onClick={onClose}
          aria-label="Voltar para atletas"
        >
          ‹
        </button>

        <div className="athlete-overview-identity">
          <span className="athlete-overview-avatar">
            {initials(athlete.name)}
          </span>

          <div>
            <div>
              <h1>{athlete.name}</h1>
              <span className={
                athlete.active
                  ? "athlete-status active"
                  : "athlete-status inactive"
              }>
                {athlete.active
                  ? "Ativo"
                  : "Inativo"}
              </span>
            </div>

            <p>
              {goal}
              {targetDate
                ? ` · Prova em ${formatDate(targetDate)}`
                : ""}
            </p>
          </div>
        </div>

        <div className="athlete-overview-actions">
          <button
            type="button"
            className="btn-ghost"
            onClick={() =>
              onOpenTraining(athlete)
            }
          >
            Planejamento
          </button>

          <button
            type="button"
            className="btn-ghost"
            onClick={() =>
              onOpenEvaluations(athlete)
            }
          >
            Avaliações
          </button>

          <button
            type="button"
            className="btn-link-danger"
            onClick={onRemove}
          >
            Remover
          </button>
        </div>
      </header>

      <nav className="athlete-overview-tabs">
        <button
          type="button"
          className={
            tab === "summary" ? "active" : ""
          }
          onClick={() => setTab("summary")}
        >
          Resumo
        </button>

        <button
          type="button"
          className={
            tab === "training" ? "active" : ""
          }
          onClick={() => setTab("training")}
        >
          Treinos
        </button>

        <button
          type="button"
          className={
            tab === "load" ? "active" : ""
          }
          onClick={() => setTab("load")}
        >
          Evolução
        </button>

        <button
          type="button"
          className={
            tab === "health" ? "active" : ""
          }
          onClick={() => setTab("health")}
        >
          Histórico
        </button>

        <button
          type="button"
          className={
            tab === "analytics" ? "active" : ""
          }
          onClick={() => setTab("analytics")}
        >
          Análise
        </button>

        <button
          type="button"
          className={
            tab === "profile" ? "active" : ""
          }
          onClick={() => setTab("profile")}
        >
          Perfil
        </button>
      </nav>

      {tab === "summary" && (
        <section className="athlete-summary-grid">
          <article className="athlete-summary-card">
            <span>Último treino</span>

            {summary.lastWorkout ? (
              <>
                <small>
                  {formatDate(
                    summary.lastWorkout.session_date,
                  )}
                  {" · "}
                  {formatWeekday(
                    summary.lastWorkout.session_date,
                  )}
                </small>
                <strong>
                  {summary.lastWorkout.workout_name}
                </strong>
                <p>
                  {formatDistance(
                    summary.lastWorkout,
                  )}
                </p>
              </>
            ) : (
              <p>Nenhum treino concluído.</p>
            )}
          </article>

          <article className="athlete-summary-card">
            <span>Volume da semana</span>
            <strong>
              {summary.weeklyVolume.toLocaleString(
                "pt-BR",
                {
                  minimumFractionDigits: 1,
                  maximumFractionDigits: 1,
                },
              )} km
            </strong>
            <small>Volume planejado</small>
          </article>

          <article className="athlete-summary-card">
            <span>Dias sem treinar</span>
            <strong>
              {summary.daysWithoutTraining ?? "—"}
            </strong>
            <small>
              {summary.lastWorkout
                ? `Último em ${formatDate(
                    summary.lastWorkout.session_date,
                  )}`
                : "Sem treino concluído"}
            </small>
          </article>

          <article className="athlete-summary-card next">
            <span>Próximo treino</span>

            {summary.nextWorkout ? (
              <>
                <small>
                  {formatDate(
                    summary.nextWorkout.session_date,
                  )}
                  {" · "}
                  {formatWeekday(
                    summary.nextWorkout.session_date,
                  )}
                </small>
                <strong>
                  {summary.nextWorkout.workout_name}
                </strong>
                <p>
                  {formatDistance(
                    summary.nextWorkout,
                  )}
                </p>
              </>
            ) : (
              <p>Nenhum treino futuro.</p>
            )}
          </article>

          <article className="athlete-summary-card">
            <span>Média semanal</span>
            <strong>
              {summary.averageVolume.toLocaleString(
                "pt-BR",
                {
                  minimumFractionDigits: 1,
                  maximumFractionDigits: 1,
                },
              )} km
            </strong>
            <small>Últimas quatro semanas</small>
          </article>

          <article className="athlete-summary-card">
            <span>Carga semanal</span>
            <strong>
              {load
                ? Number(
                    load.weekly_load || 0,
                  ).toFixed(0)
                : "—"}
            </strong>
            <small>
              {load
                ? "PSE × duração"
                : "Sem feedback suficiente"}
            </small>
          </article>

          <article className="athlete-observations-card">
            <span>Observações</span>
            <p>
              {athlete.notes
                || personal.notes
                || "Nenhuma observação registrada."}
            </p>
          </article>
        </section>
      )}

      {tab === "analytics" && (
        <section className="profile-card analytics-profile-card">
          <div className="athlete-section-heading">
            <div>
              <h2>Perfil analítico</h2>
              <p className="muted">
                Indicadores objetivos calculados a partir das
                atividades importadas.
              </p>
            </div>
          </div>

          {analyticsError ? (
            <p className="muted">
              Não foi possível carregar o perfil analítico:
              {" "}{analyticsError}
            </p>
          ) : analytics ? (
            <>
              <div className="athlete-summary-grid">
              <article className="athlete-summary-card">
                <span>Atividades analisadas</span>
                <strong>
                  {analytics.activity_count ?? 0}
                </strong>
                <small>
                  Corridas com data válida
                </small>
              </article>

              <article className="athlete-summary-card">
                <span>Volume da última semana</span>
                <strong>
                  {latestAnalyticsWeek
                    ? `${Number(
                        latestAnalyticsWeek.distance_km || 0,
                      ).toLocaleString(
                        "pt-BR",
                        {
                          minimumFractionDigits: 1,
                          maximumFractionDigits: 1,
                        },
                      )} km`
                    : "—"}
                </strong>
                <small>
                  Atividades realizadas
                </small>
              </article>

              <article className="athlete-summary-card">
                <span>Tempo da última semana</span>
                <strong>
                  {latestAnalyticsWeek
                    ? formatDuration(
                        latestAnalyticsWeek
                          .moving_time_seconds || 0,
                      )
                    : "—"}
                </strong>
                <small>
                  Tempo em movimento
                </small>
              </article>

              <article className="athlete-summary-card">
                <span>Faixas de ritmo</span>
                <strong>
                  {analytics.pace_baselines?.length || 0}
                </strong>
                <small>
                  Baselines por pace médio
                </small>
              </article>

              <article className="athlete-summary-card">
                <span>Cobertura dos dados</span>
                <strong>
                  {dataCoverage.toLocaleString(
                    "pt-BR",
                    {
                      minimumFractionDigits: 0,
                      maximumFractionDigits: 1,
                    },
                  )}%
                </strong>
                <small>
                  Qualidade dos campos disponíveis
                </small>
              </article>
            </div>

            <div>
              <div className="athlete-section-heading">
                <div>
                  <h2>Comparação 28 × 28 dias</h2>
                  <p className="muted">
                    Período atual comparado aos 28 dias
                    imediatamente anteriores.
                  </p>
                </div>
              </div>

              <div className="athlete-summary-grid">
                <article className="athlete-summary-card">
                  <span>Volume</span>
                  <strong>
                    {Number(
                      currentPeriod.distance_km || 0,
                    ).toLocaleString(
                      "pt-BR",
                      {
                        minimumFractionDigits: 1,
                        maximumFractionDigits: 1,
                      },
                    )} km
                  </strong>
                  <small>
                    Anterior:{" "}
                    {Number(
                      previousPeriod.distance_km || 0,
                    ).toLocaleString(
                      "pt-BR",
                      {
                        minimumFractionDigits: 1,
                        maximumFractionDigits: 1,
                      },
                    )} km
                    {" · Δ "}
                    {formatPercentDelta(
                      periodDelta.distance_km?.percent,
                    )}
                  </small>
                </article>

                <article className="athlete-summary-card">
                  <span>Atividades</span>
                  <strong>
                    {currentPeriod.activity_count ?? 0}
                  </strong>
                  <small>
                    Anterior:{" "}
                    {previousPeriod.activity_count ?? 0}
                    {" · Δ "}
                    {formatPercentDelta(
                      periodDelta.activity_count?.percent,
                    )}
                  </small>
                </article>

                <article className="athlete-summary-card">
                  <span>Tempo em movimento</span>
                  <strong>
                    {formatAnalyticsDuration(
                      currentPeriod.moving_time_seconds || 0,
                    )}
                  </strong>
                  <small>
                    Anterior:{" "}
                    {formatAnalyticsDuration(
                      previousPeriod.moving_time_seconds || 0,
                    )}
                    {" · Δ "}
                    {formatPercentDelta(
                      periodDelta
                        .moving_time_seconds?.percent,
                    )}
                  </small>
                </article>

                <article className="athlete-summary-card">
                  <span>Ritmo médio</span>
                  <strong>
                    {currentPeriod.average_pace
                      ? `${currentPeriod.average_pace}/km`
                      : "—"}
                  </strong>
                  <small>
                    Anterior:{" "}
                    {previousPeriod.average_pace
                      ? `${previousPeriod.average_pace}/km`
                      : "—"}
                    {" · Δ "}
                    {formatPercentDelta(
                      periodDelta
                        .average_pace_seconds_per_km
                        ?.percent,
                    )}
                  </small>
                </article>

                <article className="athlete-summary-card">
                  <span>FC média</span>
                  <strong>
                    {currentPeriod.average_heartrate
                      ?? "—"}
                  </strong>
                  <small>
                    Anterior:{" "}
                    {previousPeriod.average_heartrate
                      ?? "—"}
                    {" · Δ "}
                    {formatPercentDelta(
                      periodDelta.average_heartrate?.percent,
                    )}
                  </small>
                </article>

                <article className="athlete-summary-card">
                  <span>Cadência média</span>
                  <strong>
                    {currentPeriod.average_cadence
                      ?? "—"}
                  </strong>
                  <small>
                    Anterior:{" "}
                    {previousPeriod.average_cadence
                      ?? "—"}
                    {" · Δ "}
                    {formatPercentDelta(
                      periodDelta.average_cadence?.percent,
                    )}
                  </small>
                </article>
              </div>
            </div>

            <div>
              <div className="athlete-section-heading">
                <div>
                  <h2>Baselines por faixa de ritmo</h2>
                  <p className="muted">
                    Agrupamento por ritmo médio da atividade.
                    O baseline exige pelo menos três amostras.
                  </p>
                </div>
              </div>

              {paceBaselines.length ? (
                <div className="athlete-training-list">
                  {paceBaselines.map((baseline) => (
                    <article key={baseline.key}>
                      <div>
                        <small>
                          {baseline.label}
                        </small>
                        <strong>
                          {baseline.average_pace
                            ? `${baseline.average_pace}/km`
                            : "Ritmo indisponível"}
                        </strong>
                        <span>
                          {baseline.activity_count} atividade
                          {baseline.activity_count === 1
                            ? ""
                            : "s"}
                          {" · "}
                          {Number(
                            baseline.total_distance_km || 0,
                          ).toLocaleString(
                            "pt-BR",
                            {
                              minimumFractionDigits: 1,
                              maximumFractionDigits: 1,
                            },
                          )} km
                        </span>
                      </div>

                      <div>
                        <small>
                          {baseline.baseline_available
                            ? "Baseline disponível"
                            : "Amostra insuficiente"}
                        </small>
                        <span>
                          FC média:{" "}
                          {baseline.average_heartrate ?? "—"}
                        </span>
                        <span>
                          Cadência média:{" "}
                          {baseline.average_cadence ?? "—"}
                        </span>
                      </div>
                    </article>
                  ))}
                </div>
              ) : (
                <p className="muted">
                  Ainda não há faixas de ritmo calculadas.
                </p>
              )}
            </div>

            <div>
              <div className="athlete-section-heading">
                <div>
                  <h2>Qualidade dos dados</h2>
                  <p className="muted">
                    Cobertura dos campos disponíveis nas
                    atividades analisadas.
                  </p>
                </div>
              </div>

              {qualityFields.length ? (
                <div className="athlete-training-list">
                  {qualityFields.map(([field, data]) => {
                    const labels = {
                      date: "Data",
                      distance: "Distância",
                      moving_time: "Tempo em movimento",
                      pace: "Ritmo",
                      heart_rate: "Frequência cardíaca",
                      cadence: "Cadência",
                    };

                    return (
                      <article key={field}>
                        <div>
                          <small>
                            {labels[field] || field}
                          </small>
                          <strong>
                            {Number(
                              data.coverage_percent || 0,
                            ).toLocaleString(
                              "pt-BR",
                              {
                                minimumFractionDigits: 0,
                                maximumFractionDigits: 1,
                              },
                            )}%
                          </strong>
                        </div>

                        <div>
                          <span>
                            Disponíveis: {data.available ?? 0}
                          </span>
                          <span>
                            Ausentes: {data.missing ?? 0}
                          </span>
                        </div>
                      </article>
                    );
                  })}
                </div>
              ) : (
                <p className="muted">
                  Nenhum indicador de qualidade disponível.
                </p>
              )}
            </div>

            <div>
              <div className="athlete-section-heading">
                <div>
                  <h2>Disponibilidade das análises</h2>
                  <p className="muted">
                    Estado das análises conforme os dados
                    atualmente persistidos.
                  </p>
                </div>
              </div>

              {analysisAvailability.length ? (
                <div className="athlete-training-list">
                  {analysisAvailability.map(
                    ([analysisKey, status]) => {
                      const labels = {
                        weekly_volume: "Volume semanal",
                        weekly_duration: "Duração semanal",
                        pace_baselines: "Baselines de ritmo",
                        heart_rate_by_pace: "FC por ritmo",
                        cadence_by_pace: "Cadência por ritmo",
                        comparison_28_days:
                          "Comparação de 28 dias",
                        local_calendar_analysis:
                          "Calendário em horário local",
                        lap_or_stream_analysis:
                          "Análise de laps/streams",
                      };

                      return (
                        <article key={analysisKey}>
                          <div>
                            <small>
                              {labels[analysisKey]
                                || analysisKey}
                            </small>
                            <strong>
                              {status.available
                                ? "Disponível"
                                : "Indisponível"}
                            </strong>
                          </div>

                          <div>
                            {!status.available
                              && status.reason && (
                                <span>
                                  Motivo técnico:{" "}
                                  {status.reason}
                                </span>
                              )}
                            {status.sample_count
                              !== undefined && (
                                <span>
                                  Amostras:{" "}
                                  {status.sample_count}
                                </span>
                              )}
                            {status.available_band_count
                              !== undefined && (
                                <span>
                                  Faixas disponíveis:{" "}
                                  {status.available_band_count}
                                </span>
                              )}
                          </div>
                        </article>
                      );
                    },
                  )}
                </div>
              ) : (
                <p className="muted">
                  Nenhum estado de análise disponível.
                </p>
              )}
            </div>

            <div>
              <div className="athlete-section-heading">
                <div>
                  <h2>Evolução semanal</h2>
                  <p className="muted">
                    Histórico objetivo das semanas com
                    atividades de corrida importadas.
                  </p>
                </div>
              </div>

              {weeklyEvolution.length ? (
                <div className="athlete-training-list">
                  {weeklyEvolution.map((week) => (
                    <article key={week.week_start}>
                      <div>
                        <small>
                          Semana de {formatDate(
                            week.week_start,
                          )}
                        </small>
                        <strong>
                          {Number(
                            week.distance_km || 0,
                          ).toLocaleString(
                            "pt-BR",
                            {
                              minimumFractionDigits: 1,
                              maximumFractionDigits: 1,
                            },
                          )} km
                        </strong>
                        <span>
                          {week.activity_count ?? 0} atividade
                          {(week.activity_count ?? 0) === 1
                            ? ""
                            : "s"}
                        </span>
                      </div>

                      <div>
                        <span>
                          Em movimento:{" "}
                          {formatAnalyticsDuration(
                            week.moving_time_seconds || 0,
                          )}
                        </span>
                        <span>
                          Tempo total:{" "}
                          {formatAnalyticsDuration(
                            week.elapsed_time_seconds || 0,
                          )}
                        </span>
                      </div>
                    </article>
                  ))}
                </div>
              ) : (
                <p className="muted">
                  Ainda não há evolução semanal calculada.
                </p>
              )}
            </div>

            <div>
              <div className="athlete-section-heading">
                <div>
                  <h2>Contexto dos cálculos</h2>
                  <p className="muted">
                    Convenções técnicas usadas pelo perfil
                    analítico.
                  </p>
                </div>
              </div>

              <div className="athlete-training-list">
                <article>
                  <div>
                    <small>Unidades</small>
                    <strong>
                      Distância:{" "}
                      {calculationContext.distance_unit
                        || "—"}
                    </strong>
                  </div>

                  <div>
                    <span>
                      Duração:{" "}
                      {calculationContext.duration_unit
                        || "—"}
                    </span>
                    <span>
                      Pace:{" "}
                      {calculationContext.pace_unit
                        || "—"}
                    </span>
                  </div>
                </article>

                <article>
                  <div>
                    <small>Faixas de ritmo</small>
                    <strong>
                      {calculationContext.pace_band_seconds
                        ?? "—"} s/km
                    </strong>
                  </div>

                  <div>
                    <span>
                      Baseline mínimo:{" "}
                      {calculationContext
                        .minimum_baseline_samples ?? "—"}
                      {" "}amostras
                    </span>
                    <span>
                      Granularidade:{" "}
                      {calculationContext
                        .pace_baseline_granularity || "—"}
                    </span>
                  </div>
                </article>

                <article>
                  <div>
                    <small>Base temporal</small>
                    <strong>
                      {calculationContext.activity_date_basis
                        || "—"}
                    </strong>
                  </div>

                  <div>
                    <span>
                      Data local persistida:{" "}
                      {calculationContext
                        .local_activity_date_persisted
                        ? "Sim"
                        : "Não"}
                    </span>
                  </div>
                </article>

                <article>
                  <div>
                    <small>Dados granulares</small>
                    <strong>
                      Persistência atual
                    </strong>
                  </div>

                  <div>
                    <span>
                      Laps:{" "}
                      {calculationContext.laps_persisted
                        ? "Sim"
                        : "Não"}
                    </span>
                    <span>
                      Streams:{" "}
                      {calculationContext.streams_persisted
                        ? "Sim"
                        : "Não"}
                    </span>
                  </div>
                </article>
              </div>
            </div>
            </>
          ) : (
            <p className="muted">
              Carregando perfil analítico...
            </p>
          )}
        </section>
      )}

      {tab === "training" && (
        <section className="profile-card">
          <div className="athlete-section-heading">
            <div>
              <h2>Treinos programados</h2>
              <p className="muted">
                Sessões existentes no planejamento atual.
              </p>
            </div>

            <button
              type="button"
              className="btn-primary"
              onClick={() =>
                onOpenTraining(athlete)
              }
            >
              Abrir planejamento
            </button>
          </div>

          <div className="athlete-training-list">
            {summary.sessions.length ? (
              summary.sessions.slice(0, 12).map(
                (session) => (
                  <article key={session.id}>
                    <div>
                      <small>
                        {formatDate(
                          session.session_date,
                        )}
                      </small>
                      <strong>
                        {session.workout_name}
                      </strong>
                    </div>

                    <span>
                      {formatDistance(session)}
                    </span>
                  </article>
                ),
              )
            ) : (
              <p className="muted">
                Nenhuma sessão programada.
              </p>
            )}
          </div>
        </section>
      )}

      {tab === "load" && (
        <section className="profile-card">
          <h2>Evolução da carga</h2>
          <p className="muted">
            Calculada a partir de PSE × tempo em movimento,
            informado pelo aluno após as atividades.
          </p>

          {load ? (
            <>
              <div className="load-overview">
                <div className="load-highlights">
                  <article className="load-highlight fitness">
                    <span>Fitness</span>
                    <strong>
                      {currentLoad?.fitness?.toFixed(1)
                        || "0.0"}
                    </strong>
                  </article>

                  <article className="load-highlight load">
                    <span>Carga</span>
                    <strong>
                      {load.weekly_load.toFixed(0)}
                    </strong>
                  </article>

                  <article className="load-highlight form">
                    <span>Forma</span>
                    <strong>
                      {currentLoad?.form?.toFixed(1)
                        || "0.0"}
                    </strong>
                  </article>
                </div>
              </div>

              <LoadChart
                points={load.points}
                metrics={{
                  monotony: load.monotony,
                  strain: load.strain,
                  feedbackCount:
                    load.feedback_count,
                }}
              />
            </>
          ) : (
            <p className={
              loadError ? "alert" : "muted"
            }>
              {loadError
                || "Aguardando feedbacks das atividades do aluno."}
            </p>
          )}
        </section>
      )}

      {tab === "health" && (
        <section className="profile-card">
          <h2>PAR-Q e dados de saúde</h2>

          <div className="viewer-grid">
            <Item
              label="Tipo sanguíneo"
              value={parq.blood_type}
            />
            <Item
              label="Plano de saúde"
              value={parq.health_plan}
            />
            <Item
              label="Contato de emergência"
              value={parq.emergency_contact}
            />
            <Item
              label="Telefone de emergência"
              value={parq.emergency_phone}
            />
            <Item
              label="Restrição médica"
              value={parq.medical_restriction}
            />
          </div>

          <div className="viewer-questions">
            {questions.map((question, index) => (
              <Item
                key={question}
                label={question}
                value={parq[`q${index + 1}`]}
              />
            ))}
          </div>
        </section>
      )}

      {tab === "profile" && (
        <section className="profile-card">
          <h2>Dados pessoais e de treino</h2>

          <div className="viewer-grid">
            <Item
              label="Nome"
              value={personal.name}
            />
            <Item
              label="E-mail"
              value={personal.email}
            />
            <Item
              label="Celular"
              value={personal.phone}
            />
            <Item
              label="Objetivo inicial"
              value={personal.goal}
            />
            <Item
              label="Sexo"
              value={personal.sex}
            />
            <Item
              label="Nascimento"
              value={personal.birth_date}
            />
            <Item
              label="Cidade / UF"
              value={[
                personal.city,
                personal.state,
              ].filter(Boolean).join(" / ")}
            />
            <Item
              label="Profissão"
              value={personal.profession}
            />
            <Item
              label="Dias disponíveis"
              value={(training.days || []).join(", ")}
            />
            <Item
              label="Horário preferido"
              value={training.preferred_time}
            />
            <Item
              label="Local"
              value={training.location}
            />
            <Item
              label="Modalidade"
              value={training.modality}
            />
          </div>
        </section>
      )}
    </main>
  );
}
