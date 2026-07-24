import { useEffect, useState } from "react";
import {
  clearSession,
  createAthlete,
  createEvaluation,
  createTraining,
  deleteAthlete,
  deleteEvaluation,
  listAthletes,
  listEvaluations,
  getTraining,
  regenerateTraining,
  updateTrainingSession,
  getCurrentUser,
  hasSession,
  createInvitation,
  listInvitations,
  approveInvitation,
} from "./api";
import LoginScreen from "./LoginScreen";
import StudentPortal from "./StudentPortal";
import AthleteProfileView from "./AthleteProfileView";
import "./App.css";

const emptyAthlete = { name: "", phone: "", email: "", goal: "", notes: "" };
const emptyEvaluation = {
  weight: "",
  height: "",
  max_hr: "",
  resting_hr: "",
  test_type: "",
  time: "",
  test_date: new Date().toISOString().slice(0, 10),
};

const weekdays = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"];

function asNumber(value) {
  return value === "" ? 0 : Number(value);
}

function formatTestTimeInput(value) {
  const digits = value.replace(/\D/g, "").slice(0, 6);
  return [digits.slice(0, 2), digits.slice(2, 4), digits.slice(4, 6)]
    .filter(Boolean)
    .join(":");
}

function formatDate(value) {
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(value));
}

function formatTestDate(value) {
  return value ? new Intl.DateTimeFormat("pt-BR", { dateStyle: "short" }).format(new Date(`${value}T00:00:00`)) : "—";
}

function formatDuration(seconds) {
  const value = Math.round(seconds);
  const hours = Math.floor(value / 3600);
  const minutes = Math.floor((value % 3600) / 60);
  const remainder = value % 60;
  return [hours, minutes, remainder].map((part) => String(part).padStart(2, "0")).join(":");
}

function totalSessionDistance(session) {
  return session.steps.reduce(
    (total, step) => total + (step.distance * (step.repetitions || 1)),
    0,
  );
}

function stepTone(type = "") {
  const label = type.toLowerCase();
  if (label.includes("desaqueci")) return "cooldown";
  if (label.includes("aquecimento")) return "warmup";
  if (label.includes("descanso") || label.includes("recupera")) return "recovery";
  return "run";
}

function weekdayForDate(value) {
  if (!value) return "";
  return new Intl.DateTimeFormat("pt-BR", { weekday: "long" }).format(new Date(`${value}T12:00:00`));
}

function BrandLogo() {
  return <span className="brand-logo"><img src="/logo-horizontal.png?v=1" alt="RunCore" /></span>;
}

function SessionAdjustment({ value, onChange, onSave, saving }) {
  const [openTypePicker, setOpenTypePicker] = useState(null);
  const stepTypes = ["Aquecimento", "Corrida", "Caminhada", "Recuperação", "Descanso", "Desaquecimento", "Outros"];
  function changeStep(index, field, nextValue) {
    onChange((session) => ({ ...session, steps: session.steps.map((step, position) => position === index ? { ...step, [field]: nextValue } : step) }));
  }
  function addStep() {
    onChange((session) => ({ ...session, steps: [...session.steps, { type: "Corrida", distance: 1, distance_unit: "km", repetitions: 0, recovery: "", pace_min: "", pace_max: "", notes: "" }] }));
  }
  function removeStep(index) {
    onChange((session) => ({ ...session, steps: session.steps.filter((_, position) => position !== index) }));
  }
  return <form className="workout-adjustment" onSubmit={onSave}>
    <h3>Ajustar esta sessão</h3>
    <div className="form-grid">
      <label>Dia do treino<input type="date" value={value.session_date || ""} onChange={(event) => onChange((item) => ({ ...item, session_date: event.target.value }))} /><small>{weekdayForDate(value.session_date)}</small></label>
      <label>Nome<input value={value.workout_name} onChange={(event) => onChange((item) => ({ ...item, workout_name: event.target.value }))} /></label>
      <label>Zona<input value={value.zone} onChange={(event) => onChange((item) => ({ ...item, zone: event.target.value }))} /></label>
      <label>Distância total<input type="number" step="0.1" min="0" value={value.planned_distance} onChange={(event) => onChange((item) => ({ ...item, planned_distance: event.target.value }))} /></label>
      <label>Repetições da sessão<input type="number" min="0" value={value.repetitions} onChange={(event) => onChange((item) => ({ ...item, repetitions: event.target.value }))} /></label>
    </div>
    <label>Orientação geral do treinador<textarea value={value.notes} onChange={(event) => onChange((item) => ({ ...item, notes: event.target.value }))} /></label>
    <div className="step-editor-heading"><h3>Estrutura do treino</h3><button type="button" className="btn-ghost" onClick={addStep}>+ Adicionar etapa</button></div>
    {value.steps.map((step, index) => <section className={`step-editor ${stepTone(step.type)}`} key={step.id || index}>
      <div className="step-editor-title"><strong>Etapa {index + 1}</strong>{value.steps.length > 1 && <button type="button" className="btn-link-danger" onClick={() => removeStep(index)}>Remover</button>}</div>
      <div className="form-grid step-fields">
        <label>Tipo<div className="step-type-picker"><button type="button" onClick={() => setOpenTypePicker((current) => current === index ? null : index)}>{step.type}<span>⌄</span></button>{openTypePicker === index && <div className="step-type-menu">{stepTypes.map((type) => <button type="button" className={step.type === type ? "active" : ""} key={type} onClick={() => { changeStep(index, "type", type); setOpenTypePicker(null); }}>{type}</button>)}</div>}</div></label>
        <label>Distância<div className="distance-input"><input type="number" step="0.1" min="0" value={step.distance} onChange={(event) => changeStep(index, "distance", event.target.value)} /><select value={step.distance_unit || (step.repetitions ? "m" : "km")} onChange={(event) => changeStep(index, "distance_unit", event.target.value)}><option value="km">km</option><option value="m">m</option></select></div></label>
        <label>Repetições<input type="number" min="0" value={step.repetitions} onChange={(event) => changeStep(index, "repetitions", event.target.value)} /></label>
        <label>Recuperação<input value={step.recovery || ""} placeholder="Ex.: 200 m trote" onChange={(event) => changeStep(index, "recovery", event.target.value)} /></label>
        <label>Ritmo mínimo<input value={step.pace_min || ""} placeholder="05:20" onChange={(event) => changeStep(index, "pace_min", event.target.value)} /></label>
        <label>Ritmo máximo<input value={step.pace_max || ""} placeholder="05:00" onChange={(event) => changeStep(index, "pace_max", event.target.value)} /></label>
      </div>
      <label>Instrução da etapa<textarea value={step.notes || ""} onChange={(event) => changeStep(index, "notes", event.target.value)} /></label>
    </section>)}
    <button className="btn-primary" disabled={saving || value.steps.length === 0}>{saving ? "Salvando..." : "Salvar ajuste semanal"}</button>
  </form>;
}

export default function App() {
  const [athletes, setAthletes] = useState([]);
  const [currentUser, setCurrentUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [athleteForm, setAthleteForm] = useState(emptyAthlete);
  const [evaluationForm, setEvaluationForm] = useState(emptyEvaluation);
  const [showForm, setShowForm] = useState(false);
  const [selectedAthlete, setSelectedAthlete] = useState(null);
  const [selectedWorkout, setSelectedWorkout] = useState(null);
  const [selectedView, setSelectedView] = useState("evaluations");
  const [evaluations, setEvaluations] = useState([]);
  const [training, setTraining] = useState(null);
  const [loading, setLoading] = useState(true);
  const [savingEvaluation, setSavingEvaluation] = useState(false);
  const [savingTraining, setSavingTraining] = useState(false);
  const [trainingForm, setTrainingForm] = useState({ name: "Planejamento Principal", objective: "", target_distance: "", start_date: new Date().toISOString().slice(0, 10), target_date: "", total_weeks: "8" });
  const [workoutEdit, setWorkoutEdit] = useState(null);
  const [error, setError] = useState(null);
  const [invitations, setInvitations] = useState({ pending: [], sent: [] });
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteLink, setInviteLink] = useState("");
  const [quickAction, setQuickAction] = useState(null);

  async function loadAthletes(currentSearch = search) {
    setLoading(true);
    setError(null);
    try {
      setAthletes(await listAthletes(currentSearch));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function loadEvaluations(athleteId) {
    setLoading(true);
    setError(null);
    try {
      setEvaluations(await listEvaluations(athleteId));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!hasSession()) { setAuthLoading(false); return; }
    getCurrentUser().then(setCurrentUser).catch(clearSession).finally(() => setAuthLoading(false));
  }, []);

  useEffect(() => {
    if (currentUser?.role === "coach") { loadAthletes(""); loadInvitations(); }
  }, [currentUser]);

  useEffect(() => {
    if (currentUser?.role !== "coach") return undefined;
    const refreshInvitations = () => loadInvitations();
    const interval = window.setInterval(refreshInvitations, 5000);
    window.addEventListener("focus", refreshInvitations);
    return () => { window.clearInterval(interval); window.removeEventListener("focus", refreshInvitations); };
  }, [currentUser]);

  async function loadInvitations() {
    try { setInvitations(await listInvitations()); } catch (err) { setError(err.message); }
  }

  async function handleCreateInvitation(event) {
    event.preventDefault();
    try {
      const invitation = await createInvitation({ email: inviteEmail });
      setInviteEmail("");
      setInviteLink(invitation.registration_url);
      loadInvitations();
    } catch (err) { setError(err.message); }
  }

  async function handleApproveInvitation(id) {
    try { await approveInvitation(id); await Promise.all([loadInvitations(), loadAthletes(search)]); } catch (err) { setError(err.message); }
  }

  function handleSearchSubmit(event) {
    event.preventDefault();
    loadAthletes(search);
  }

  async function handleCreateAthlete(event) {
    event.preventDefault();
    if (!athleteForm.name.trim()) return;
    try {
      await createAthlete({ ...athleteForm, active: true });
      setAthleteForm(emptyAthlete);
      setShowForm(false);
      loadAthletes(search);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleDeleteAthlete(id) {
    if (!window.confirm("Remover este atleta?")) return;
    try {
      await deleteAthlete(id);
      if (selectedAthlete?.id === id) setSelectedAthlete(null);
      loadAthletes(search);
    } catch (err) {
      setError(err.message);
    }
  }

  function openEvaluations(athlete) {
    setSelectedAthlete(athlete);
    setSelectedView("evaluations");
    setEvaluationForm(emptyEvaluation);
    setSelectedWorkout(null);
    loadEvaluations(athlete.id);
  }

  function openProfile(athlete) {
    setSelectedAthlete(athlete);
    setSelectedView("profile");
  }

  async function openTraining(athlete) {
    setSelectedAthlete(athlete);
    setSelectedView("training");
    setSelectedWorkout(null);
    setWorkoutEdit(null);
    setTrainingForm({ name: "Planejamento Principal", objective: athlete.goal || "Preparação para prova", target_distance: "", start_date: new Date().toISOString().slice(0, 10), target_date: "", total_weeks: "8" });
    setLoading(true);
    setError(null);
    try {
      setTraining(await getTraining(athlete.id));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateTraining(regenerate = false) {
    if (savingTraining) return;

    setSavingTraining(true);
    setError(null);
    try {
      const data = regenerate
        ? await regenerateTraining(selectedAthlete.id)
        : await createTraining(selectedAthlete.id, { ...trainingForm, target_distance: Number(trainingForm.target_distance), total_weeks: trainingForm.target_date ? null : Number(trainingForm.total_weeks) });
      setTraining(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setSavingTraining(false);
    }
  }

  async function handleUpdateWorkout(event) {
    event.preventDefault();
    if (!workoutEdit || savingTraining) return;
    setSavingTraining(true);
    try {
      const updated = await updateTrainingSession(selectedAthlete.id, workoutEdit.id, { ...workoutEdit, planned_distance: Number(workoutEdit.planned_distance), repetitions: Number(workoutEdit.repetitions), steps: workoutEdit.steps.map((step) => ({ ...step, distance: Number(step.distance), repetitions: Number(step.repetitions) })) });
      setTraining(updated);
      setSelectedWorkout(updated.sessions.find((session) => session.id === workoutEdit.id) || null);
      setWorkoutEdit(null);
    } catch (err) { setError(err.message); } finally { setSavingTraining(false); }
  }

  async function handleCreateEvaluation(event) {
    event.preventDefault();
    if (savingEvaluation) return;

    setSavingEvaluation(true);
    try {
      await createEvaluation(selectedAthlete.id, {
        weight: asNumber(evaluationForm.weight),
        height: asNumber(evaluationForm.height),
        max_hr: asNumber(evaluationForm.max_hr),
        resting_hr: asNumber(evaluationForm.resting_hr),
        test_type: evaluationForm.test_type,
        time: evaluationForm.time,
        test_date: evaluationForm.test_date,
      });
      setEvaluationForm(emptyEvaluation);
      loadEvaluations(selectedAthlete.id);
    } catch (err) {
      setError(err.message);
    } finally {
      setSavingEvaluation(false);
    }
  }

  async function handleDeleteEvaluation(evaluationId) {
    if (!window.confirm("Remover esta avaliação?")) return;
    try {
      await deleteEvaluation(selectedAthlete.id, evaluationId);
      loadEvaluations(selectedAthlete.id);
    } catch (err) {
      setError(err.message);
    }
  }

  if (authLoading) return <main className="login-page"><p className="muted">Carregando...</p></main>;
  if (!currentUser) return <LoginScreen onAuthenticated={setCurrentUser} />;
  if (currentUser.role === "student") return <StudentPortal user={currentUser} onLogout={() => setCurrentUser(null)} />;
  if (selectedAthlete && selectedView === "profile") return <AthleteProfileView athlete={selectedAthlete} onClose={() => setSelectedAthlete(null)} onRemove={() => handleDeleteAthlete(selectedAthlete.id)} />;

  if (selectedAthlete && selectedView === "evaluations") {
    return (
      <div className="page">
        <header className="topbar">
          <div className="brand">
            <BrandLogo />
            <div>
              <h1>Avaliações físicas e VDOT</h1>
              <p>Aluno: {selectedAthlete.name}</p>
            </div>
          </div>
          <div className="header-actions"><button className="btn-ghost" onClick={() => openTraining(selectedAthlete)}>Planejamento</button><button className="btn-ghost" onClick={() => setSelectedAthlete(null)}>Voltar para atletas</button></div>
        </header>

        <main className="content">
          {error && <div className="alert">{error}</div>}

          <form className="card evaluation-form" onSubmit={handleCreateEvaluation}>
            <h2>Nova avaliação</h2>
            <div className="form-grid">
              <label>Peso (kg)<input type="number" min="0.1" step="0.1" required value={evaluationForm.weight} onChange={(e) => setEvaluationForm({ ...evaluationForm, weight: e.target.value })} /></label>
              <label>Altura (m)<input type="number" min="0.01" step="0.01" required value={evaluationForm.height} onChange={(e) => setEvaluationForm({ ...evaluationForm, height: e.target.value })} /></label>
              <label>FC máxima<input type="number" min="1" required value={evaluationForm.max_hr} onChange={(e) => setEvaluationForm({ ...evaluationForm, max_hr: e.target.value })} /></label>
              <label>FC repouso<input type="number" min="1" required value={evaluationForm.resting_hr} onChange={(e) => setEvaluationForm({ ...evaluationForm, resting_hr: e.target.value })} /></label>
              <label>Data do teste<input type="date" required value={evaluationForm.test_date} onChange={(e) => setEvaluationForm({ ...evaluationForm, test_date: e.target.value })} /></label>
              <label>Tipo de teste<select required value={evaluationForm.test_type} onChange={(e) => setEvaluationForm({ ...evaluationForm, test_type: e.target.value })}><option value="" disabled>Selecione</option><option value="3K">3 km</option><option value="5K">5 km</option><option value="10K">10 km</option><option value="21K">Meia maratona</option></select></label>
              <label>Tempo do teste (HH:MM:SS)<input type="text" inputMode="numeric" placeholder="00:25:30" pattern="\d{2}:[0-5]\d:[0-5]\d" required value={evaluationForm.time} onChange={(e) => setEvaluationForm({ ...evaluationForm, time: formatTestTimeInput(e.target.value) })} /></label>
            </div>
            <button type="submit" className="btn-primary" disabled={savingEvaluation}>{savingEvaluation ? "Salvando..." : "Salvar avaliação"}</button>
          </form>

          {loading ? <p className="muted">Carregando...</p> : evaluations.length === 0 ? (
            <div className="empty-state"><p>Nenhuma avaliação registrada.</p></div>
          ) : (
            <table className="athletes-table">
              <thead><tr><th>Data</th><th>VDOT</th><th>Teste</th><th>Dados</th><th></th></tr></thead>
              <tbody>
                {evaluations.map((evaluation) => (
                  <tr key={evaluation.id}>
                    <td>{formatTestDate(evaluation.test_date)}</td>
                    <td className="name-cell">{evaluation.vdot.toFixed(1)}</td>
                    <td>{evaluation.test_type}</td>
                    <td className="muted">{evaluation.distance ? `${evaluation.distance / 1000} km em ${formatDuration(evaluation.time_seconds)}` : "Sem teste de corrida"}</td>
                    <td><button className="btn-link-danger" onClick={() => handleDeleteEvaluation(evaluation.id)}>Remover</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </main>
      </div>
    );
  }

  if (selectedAthlete && selectedView === "training") {
    const sessionsByWeek = (training?.sessions || []).reduce((weeks, session) => {
      (weeks[session.week] ||= []).push(session);
      return weeks;
    }, {});

    return (
      <div className="page">
        <header className="topbar">
          <div className="brand"><BrandLogo /><div><h1>Planejamento de treino</h1><p>Aluno: {selectedAthlete.name}</p></div></div>
          <div className="header-actions"><button className="btn-ghost" onClick={() => openEvaluations(selectedAthlete)}>Avaliações</button><button className="btn-ghost" onClick={() => setSelectedAthlete(null)}>Voltar para atletas</button></div>
        </header>
        <main className="content">
          {error && <div className="alert">{error}</div>}
          {loading ? <p className="muted">Carregando...</p> : !training ? (
            <section className="card training-config"><p className="eyebrow">NOVO MACROCICLO</p><h2>Monte o ciclo a partir da meta do aluno</h2><p className="muted">Use a data da prova para calcular as semanas disponíveis ou informe a duração do ciclo.</p><div className="form-grid"><label>Planejamento<input value={trainingForm.name} onChange={(event) => setTrainingForm((form) => ({ ...form, name: event.target.value }))} /></label><label>Objetivo principal<input required value={trainingForm.objective} onChange={(event) => setTrainingForm((form) => ({ ...form, objective: event.target.value }))} placeholder="Ex.: Meia Maratona de Vitória" /></label><label>Distância-alvo (km)<input required type="number" min="0.1" step="0.1" value={trainingForm.target_distance} onChange={(event) => setTrainingForm((form) => ({ ...form, target_distance: event.target.value }))} placeholder="21.1" /></label><label>Início do ciclo<input required type="date" value={trainingForm.start_date} onChange={(event) => setTrainingForm((form) => ({ ...form, start_date: event.target.value }))} /></label><label>Data da prova (opcional)<input type="date" value={trainingForm.target_date} onChange={(event) => setTrainingForm((form) => ({ ...form, target_date: event.target.value }))} /></label><label>Semanas disponíveis {trainingForm.target_date && <small>(calculadas pela data)</small>}<input disabled={Boolean(trainingForm.target_date)} type="number" min="4" max="52" value={trainingForm.total_weeks} onChange={(event) => setTrainingForm((form) => ({ ...form, total_weeks: event.target.value }))} /></label></div><button className="btn-primary" disabled={savingTraining || !trainingForm.objective || !trainingForm.target_distance} onClick={() => handleCreateTraining()}>{savingTraining ? "Gerando ciclo..." : "Gerar macrociclo"}</button></section>
          ) : (
            <>
              <section className="card training-summary"><div><p className="eyebrow">MACROCICLO · FASE ATUAL: {training.current_phase}</p><h2>{training.name}</h2><p>Meta: {training.target_distance} km</p><small>Semana {training.current_week} de {training.total_weeks} · início {formatTestDate(training.start_date)}{training.target_date ? ` · prova ${formatTestDate(training.target_date)}` : ""}</small></div><button className="btn-ghost" disabled={savingTraining} onClick={() => handleCreateTraining(true)}>{savingTraining ? "Atualizando..." : "Atualizar planilha"}</button></section>
              {Object.entries(sessionsByWeek).map(([week, sessions]) => (
                <section key={week} className="week-section"><h2>Semana {week} <small>· {sessions[0]?.phase}</small></h2><div className="session-grid">{sessions.map((session) => <article className="card session-card" key={session.id}><span className="session-day">{weekdays[session.weekday]} · {formatTestDate(session.session_date)}</span><h3>{session.workout_name}</h3><p className="zone">{session.zone}</p><p>{session.repetitions ? `${session.repetitions} × ${session.planned_distance} m` : `${session.planned_distance.toFixed(1)} km`}</p><button className="btn-link open-workout" onClick={() => { setSelectedWorkout(session); setWorkoutEdit({ ...session, notes: session.notes || "", steps: session.steps || [] }); }}>Abrir e ajustar</button></article>)}</div></section>
              ))}
            </>
          )}
        </main>
        {selectedWorkout && <div className="modal-backdrop" role="presentation" onMouseDown={() => setSelectedWorkout(null)}><section className="workout-modal" role="dialog" aria-modal="true" aria-labelledby="workout-title" onMouseDown={(event) => event.stopPropagation()}><header className="modal-header"><div><span className="session-day">Semana {selectedWorkout.week} · {weekdays[selectedWorkout.weekday]}</span><h2 id="workout-title">{selectedWorkout.workout_name}</h2><p>{selectedWorkout.zone} · {selectedWorkout.repetitions ? `${selectedWorkout.repetitions} × ${selectedWorkout.planned_distance} m` : `${selectedWorkout.planned_distance.toFixed(1)} km`}</p></div><button className="modal-close" onClick={() => setSelectedWorkout(null)} aria-label="Fechar detalhes">×</button></header><div className="workout-metrics"><div><span>Volume estruturado</span><strong>{totalSessionDistance(selectedWorkout).toFixed(1)} km</strong></div><div><span>Etapas</span><strong>{selectedWorkout.steps.length}</strong></div><div><span>Zona</span><strong>{selectedWorkout.zone}</strong></div></div><section className="adaptations"><h3>Adaptações esperadas</h3><ul>{selectedWorkout.adaptations?.map((adaptation) => <li key={adaptation}>{adaptation}</li>)}</ul></section>{selectedWorkout.steps.length === 0 ? <div className="empty-state"><p>Este plano foi gerado antes da estrutura detalhada.</p><p className="muted">Feche esta janela e use “Regenerar plano”.</p></div> : <ol className="detailed-steps">{selectedWorkout.steps.map((step) => <li key={step.order}><div className="step-number">{step.order}</div><div><h3>{step.type}</h3><p className="step-target">{step.repetitions ? `${step.repetitions} × ${step.distance} m` : `${step.distance.toFixed(1)} km`} <span>· {step.pace_min}–{step.pace_max}/km</span></p>{step.recovery && <p className="step-recovery">Recuperação: {step.recovery}</p>}<p className="step-note">{step.notes}</p></div></li>)}</ol>}{workoutEdit && <form className="workout-adjustment" onSubmit={handleUpdateWorkout}><h3>Ajustar esta sessão</h3><div className="form-grid"><label>Nome<input value={workoutEdit.workout_name} onChange={(event) => setWorkoutEdit((item) => ({ ...item, workout_name: event.target.value }))} /></label><label>Zona<input value={workoutEdit.zone} onChange={(event) => setWorkoutEdit((item) => ({ ...item, zone: event.target.value }))} /></label><label>Distância<input type="number" step="0.1" min="0" value={workoutEdit.planned_distance} onChange={(event) => setWorkoutEdit((item) => ({ ...item, planned_distance: event.target.value }))} /></label><label>Repetições<input type="number" min="0" value={workoutEdit.repetitions} onChange={(event) => setWorkoutEdit((item) => ({ ...item, repetitions: event.target.value }))} /></label></div><label>Orientação do treinador<textarea value={workoutEdit.notes} onChange={(event) => setWorkoutEdit((item) => ({ ...item, notes: event.target.value }))} /></label><button className="btn-primary" disabled={savingTraining}>{savingTraining ? "Salvando..." : "Salvar ajuste semanal"}</button></form>}<footer className="modal-footer"><button className="btn-ghost" onClick={() => setSelectedWorkout(null)}>Fechar</button></footer></section></div>}
        {selectedWorkout && workoutEdit && <div className="session-editor-overlay" role="presentation" onMouseDown={() => setSelectedWorkout(null)}><section className="session-editor-modal" role="dialog" aria-modal="true" aria-label="Ajustar sessão" onMouseDown={(event) => event.stopPropagation()}><header><div><p className="eyebrow">EDIÇÃO COMPLETA</p><h2>Ajustar sessão</h2></div><button className="modal-close" onClick={() => setSelectedWorkout(null)} aria-label="Fechar edição">×</button></header><SessionAdjustment value={workoutEdit} onChange={setWorkoutEdit} onSave={handleUpdateWorkout} saving={savingTraining} /></section></div>}
      </div>
    );
  }

  return (
    <div className="page">
      <header className="topbar">
        <div className="brand">
          <BrandLogo />

          <div>
            <h1>RunCore</h1>
            <p>Painel do treinador</p>
          </div>
        </div>

        <div className="header-actions">
          <button
            className="btn-ghost"
            onClick={() => {
              clearSession();
              setCurrentUser(null);
            }}
          >
            Sair
          </button>

          <button
            className="btn-primary"
            onClick={() => setShowForm((value) => !value)}
          >
            {showForm ? "Cancelar" : "+ Novo atleta"}
          </button>
        </div>
      </header>

      {quickAction && (
        <div
          className="quick-action-overlay"
          role="dialog"
          aria-modal="true"
          aria-label="Escolher atleta"
        >
          <section className="quick-action-dialog">
            <div>
              <p className="eyebrow">ATALHO</p>

              <h2>
                {quickAction === "athletes"
                  ? "Abrir cadastro do atleta"
                  : quickAction === "evaluations"
                    ? "Abrir avaliações"
                    : "Abrir planejamento"}
              </h2>

              <p className="muted">
                Escolha o atleta que deseja acompanhar.
              </p>
            </div>

            <div className="quick-action-list">
              {athletes.length ? (
                athletes.map((athlete) => (
                  <button
                    type="button"
                    key={athlete.id}
                    onClick={() => {
                      setQuickAction(null);

                      if (quickAction === "athletes") {
                        openProfile(athlete);
                      } else if (quickAction === "evaluations") {
                        openEvaluations(athlete);
                      } else {
                        openTraining(athlete);
                      }
                    }}
                  >
                    <span>{athlete.name}</span>

                    <small>
                      {athlete.goal || "Sem objetivo informado"}
                    </small>
                  </button>
                ))
              ) : (
                <p className="muted">Nenhum atleta cadastrado.</p>
              )}
            </div>

            <button
              type="button"
              className="btn-ghost"
              onClick={() => setQuickAction(null)}
            >
              Cancelar
            </button>
          </section>
        </div>
      )}

      <main className="content">
        <section
          id="visao-geral"
          className="coach-hero"
        >
          <div>
            <p className="eyebrow">VISÃO GERAL</p>

            <h2>Olá, {currentUser.name}.</h2>

            <p>
              Organize seus atletas, acompanhe avaliações e mantenha
              cada plano em dia.
            </p>
          </div>

          <div className="hero-date">
            <span>RUNCORE</span>
            <strong>Assessoria em movimento</strong>
          </div>
        </section>

        <nav
          className="portal-menu coach-nav coach-nav-below"
          aria-label="Navegação do treinador"
        >
          <button
            type="button"
            onClick={() =>
              document
                .getElementById("visao-geral")
                ?.scrollIntoView({
                  behavior: "smooth",
                  block: "start",
                })
            }
          >
            Visão geral
          </button>

          <button
            type="button"
            onClick={() =>
              document
                .getElementById("convites")
                ?.scrollIntoView({
                  behavior: "smooth",
                  block: "start",
                })
            }
          >
            Convites e aprovações
          </button>

          <button
            type="button"
            onClick={() => setQuickAction("athletes")}
          >
            Atletas
          </button>

          <button
            type="button"
            onClick={() => setQuickAction("evaluations")}
          >
            Avaliações
          </button>

          <button
            type="button"
            onClick={() => setQuickAction("training")}
          >
            Planejamentos
          </button>
        </nav>

        <section
          id="convites"
          className="card invitations-card"
        >
          <div>
            <p className="eyebrow">NOVOS ALUNOS</p>

            <h2>Convites e aprovações</h2>

            <p className="muted">
              Envie o link, receba o pré-cadastro e aprove o aluno
              quando estiver pronto.
            </p>
          </div>

          <form
            className="invite-form"
            onSubmit={handleCreateInvitation}
          >
            <input
              type="email"
              value={inviteEmail}
              onChange={(event) =>
                setInviteEmail(event.target.value)
              }
              placeholder="E-mail do aluno (opcional)"
            />

            <button className="btn-primary">
              Gerar link de convite
            </button>
          </form>

          {inviteLink && (
            <div className="invite-link">
              <span>Link pronto para compartilhar</span>

              <input
                readOnly
                value={inviteLink}
                onFocus={(event) => event.target.select()}
              />

              <button
                type="button"
                className="btn-ghost"
                onClick={() =>
                  navigator.clipboard?.writeText(inviteLink)
                }
              >
                Copiar
              </button>
            </div>
          )}

          <div className="invitation-status-grid">
            <section className="pending-invitations">
              <div className="invitation-section-heading">
                <strong>Aguardando sua aprovação</strong>
                <span>{invitations.pending.length}</span>
              </div>

              {invitations.pending.length ? (
                invitations.pending.map((invitation) => (
                  <div
                    className="invitation-row"
                    key={invitation.id}
                  >
                    <div>
                      <strong>
                        {invitation.student_name || "Novo aluno"}
                      </strong>

                      <small>
                        {invitation.email ||
                          "E-mail informado no pré-cadastro"}
                        {" · "}
                        {formatDate(invitation.created_at)}
                      </small>
                    </div>

                    <div className="invitation-actions">
                      {invitation.athlete_id && (
                        <button
                          type="button"
                          className="btn-ghost"
                          onClick={() =>
                            openProfile({
                              id: invitation.athlete_id,
                              name:
                                invitation.student_name ||
                                "Novo aluno",
                            })
                          }
                        >
                          Ver cadastro
                        </button>
                      )}

                      <button
                        type="button"
                        className="btn-primary"
                        onClick={() =>
                          handleApproveInvitation(invitation.id)
                        }
                      >
                        Aprovar
                      </button>
                    </div>
                  </div>
                ))
              ) : (
                <p className="invitation-empty">
                  Nenhum aluno aguardando aprovação.
                </p>
              )}
            </section>

            <section className="sent-invitations">
              <div className="invitation-section-heading">
                <strong>Convites enviados</strong>
                <span>{invitations.sent.length}</span>
              </div>

              {invitations.sent.length ? (
                invitations.sent
                  .slice(0, 3)
                  .map((invitation) => (
                    <div
                      className="sent-invitation"
                      key={invitation.id}
                    >
                      <span>
                        {invitation.email ||
                          "Link sem e-mail definido"}
                      </span>

                      <small>
                        Enviado em{" "}
                        {formatDate(invitation.created_at)}
                      </small>
                    </div>
                  ))
              ) : (
                <p className="invitation-empty">
                  Nenhum convite pendente de uso.
                </p>
              )}
            </section>
          </div>
        </section>

        <section className="stat-grid">
          <article className="stat-card">
            <span className="stat-icon">●</span>

            <div>
              <span>Atletas ativos</span>

              <strong>
                {
                  athletes.filter(
                    (athlete) => athlete.active,
                  ).length
                }
              </strong>

              <small>em acompanhamento</small>
            </div>
          </article>

          <article className="stat-card">
            <span className="stat-icon stat-blue">↗</span>

            <div>
              <span>Total de atletas</span>
              <strong>{athletes.length}</strong>
              <small>cadastros na equipe</small>
            </div>
          </article>

          <article className="stat-card">
            <span className="stat-icon stat-amber">✓</span>

            <div>
              <span>Próximo passo</span>
              <strong>Avaliar</strong>
              <small>atualize o VDOT dos atletas</small>
            </div>
          </article>
        </section>

        <section
          id="atletas"
          className="section-heading"
        >
          <div>
            <p className="eyebrow">EQUIPE</p>
            <h2>Seus atletas</h2>
          </div>

          <span>{athletes.length} cadastrados</span>
        </section>

        <form
          className="search-row"
          onSubmit={handleSearchSubmit}
        >
          <input
            type="text"
            placeholder="Buscar por nome..."
            value={search}
            onChange={(event) =>
              setSearch(event.target.value)
            }
          />

          <button
            type="submit"
            className="btn-ghost"
          >
            Buscar
          </button>
        </form>

        {showForm && (
          <form
            className="card new-athlete-form"
            onSubmit={handleCreateAthlete}
          >
            <div className="form-grid">
              <label>
                Nome

                <input
                  required
                  value={athleteForm.name}
                  onChange={(event) =>
                    setAthleteForm({
                      ...athleteForm,
                      name: event.target.value,
                    })
                  }
                />
              </label>

              <label>
                Telefone

                <input
                  value={athleteForm.phone}
                  onChange={(event) =>
                    setAthleteForm({
                      ...athleteForm,
                      phone: event.target.value,
                    })
                  }
                />
              </label>

              <label>
                E-mail

                <input
                  type="email"
                  value={athleteForm.email}
                  onChange={(event) =>
                    setAthleteForm({
                      ...athleteForm,
                      email: event.target.value,
                    })
                  }
                />
              </label>

              <label>
                Objetivo

                <input
                  placeholder="Ex: Maratona, 10K..."
                  value={athleteForm.goal}
                  onChange={(event) =>
                    setAthleteForm({
                      ...athleteForm,
                      goal: event.target.value,
                    })
                  }
                />
              </label>
            </div>

            <label className="notes-label">
              Observações

              <textarea
                rows={2}
                value={athleteForm.notes}
                onChange={(event) =>
                  setAthleteForm({
                    ...athleteForm,
                    notes: event.target.value,
                  })
                }
              />
            </label>

            <button
              type="submit"
              className="btn-primary"
            >
              Salvar atleta
            </button>
          </form>
        )}

        {error && (
          <div className="alert">
            {error}
          </div>
        )}

        {loading ? (
          <p className="muted">Carregando...</p>
        ) : athletes.length === 0 ? (
          <div className="empty-state">
            <p>Nenhum atleta cadastrado ainda.</p>

            <p className="muted">
              Use "+ Novo atleta" para começar.
            </p>
          </div>
        ) : (
          <table className="athletes-table">
            <thead>
              <tr>
                <th>Nome</th>
                <th>Contato</th>
                <th>Objetivo</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>

            <tbody>
              {athletes.map((athlete) => (
                <tr key={athlete.id}>
                  <td className="name-cell">
                    <button
                      type="button"
                      className="btn-link athlete-name-link"
                      onClick={() => openProfile(athlete)}
                    >
                      {athlete.name}
                    </button>
                  </td>

                  <td className="muted">
                    {athlete.phone || "Não informado"}
                  </td>

                  <td>
                    {athlete.goal || "—"}
                  </td>

                  <td>
                    <span
                      className={`badge ${
                        athlete.active
                          ? "badge-active"
                          : "badge-inactive"
                      }`}
                    >
                      {athlete.active
                        ? "Ativo"
                        : "Inativo"}
                    </span>
                  </td>

                  <td className="table-actions">
                    <button
                      type="button"
                      className="btn-link"
                      onClick={() =>
                        openEvaluations(athlete)
                      }
                    >
                      Avaliações
                    </button>

                    <button
                      type="button"
                      className="btn-link"
                      onClick={() =>
                        openTraining(athlete)
                      }
                    >
                      Planejamento
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </main>
    </div>
  );
}