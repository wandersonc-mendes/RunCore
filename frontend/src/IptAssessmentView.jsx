import { useEffect, useMemo, useState } from "react";
import {
  createIptAssessment,
  deleteIptAssessment,
  listIptAssessments,
  listIptProtocols,
} from "./api";

const TEXT = {
  title: "Indice de Perfil de Treinamento",
  subtitle: "Compare a velocidade do esfor\u00e7o curto com a capacidade de sustenta\u00e7\u00e3o.",
  newAssessment: "Nova avalia\u00e7\u00e3o IPT",
  protocol: "Protocolo",
  choose: "Selecione",
  shortTime: "Tempo do esfor\u00e7o curto",
  longTime: "Tempo do esfor\u00e7o longo",
  shortDistance: "Dist\u00e2ncia no esfor\u00e7o curto (m)",
  longDistance: "Dist\u00e2ncia no esfor\u00e7o longo (m)",
  timeHint: "Informe MM:SS ou HH:MM:SS.",
  notes: "Observa\u00e7\u00f5es",
  save: "Calcular e salvar IPT",
  saving: "Calculando...",
  loading: "Carregando...",
  current: "IPT atual",
  profile: "Perfil",
  shortSpeed: "Velocidade curta",
  longSpeed: "Velocidade longa",
  interpretation: "Interpreta\u00e7\u00e3o",
  emphasis: "\u00canfase sugerida",
  history: "Hist\u00f3rico",
  empty: "Nenhuma avalia\u00e7\u00e3o IPT registrada.",
  date: "Data",
  result: "IPT",
  actions: "A\u00e7\u00f5es",
  remove: "Remover",
  removeConfirm: "Remover esta avalia\u00e7\u00e3o IPT?",
  back: "Voltar para atletas",
  evaluations: "Avalia\u00e7\u00f5es",
  training: "Planejamento",
  invalidTime: "Informe os dois tempos no formato MM:SS ou HH:MM:SS.",
};

const emptyForm = {
  protocol_id: "",
  short_result: "",
  long_result: "",
  short_time: "",
  long_time: "",
  notes: "",
};

function parseTime(value) {
  const parts = value
    .trim()
    .split(":")
    .map(Number);

  if (
    parts.length < 2 ||
    parts.length > 3 ||
    parts.some((part) => !Number.isFinite(part) || part < 0)
  ) {
    return null;
  }

  if (parts.length === 2) {
    const [minutes, seconds] = parts;

    if (seconds >= 60) return null;

    return minutes * 60 + seconds;
  }

  const [hours, minutes, seconds] = parts;

  if (minutes >= 60 || seconds >= 60) return null;

  return hours * 3600 + minutes * 60 + seconds;
}

function formatTimeInput(value) {
  const digits = value.replace(/\D/g, "").slice(0, 6);

  if (digits.length <= 2) return digits;
  if (digits.length <= 4) {
    return `${digits.slice(0, -2)}:${digits.slice(-2)}`;
  }

  return [
    digits.slice(0, -4),
    digits.slice(-4, -2),
    digits.slice(-2),
  ].join(":");
}

function formatDate(value) {
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(value));
}

function profileClass(profile) {
  return `ipt-profile ipt-profile-${profile.toLowerCase()}`;
}

export default function IptAssessmentView({
  athlete,
  onBack,
  onEvaluations,
  onTraining,
}) {
  const [protocols, setProtocols] = useState([]);
  const [assessments, setAssessments] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const selectedProtocol = useMemo(
    () =>
      protocols.find(
        (protocol) => protocol.id === Number(form.protocol_id),
      ) || null,
    [form.protocol_id, protocols],
  );

  const latest = assessments[0] || null;

  async function load() {
    setLoading(true);
    setError(null);

    try {
      const [protocolData, assessmentData] = await Promise.all([
        listIptProtocols(),
        listIptAssessments(athlete.id),
      ]);

      setProtocols(protocolData);
      setAssessments(assessmentData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [athlete.id]);

  async function handleSubmit(event) {
    event.preventDefault();

    if (!selectedProtocol || saving) return;

    let shortResult;
    let longResult;

    if (selectedProtocol.input_mode === "time") {
      shortResult = parseTime(form.short_time);
      longResult = parseTime(form.long_time);

      if (!shortResult || !longResult) {
        setError(TEXT.invalidTime);
        return;
      }
    } else {
      shortResult = Number(form.short_result);
      longResult = Number(form.long_result);
    }

    setSaving(true);
    setError(null);

    try {
      await createIptAssessment(athlete.id, {
        protocol_id: selectedProtocol.id,
        short_result: shortResult,
        long_result: longResult,
        notes: form.notes,
      });

      setForm(emptyForm);
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id) {
    if (!window.confirm(TEXT.removeConfirm)) return;

    try {
      await deleteIptAssessment(id);
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="page">
      <header className="topbar">
        <div className="brand">
          <span className="brand-logo">
            <img src="/logo-horizontal.png?v=2" alt="RunCore" />
          </span>

          <div>
            <h1>{TEXT.title}</h1>
            <p>Aluno: {athlete.name}</p>
          </div>
        </div>

        <div className="header-actions">
          <button className="btn-ghost" onClick={onEvaluations}>
            {TEXT.evaluations}
          </button>

          <button className="btn-ghost" onClick={onTraining}>
            {TEXT.training}
          </button>

          <button className="btn-ghost" onClick={onBack}>
            {TEXT.back}
          </button>
        </div>
      </header>

      <main className="content ipt-page">
        <section className="ipt-intro">
          <div>
            <p className="eyebrow">IPT</p>
            <h2>{TEXT.title}</h2>
            <p className="muted">{TEXT.subtitle}</p>
          </div>
        </section>

        {error && <div className="alert">{error}</div>}

        {latest && (
          <section className="card ipt-current-card">
            <div className="ipt-current-value">
              <span>{TEXT.current}</span>
              <strong>{latest.ipt_percentage.toFixed(2)}%</strong>
              <span className={profileClass(latest.profile)}>
                {latest.profile}
              </span>
            </div>

            <div className="ipt-speed-grid">
              <div>
                <span>{TEXT.shortSpeed}</span>
                <strong>{latest.short_speed.toFixed(2)} km/h</strong>
              </div>

              <div>
                <span>{TEXT.longSpeed}</span>
                <strong>{latest.long_speed.toFixed(2)} km/h</strong>
              </div>

              <div>
                <span>{TEXT.protocol}</span>
                <strong>{latest.protocol_name}</strong>
              </div>
            </div>

            <div className="ipt-guidance-grid">
              <div>
                <span>{TEXT.interpretation}</span>
                <p>{latest.interpretation}</p>
              </div>

              <div>
                <span>{TEXT.emphasis}</span>
                <p>{latest.emphasis}</p>
              </div>
            </div>
          </section>
        )}

        <form className="card ipt-form" onSubmit={handleSubmit}>
          <div className="section-heading">
            <div>
              <p className="eyebrow">TESTE PAREADO</p>
              <h2>{TEXT.newAssessment}</h2>
            </div>
          </div>

          <div className="form-grid">
            <label>
              {TEXT.protocol}

              <select
                required
                value={form.protocol_id}
                onChange={(event) =>
                  setForm({
                    ...emptyForm,
                    protocol_id: event.target.value,
                  })
                }
              >
                <option value="" disabled>
                  {TEXT.choose}
                </option>

                {protocols.map((protocol) => (
                  <option key={protocol.id} value={protocol.id}>
                    {protocol.name}
                  </option>
                ))}
              </select>
            </label>

            {selectedProtocol?.input_mode === "time" && (
              <>
                <label>
                  {TEXT.shortTime}

                  <input
                    required
                    inputMode="numeric"
                    placeholder="03:30"
                    value={form.short_time}
                    onChange={(event) =>
                      setForm({
                        ...form,
                        short_time: formatTimeInput(event.target.value),
                      })
                    }
                  />

                  <small>{TEXT.timeHint}</small>
                </label>

                <label>
                  {TEXT.longTime}

                  <input
                    required
                    inputMode="numeric"
                    placeholder="11:30"
                    value={form.long_time}
                    onChange={(event) =>
                      setForm({
                        ...form,
                        long_time: formatTimeInput(event.target.value),
                      })
                    }
                  />

                  <small>{TEXT.timeHint}</small>
                </label>
              </>
            )}

            {selectedProtocol?.input_mode === "distance" && (
              <>
                <label>
                  {TEXT.shortDistance}

                  <input
                    required
                    type="number"
                    min="1"
                    step="1"
                    value={form.short_result}
                    onChange={(event) =>
                      setForm({
                        ...form,
                        short_result: event.target.value,
                      })
                    }
                  />
                </label>

                <label>
                  {TEXT.longDistance}

                  <input
                    required
                    type="number"
                    min="1"
                    step="1"
                    value={form.long_result}
                    onChange={(event) =>
                      setForm({
                        ...form,
                        long_result: event.target.value,
                      })
                    }
                  />
                </label>
              </>
            )}
          </div>
          <div className="ipt-form-footer">
            <label className="ipt-notes-field">
              <span>{TEXT.notes}</span>

              <textarea
                rows={3}
                value={form.notes}
                onChange={(event) =>
                  setForm({
                    ...form,
                    notes: event.target.value,
                  })
                }
              />
            </label>

            <button
              className="btn-primary ipt-submit-button"
              disabled={!selectedProtocol || saving}
            >
              {saving ? TEXT.saving : TEXT.save}
            </button>
          </div>
        </form>

        <section className="section-heading">
          <div>
            <p className="eyebrow">EVOLUCAO</p>
            <h2>{TEXT.history}</h2>
          </div>

          <span>{assessments.length} registros</span>
        </section>

        {loading ? (
          <p className="muted">{TEXT.loading}</p>
        ) : assessments.length === 0 ? (
          <div className="empty-state">
            <p>{TEXT.empty}</p>
          </div>
        ) : (
          <div className="table-scroll">
            <table className="athletes-table ipt-history-table">
              <thead>
                <tr>
                  <th>{TEXT.date}</th>
                  <th>{TEXT.protocol}</th>
                  <th>{TEXT.result}</th>
                  <th>{TEXT.profile}</th>
                  <th>{TEXT.shortSpeed}</th>
                  <th>{TEXT.longSpeed}</th>
                  <th>{TEXT.actions}</th>
                </tr>
              </thead>

              <tbody>
                {assessments.map((assessment) => (
                  <tr key={assessment.id}>
                    <td>{formatDate(assessment.created_at)}</td>
                    <td>{assessment.protocol_name}</td>
                    <td className="name-cell">
                      {assessment.ipt_percentage.toFixed(2)}%
                    </td>
                    <td>
                      <span className={profileClass(assessment.profile)}>
                        {assessment.profile}
                      </span>
                    </td>
                    <td>{assessment.short_speed.toFixed(2)} km/h</td>
                    <td>{assessment.long_speed.toFixed(2)} km/h</td>
                    <td>
                      <button
                        className="btn-link-danger"
                        onClick={() => handleDelete(assessment.id)}
                      >
                        {TEXT.remove}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}