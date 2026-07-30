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


function activityLoad(activity) {
  const suppliedLoad = Number(
    activity?.training_load
    || activity?.relative_effort
    || activity?.suffer_score
    || 0,
  );

  if (suppliedLoad > 0) return suppliedLoad;

  const minutes = activitySeconds(activity) / 60;
  const perceivedEffort = Number(
    activity?.perceived_exertion
    || activity?.rpe
    || activity?.feedback?.perceived_exertion
    || 1,
  );

  return minutes * Math.min(10, Math.max(1, perceivedEffort));
}


function dateKey(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");

  return `${year}-${month}-${day}`;
}


function buildLoadSeries(activities, days = 90) {
  const today = new Date();
  today.setHours(12, 0, 0, 0);

  const start = new Date(today);
  start.setDate(start.getDate() - days + 1);

  const dailyLoads = activities.reduce((result, activity) => {
    const date = activityStartDate(activity);

    if (!date) return result;

    const key = dateKey(date);
    result[key] = (result[key] || 0) + activityLoad(activity);
    return result;
  }, {});

  const series = [];
  let ctl = 0;
  let atl = 0;

  for (let index = 0; index < days; index += 1) {
    const date = new Date(start);
    date.setDate(start.getDate() + index);

    const load = dailyLoads[dateKey(date)] || 0;

    ctl += (load - ctl) / 42;
    atl += (load - atl) / 7;

    series.push({
      date,
      load,
      ctl,
      atl,
      tsb: ctl - atl,
    });
  }

  return series;
}


function linePath(values, width, height, minValue, maxValue) {
  const range = Math.max(1, maxValue - minValue);

  return values.map((value, index) => {
    const x = values.length === 1
      ? width / 2
      : (index / (values.length - 1)) * width;
    const y = height
      - ((value - minValue) / range) * height;

    return `${index === 0 ? "M" : "L"} ${x.toFixed(2)} ${y.toFixed(2)}`;
  }).join(" ");
}


function formInterpretation(value) {
  if (value <= -25) {
    return {
      tone: "high-fatigue",
      title: "Fadiga elevada",
      description:
        "A carga aguda está muito acima da carga crônica. "
        + "Considere recuperação e percepção do atleta antes "
        + "de aumentar a intensidade.",
    };
  }

  if (value < -10) {
    return {
      tone: "productive",
      title: "Carga produtiva",
      description:
        "Há fadiga acumulada compatível com um bloco de carga. "
        + "A resposta individual e a recuperação devem orientar "
        + "a continuidade.",
    };
  }

  if (value <= 10) {
    return {
      tone: "balanced",
      title: "Estado equilibrado",
      description:
        "Fitness e fadiga estão próximos. O atleta tende a estar "
        + "em uma faixa neutra de treinamento.",
    };
  }

  if (value <= 25) {
    return {
      tone: "fresh",
      title: "Boa recuperação",
      description:
        "A fadiga aguda está abaixo do fitness. Pode representar "
        + "recuperação ou redução planejada de carga.",
    };
  }

  return {
    tone: "detraining",
    title: "Carga recente baixa",
    description:
      "A forma está muito positiva porque a fadiga caiu bastante. "
      + "Verifique se isso corresponde a polimento, pausa ou perda "
      + "de continuidade.",
  };
}


function TrainingLoadChart({ series }) {
  const [activeIndex, setActiveIndex] = useState(
    Math.max(0, series.length - 1),
  );
  const width = 920;
  const height = 320;
  const padding = 36;
  const chartWidth = width - padding * 2;
  const chartHeight = height - padding * 2;

  const allValues = series.flatMap(
    (item) => [item.ctl, item.atl, item.tsb],
  );
  const minValue = Math.min(0, ...allValues);
  const maxValue = Math.max(1, ...allValues);

  const ctlPath = linePath(
    series.map((item) => item.ctl),
    chartWidth,
    chartHeight,
    minValue,
    maxValue,
  );
  const atlPath = linePath(
    series.map((item) => item.atl),
    chartWidth,
    chartHeight,
    minValue,
    maxValue,
  );
  const tsbPath = linePath(
    series.map((item) => item.tsb),
    chartWidth,
    chartHeight,
    minValue,
    maxValue,
  );

  const zeroY = padding + chartHeight
    - ((0 - minValue) / Math.max(1, maxValue - minValue))
    * chartHeight;

  const active = series[activeIndex] || series[series.length - 1];
  const activeX = series.length === 1
    ? padding + chartWidth / 2
    : padding + (activeIndex / (series.length - 1)) * chartWidth;

  const pointY = (value) => (
    padding + chartHeight
    - ((value - minValue) / Math.max(1, maxValue - minValue))
    * chartHeight
  );

  const dateTicks = [0, 30, 60, series.length - 1]
    .filter(
      (index, position, values) =>
        index >= 0
        && index < series.length
        && values.indexOf(index) === position,
    );

  return (
    <div className="student-load-chart">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label="Gráfico interativo de fitness, fadiga e forma"
        onMouseLeave={() =>
          setActiveIndex(Math.max(0, series.length - 1))
        }
      >
        <line
          className="student-load-zero"
          x1={padding}
          x2={width - padding}
          y1={zeroY}
          y2={zeroY}
        />

        {dateTicks.map((index) => {
          const x = series.length === 1
            ? padding + chartWidth / 2
            : padding + (index / (series.length - 1)) * chartWidth;

          return (
            <g key={series[index].date.toISOString()}>
              <line
                className="student-load-grid"
                x1={x}
                x2={x}
                y1={padding}
                y2={height - padding}
              />
              <text
                className="student-load-axis-label"
                x={x}
                y={height - 8}
                textAnchor={
                  index === 0
                    ? "start"
                    : index === series.length - 1
                      ? "end"
                      : "middle"
                }
              >
                {new Intl.DateTimeFormat("pt-BR", {
                  day: "2-digit",
                  month: "short",
                }).format(series[index].date)}
              </text>
            </g>
          );
        })}

        <g transform={`translate(${padding} ${padding})`}>
          <path
            className="student-load-line ctl"
            d={ctlPath}
          />
          <path
            className="student-load-line atl"
            d={atlPath}
          />
          <path
            className="student-load-line tsb"
            d={tsbPath}
          />
        </g>

        {series.map((item, index) => {
          const x = series.length === 1
            ? padding + chartWidth / 2
            : padding + (index / (series.length - 1)) * chartWidth;

          return (
            <rect
              className="student-load-hit-area"
              key={item.date.toISOString()}
              x={x - Math.max(3, chartWidth / series.length / 2)}
              y={padding}
              width={Math.max(6, chartWidth / series.length)}
              height={chartHeight}
              onMouseEnter={() => setActiveIndex(index)}
              onFocus={() => setActiveIndex(index)}
              tabIndex={index % 7 === 0 || index === series.length - 1
                ? 0
                : -1}
            >
              <title>
                {new Intl.DateTimeFormat("pt-BR").format(item.date)}
              </title>
            </rect>
          );
        })}

        {active && (
          <>
            <line
              className="student-load-active-line"
              x1={activeX}
              x2={activeX}
              y1={padding}
              y2={height - padding}
            />

            <circle
              className="student-load-point ctl"
              cx={activeX}
              cy={pointY(active.ctl)}
              r="5"
            />
            <circle
              className="student-load-point atl"
              cx={activeX}
              cy={pointY(active.atl)}
              r="5"
            />
            <circle
              className="student-load-point tsb"
              cx={activeX}
              cy={pointY(active.tsb)}
              r="5"
            />
          </>
        )}
      </svg>

      {active && (
        <div className="student-load-tooltip" aria-live="polite">
          <strong>
            {new Intl.DateTimeFormat("pt-BR", {
              day: "2-digit",
              month: "long",
              year: "numeric",
            }).format(active.date)}
          </strong>

          <span>
            Carga diária: {active.load.toFixed(1)}
          </span>
          <span>
            Fitness: {active.ctl.toFixed(1)}
          </span>
          <span>
            Fadiga: {active.atl.toFixed(1)}
          </span>
          <span>
            Forma: {active.tsb > 0 ? "+" : ""}
            {active.tsb.toFixed(1)}
          </span>
        </div>
      )}
    </div>
  );
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

  const loadSeries = useMemo(
    () => buildLoadSeries(activities, 90),
    [activities],
  );

  const loadSummary = useMemo(() => {
    const latest = loadSeries[loadSeries.length - 1] || {
      ctl: 0,
      atl: 0,
      tsb: 0,
    };

    return {
      fitness: latest.ctl,
      fatigue: latest.atl,
      form: latest.tsb,
      interpretation: formInterpretation(latest.tsb),
    };
  }, [loadSeries]);

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

          <section className="student-training-load-section">
            <header>
              <div>
                <span>Carga de treinamento</span>
                <h3>Fitness, fadiga e forma</h3>
                <p>
                  Tendência estimada dos últimos 90 dias. A carga usa
                  o valor da atividade quando disponível e duração × PSE
                  como alternativa.
                </p>
              </div>
            </header>

            <section className="student-load-current-metrics">
              <article>
                <span>Fitness · CTL</span>
                <strong>{loadSummary.fitness.toFixed(1)}</strong>
                <small>carga crônica de 42 dias</small>
              </article>

              <article>
                <span>Fadiga · ATL</span>
                <strong>{loadSummary.fatigue.toFixed(1)}</strong>
                <small>carga aguda de 7 dias</small>
              </article>

              <article>
                <span>Forma · TSB</span>
                <strong>
                  {loadSummary.form > 0 ? "+" : ""}
                  {loadSummary.form.toFixed(1)}
                </strong>
                <small>fitness menos fadiga</small>
              </article>
            </section>

            <article
              className={`student-form-interpretation ${
                loadSummary.interpretation.tone
              }`}
            >
              <div>
                <span>Leitura da forma atual</span>
                <strong>
                  {loadSummary.interpretation.title}
                </strong>
              </div>
              <p>
                {loadSummary.interpretation.description}
              </p>
            </article>

            <div className="student-load-legend">
              <span className="ctl">Fitness · CTL</span>
              <span className="atl">Fadiga · ATL</span>
              <span className="tsb">Forma · TSB</span>
            </div>

            <TrainingLoadChart series={loadSeries} />

            <p className="student-load-disclaimer">
              Estes indicadores são estimativas de acompanhamento e não
              substituem avaliação profissional, recuperação percebida
              ou análise clínica.
            </p>
          </section>
        </>
      )}
    </section>
  );
}
