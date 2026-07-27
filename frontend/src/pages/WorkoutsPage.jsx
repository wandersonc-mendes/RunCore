import { useMemo, useState } from "react";

import { getTraining } from "../api";
import "./WorkoutsPage.css";


const STORAGE_KEY = "runcore.workout-library.v1";

const categories = [
  "Todos",
  "Rodagem",
  "Intervalado",
  "Tempo Run",
  "Fartlek",
  "Longão",
  "Recuperação",
];

const defaultTemplates = [
  {
    id: "base-rodagem-leve",
    system: true,
    name: "Rodagem leve",
    category: "Rodagem",
    objective: "Desenvolver base aeróbia e favorecer recuperação.",
    zone: "Z1–Z2",
    estimatedDistance: 8,
    estimatedTime: 48,
    notes: "Ritmo confortável, mantendo respiração controlada.",
    steps: [
      { id: "step-1", type: "Aquecimento", repetitions: 1, distance: 1, unit: "km", pace: "05:50", recovery: "" },
      { id: "step-2", type: "Rodagem", repetitions: 1, distance: 6, unit: "km", pace: "05:30", recovery: "" },
      { id: "step-3", type: "Desaquecimento", repetitions: 1, distance: 1, unit: "km", pace: "06:00", recovery: "" },
    ],
  },
  {
    id: "base-intervalado-400",
    system: true,
    name: "Intervalado 8 × 400 m",
    category: "Intervalado",
    objective: "Estimular VO₂ e economia de corrida.",
    zone: "Z4–Z5",
    estimatedDistance: 8.2,
    estimatedTime: 50,
    notes: "Manter regularidade entre as repetições.",
    steps: [
      { id: "step-1", type: "Aquecimento", repetitions: 1, distance: 2, unit: "km", pace: "05:30", recovery: "" },
      { id: "step-2", type: "Intervalado", repetitions: 8, distance: 400, unit: "m", pace: "03:45", recovery: "1min30" },
      { id: "step-3", type: "Desaquecimento", repetitions: 1, distance: 3, unit: "km", pace: "05:50", recovery: "" },
    ],
  },
  {
    id: "base-tempo-run",
    system: true,
    name: "Tempo Run progressivo",
    category: "Tempo Run",
    objective: "Elevar tolerância ao esforço sustentado.",
    zone: "Z3–Z4",
    estimatedDistance: 10,
    estimatedTime: 47,
    notes: "Iniciar controlado e progredir sem sprint final.",
    steps: [
      { id: "step-1", type: "Aquecimento", repetitions: 1, distance: 2, unit: "km", pace: "05:20", recovery: "" },
      { id: "step-2", type: "Tempo Run", repetitions: 1, distance: 6, unit: "km", pace: "04:25", recovery: "" },
      { id: "step-3", type: "Desaquecimento", repetitions: 1, distance: 2, unit: "km", pace: "05:40", recovery: "" },
    ],
  },
  {
    id: "base-fartlek",
    system: true,
    name: "Fartlek 10 × 1 min",
    category: "Fartlek",
    objective: "Alternar intensidade e recuperação ativa.",
    zone: "Z2–Z4",
    estimatedDistance: 9,
    estimatedTime: 50,
    notes: "Trechos fortes controlados, sem chegar ao máximo.",
    steps: [
      { id: "step-1", type: "Aquecimento", repetitions: 1, distance: 2, unit: "km", pace: "05:35", recovery: "" },
      { id: "step-2", type: "Fartlek", repetitions: 10, distance: 1, unit: "min", pace: "04:00", recovery: "1 min leve" },
      { id: "step-3", type: "Desaquecimento", repetitions: 1, distance: 2, unit: "km", pace: "05:50", recovery: "" },
    ],
  },
  {
    id: "base-longao",
    system: true,
    name: "Longão aeróbio",
    category: "Longão",
    objective: "Aumentar resistência e tolerância ao volume.",
    zone: "Z2",
    estimatedDistance: 18,
    estimatedTime: 100,
    notes: "Hidratação e estratégia de carboidrato conforme duração.",
    steps: [
      { id: "step-1", type: "Rodagem", repetitions: 1, distance: 18, unit: "km", pace: "05:35", recovery: "" },
    ],
  },
  {
    id: "base-recuperacao",
    system: true,
    name: "Corrida regenerativa",
    category: "Recuperação",
    objective: "Favorecer recuperação sem interromper o estímulo aeróbio.",
    zone: "Z1",
    estimatedDistance: 6,
    estimatedTime: 38,
    notes: "Ritmo deliberadamente leve.",
    steps: [
      { id: "step-1", type: "Rodagem", repetitions: 1, distance: 6, unit: "km", pace: "06:20", recovery: "" },
    ],
  },
];


function cloneTemplates(items) {
  return items.map((template) => ({
    ...template,
    steps: template.steps.map((step) => ({ ...step })),
  }));
}


function loadTemplates() {
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);

    if (!stored) {
      return cloneTemplates(defaultTemplates);
    }

    const parsed = JSON.parse(stored);

    return Array.isArray(parsed) && parsed.length
      ? parsed
      : cloneTemplates(defaultTemplates);
  } catch {
    return cloneTemplates(defaultTemplates);
  }
}


function saveTemplates(items) {
  window.localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify(items),
  );
}


function emptyTemplate() {
  return {
    id: `custom-${Date.now()}`,
    system: false,
    name: "Novo treino",
    category: "Rodagem",
    objective: "",
    zone: "Z2",
    estimatedDistance: 0,
    estimatedTime: 0,
    notes: "",
    steps: [
      {
        id: `step-${Date.now()}`,
        type: "Aquecimento",
        repetitions: 1,
        distance: 1,
        unit: "km",
        pace: "",
        recovery: "",
      },
    ],
  };
}


function stepSummary(step) {
  const repetitions = Number(step.repetitions || 1);
  const amount = Number(step.distance || 0);
  const measure = step.unit || "km";
  const prefix = repetitions > 1 ? `${repetitions} × ` : "";
  const pace = step.pace ? ` · ${step.pace}/km` : "";
  const recovery = step.recovery ? ` · pausa ${step.recovery}` : "";

  return `${prefix}${amount} ${measure}${pace}${recovery}`;
}


export default function WorkoutsPage({
  athletes = [],
  onApplyTemplate,
}) {
  const [templates, setTemplates] = useState(loadTemplates);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("Todos");
  const [editing, setEditing] = useState(null);
  const [applying, setApplying] = useState(null);

  const filteredTemplates = useMemo(() => {
    const term = search.trim().toLocaleLowerCase("pt-BR");

    return templates.filter((template) => {
      const matchesCategory = category === "Todos"
        || template.category === category;

      const content = [
        template.name,
        template.category,
        template.objective,
        template.zone,
        template.notes,
      ]
        .filter(Boolean)
        .join(" ")
        .toLocaleLowerCase("pt-BR");

      return matchesCategory && (!term || content.includes(term));
    });
  }, [templates, search, category]);

  function persist(nextTemplates) {
    setTemplates(nextTemplates);
    saveTemplates(nextTemplates);
  }

  function beginApply(template) {
    setApplying({
      template,
      athleteId: "",
      sessions: [],
      loading: false,
      error: "",
    });
  }

  async function selectApplyAthlete(athleteId) {
    setApplying((current) => ({
      ...current,
      athleteId,
      sessions: [],
      loading: Boolean(athleteId),
      error: "",
    }));

    if (!athleteId) return;

    try {
      const plan = await getTraining(Number(athleteId));

      setApplying((current) => ({
        ...current,
        sessions: plan?.sessions || [],
        loading: false,
        error: plan
          ? ""
          : "O atleta ainda não possui planejamento.",
      }));
    } catch (error) {
      setApplying((current) => ({
        ...current,
        sessions: [],
        loading: false,
        error: error.message,
      }));
    }
  }

  function applyToSession(session) {
    const athlete = athletes.find(
      (item) => String(item.id) === String(applying.athleteId),
    );

    if (!athlete || !session || !applying?.template) return;

    onApplyTemplate(athlete, session, applying.template);
    setApplying(null);
  }

  function openEditor(template) {
    setEditing({
      ...template,
      steps: template.steps.map((step) => ({ ...step })),
    });
  }

  function duplicateTemplate(template) {
    const duplicate = {
      ...template,
      id: `custom-${Date.now()}`,
      system: false,
      name: `${template.name} - cópia`,
      steps: template.steps.map((step, index) => ({
        ...step,
        id: `step-${Date.now()}-${index}`,
      })),
    };

    persist([duplicate, ...templates]);
    openEditor(duplicate);
  }

  function deleteTemplate(template) {
    if (template.system) return;

    if (!window.confirm(`Excluir o modelo "${template.name}"?`)) {
      return;
    }

    persist(
      templates.filter((item) => item.id !== template.id),
    );
  }

  function restoreDefaults() {
    if (!window.confirm(
      "Restaurar a biblioteca original? Modelos personalizados serão removidos.",
    )) {
      return;
    }

    const restored = cloneTemplates(defaultTemplates);
    persist(restored);
    setEditing(null);
  }

  function updateEditing(field, value) {
    setEditing((current) => ({
      ...current,
      [field]: value,
    }));
  }

  function updateStep(index, field, value) {
    setEditing((current) => ({
      ...current,
      steps: current.steps.map((step, stepIndex) => (
        stepIndex === index
          ? { ...step, [field]: value }
          : step
      )),
    }));
  }

  function addStep() {
    setEditing((current) => ({
      ...current,
      steps: [
        ...current.steps,
        {
          id: `step-${Date.now()}`,
          type: "Rodagem",
          repetitions: 1,
          distance: 1,
          unit: "km",
          pace: "",
          recovery: "",
        },
      ],
    }));
  }

  function removeStep(index) {
    setEditing((current) => ({
      ...current,
      steps: current.steps.filter(
        (_, stepIndex) => stepIndex !== index,
      ),
    }));
  }

  function saveEditing(event) {
    event.preventDefault();

    const normalized = {
      ...editing,
      name: editing.name.trim() || "Treino sem nome",
      estimatedDistance: Number(editing.estimatedDistance || 0),
      estimatedTime: Number(editing.estimatedTime || 0),
      steps: editing.steps.map((step) => ({
        ...step,
        repetitions: Number(step.repetitions || 1),
        distance: Number(step.distance || 0),
      })),
    };

    const exists = templates.some(
      (template) => template.id === normalized.id,
    );

    persist(
      exists
        ? templates.map((template) => (
            template.id === normalized.id
              ? normalized
              : template
          ))
        : [normalized, ...templates],
    );

    setEditing(null);
  }

  return (
    <section className="workout-library-page">
      <header className="workout-library-heading">
        <div>
          <p className="eyebrow">BIBLIOTECA</p>
          <h2>Modelos de treino</h2>
          <p className="muted">
            Organize sessões reutilizáveis e ajuste os blocos
            conforme sua metodologia.
          </p>
        </div>

        <div className="workout-library-actions">
          <button type="button" className="btn-ghost" onClick={restoreDefaults}>
            Restaurar modelos
          </button>
          <button type="button" className="btn-primary" onClick={() => setEditing(emptyTemplate())}>
            + Novo modelo
          </button>
        </div>
      </header>

      <section className="workout-library-metrics">
        <article><strong>{templates.length}</strong><span>modelos</span></article>
        <article><strong>{templates.filter((template) => !template.system).length}</strong><span>personalizados</span></article>
        <article><strong>{new Set(templates.map((template) => template.category)).size}</strong><span>categorias</span></article>
      </section>

      <section className="workout-library-toolbar">
        <label>
          <span>Buscar modelo</span>
          <input
            type="search"
            placeholder="Ex.: intervalado, longão..."
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </label>

        <label>
          <span>Categoria</span>
          <select value={category} onChange={(event) => setCategory(event.target.value)}>
            {categories.map((item) => <option key={item} value={item}>{item}</option>)}
          </select>
        </label>

        <span>{filteredTemplates.length} resultado(s)</span>
      </section>

      <div className="workout-template-grid">
        {filteredTemplates.map((template) => (
          <article key={template.id} className="workout-template-card">
            <header>
              <div>
                <span className="workout-template-category">{template.category}</span>
                <h3>{template.name}</h3>
              </div>
              <span className="workout-template-zone">{template.zone}</span>
            </header>

            <p>{template.objective}</p>

            <div className="workout-template-numbers">
              <span><strong>{template.estimatedDistance}</strong>km</span>
              <span><strong>{template.estimatedTime}</strong>min</span>
              <span><strong>{template.steps.length}</strong>blocos</span>
            </div>

            <div className="workout-template-steps">
              {template.steps.slice(0, 3).map((step) => (
                <div key={step.id}>
                  <strong>{step.type}</strong>
                  <span>{stepSummary(step)}</span>
                </div>
              ))}
              {template.steps.length > 3 && <small>+ {template.steps.length - 3} bloco(s)</small>}
            </div>

            <footer>
              <button type="button" className="btn-primary" onClick={() => beginApply(template)}>Aplicar</button>
              <button type="button" className="btn-ghost" onClick={() => duplicateTemplate(template)}>Duplicar</button>
              <button type="button" className="btn-ghost" onClick={() => openEditor(template)}>Editar</button>
              {!template.system && (
                <button type="button" className="btn-link-danger" onClick={() => deleteTemplate(template)}>Excluir</button>
              )}
            </footer>
          </article>
        ))}
      </div>

      {applying && (
        <div className="workout-apply-overlay" role="dialog" aria-modal="true" aria-label="Aplicar modelo ao planejamento">
          <section className="workout-apply-dialog">
            <header>
              <div>
                <p className="eyebrow">APLICAR MODELO</p>
                <h2>{applying.template.name}</h2>
                <p>Escolha o atleta e a sessão que receberá este modelo.</p>
              </div>
              <button type="button" className="btn-ghost" onClick={() => setApplying(null)}>Cancelar</button>
            </header>

            <label>
              Atleta
              <select value={applying.athleteId} onChange={(event) => selectApplyAthlete(event.target.value)}>
                <option value="">Selecione um atleta</option>
                {athletes.filter((athlete) => athlete.active).map((athlete) => (
                  <option key={athlete.id} value={athlete.id}>{athlete.name}</option>
                ))}
              </select>
            </label>

            {applying.loading && <p className="muted">Carregando sessões...</p>}
            {applying.error && <div className="alert">{applying.error}</div>}

            {!applying.loading && applying.sessions.length > 0 && (
              <div className="workout-apply-session-list">
                {applying.sessions.map((session) => (
                  <button type="button" key={session.id} onClick={() => applyToSession(session)}>
                    <div>
                      <strong>{session.workout_name}</strong>
                      <span>Semana {session.week} · {session.session_date || "Sem data"}</span>
                    </div>
                    <span>Aplicar →</span>
                  </button>
                ))}
              </div>
            )}
          </section>
        </div>
      )}

      {editing && (
        <div className="workout-template-editor-overlay" role="dialog" aria-modal="true" aria-label="Editar modelo de treino">
          <form className="workout-template-editor" onSubmit={saveEditing}>
            <header>
              <div>
                <p className="eyebrow">MODELO DE TREINO</p>
                <h2>{editing.name}</h2>
              </div>
              <div>
                <button type="button" className="btn-ghost" onClick={() => setEditing(null)}>Cancelar</button>
                <button type="submit" className="btn-primary">Salvar modelo</button>
              </div>
            </header>

            <section className="workout-template-editor-fields">
              <label>Nome do treino<input value={editing.name} onChange={(event) => updateEditing("name", event.target.value)} /></label>
              <label>Categoria<select value={editing.category} onChange={(event) => updateEditing("category", event.target.value)}>{categories.filter((item) => item !== "Todos").map((item) => <option key={item} value={item}>{item}</option>)}</select></label>
              <label>Zona<input value={editing.zone} onChange={(event) => updateEditing("zone", event.target.value)} /></label>
              <label>Distância estimada (km)<input type="number" min="0" step="0.1" value={editing.estimatedDistance} onChange={(event) => updateEditing("estimatedDistance", event.target.value)} /></label>
              <label>Tempo estimado (min)<input type="number" min="0" value={editing.estimatedTime} onChange={(event) => updateEditing("estimatedTime", event.target.value)} /></label>
              <label className="wide">Objetivo<input value={editing.objective} onChange={(event) => updateEditing("objective", event.target.value)} /></label>
              <label className="wide">Observações<textarea value={editing.notes} onChange={(event) => updateEditing("notes", event.target.value)} /></label>
            </section>

            <section className="workout-template-blocks">
              <div className="workout-template-blocks-heading">
                <div><h3>Blocos do treino</h3><p>Defina ordem, volume, ritmo e recuperação.</p></div>
                <button type="button" className="btn-ghost" onClick={addStep}>+ Adicionar bloco</button>
              </div>

              {editing.steps.map((step, index) => (
                <article key={step.id}>
                  <span className="workout-template-block-number">{index + 1}</span>
                  <label>Tipo<input value={step.type} onChange={(event) => updateStep(index, "type", event.target.value)} /></label>
                  <label>Repetições<input type="number" min="1" value={step.repetitions} onChange={(event) => updateStep(index, "repetitions", event.target.value)} /></label>
                  <label>Distância / tempo<input type="number" min="0" step="0.1" value={step.distance} onChange={(event) => updateStep(index, "distance", event.target.value)} /></label>
                  <label>Unidade<select value={step.unit} onChange={(event) => updateStep(index, "unit", event.target.value)}><option value="m">m</option><option value="km">km</option><option value="min">min</option></select></label>
                  <label>Ritmo<input placeholder="04:30" value={step.pace} onChange={(event) => updateStep(index, "pace", event.target.value)} /></label>
                  <label>Recuperação<input placeholder="1min30" value={step.recovery} onChange={(event) => updateStep(index, "recovery", event.target.value)} /></label>
                  <button type="button" className="btn-link-danger" disabled={editing.steps.length === 1} onClick={() => removeStep(index)}>Remover</button>
                </article>
              ))}
            </section>
          </form>
        </div>
      )}
    </section>
  );
}
