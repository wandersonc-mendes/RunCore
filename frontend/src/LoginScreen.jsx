import { useState } from "react";
import { login, register, saveSession } from "./api";

export default function LoginScreen({ onAuthenticated }) {
  const inviteToken = new URLSearchParams(window.location.search).get("invite");
  const [mode, setMode] = useState(inviteToken ? "student-register" : "login");
  const [form, setForm] = useState({ name: "", email: "", password: "", role: "coach" });
  const [loginRole, setLoginRole] = useState("coach");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const registeringStudent = mode === "student-register";
  const registeringCoach = mode === "coach-register";

  async function submit(event) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      const session = mode === "login"
        ? await login(form)
        : await register({ ...form, role: registeringStudent ? "student" : "coach", invite_token: inviteToken });
      saveSession(session);
      onAuthenticated(session.user);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  function showLogin() {
    setMode("login");
    setError("");
  }

  return <main className="login-page"><section className="login-card">
    <span className="brand-mark">RC</span>
    <h1>RunCore</h1>
    <p>{registeringStudent ? "Pré-cadastro de aluno" : registeringCoach ? "Cadastro de treinador" : `Entrar como ${loginRole === "coach" ? "treinador" : "atleta"}`}</p>
    {mode === "login" && <div className="login-role-choice"><button type="button" className={loginRole === "coach" ? "active" : ""} onClick={() => setLoginRole("coach")}>Sou treinador</button><button type="button" className={loginRole === "student" ? "active" : ""} onClick={() => setLoginRole("student")}>Sou atleta</button></div>}
    <form onSubmit={submit}>
      {(registeringStudent || registeringCoach) && <label>Nome<input required value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} /></label>}
      {registeringStudent && <p className="muted">Seu cadastro ficará aguardando a aprovação do treinador.</p>}
      {registeringCoach && <p className="muted">Crie sua conta para administrar atletas e planejamentos.</p>}
      <label>E-mail<input type="email" required value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} /></label>
      <label>Senha<input type="password" required minLength="8" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} /></label>
      {error && <div className="alert">{error}</div>}
      <button className="btn-primary" disabled={saving}>{saving ? "Aguarde..." : mode === "login" ? "Entrar" : registeringCoach ? "Criar conta de treinador" : "Enviar pré-cadastro"}</button>
    </form>
    {!inviteToken && <div className="auth-actions">{mode === "login" ? <button className="auth-switch" onClick={() => setMode("coach-register")}>Cadastrar novo treinador</button> : <button className="auth-switch" onClick={showLogin}>Já tenho uma conta</button>}<small>{loginRole === "student" ? "Ainda não possui acesso? Solicite o link de convite ao seu treinador." : "Alunos entram pelo link de convite enviado pelo treinador."}</small></div>}
  </section></main>;
}
