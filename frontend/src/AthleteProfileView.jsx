import { useEffect, useState } from "react";
import { getAthleteProfile, getAthleteTrainingLoad } from "./api";

const questions = ["Supervisão médica por problema cardíaco", "Dor no peito durante atividade", "Dor no peito no último mês", "Desmaio ou tontura", "Problema ósseo ou articular", "Medicação para pressão ou coração", "Outro motivo médico para evitar exercício"];

function Item({ label, value }) {
  return <div className="viewer-item"><span>{label}</span><strong>{value || "Não informado"}</strong></div>;
}

function LoadChart({ points = [], metrics }) {
  if (!points.length) return <p className="muted">Ainda não há feedbacks suficientes para calcular a carga.</p>;
  const values = points.flatMap((point) => [point.fitness, point.fatigue, point.form]);
  const min = Math.min(...values, 0), max = Math.max(...values, 1), range = Math.max(max - min, 1);
  const line = (field) => points.map((point, index) => `${(index / Math.max(points.length - 1, 1)) * 100},${100 - ((point[field] - min) / range) * 100}`).join(" ");
  return <div className="load-chart"><svg viewBox="0 0 100 100" preserveAspectRatio="none"><line x1="0" y1={100 - ((0 - min) / range) * 100} x2="100" y2={100 - ((0 - min) / range) * 100} className="load-zero" /><polyline points={line("fitness")} className="load-fitness" /><polyline points={line("fatigue")} className="load-fatigue" /><polyline points={line("form")} className="load-form" /></svg><div className="load-legend"><span className="fitness">Fitness</span><span className="fatigue">Fadiga</span><span className="form">Forma</span>{metrics && <div className="load-chart-meta"><span title="Monotonia">MON {metrics.monotony || "—"}</span><span title="Strain">STR {metrics.strain || "—"}</span><span title="Feedbacks recebidos">FB {metrics.feedbackCount}</span></div>}</div></div>;
}

export default function AthleteProfileView({ athlete, onClose, onRemove }) {
  const [profile, setProfile] = useState(null);
  const [load, setLoad] = useState(null);
  const [loadError, setLoadError] = useState("");
  const [tab, setTab] = useState("personal");
  useEffect(() => { getAthleteProfile(athlete.id).then(setProfile).catch(() => setProfile({ personal: {}, parq: {}, training: {} })); getAthleteTrainingLoad(athlete.id).then(setLoad).catch((error) => { setLoad(null); setLoadError(error.message); }); }, [athlete.id]);
  if (!profile) return <main className="profile-page"><p className="muted">Carregando perfil…</p></main>;
  const personal = profile.personal || {}, parq = profile.parq || {}, training = profile.training || {};
  const currentLoad = load?.points?.at(-1);
  return <main className="profile-page">
    <header className="topbar"><div className="brand"><span className="brand-logo"><img src="/logo-horizontal.png?v=2" alt="RunCore" /></span><div><h1>Cadastro do aluno</h1><p>Aluno: {athlete.name}</p></div></div><div className="header-actions"><button className="btn-link-danger" onClick={onRemove}>Remover atleta</button><button className="btn-ghost" onClick={onClose}>Voltar para atletas</button></div></header>
    <section className="profile-content"><div className="profile-tabs"><button className={tab === "personal" ? "active" : ""} onClick={() => setTab("personal")}>Dados pessoais</button><button className={tab === "parq" ? "active" : ""} onClick={() => setTab("parq")}>PAR-Q e saúde</button><button className={tab === "training" ? "active" : ""} onClick={() => setTab("training")}>Dados de treino</button><button className={tab === "load" ? "active" : ""} onClick={() => setTab("load")}>Carga de treino</button></div>
      {tab === "personal" && <section className="profile-card"><h2>Dados pessoais</h2><div className="viewer-grid"><Item label="Nome" value={personal.name}/><Item label="E-mail" value={personal.email}/><Item label="Celular" value={personal.phone}/><Item label="Objetivo inicial" value={personal.goal}/><Item label="Sexo" value={personal.sex}/><Item label="Nascimento" value={personal.birth_date}/><Item label="CPF" value={personal.cpf}/><Item label="Endereço" value={[personal.address, personal.address_number, personal.address_extra].filter(Boolean).join(", ")}/><Item label="Bairro" value={personal.neighborhood}/><Item label="Cidade / UF" value={[personal.city, personal.state].filter(Boolean).join(" / ")}/><Item label="Profissão" value={personal.profession}/><Item label="Empresa" value={personal.company}/><Item label="Instagram" value={personal.instagram}/></div></section>}
      {tab === "parq" && <section className="profile-card"><h2>PAR-Q e dados de saúde</h2><div className="viewer-grid"><Item label="Tipo sanguíneo" value={parq.blood_type}/><Item label="Plano de saúde" value={parq.health_plan}/><Item label="Contato de emergência" value={parq.emergency_contact}/><Item label="Telefone de emergência" value={parq.emergency_phone}/><Item label="Restrição médica" value={parq.medical_restriction}/></div><div className="viewer-questions">{questions.map((question, index) => <Item key={question} label={question} value={parq[`q${index + 1}`]}/>)}</div></section>}
      {tab === "training" && <section className="profile-card"><h2>Dados de treino</h2><div className="viewer-grid"><Item label="Dias disponíveis" value={(training.days || []).join(", ")}/><Item label="Horário preferido" value={training.preferred_time}/><Item label="Local" value={training.location}/><Item label="Modalidade" value={training.modality}/><Item label="Objetivo" value={training.goal}/></div></section>}
      {tab === "load" && <section className="profile-card"><h2>Carga de treinamento</h2><p className="muted">Calculada a partir de PSE × tempo em movimento, informado pelo aluno após as atividades.</p>{load ? <><div className="load-overview"><div className="load-highlights"><article className="load-highlight fitness"><span>Fitness</span><strong>{currentLoad?.fitness?.toFixed(1) || "0.0"}</strong></article><article className="load-highlight load"><span>Carga</span><strong>{load.weekly_load.toFixed(0)}</strong></article><article className="load-highlight form"><span>Forma</span><strong>{currentLoad?.form?.toFixed(1) || "0.0"}</strong></article></div></div><LoadChart points={load.points} metrics={{ monotony: load.monotony, strain: load.strain, feedbackCount: load.feedback_count }}/></> : <p className={loadError ? "alert" : "muted"}>{loadError || "Aguardando feedbacks das atividades do aluno."}</p>}</section>}
    </section>
  </main>;
}
