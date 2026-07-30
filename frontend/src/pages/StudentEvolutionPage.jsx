import { useEffect, useMemo, useState } from "react";

import { listStravaActivities } from "../api";
import "./StudentEvolutionPage.css";


import {
  activityLocalDateKey,
  activityStartDate,
  activityStartValue,
} from "../utils/activityDate";
function km(value) {
  const number = Number(value || 0);

  if (number > 1000) {
    return number / 1000;
  }

  return number;
}


function formatDate(value) {
  if (!value) return "Sem data";

  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(new Date(value));
}


export default function StudentEvolutionPage() {
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

  const summary = useMemo(() => {
    const runningActivities = activities.filter(
      (activity) => {
        const type = String(
          activity.sport_type
          || activity.type
          || "",
        ).toLowerCase();

        return type.includes("run")
          || type.includes("corrida");
      },
    );

    const source = runningActivities.length
      ? runningActivities
      : activities;

    const totalDistance = source.reduce(
      (total, activity) =>
        total + km(
          activity.distance
          || activity.distance_meters,
        ),
      0,
    );

    const totalSeconds = source.reduce(
      (total, activity) =>
        total + Number(
          activity.moving_time
          || activity.elapsed_time
          || 0,
        ),
      0,
    );

    const averagePace = totalDistance > 0
      ? totalSeconds / totalDistance
      : 0;

    return {
      source,
      totalDistance,
      totalSeconds,
      averagePace,
    };
  }, [activities]);

  function formatPace(seconds) {
    if (!seconds) return "—";

    const minutes = Math.floor(seconds / 60);
    const remaining = Math.round(seconds % 60);

    return `${minutes}:${String(remaining).padStart(2, "0")}/km`;
  }

  return (
    <section className="student-evolution-page">
      <header className="student-evolution-heading">
        <div>
          <p className="eyebrow">EVOLUÇÃO</p>
          <h2>Sua evolução</h2>
          <p className="muted">
            Resumo das atividades sincronizadas
            com o Strava.
          </p>
        </div>
      </header>

      {error && <div className="alert">{error}</div>}

      {loading ? (
        <p className="muted">
          Carregando sua evolução...
        </p>
      ) : summary.source.length === 0 ? (
        <section className="student-evolution-empty">
          <h3>Nenhuma atividade sincronizada</h3>
          <p>
            Conecte o Strava e sincronize suas atividades
            para acompanhar a evolução.
          </p>
        </section>
      ) : (
        <>
          <section className="student-evolution-metrics">
            <article>
              <span>Atividades</span>
              <strong>{summary.source.length}</strong>
            </article>

            <article>
              <span>Distância total</span>
              <strong>
                {summary.totalDistance.toFixed(1)} km
              </strong>
            </article>

            <article>
              <span>Ritmo médio</span>
              <strong>
                {formatPace(summary.averagePace)}
              </strong>
            </article>
          </section>

          <section className="student-evolution-list">
            <header>
              <div>
                <h3>Atividades recentes</h3>
                <p>
                  Últimos registros recebidos
                  da integração.
                </p>
              </div>
            </header>

            <div>
              {summary.source
                .slice(0, 10)
                .map((activity) => (
                  <article key={activity.id}>
                    <div>
                      <strong>
                        {activity.name
                          || "Atividade de corrida"}
                      </strong>
                      <span>
                        {formatDate(
                          activityStartValue(activity),
                        )}
                      </span>
                    </div>

                    <div className="student-evolution-activity-data">
                      <span>
                        {km(
                          activity.distance
                          || activity.distance_meters,
                        ).toFixed(2)} km
                      </span>

                      <span>
                        {formatPace(
                          km(
                            activity.distance
                            || activity.distance_meters,
                          ) > 0
                            ? Number(
                                activity.moving_time
                                || activity.elapsed_time
                                || 0,
                              )
                              / km(
                                activity.distance
                                || activity.distance_meters,
                              )
                            : 0,
                        )}
                      </span>
                    </div>
                  </article>
                ))}
            </div>
          </section>
        </>
      )}
    </section>
  );
}
