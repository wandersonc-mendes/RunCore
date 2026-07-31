import { useEffect, useState } from "react";
import { getStudentProfile, saveStudentProfile } from "./api";

const questions = [
  "Seu médico já recomendou supervisão para atividade física por problema cardíaco?",
  "Você sente dor no peito durante atividades físicas?",
  "Você sentiu dor no peito no último mês?",
  "Você já perdeu a consciência ou sofreu queda por tontura?",
  "Você tem problema ósseo ou articular que pode piorar com exercício?",
  "Algum médico prescreveu medicamento para pressão ou coração?",
  "Há algum outro motivo médico para evitar exercício sem supervisão?",
];

function Field({ label, name, data, setData, type = "text" }) {
  return <label>{label}<input type={type} value={data[name] || ""} onChange={(event) => setData({ ...data, [name]: event.target.value })} /></label>;
}

const states = ["AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"];

function PhoneField({ data, setData }) {
  function change(value) {
    const digits = value.replace(/\D/g, "").slice(0, 11);
    const formatted = digits.length <= 2 ? digits : `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}${digits.length > 7 ? `-${digits.slice(7)}` : ""}`;
    setData({ ...data, phone: formatted });
  }
  return <label>Celular<input inputMode="numeric" placeholder="(27) 99999-9999" value={data.phone || ""} onChange={(event) => change(event.target.value)} /></label>;
}

function ZipField({ data, setData }) {
  const [loading, setLoading] = useState(false);
  async function change(value) {
    const digits = value.replace(/\D/g, "").slice(0, 8);
    const zip = digits.length > 5 ? `${digits.slice(0, 5)}-${digits.slice(5)}` : digits;
    setData({ ...data, zip_code: zip });
    if (digits.length !== 8) return;
    setLoading(true);
    try {
      const response = await fetch(`https://viacep.com.br/ws/${digits}/json/`);
      const result = await response.json();
      if (!result.erro) setData({ ...data, zip_code: zip, address: result.logradouro || data.address || "", neighborhood: result.bairro || data.neighborhood || "", city: result.localidade || data.city || "", state: result.uf || data.state || "" });
    } finally { setLoading(false); }
  }
  return <label>CEP<input inputMode="numeric" placeholder="00000-000" value={data.zip_code || ""} onChange={(event) => change(event.target.value)} />{loading && <small>Buscando endereço…</small>}</label>;
}

export default function ProfilePanel({
  onClose,
  onboarding = false,
  onSaved,
}) {
  const [tab, setTab] = useState("personal");
  const [profile, setProfile] = useState({ personal: {}, parq: {}, training: {} });
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => { getStudentProfile().then(setProfile).catch((error) => setMessage(error.message)); }, []);
  const personal = profile.personal || {}, parq = profile.parq || {}, training = profile.training || {};
  const setPersonal = (value) => setProfile({ ...profile, personal: value });
  const setParq = (value) => setProfile({ ...profile, parq: value });
  const setTraining = (value) => setProfile({ ...profile, training: value });
  async function save() {
    setSaving(true);
    setMessage("");

    try {
      const savedProfile = await saveStudentProfile(profile);
      setProfile(savedProfile);

      if (savedProfile.complete) {
        setMessage("Cadastro concluído com sucesso.");
      } else {
        setMessage(
          `Complete os campos obrigatórios: ${
            savedProfile.missing_fields.join(", ")
          }.`,
        );
      }

      onSaved?.(savedProfile);
    } catch (error) {
      setMessage(error.message);
    } finally {
      setSaving(false);
    }
  }

  return <main className="profile-page"><header className="student-header"><div className="brand"><span className="profile-brand-symbol"><img src="/logo-symbol-mark.png?v=1" alt="RunCore" /></span><div><h1>{onboarding ? "Complete seu cadastro" : "Meu perfil"}</h1><p>{onboarding ? "Preencha os dados essenciais para liberar seu acesso ao RunCore" : "Complete seus dados para o acompanhamento"}</p></div></div>{!onboarding && <button className="btn-ghost" onClick={onClose}>Voltar</button>}</header><section className="profile-content"><div className="profile-tabs"><button className={tab === "personal" ? "active" : ""} onClick={() => setTab("personal")}>Dados pessoais</button><button className={tab === "parq" ? "active" : ""} onClick={() => setTab("parq")}>PAR-Q e saúde</button><button className={tab === "training" ? "active" : ""} onClick={() => setTab("training")}>Dados de treino</button></div>
    {tab === "personal" && <section className="profile-card"><h2>Dados pessoais</h2><p>Informações pessoais, endereço e informações complementares.</p><div className="profile-grid"><Field label="Nome completo" name="name" data={personal} setData={setPersonal}/><Field label="Apelido" name="nickname" data={personal} setData={setPersonal}/><Field label="Data de nascimento" name="birth_date" type="date" data={personal} setData={setPersonal}/><label>Sexo<select value={personal.sex || ""} onChange={(event) => setPersonal({ ...personal, sex: event.target.value })}><option value="">Selecione</option><option>Feminino</option><option>Masculino</option><option>Não informar</option></select></label><PhoneField data={personal} setData={setPersonal}/><Field label="CPF" name="cpf" data={personal} setData={setPersonal}/><Field label="RG" name="rg" data={personal} setData={setPersonal}/><Field label="Tamanho da camiseta" name="shirt_size" data={personal} setData={setPersonal}/><ZipField data={personal} setData={setPersonal}/><Field label="Endereço" name="address" data={personal} setData={setPersonal}/><Field label="Número" name="address_number" data={personal} setData={setPersonal}/><Field label="Complemento" name="address_extra" data={personal} setData={setPersonal}/><Field label="Bairro" name="neighborhood" data={personal} setData={setPersonal}/><Field label="Cidade" name="city" data={personal} setData={setPersonal}/><label>Estado<select value={personal.state || ""} onChange={(event) => setPersonal({ ...personal, state: event.target.value })}><option value="">Selecione</option>{states.map((state) => <option key={state}>{state}</option>)}</select></label><Field label="Profissão" name="profession" data={personal} setData={setPersonal}/><Field label="Empresa" name="company" data={personal} setData={setPersonal}/><Field label="Instagram" name="instagram" data={personal} setData={setPersonal}/><Field label="Número do tênis" name="shoe_size" data={personal} setData={setPersonal}/></div></section>}
    {tab === "parq" && <section className="profile-card"><h2>PAR-Q e dados de saúde</h2><div className="profile-grid"><label>Tipo sanguíneo<select value={parq.blood_type || ""} onChange={(event) => setParq({ ...parq, blood_type: event.target.value })}><option value="">Selecione</option>{["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "Não informado"].map((type) => <option key={type}>{type}</option>)}</select></label><Field label="Plano de saúde" name="health_plan" data={parq} setData={setParq}/><Field label="Contato de emergência" name="emergency_contact" data={parq} setData={setParq}/><Field label="Telefone de emergência" name="emergency_phone" data={parq} setData={setParq}/><Field label="Restrição médica" name="medical_restriction" data={parq} setData={setParq}/><Field label="Situação do atestado" name="medical_certificate" data={parq} setData={setParq}/></div><div className="parq-questions">{questions.map((question, index) => <label key={question}><span>{index + 1}. {question}</span><select value={parq[`q${index + 1}`] || ""} onChange={(event) => setParq({ ...parq, [`q${index + 1}`]: event.target.value })}><option value="" disabled>Selecione</option><option value="Não">Não</option><option value="Sim">Sim</option></select></label>)}</div></section>}
    {tab === "training" && <section className="profile-card"><h2>Dados de treino</h2><p>Informe sua disponibilidade atual para que o treinador organize a planilha.</p><div className="training-days">{["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"].map((day) => <label key={day}><input type="checkbox" checked={(training.days || []).includes(day)} onChange={() => { const days = training.days || []; setTraining({ ...training, days: days.includes(day) ? days.filter((item) => item !== day) : [...days, day] }); }}/>{day}</label>)}</div><div className="profile-grid"><Field label="Horário preferido" name="preferred_time" data={training} setData={setTraining}/><Field label="Local de treino" name="location" data={training} setData={setTraining}/><Field label="Modalidade principal" name="modality" data={training} setData={setTraining}/><Field label="Objetivo atual" name="goal" data={training} setData={setTraining}/></div></section>}
    {message && <p className="profile-message">{message}</p>}<footer className="profile-actions"><button className="btn-primary" disabled={saving} onClick={save}>{saving ? "Salvando..." : "Salvar perfil"}</button></footer></section></main>;
}
