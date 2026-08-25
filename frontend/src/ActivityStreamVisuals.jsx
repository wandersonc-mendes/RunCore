const WIDTH = 720;
const HEIGHT = 210;
const PADDING = 24;

function sample(items, limit = 300) {
  if (items.length <= limit) return items;
  const step = (items.length - 1) / (limit - 1);
  return Array.from(
    { length: limit },
    (_, index) => items[Math.round(index * step)],
  );
}

function chartPoints(points, valueForPoint) {
  const values = sample(points)
    .map((point) => ({
      x: Number(point.distance ?? point.time),
      y: Number(valueForPoint(point)),
    }))
    .filter((point) => Number.isFinite(point.x) && Number.isFinite(point.y));

  if (values.length < 2) return null;
  const xValues = values.map((point) => point.x);
  const yValues = values.map((point) => point.y);
  const minX = Math.min(...xValues);
  const maxX = Math.max(...xValues);
  const minY = Math.min(...yValues);
  const maxY = Math.max(...yValues);
  const scaleX = (value) => PADDING + (
    ((value - minX) / (maxX - minX || 1)) * (WIDTH - PADDING * 2)
  );
  const scaleY = (value) => HEIGHT - PADDING - (
    ((value - minY) / (maxY - minY || 1)) * (HEIGHT - PADDING * 2)
  );

  return {
    path: values.map(
      (point, index) => `${index ? "L" : "M"} ${scaleX(point.x)} ${scaleY(point.y)}`,
    ).join(" "),
    min: minY,
    max: maxY,
  };
}

function formatPaceSeconds(value) {
  if (!Number.isFinite(value)) return "—";
  const minutes = Math.floor(value / 60);
  const seconds = Math.round(value % 60);
  return `${minutes}:${String(seconds).padStart(2, "0")}/km`;
}

function StreamChart({ title, points, valueForPoint, formatValue }) {
  const chart = chartPoints(points, valueForPoint);
  if (!chart) return null;

  return (
    <article className="activity-stream-card">
      <header>
        <h4>{title}</h4>
        <span>{formatValue(chart.min)} – {formatValue(chart.max)}</span>
      </header>
      <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img" aria-label={`Gráfico de ${title.toLowerCase()}`}>
        <line x1={PADDING} y1={HEIGHT - PADDING} x2={WIDTH - PADDING} y2={HEIGHT - PADDING} />
        <path d={chart.path} />
      </svg>
    </article>
  );
}

function RouteMap({ points }) {
  const coordinates = sample(points
    .map((point) => point.latlng)
    .filter((value) => (
      Array.isArray(value)
      && Number.isFinite(Number(value[0]))
      && Number.isFinite(Number(value[1]))
    )));
  if (coordinates.length < 2) return null;

  const latitudes = coordinates.map((point) => Number(point[0]));
  const longitudes = coordinates.map((point) => Number(point[1]));
  const minLatitude = Math.min(...latitudes);
  const maxLatitude = Math.max(...latitudes);
  const minLongitude = Math.min(...longitudes);
  const maxLongitude = Math.max(...longitudes);
  const path = coordinates.map((point, index) => {
    const x = PADDING + (
      ((Number(point[1]) - minLongitude) / (maxLongitude - minLongitude || 1))
      * (WIDTH - PADDING * 2)
    );
    const y = HEIGHT - PADDING - (
      ((Number(point[0]) - minLatitude) / (maxLatitude - minLatitude || 1))
      * (HEIGHT - PADDING * 2)
    );
    return `${index ? "L" : "M"} ${x} ${y}`;
  }).join(" ");

  return (
    <article className="activity-stream-card activity-route-map">
      <header><h4>Percurso GPS</h4><span>Traçado registrado</span></header>
      <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img" aria-label="Mapa simplificado do percurso GPS">
        <path d={path} />
      </svg>
    </article>
  );
}

export default function ActivityStreamVisuals({ streams }) {
  const points = streams?.points || [];
  const available = streams?.available || {};
  if (!points.length) {
    return <p className="muted">O Strava não disponibilizou séries para esta atividade.</p>;
  }

  return (
    <>
      <div className="activity-stream-grid">
        {available.velocity_smooth && (
          <StreamChart
            title="Ritmo"
            points={points}
            valueForPoint={(point) => (
              Number(point.velocity_smooth) > 0
                ? 1000 / Number(point.velocity_smooth)
                : Number.NaN
            )}
            formatValue={formatPaceSeconds}
          />
        )}
        {available.altitude && (
          <StreamChart title="Elevação" points={points} valueForPoint={(point) => point.altitude} formatValue={(value) => `${Math.round(value)} m`} />
        )}
        {available.heartrate && (
          <StreamChart title="Frequência cardíaca" points={points} valueForPoint={(point) => point.heartrate} formatValue={(value) => `${Math.round(value)} bpm`} />
        )}
        {available.cadence && (
          <StreamChart title="Cadência" points={points} valueForPoint={(point) => point.cadence} formatValue={(value) => `${Math.round(value)} rpm`} />
        )}
        {available.latlng && <RouteMap points={points} />}
      </div>
      {!available.heartrate && !available.cadence && (
        <p className="muted activity-stream-note">
          Esta atividade tem dados úteis de celular; FC e cadência não foram registradas e foram omitidas.
        </p>
      )}
    </>
  );
}
