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
  void analytics;
  void analyticsError;

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
