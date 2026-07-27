import { useEffect, useState } from "react";
import { clearSession, connectStrava, createGoal, deleteGoal, getActivityFeedback, getStravaActivityDetails, getStravaStatus, getStudentTraining, listGoals, listStravaActivities, saveActivityFeedback, syncStravaActivities } from "./api";
import ProfilePanel from "./ProfilePanel";

function formatDuration(seconds = 0) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainder = seconds % 60;
  return [hours, minutes, remainder].map((part) => String(part).padStart(2, "0")).join(":");
}

function formatPace(speed) {
  if (!speed) return "—";
  const seconds = Math.round(1000 / speed);
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}/km`;
}

function stepDistance(step) {
  return `${Number(step.distance).toFixed(step.distance_unit === "m" ? 0 : 1)} ${step.distance_unit || (step.repetitions ? "m" : "km")}`;
}

function stepTone(type = "") {
  const label = type.toLowerCase();
  if (label.includes("desaqueci")) return "cooldown";
  if (label.includes("aquecimento")) return "warmup";
  if (label.includes("descanso") || label.includes("recupera")) return "recovery";
  return "run";
}

function paceToSeconds(value) {
  const match = String(value || "").match(/^(\d{1,2}):(\d{2})$/);
  return match ? (Number(match[1]) * 60) + Number(match[2]) : null;
}

function plannedDistanceKm(step) {
  return Number(step.distance || 0) * ((step.distance_unit || (step.repetitions ? "m" : "km")) === "m" ? 0.001 : 1);
}

function statusForRange(value, low, high, fasterIsHigher = false) {
  if (!Number.isFinite(value) || !Number.isFinite(low) || !Number.isFinite(high)) return "unknown";
  const minimum = Math.min(low, high), maximum = Math.max(low, high);
  if (value >= minimum && value <= maximum) return "inside";
  if (fasterIsHigher) return value > maximum ? "above" : "below";
  return value < minimum ? "above" : "below";
}

function statusLabel(status, metric = "pace") {
  if (status === "inside") return "Dentro do planejado";
  if (status === "above") return metric === "pace" ? "Mais rápido que o planejado" : "Acima do planejado";
  if (status === "below") return metric === "pace" ? "Mais lento que o planejado" : "Abaixo do planejado";
  return "Sem referência suficiente";
}

function sessionForActivity(training, activity) {
  if (!training?.sessions || !activity?.start_at) return null;
  const date = new Date(activity.start_at).toISOString().slice(0, 10);
  return training.sessions.find((session) => session.session_date === date) || null;
}

function analyseActivity(training, activity, details) {
  const session = sessionForActivity(training, activity);
  if (!session) return null;
  const expectedSteps = session.steps.flatMap((step) => Array.from({ length: Math.max(1, Number(step.repetitions || 1)) }, () => ({ ...step, repetitions: 0 })));
  const plannedDistance = expectedSteps.reduce((total, step) => total + plannedDistanceKm(step), 0);
  const distanceStatus = statusForRange(activity.distance, plannedDistance * .92, plannedDistance * 1.08, true);
  const laps = details?.laps || [];
  const aligned = expectedSteps.length > 0 && laps.length >= expectedSteps.length;
  const blocks = aligned ? expectedSteps.map((step, index) => {
    const lap = laps[index];
    const expectedPaces = [paceToSeconds(step.pace_min), paceToSeconds(step.pace_max)].filter(Number.isFinite);
    const actualPace = lap.average_speed ? Math.round(1000 / lap.average_speed) : null;
    const paceStatus = expectedPaces.length === 2 ? statusForRange(actualPace, expectedPaces[0], expectedPaces[1]) : "unknown";
    const expectedDistance = plannedDistanceKm(step);
    const tolerance = Math.max(.05, expectedDistance * .16);
    const blockDistanceStatus = statusForRange(lap.distance, expectedDistance - tolerance, expectedDistance + tolerance, true);
    return { step, lap, paceStatus, distanceStatus: blockDistanceStatus, expectedDistance };
  }) : [];
  const inside = blocks.filter((block) => block.paceStatus === "inside" && block.distanceStatus === "inside").length;
  return { session, plannedDistance, distanceStatus, blocks, aligned, inside };
}

function WorkoutChart({ steps = [] }) {
  const chartWeight = (step) => Math.max(1, Math.sqrt(Number(step.distance || 0) * ((step.distance_unit || "km") === "km" ? 1000 : 1)));
  const paceSeconds = (value) => {
    const match = String(value || "").match(/^(\d{1,2}):(\d{2})$/);
    return match ? (Number(match[1]) * 60) + Number(match[2]) : null;
  };
  const weightedSteps = [];
  for (let index = 0; index < steps.length; index += 1) {
    const step = steps[index];
    const next = steps[index + 1];
    const repetitions = Math.max(1, Number(step.repetitions || 1));
    const nextIsRecovery = next && (stepTone(next.type) === "recovery");
    if (repetitions > 1 && nextIsRecovery) {
      for (let repetition = 0; repetition < repetitions; repetition += 1) {
        weightedSteps.push({ ...step, repetitions: 0, weight: chartWeight(step), chartKey: `${step.order}-run-${repetition}` });
        weightedSteps.push({ ...next, repetitions: 0, weight: chartWeight(next), chartKey: `${next.order}-recovery-${repetition}` });
      }
      index += 1;
    } else if (repetitions > 1) {
      for (let repetition = 0; repetition < repetitions; repetition += 1) weightedSteps.push({ ...step, repetitions: 0, weight: chartWeight(step), chartKey: `${step.order}-${repetition}` });
    } else {
      weightedSteps.push({ ...step, weight: chartWeight(step), chartKey: `${step.order}-single` });
    }
  }
  const pacedSegments = weightedSteps.map((step) => {
    const values = [paceSeconds(step.pace_min), paceSeconds(step.pace_max)].filter(Number.isFinite);
    return values.length ? values.reduce((total, value) => total + value, 0) / values.length : null;
  }).filter(Number.isFinite);
  const slowest = Math.max(...pacedSegments, 1);
  const fastest = Math.min(...pacedSegments, slowest);
  const chartHeight = (step) => {
    const values = [paceSeconds(step.pace_min), paceSeconds(step.pace_max)].filter(Number.isFinite);
    if (values.length) {
      const average = values.reduce((total, value) => total + value, 0) / values.length;
      const intensity = slowest === fastest ? .72 : (slowest - average) / (slowest - fastest);
      return `${54 + (intensity * 36)}%`;
    }
    if (stepTone(step.type) === "recovery") return "44%";
    if (stepTone(step.type) === "warmup" || stepTone(step.type) === "cooldown") return "56%";
    return "68%";
  };
  return <section className="workout-chart" aria-label="Gráfico da estrutura do treino">
    <div className="workout-chart-bars">{weightedSteps.map((step) => <div key={step.chartKey} className={`chart-segment ${stepTone(step.type)}`} style={{ flexGrow: step.weight, height: chartHeight(step) }} title={`${step.type}: ${stepDistance(step)} `}><span>{weightedSteps.length <= 7 ? step.type : ""}</span></div>)}</div>
    <div className="workout-chart-legend"><span className="warmup">Aquecimento</span><span className="run">Corrida</span><span className="recovery">Recuperação</span><span className="cooldown">Desaquecimento</span></div>
  </section>;
}

function activityMetric(activity) {
  if (!activity.distance || !activity.moving_time) return "Sem dados de distância";
  if (activity.sport_type === "Run") return `Pace médio: ${formatPace(activity.distance * 1000 / activity.moving_time)}`;
  return `Velocidade média: ${(activity.distance / (activity.moving_time / 3600)).toFixed(1)} km/h`;
}

export default function StudentPortal({ user, onLogout, view = "dashboard" }) {
  const [strava, setStrava] = useState(null);
  const [error, setError] = useState("");
  const [activities, setActivities] = useState([]);
  const [syncing, setSyncing] = useState(false);
  const [expandedActivity, setExpandedActivity] = useState(null);
  const [activityDetails, setActivityDetails] = useState({});
  const [activityFeedbacks, setActivityFeedbacks] = useState({});
  const [feedbackForms, setFeedbackForms] = useState({});
  const [savingFeedback, setSavingFeedback] = useState(null);
  const [loadingActivity, setLoadingActivity] = useState(null);
  const [training, setTraining] = useState(null);
  const [showActivities, setShowActivities] = useState(false);
  const [calculator, setCalculator] = useState(null);
  const [pace, setPace] = useState("05:00");
  const [distance, setDistance] = useState("10");
  const [goals, setGoals] = useState([]);
  const [goalForm, setGoalForm] = useState({ name: "", distance: "", target_date: "", priority: "Principal" });
  const [savingGoal, setSavingGoal] = useState(false);
  const [showProfile, setShowProfile] = useState(false);
  const [selectedSession, setSelectedSession] = useState(null);

  useEffect(() => {
    function loadStatus() {
      getStravaStatus()
        .then((status) => {
          setStrava(status);
          if (status.connected) listStravaActivities().then(setActivities).catch(() => {});
        })
        .catch((err) => setError(err.message));
      getStudentTraining().then(setTraining).catch(() => {});
      listGoals().then(setGoals).catch(() => {});
    }

    loadStatus();
    const interval = window.setInterval(loadStatus, 10000);
    window.addEventListener("focus", loadStatus);
    return () => {
      window.clearInterval(interval);
      window.removeEventListener("focus", loadStatus);
    };
  }, []);

  async function sync() {
    setSyncing(true);
    setError("");
    try {
      const result = await syncStravaActivities();
      setActivities(result.activities);
      setActivityDetails({});
    } catch (err) {
      setError(err.message);
    } finally {
      setSyncing(false);
    }
  }

  async function toggleActivity(activityId) {
    if (expandedActivity === activityId) {
      setExpandedActivity(null);
      return;
    }
    setExpandedActivity(activityId);
    if (activityDetails[activityId]) return;

    setLoadingActivity(activityId);
    try {
      const [details, feedback] = await Promise.all([getStravaActivityDetails(activityId), getActivityFeedback(activityId)]);
      setActivityDetails((current) => ({ ...current, [activityId]: details }));
      if (feedback) {
        setActivityFeedbacks((current) => ({ ...current, [activityId]: feedback }));
        setFeedbackForms((current) => ({ ...current, [activityId]: feedback }));
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingActivity(null);
    }
  }

  async function saveGoal(event) {
    event.preventDefault();
    setSavingGoal(true);
    setError("");
    try {
      const goal = await createGoal({ ...goalForm, distance: Number(goalForm.distance) });
      setGoals((current) => [...current, goal].sort((a, b) => a.target_date.localeCompare(b.target_date)));
      setGoalForm({ name: "", distance: "", target_date: "", priority: "Principal" });
    } catch (err) {
      setError(err.message);
    } finally {
      setSavingGoal(false);
    }
  }

  async function removeGoal(goalId) {
    try {
      await deleteGoal(goalId);
      setGoals((current) => current.filter((goal) => goal.id !== goalId));
    } catch (err) {
      setError(err.message);
    }
  }

  function feedbackFor(activityId) {
    return feedbackForms[activityId] || activityFeedbacks[activityId] || { perceived_effort: 5, feeling: "bem", pain: "", sleep_quality: "", pre_fatigue: "", notes: "" };
  }

  async function saveFeedback(activityId) {
    const form = feedbackFor(activityId);
    setSavingFeedback(activityId);
    setError("");
    try {
      const feedback = await saveActivityFeedback(activityId, {
        ...form,
        perceived_effort: Number(form.perceived_effort),
        sleep_quality: form.sleep_quality === "" ? null : Number(form.sleep_quality),
        pre_fatigue: form.pre_fatigue === "" ? null : Number(form.pre_fatigue),
      });
      setActivityFeedbacks((current) => ({ ...current, [activityId]: feedback }));
      setFeedbackForms((current) => ({ ...current, [activityId]: feedback }));
    } catch (err) { setError(err.message); } finally { setSavingFeedback(null); }
  }

  function changeFeedback(activityId, field, value) {
    setFeedbackForms((current) => ({ ...current, [activityId]: { ...feedbackFor(activityId), [field]: value } }));
  }

  const runs = activities.filter((activity) => activity.sport_type === "Run");
  const runDistance = runs.reduce((total, activity) => total + activity.distance, 0);
  const runTime = runs.reduce((total, activity) => total + activity.moving_time, 0);
  const currentWeekSessions = training?.sessions?.filter((session) => session.week === training.current_week) || [];
  const weekdays = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"];
  const paceParts = pace.split(":").map(Number);
  const paceSeconds = paceParts.length === 2 && paceParts.every(Number.isFinite) ? paceParts[0] * 60 + paceParts[1] : 0;
  const calculatorDistance = Number(distance) || 0;
  const velocity = paceSeconds ? 3600 / paceSeconds : 0;
  const predictedTime = paceSeconds * calculatorDistance;

  useEffect(() => {
    if (view === "activities") {
      setShowActivities(true);
    }

    if (view === "calculators") {
      setCalculator((current) => current || "pace");
    }
  }, [view]);

  if (showProfile || view === "profile") {
    return (
      <ProfilePanel
        onClose={() => setShowProfile(false)}
      />
    );
  }

  return (
    <main className="student-page routed-student-page" data-view={view}>
      <header className="student-header">
        <div className="brand"><span className="brand-logo"><img src="/logo-horizontal.png?v=2" alt="RunCore" />
        </span><div><h1>RunCore</h1><p>Área do aluno</p></div></div>
        <button className="btn-ghost" onClick={() => { clearSession(); onLogout(); }}>Sair</button>
      </header>
      <section className="student-hero"><p className="eyebrow">SEU TREINAMENTO</p><h2>Olá, {user.name}.</h2><p>Conecte suas atividades e acompanhe o plano criado pelo seu treinador.</p></section>
      <nav className="portal-menu student-nav" aria-label="Student navigation">
        <button onClick={() => document.getElementById("planilha")?.scrollIntoView({ behavior: "smooth", block: "start" })}>Planilha</button>
        <button onClick={() => document.getElementById("metas")?.scrollIntoView({ behavior: "smooth", block: "start" })}>Metas e provas</button>
        <button onClick={() => document.getElementById("resumo")?.scrollIntoView({ behavior: "smooth", block: "start" })}>Resumo</button>
        <button onClick={() => { setShowActivities(true); window.setTimeout(() => document.getElementById("activities")?.scrollIntoView({ behavior: "smooth", block: "start" }), 0); }}>Atividades</button>
        <div className="calculator-menu"><button onClick={() => setCalculator((current) => current ? null : "pace")}>Calculadoras</button></div>
        <button onClick={() => setShowProfile(true)}>Meu perfil</button>
      </nav>
      <section className="student-content">
        {view === "dashboard" && (
          <section className="student-dashboard-hero">
            <div>
              <p className="eyebrow">VISÃO GERAL</p>
              <h2>Olá, {user.name}.</h2>
              <p>
                Acompanhe sua semana de treino, suas atividades
                e sua evolução em um único lugar.
              </p>
            </div>

            <div className="student-dashboard-hero-brand">
              <span>RUNCORE</span>
              <strong>Seu treinamento em movimento</strong>
            </div>
          </section>
        )}

        <nav className="student-nav" aria-label="Navegação da área do aluno">
          <button onClick={() => document.getElementById("planilha")?.scrollIntoView({ behavior: "smooth", block: "start" })}>Planilha</button>
          <button onClick={() => setShowProfile(true)}>Perfil</button>
          <button onClick={() => document.getElementById("metas")?.scrollIntoView({ behavior: "smooth", block: "start" })}>Metas</button>
          <button onClick={() => document.getElementById("resumo")?.scrollIntoView({ behavior: "smooth", block: "start" })}>Resumo</button>
          <button onClick={() => { setShowActivities(true); window.setTimeout(() => document.getElementById("activities")?.scrollIntoView({ behavior: "smooth", block: "start" }), 0); }}>Atividades</button>
          <div className="calculator-menu"><button onClick={() => setCalculator((current) => current ? null : "pace")}>Calculadora</button></div>
        </nav>
        <section id="metas" className="goals-card">
          <div className="goals-heading"><div><p className="eyebrow">SEUS OBJETIVOS</p><h3>Metas e provas</h3></div><span>{goals.length} {goals.length === 1 ? "meta" : "metas"}</span></div>
          <form className="goal-form" onSubmit={saveGoal}><input required value={goalForm.name} onChange={(event) => setGoalForm((current) => ({ ...current, name: event.target.value }))} placeholder="Ex.: Maratona de Vitória" /><input required type="number" min="0.1" step="0.1" value={goalForm.distance} onChange={(event) => setGoalForm((current) => ({ ...current, distance: event.target.value }))} placeholder="Distância (km)" /><input required type="date" value={goalForm.target_date} onChange={(event) => setGoalForm((current) => ({ ...current, target_date: event.target.value }))} /><select value={goalForm.priority} onChange={(event) => setGoalForm((current) => ({ ...current, priority: event.target.value }))}><option>Principal</option><option>Secundária</option></select><button className="btn-primary" disabled={savingGoal}>{savingGoal ? "Salvando..." : "Adicionar"}</button></form>
          {goals.length > 0 ? <div className="goals-list">{goals.map((goal) => { const days = Math.ceil((new Date(`${goal.target_date}T00:00:00`) - new Date()) / 86400000); return <article key={goal.id}><div><strong>{goal.name}</strong><span>{goal.distance.toFixed(3)} km · {goal.priority}</span></div><b className={days < 0 ? "late" : ""}>{days < 0 ? `há ${Math.abs(days)} dias` : days === 0 ? "é hoje" : `faltam ${days} dias`}</b><button className="btn-ghost" onClick={() => removeGoal(goal.id)}>Remover</button></article>; })}</div> : <p className="muted">Adicione sua próxima prova ou objetivo de corrida.</p>}
        </section>
        {calculator && <section className="calculator-card">
          <div><p className="eyebrow">CALCULADORA</p><h3>{calculator === "pace" ? "Pace e velocidade" : "Previsão de tempo final"}</h3><div className="calculator-tabs"><button className={calculator === "pace" ? "active" : ""} onClick={() => setCalculator("pace")}>Pace</button><button className={calculator === "prediction" ? "active" : ""} onClick={() => setCalculator("prediction")}>Previsão</button></div></div>
          <label>Pace (min/km)<input value={pace} onChange={(event) => setPace(event.target.value)} placeholder="05:00" /></label>
          {calculator === "prediction" && <label>Distância (km)<input type="number" min="0" step="0.1" value={distance} onChange={(event) => setDistance(event.target.value)} /></label>}
          <strong>{calculator === "pace" ? `${velocity.toFixed(2)} km/h` : formatDuration(predictedTime)}</strong>
          <button className="btn-ghost" onClick={() => setCalculator(null)}>Fechar</button>
        </section>}
        <article className="connection-card">
          <div><span className="connection-logo">S</span><div><h3>Strava</h3><p>{strava?.connected ? "Conta conectada. Sincronize suas atividades quando quiser." : "Conecte sua conta para importar suas atividades."}</p></div></div>
          {strava?.connected ? <button className="btn-primary" disabled={syncing} onClick={sync}>{syncing ? "Sincronizando..." : "Sincronizar atividades"}</button> : <button className="btn-primary" disabled={!strava?.configured} onClick={() => connectStrava().catch((err) => setError(err.message))}>{strava ? "Conectar Strava" : "Verificando..."}</button>}
        </article>
        {strava && !strava.configured && <p className="muted">A integração Strava ainda está sendo configurada pelo treinador.</p>}
        {error && <div className="alert">{error}</div>}
        {strava?.connected && activities.length > 0 && <section id="resumo" className="student-stats" aria-label="Resumo das atividades importadas">
          <article><span>Atividades</span><strong>{activities.length}</strong><small>importadas</small></article>
          <article><span>Corridas</span><strong>{runs.length}</strong><small>registradas</small></article>
          <article><span>Quilometragem</span><strong>{runDistance.toFixed(1)} km</strong><small>em corridas</small></article>
          <article><span>Tempo correndo</span><strong>{formatDuration(runTime)}</strong><small>em movimento</small></article>
        </section>}
        {strava?.connected && <article id="activities" className={`activity-card ${showActivities ? "is-open" : "is-collapsed"}`}>
          <div className="activity-card-heading"><h3>Atividades recentes</h3><button className="btn-ghost activity-collapse" onClick={() => setShowActivities((current) => !current)}>{showActivities ? "Recolher" : "Ver atividades"}</button></div>
          {activities.length === 0 ? <p className="muted">Nenhuma atividade importada ainda. Clique em “Sincronizar atividades”.</p> : <div className="activity-list">
            {activities.map((activity) => {
              const expanded = expandedActivity === activity.id;
              const details = activityDetails[activity.id];
              const analysis = analyseActivity(training, activity, details);
              return <article className={`activity-row ${expanded ? "expanded" : ""}`} key={activity.id}>
                <button className="activity-toggle" onClick={() => toggleActivity(activity.id)}>
                  <div><strong>{activity.name}</strong><span>{activity.sport_type} · {activity.distance.toFixed(2)} km · {Math.floor(activity.moving_time / 60)} min</span></div><b>{expanded ? "−" : "+"}</b>
                </button>
                {expanded && <section className="activity-details">
                  {loadingActivity === activity.id ? <p className="muted">Carregando detalhes do Strava…</p> : <>
                    <div><span>Distância</span><strong>{activity.distance.toFixed(2)} km</strong></div>
                    <div><span>Tempo em movimento</span><strong>{formatDuration(activity.moving_time)}</strong></div>
                    <div><span>{activity.sport_type === "Run" ? "Pace médio" : "Velocidade média"}</span><strong>{activityMetric(activity).replace(/^(Pace médio: |Velocidade média: )/, "")}</strong></div>
                    <div><span>Elevação</span><strong>{details?.total_elevation_gain == null ? "Não informada" : `${Math.round(details.total_elevation_gain)} m`}</strong></div>
                    <div><span>FC média</span><strong>{details?.average_heartrate ? `${Math.round(details.average_heartrate)} bpm` : "Não informada"}</strong></div>
                    <div><span>FC máxima</span><strong>{details?.max_heartrate ? `${Math.round(details.max_heartrate)} bpm` : "Não informada"}</strong></div>
                    <div><span>Cadência média</span><strong>{details?.average_cadence ? `${Math.round(details.average_cadence)} spm` : "Não informada"}</strong></div>
                    <div><span>Data</span><strong>{activity.start_at ? new Intl.DateTimeFormat("pt-BR", { dateStyle: "medium" }).format(new Date(activity.start_at)) : "Não informada"}</strong></div>
                    {analysis && <section className="adherence-card"><div className="adherence-heading"><div><span>ADERÊNCIA AO TREINO</span><strong>{analysis.session.workout_name}</strong></div><b className={`adherence-status ${analysis.distanceStatus}`}>{statusLabel(analysis.distanceStatus, "distance")}</b></div><p>Planejado: {analysis.plannedDistance.toFixed(2)} km · Executado: {activity.distance.toFixed(2)} km</p>{analysis.aligned ? <><strong className="adherence-result">{analysis.inside} de {analysis.blocks.length} blocos dentro do planejado</strong><div className="adherence-blocks">{analysis.blocks.map((block, index) => <div className="adherence-block" key={`${block.step.order}-${index}`}><span>{block.step.type} {index + 1}</span><div><b className={`adherence-dot ${block.paceStatus}`} title={statusLabel(block.paceStatus)}></b><strong>{formatPace(block.lap.average_speed)}</strong><small>{block.lap.distance.toFixed(2)} km · alvo {block.expectedDistance.toFixed(2)} km</small></div><em className={block.paceStatus}>{statusLabel(block.paceStatus)}</em></div>)}</div></> : <p className="muted">As voltas importadas não correspondem diretamente às etapas do plano; por enquanto, a comparação está disponível para a sessão como um todo.</p>}</section>}
                    {details?.laps?.length > 0 && <div className="laps"><strong>Parciais</strong>{details.laps.map((lap) => <div className="lap" key={lap.number}><div className="lap-main"><strong>Volta {lap.number} — {formatDuration(lap.moving_time)}</strong><span>{lap.distance.toFixed(2)} km · {formatPace(lap.average_speed)}</span></div><small>{lap.average_heartrate ? `${Math.round(lap.average_heartrate)} bpm` : "FC não informada"} · {lap.elevation_gain == null ? "elevação não informada" : `${Math.round(lap.elevation_gain)} m`}</small></div>)}</div>}
                    <section className="training-feedback">
                      <div className="feedback-heading"><div><span>SEU RELATO</span><h4>Como foi este treino?</h4></div>{activityFeedbacks[activity.id] && <b>Registrado</b>}</div>
                      <p>Seu feedback complementa os dados do relógio e alimenta a carga de treinamento.</p>
                      <div className="feedback-fields">
                        <label>PSE (1 a 10)<select value={feedbackFor(activity.id).perceived_effort} onChange={(event) => changeFeedback(activity.id, "perceived_effort", event.target.value)}>{Array.from({ length: 10 }, (_, index) => <option key={index + 1} value={index + 1}>{index + 1}</option>)}</select></label>
                        <label>Como se sentiu?<select value={feedbackFor(activity.id).feeling} onChange={(event) => changeFeedback(activity.id, "feeling", event.target.value)}><option value="otimo">Ótimo</option><option value="bem">Bem</option><option value="pesado">Pesado</option><option value="muito_dificil">Muito difícil</option></select></label>
                        <label>Sono (1 a 5)<select value={feedbackFor(activity.id).sleep_quality} onChange={(event) => changeFeedback(activity.id, "sleep_quality", event.target.value)}><option value="">Não informar</option>{[1, 2, 3, 4, 5].map((value) => <option key={value} value={value}>{value}</option>)}</select></label>
                        <label>Fadiga antes (1 a 5)<select value={feedbackFor(activity.id).pre_fatigue} onChange={(event) => changeFeedback(activity.id, "pre_fatigue", event.target.value)}><option value="">Não informar</option>{[1, 2, 3, 4, 5].map((value) => <option key={value} value={value}>{value}</option>)}</select></label>
                      </div>
                      <label>Houve dor ou desconforto?<input value={feedbackFor(activity.id).pain} onChange={(event) => changeFeedback(activity.id, "pain", event.target.value)} placeholder="Ex.: panturrilha direita leve" /></label>
                      <label>Comentário do aluno<textarea rows="2" value={feedbackFor(activity.id).notes} onChange={(event) => changeFeedback(activity.id, "notes", event.target.value)} placeholder="Conte ao treinador como o treino aconteceu." /></label>
                      <button type="button" className="btn-primary" disabled={savingFeedback === activity.id} onClick={() => saveFeedback(activity.id)}>{savingFeedback === activity.id ? "Salvando..." : "Salvar feedback"}</button>
                    </section>
                  </>}
                </section>}
              </article>;
            })}
          </div>}
        </article>}
        {training ? <article id="planilha" className="student-plan">
          <div className="student-plan-heading">
            <div className="student-plan-title-block">
              <div className="student-plan-kicker">
                <p className="eyebrow">
                  SUA PLANILHA · {training.current_phase}
                </p>

                <span>
                  Semana {training.current_week} de {training.total_weeks}
                </span>
              </div>

              <div className="student-plan-name-row">
                <h3>{training.name}</h3>

                <strong>
                  Meta: {
                    goals.find(
                      (goal) =>
                        goal.priority === "Principal"
                        && goal.target_date
                        && new Date(`${goal.target_date}T23:59:59`)
                          >= new Date(),
                    )?.name
                    || training.objective
                    || `${training.target_distance.toFixed(1)} km`
                  }
                </strong>
              </div>
            </div>
          </div>

          <div className="student-sessions">
            {currentWeekSessions.map((session) => (
              <article key={session.id}>
                <span>{weekdays[session.weekday] || "Treino"}</span>
                <strong>{session.workout_name}</strong>
                <small>{session.zone}</small>
                <b>
                  {session.repetitions
                    ? `${session.repetitions} × ${session.planned_distance} m`
                    : `${session.planned_distance.toFixed(1)} km`}
                </b>
                <p>
                  {session.steps?.[0]?.notes
                    || "Confira os detalhes do treino com seu treinador."}
                </p>
                <button
                  className="btn-link"
                  onClick={() => setSelectedSession(session)}
                >
                  Ver estrutura e benefícios
                </button>
              </article>
            ))}
          </div>
        </article> : <article id="planilha" className="student-empty"><h3>Planilha</h3><p>Seu plano e a execução dos treinos aparecerão aqui após o vínculo com seu treinador.</p></article>}
      </section>
      {selectedSession && <div className="student-session-modal-backdrop" role="presentation" onMouseDown={() => setSelectedSession(null)}><section className="student-session-modal" role="dialog" aria-modal="true" aria-labelledby="student-session-title" onMouseDown={(event) => event.stopPropagation()}><header><div><span>{weekdays[selectedSession.weekday] || "Treino"} · Semana {selectedSession.week}</span><h3 id="student-session-title">{selectedSession.workout_name}</h3><p>{selectedSession.zone} · {selectedSession.repetitions ? `${selectedSession.repetitions} × ${selectedSession.planned_distance} m` : `${selectedSession.planned_distance.toFixed(1)} km`}</p></div><button className="modal-close" onClick={() => setSelectedSession(null)} aria-label="Fechar">×</button></header><WorkoutChart steps={selectedSession.steps} /><section><h4>Como executar</h4><ol>{selectedSession.steps?.map((step) => <li className={`workout-step ${stepTone(step.type)}`} key={step.order}><strong>{step.type}</strong><span>{step.repetitions ? `${step.repetitions} × ${stepDistance(step)}` : stepDistance(step)} · {step.pace_min}–{step.pace_max}/km{step.recovery ? ` · recuperação: ${step.recovery}` : ""}</span><small>{step.notes}</small></li>)}</ol></section><section className="student-adaptations"><h4>Benefícios e adaptações</h4><ul>{selectedSession.adaptations?.map((adaptation) => <li key={adaptation}>{adaptation}</li>)}</ul></section><footer><button className="btn-ghost" onClick={() => setSelectedSession(null)}>Fechar</button></footer></section></div>}
    </main>
  );
}
