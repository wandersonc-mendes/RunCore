import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { listStravaActivities } from "../api";
import { studentPaths } from "../router/paths";
import { activityStartDate } from "../utils/activityDate";
import "./StudentEvolutionPage.css";


function km(value) {
  const number = Number(value || 0);
  return number > 1000 ? number / 1000 : number;
}


function activitySeconds(activity) {
  return Number(
    activity?.moving_time
    || activity?.elapsed_time
    || 0,
  );
}


function isRunning(activity) {
  const type = String(
    activity?.sport_type
    || activity?.type
    || "",
  ).toLowerCase();

  return type.includes("run") || type.includes("corrida");
}


function formatPace(seconds) {
  if (!seconds || !Number.isFinite(seconds)) return "—";

  const minutes = Math.floor(seconds / 60);
  const remaining = Math.round(seconds % 60);

  return `${minutes}:${String(remaining).padStart(2, "0")}/km`;
}


function periodMetrics(activities) {
  const totalDistance = activities.reduce(
    (total, activity) =>
      total + km(
        activity.distance
        || activity.distance_meters,
      ),
    0,
  );

  const totalSeconds = activities.reduce(
    (total, activity) =>
      total + activitySeconds(activity),
    0,
  );

  return {
    activities: activities.length,
    totalDistance,
    averagePace:
      totalDistance > 0
        ? totalSeconds / totalDistance
        : 0,
  };
}


function percentChange(current, previous) {
  if (!previous) return current ? 100 : 0;
  return ((current - previous) / previous) * 100;
}


function comparisonLabel(value, inverse = false) {
  if (!Number.isFinite(value) || Math.abs(value) < 0.5) {
    return "estável";
  }

  const improved = inverse ? value < 0 : value > 0;
  const magnitude = Math.abs(value).toFixed(0);

  return `${improved ? "melhora" : "queda"} de ${magnitude}%`;
}


export default function StudentEvolutionPage() {
  const navigate = useNavigate();
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function loadActivities() {
      setLoading(true);
      setError("");

      try {
        const result = await listStravaActivities();

        if (active) {
          setActivities(
            Array.isArray(result)
              ? result
              : result?.activities || [],
          );
        }
      } catch (err) {
        if (active) {
          setError(
            err?.message
            || "Não foi possível carregar sua evolução.",
          );
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    loadActivities();

    return () => {
      active = false;
    };
  }, []);

  const evolution = useMemo(() => {
    const now = new Date();
    const currentStart = new Date(now);
    const previousStart = new Date(now);

    currentStart.setDate(currentStart.getDate() - 30);
    previousStart.setDate(previousStart.getDate() - 60);

    const source = activities.filter(isRunning);
    const runningActivities = source.length ? source : activities;

    const currentActivities = runningActivities.filter((activity) => {
      const date = activityStartDate(activity);
      return date && date >= currentStart && date <= now;
    });

    const previousActivities = runningActivities.filter((activity) => {
      const date = activityStartDate(activity);
      return date && date >= previousStart && date < currentStart;
    });

    const current = periodMetrics(currentActivities);
    const previous = periodMetrics(previousActivities);

    return {
      current,
      previous,
      distanceChange: percentChange(
        current.totalDistance,
        previous.totalDistance,
      ),
      frequencyChange: percentChange(
        current.activities,
        previous.activities,
      ),
      paceChange: percentChange(
        current.averagePace,
        previous.averagePace,
      ),
    };
  }, [activities]);

  return (
    <section className="student-evolution-page">
      <header className="student-evolution-heading">
        <div>
          <p className="eyebrow">EVOLUÇÃO</p>
          <h2>Tendências do seu treinamento</h2>
          <p className="muted">
            Compare os últimos 30 dias com o período anterior.
            Detalhes individuais permanecem em Atividades.
          </p>
        </div>

        <button
          type="button"
          className="btn-ghost"
          onClick={() => navigate(studentPaths.activities)}
        >
          Abrir Atividades
        </button>
      </header>

      {error && <div className="alert">{error}</div>}

      {loading ? (
        <p className="muted">
          Carregando sua evolução...
        </p>
      ) : evolution.current.activities === 0
        && evolution.previous.activities === 0 ? (
        <section className="student-evolution-empty">
          <h3>Dados insuficientes para análise</h3>
          <p>
            Sincronize atividades para que o RunCore possa comparar
            volume, frequência e ritmo entre períodos.
          </p>
        </section>
      ) : (
        <>
          <section className="student-evolution-periods">
            <article>
              <span>Período analisado</span>
              <strong>Últimos 30 dias</strong>
              <small>
                comparação com os 30 dias anteriores
              </small>
            </article>

            <article>
              <span>Volume atual</span>
              <strong>
                {evolution.current.totalDistance.toFixed(1)} km
              </strong>
              <small>
                {comparisonLabel(evolution.distanceChange)}
              </small>
            </article>

            <article>
              <span>Frequência atual</span>
              <strong>
                {evolution.current.activities} atividades
              </strong>
              <small>
                {comparisonLabel(evolution.frequencyChange)}
              </small>
            </article>

            <article>
              <span>Ritmo médio atual</span>
              <strong>
                {formatPace(evolution.current.averagePace)}
              </strong>
              <small>
                {comparisonLabel(evolution.paceChange, true)}
              </small>
            </article>
          </section>

          <section className="student-evolution-comparison">
            <header>
              <div>
                <span>Comparação longitudinal</span>
                <h3>Período atual x período anterior</h3>
              </div>
            </header>

            <div className="student-evolution-comparison-grid">
              <article>
                <span>Distância</span>
                <div>
                  <strong>
                    {evolution.current.totalDistance.toFixed(1)} km
                  </strong>
                  <small>atual</small>
                </div>
                <div>
                  <strong>
                    {evolution.previous.totalDistance.toFixed(1)} km
                  </strong>
                  <small>anterior</small>
                </div>
              </article>

              <article>
                <span>Atividades</span>
                <div>
                  <strong>{evolution.current.activities}</strong>
                  <small>atual</small>
                </div>
                <div>
                  <strong>{evolution.previous.activities}</strong>
                  <small>anterior</small>
                </div>
              </article>

              <article>
                <span>Ritmo médio</span>
                <div>
                  <strong>
                    {formatPace(evolution.current.averagePace)}
                  </strong>
                  <small>atual</small>
                </div>
                <div>
                  <strong>
                    {formatPace(evolution.previous.averagePace)}
                  </strong>
                  <small>anterior</small>
                </div>
              </article>
            </div>
          </section>

          <section className="student-evolution-next-step">
            <div>
              <span>Próxima etapa</span>
              <h3>Carga, fadiga e forma</h3>
              <p>
                Os indicadores CTL, ATL e TSB serão incorporados
                nesta página usando atividades e percepção de esforço.
              </p>
            </div>
          </section>
        </>
      )}
    </section>
  );
}
