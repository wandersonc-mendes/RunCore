import { useState } from "react";

import {
  login,
  register,
  saveSession,
} from "./api";


export default function LoginScreen({
  onAuthenticated,
}) {
  const inviteToken = new URLSearchParams(
    window.location.search,
  ).get("invite");

  const [mode, setMode] = useState(
    inviteToken
      ? "student-register"
      : "login",
  );

  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
  });

  const [loginRole, setLoginRole] = useState(
    "coach",
  );

  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [saving, setSaving] = useState(false);

  const registeringStudent = (
    mode === "student-register"
  );

  const registeringCoach = (
    mode === "coach-register"
  );

  const registrationComplete = (
    mode === "student-pending"
  );


  async function submit(
    event,
  ) {
    event.preventDefault();

    if (saving) {
      return;
    }

    setSaving(true);
    setError("");
    setMessage("");

    try {
      if (mode === "login") {
        const session = await login({
          email: form.email,
          password: form.password,
          role: loginRole,
        });

        saveSession(
          session,
        );

        onAuthenticated(
          session.user,
        );

        return;
      }

      const result = await register({
        name: form.name,
        email: form.email,
        password: form.password,
        role: registeringStudent
          ? "student"
          : "coach",
        invite_token: registeringStudent
          ? inviteToken
          : null,
      });

      if (
        registeringStudent
        && result.pending_approval
      ) {
        setMode(
          "student-pending",
        );

        setMessage(
          result.message
          || "Pré-cadastro enviado. Aguarde a aprovação do treinador.",
        );

        setForm({
          name: "",
          email: "",
          password: "",
        });

        return;
      }

      if (
        !result.token
        || !result.user
      ) {
        throw new Error(
          "O servidor não retornou uma sessão válida.",
        );
      }

      saveSession(
        result,
      );

      onAuthenticated(
        result.user,
      );
    } catch (err) {
      setError(
        err.message
        || "Não foi possível concluir a solicitação.",
      );
    } finally {
      setSaving(false);
    }
  }


  function showLogin() {
    setMode(
      "login",
    );

    setError("");
    setMessage("");

    setForm({
      name: "",
      email: "",
      password: "",
    });

    const cleanUrl = (
      `${window.location.origin}${window.location.pathname}`
    );

    window.history.replaceState(
      {},
      "",
      cleanUrl,
    );
  }


  function showCoachRegistration() {
    setMode(
      "coach-register",
    );

    setError("");
    setMessage("");

    setForm({
      name: "",
      email: "",
      password: "",
    });
  }


  if (registrationComplete) {
    return (
      <main className="login-page">
        <section className="login-card">
          <span className="brand-mark">
            RC
          </span>

          <h1>
            RunCore
          </h1>

          <p>
            Cadastro enviado
          </p>

          <div className="alert">
            {message}
          </div>

          <p className="muted">
            O acesso será liberado depois que o treinador aprovar seu cadastro.
          </p>

          <button
            type="button"
            className="btn-primary"
            onClick={showLogin}
          >
            Voltar para o login
          </button>
        </section>
      </main>
    );
  }


  return (
    <main className="login-page">
      <section className="login-card">
        <span className="brand-mark">
          RC
        </span>

        <h1>
          RunCore
        </h1>

        <p>
          {
            registeringStudent
              ? "Pré-cadastro de aluno"
              : registeringCoach
                ? "Cadastro de treinador"
                : `Entrar como ${
                    loginRole === "coach"
                      ? "treinador"
                      : "atleta"
                  }`
          }
        </p>

        {
          mode === "login"
          && (
            <div className="login-role-choice">
              <button
                type="button"
                className={
                  loginRole === "coach"
                    ? "active"
                    : ""
                }
                onClick={() => {
                  setLoginRole(
                    "coach",
                  );

                  setError("");
                }}
              >
                Sou treinador
              </button>

              <button
                type="button"
                className={
                  loginRole === "student"
                    ? "active"
                    : ""
                }
                onClick={() => {
                  setLoginRole(
                    "student",
                  );

                  setError("");
                }}
              >
                Sou atleta
              </button>
            </div>
          )
        }

        <form onSubmit={submit}>
          {
            (
              registeringStudent
              || registeringCoach
            )
            && (
              <label>
                Nome

                <input
                  required
                  minLength="2"
                  maxLength="120"
                  value={form.name}
                  onChange={(event) => {
                    setForm({
                      ...form,
                      name: event.target.value,
                    });
                  }}
                />
              </label>
            )
          }

          {
            registeringStudent
            && (
              <p className="muted">
                Seu cadastro ficará aguardando a aprovação do treinador.
              </p>
            )
          }

          {
            registeringCoach
            && (
              <p className="muted">
                Crie sua conta para administrar atletas e planejamentos.
              </p>
            )
          }

          <label>
            E-mail

            <input
              type="email"
              required
              value={form.email}
              onChange={(event) => {
                setForm({
                  ...form,
                  email: event.target.value,
                });
              }}
            />
          </label>

          <label>
            Senha

            <input
              type="password"
              required
              minLength="8"
              maxLength="128"
              value={form.password}
              onChange={(event) => {
                setForm({
                  ...form,
                  password: event.target.value,
                });
              }}
            />
          </label>

          {
            error
            && (
              <div className="alert">
                {error}
              </div>
            )
          }

          <button
            className="btn-primary"
            disabled={saving}
          >
            {
              saving
                ? "Aguarde..."
                : mode === "login"
                  ? "Entrar"
                  : registeringCoach
                    ? "Criar conta de treinador"
                    : "Enviar pré-cadastro"
            }
          </button>
        </form>

        {
          !inviteToken
          && (
            <div className="auth-actions">
              {
                mode === "login"
                  ? (
                    <button
                      type="button"
                      className="auth-switch"
                      onClick={showCoachRegistration}
                    >
                      Cadastrar novo treinador
                    </button>
                  )
                  : (
                    <button
                      type="button"
                      className="auth-switch"
                      onClick={showLogin}
                    >
                      Já tenho uma conta
                    </button>
                  )
              }

              <small>
                {
                  loginRole === "student"
                    ? "Ainda não possui acesso? Solicite o link de convite ao seu treinador."
                    : "Alunos entram pelo link de convite enviado pelo treinador."
                }
              </small>
            </div>
          )
        }
      </section>
    </main>
  );
}