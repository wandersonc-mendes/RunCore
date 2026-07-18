import { useEffect, useState } from "react";
import {
  getAthlete,
  listEvaluations,
  createEvaluation,
  deleteEvaluation,
} from "./api";

const TEST_TYPES = [
  "Nenhum",
  "1600 m",
  "Cooper",
  "5 km",
  "10 km",
  "21,1 km",
  "42,2 km",
];

const emptyForm = {
  weight: "",
  height: "",
  max_hr: "",
  resting_hr: "",
  test_type: "5 km",
  distance: "",
  minutes: "",
  seconds: "",
};

function formatTime(totalSeconds) {
  if (!totalSeconds) return "—";
  const m = Math.floor(totalSeconds / 60);
  const s = Math.round(totalSeconds % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
}

function formatDate(isoString) {
  return new Date(isoString).toLocaleDateString("pt-BR");
}

export default function AthleteProfile({ athleteId, onBack }) {
  const [athlete, setAthlete] = useState(null);
  const [evaluations, setEvaluations] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [athleteData, evaluationsData] = await Promise.all([
        getAthlete(athleteId),
        listEvaluations(athleteId),
      ]);
      setAthlete(athleteData);
      setEvaluations(evaluationsData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [athleteId]);

  async function handleCreate(e) {
    e.preventDefault();
    try {
      const timeSeconds =
        (Number(form.minutes) || 0) * 60 + (Number(form.seconds) || 0);

      await createEvaluation(athleteId, {
        weight: Number(form.weight) || 0,
        height: Number(form.height) || 0,
        max_hr: Number(form.max_hr) || 0,
        resting_hr: Number(form.resting_hr) || 0,
        test_type: form.test_type,
        distance: Number(form.distance) || 0,
        time_seconds: timeSeconds,
      });

      setForm(emptyForm);
      setShowForm(false);
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleDelete(id) {
    if (!window.confirm("Remover esta avaliação?")) return;
    try {
      await deleteEvaluation(id);
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  if (loading) return <p className="muted">Carregando...</p>;
  if (!athlete) return <p className="muted">Atleta não encontrado.</p>;

  const latest = evaluations[0];

  return (
    <div>
      <button className="btn-ghost back-btn" onClick={onBack}>
        ← Voltar
      </button>

      <div className="card profile-header">
        <div>
          <h2 className="profile-name">{athlete.name}</h2>
          <p className="muted">
            {athlete.phone}
            {athlete.phone && athlete.email ? " · " : ""}
            {athlete.email}
          </p>
          <p className="muted">Objetivo: {athlete.goal || "—"}</p>
        </div>
        <span className={`badge ${athlete.active ? "badge-active" : "badge-inactive"}`}>
          {athlete.active ? "Ativo" : "Inativo"}
        </span>
      </div>

      {latest && (
        <div className="card vdot-card">
          <span className="muted">VDOT atual</span>
          <strong className="vdot-value">{latest.vdot}</strong>
          <span className="muted">
            ({latest.test_type}, {formatDate(latest.created_at)})
          </span>
        </div>
      )}

      <div className="section-row">
        <h3>Avaliações</h3>
        <button className="btn-primary" onClick={() => setShowForm((v) => !v)}>
          {showForm ? "Cancelar" : "+ Nova avaliação"}
        </button>
      </div>

      {showForm && (
        <form className="card new-athlete-form" onSubmit={handleCreate}>
          <div className="form-grid">
            <label>
              Peso (kg)
              <input
                type="number"
                step="0.1"
                value={form.weight}
                onChange={(e) => setForm({ ...form, weight: e.target.value })}
              />
            </label>
            <label>
              Altura (cm)
              <input
                type="number"
                value={form.height}
                onChange={(e) => setForm({ ...form, height: e.target.value })}
              />
            </label>
            <label>
              FC máxima
              <input
                type="number"
                value={form.max_hr}
                onChange={(e) => setForm({ ...form, max_hr: e.target.value })}
              />
            </label>
            <label>
              FC repouso
              <input
                type="number"
                value={form.resting_hr}
                onChange={(e) => setForm({ ...form, resting_hr: e.target.value })}
              />
            </label>
            <label>
              Tipo de teste
              <select
                value={form.test_type}
                onChange={(e) => setForm({ ...form, test_type: e.target.value })}
              >
                {TEST_TYPES.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </label>
            <label>
              Distância (m)
              <input
                type="number"
                value={form.distance}
                onChange={(e) => setForm({ ...form, distance: e.target.value })}
              />
            </label>
            <label>
              Tempo — minutos
              <input
                type="number"
                value={form.minutes}
                onChange={(e) => setForm({ ...form, minutes: e.target.value })}
              />
            </label>
            <label>
              Tempo — segundos
              <input
                type="number"
                value={form.seconds}
                onChange={(e) => setForm({ ...form, seconds: e.target.value })}
              />
            </label>
          </div>
          <button type="submit" className="btn-primary">Salvar avaliação</button>
        </form>
      )}

      {error && <div className="alert">{error}</div>}

      {evaluations.length === 0 ? (
        <div className="empty-state">
          <p>Nenhuma avaliação registrada ainda.</p>
        </div>
      ) : (
        <table className="athletes-table">
          <thead>
            <tr>
              <th>Data</th>
              <th>Tipo</th>
              <th>Distância</th>
              <th>Tempo</th>
              <th>VDOT</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {evaluations.map((ev) => (
              <tr key={ev.id}>
                <td>{formatDate(ev.created_at)}</td>
                <td>{ev.test_type}</td>
                <td>{ev.distance ? `${ev.distance} m` : "—"}</td>
                <td>{formatTime(ev.time_seconds)}</td>
                <td className="name-cell">{ev.vdot || "—"}</td>
                <td>
                  <button className="btn-link-danger" onClick={() => handleDelete(ev.id)}>
                    Remover
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
