import { useEffect, useMemo, useState } from "react";

import { listStudentEvaluations } from "../api";


function formatDuration(seconds) {
  const value = Math.max(0, Math.round(Number(seconds || 0)));
  const hours = Math.floor(value / 3600);
  const minutes = Math.floor((value % 3600) / 60);
  const remainder = value % 60;

  if (hours > 0) {
    return [hours, minutes, remainder]
      .map((part) => String(part).padStart(2, "0"))
      .join(":");
  }

  return [minutes, remainder]
    .map((part) => String(part).padStart(2, "0"))
    .join(":");
}


function formatPace(seconds, distanceMeters) {
  const distanceKm = Number(distanceMeters || 0) / 1000;

  if (!seconds || distanceKm <= 0) return "—";

  const pace = Number(seconds) / distanceKm;
  const minutes = Math.floor(pace / 60);
  const remainder = Math.round(pace % 60);

  return `${minutes}:${String(remainder).padStart(2, "0")}/km`;
}


function evaluationDate(value) {
  if (!value) return null;

  const date = new Date(`${value}T12:00:00`);

  return Number.isNaN(date.getTime()) ? null : date;
}


function formatDate(value) {
  const date = evaluationDate(value);

  return date
    ? new Intl.DateTimeFormat("pt-BR", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    }).format(date)
    : "Data não informada";
}


function chartPoints(items, width, height, padding) {
  if (!items.length) return [];

  const times = items.map((item) => Number(item.time_seconds || 0));
  const minTime = Math.min(...times);
  const maxTime = Math.max(...times);
  const range = Math.max(1, maxTime - minTime);
  const chartWidth = width - padding * 2;
  const chartHeight = height - padding * 2;

  return items.map((item, index) => {
    const x = items.length === 1
      ? width / 2
      : padding + (index / (items.length - 1)) * chartWidth;
    const normalized = (
      Number(item.time_seconds || 0) - minTime
    ) / range;
    const y = padding + normalized * chartHeight;

    return {
      ...item,
      x,
      y,
    };
  });
}


function TestChart({ items }) {
  const width = 880;
  const height = 270;
  const padding = 38;
  const points = chartPoints(items, width, height, padding);
  const path = points.map(
    (point, index) =>
      `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`,
  ).join(" ");

  return (
    <div className="student-test-chart">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label="Evolução cronológica do tempo no teste selecionado"
      >
        <line
          className="student-test-grid"
          x1={padding}
          x2={width - padding}
          y1={padding}
          y2={padding}
        />
        <line
          className="student-test-grid"
          x1={padding}
          x2={width - padding}
          y1={height / 2}
          y2={height / 2}
        />
        <line
          className="student-test-grid"
          x1={padding}
          x2={width - padding}
          y1={height - padding}
          y2={height - padding}
        />

        {points.length > 1 && (
          <path className="student-test-line" d={path} />
        )}

        {points.map((point, index) => (
          <g key={point.id || `${point.test_date}-${index}`}>
            <circle
              className="student-test-point"
              cx={point.x}
              cy={point.y}
              r="6"
            />
            <text
              className="student-test-value"
              x={point.x}
              y={Math.max(18, point.y - 13)}
              textAnchor="middle"
            >
              {formatDuration(point.time_seconds)}
            </text>
            <text
              className="student-test-date"
              x={point.x}
              y={height - 9}
              textAnchor={
                index === 0
                  ? "start"
                  : index === points.length - 1
                    ? "end"
                    : "middle"
              }
            >
              {new Intl.DateTimeFormat("pt-BR", {
                month: "short",
                year: "2-digit",
              }).format(evaluationDate(point.test_date))}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
}


export default function StudentTestEvolution() {
  const [evaluations, setEvaluations] = useState([]);
  const [selectedType, setSelectedType] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      setError("");

      try {
        const result = await listStudentEvaluations();
        const items = Array.isArray(result) ? result : [];

        if (active) {
          setEvaluations(items);
        }
      } catch (err) {
        if (active) {
          setError(
            err?.message
            || "Não foi possível carregar o histórico de testes.",
          );
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    load();

    return () => {
      active = false;
    };
  }, []);

  const groups = useMemo(() => {
    return evaluations.reduce((result, evaluation) => {
      const type = evaluation.test_type || "Teste";

      if (!result[type]) {
        result[type] = [];
      }

      result[type].push(evaluation);
      return result;
    }, {});
  }, [evaluations]);

  const types = useMemo(
    () => Object.keys(groups).sort((a, b) => a.localeCompare(b, "pt-BR")),
    [groups],
  );

  useEffect(() => {
    if (!selectedType && types.length) {
      setSelectedType(types[0]);
    } else if (
      selectedType
      && !types.includes(selectedType)
      && types.length
    ) {
      setSelectedType(types[0]);
    }
  }, [selectedType, types]);

  const selected = useMemo(() => {
    return [...(groups[selectedType] || [])].sort((a, b) => {
      const dateA = evaluationDate(a.test_date)?.getTime() || 0;
      const dateB = evaluationDate(b.test_date)?.getTime() || 0;
      return dateA - dateB;
    });
  }, [groups, selectedType]);

  const best = selected.reduce((result, item) => {
    if (!result) return item;

    return Number(item.time_seconds) < Number(result.time_seconds)
      ? item
      : result;
  }, null);

  const latest = selected[selected.length - 1] || null;
  const previous = selected[selected.length - 2] || null;
  const improvement = latest && previous
    ? Number(previous.time_seconds) - Number(latest.time_seconds)
    : 0;

  return (
    <section className="student-test-evolution">
      <header>
        <div>
          <span>TESTES DE DESEMPENHO</span>
          <h3>Evolução por distância</h3>
          <p>
            Cada distância é analisada separadamente. Menor tempo e
            menor pace representam evolução.
          </p>
        </div>

        {selected.length > 0 && (
          <strong>{selected.length} teste(s)</strong>
        )}
      </header>

      {loading ? (
        <p className="muted">Carregando testes...</p>
      ) : error ? (
        <div className="alert">{error}</div>
      ) : types.length === 0 ? (
        <div className="student-test-empty">
          <strong>Nenhum teste registrado</strong>
          <p>
            Os testes cadastrados pelo treinador aparecerão aqui em
            ordem cronológica.
          </p>
        </div>
      ) : (
        <>
          <div
            className="student-test-tabs"
            role="tablist"
            aria-label="Distâncias avaliadas"
          >
            {types.map((type) => (
              <button
                key={type}
                type="button"
                role="tab"
                aria-selected={selectedType === type}
                className={selectedType === type ? "active" : ""}
                onClick={() => setSelectedType(type)}
              >
                {type}
              </button>
            ))}
          </div>

          <div className="student-test-summary">
            <article>
              <span>Melhor marca</span>
              <strong>
                {best ? formatDuration(best.time_seconds) : "—"}
              </strong>
              <small>
                {best
                  ? `${formatPace(
                    best.time_seconds,
                    best.distance,
                  )} · ${formatDate(best.test_date)}`
                  : "Sem resultado"}
              </small>
            </article>

            <article>
              <span>Último teste</span>
              <strong>
                {latest ? formatDuration(latest.time_seconds) : "—"}
              </strong>
              <small>
                {latest
                  ? `${formatPace(
                    latest.time_seconds,
                    latest.distance,
                  )} · ${formatDate(latest.test_date)}`
                  : "Sem resultado"}
              </small>
            </article>

            <article>
              <span>Comparação anterior</span>
              <strong>
                {!previous
                  ? "—"
                  : improvement > 0
                    ? `−${formatDuration(improvement)}`
                    : improvement < 0
                      ? `+${formatDuration(Math.abs(improvement))}`
                      : "Estável"}
              </strong>
              <small>
                {!previous
                  ? "É necessário mais de um teste"
                  : improvement > 0
                    ? "mais rápido que o teste anterior"
                    : improvement < 0
                      ? "mais lento que o teste anterior"
                      : "mesmo tempo do teste anterior"}
              </small>
            </article>

            <article>
              <span>VDOT mais recente</span>
              <strong>
                {latest?.vdot == null
                  ? "—"
                  : Number(latest.vdot).toFixed(1)}
              </strong>
              <small>indicador calculado no cadastro do teste</small>
            </article>
          </div>

          <TestChart items={selected} />

          <div className="student-test-history">
            {selected.slice().reverse().map((item) => (
              <article key={item.id}>
                <div>
                  <span>{formatDate(item.test_date)}</span>
                  <strong>{formatDuration(item.time_seconds)}</strong>
                </div>

                <div>
                  <span>Pace médio</span>
                  <strong>
                    {formatPace(item.time_seconds, item.distance)}
                  </strong>
                </div>

                <div>
                  <span>VDOT</span>
                  <strong>
                    {item.vdot == null
                      ? "—"
                      : Number(item.vdot).toFixed(1)}
                  </strong>
                </div>

                {best?.id === item.id && (
                  <b>Melhor marca</b>
                )}
              </article>
            ))}
          </div>
        </>
      )}
    </section>
  );
}
