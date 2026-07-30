import { useState } from "react";

import {
  forgotPassword,
  login,
  register,
  resetPassword,
  saveSession,
} from "./api";


function LoginInstitutionalFooter() {
  return (
    <footer className="login-institutional-footer">
      <div className="login-footer-platforms">
        <span>Tecnologia e infraestrutura</span>

        <div aria-label="Serviços utilizados pelo RunCore">
          <strong className="login-provider cloudflare">
            Cloudflare
          </strong>

          <strong className="login-provider railway">
            Railway
          </strong>

          <strong className="login-provider supabase">
            Supabase
          </strong>
        </div>
      </div>

      <p>
        © 2026 RunCore. Todos os direitos reservados.
        <span aria-hidden="true"> · </span>
        Desenvolvido por Wanderson Mendes.
      </p>
    </footer>
  );
}


export default function LoginScreen({
  onAuthenticated,
}) {
  const urlParams = new URLSearchParams(
    window.location.search,
  );

  const inviteToken = urlParams.get(
    "invite",
  );

  const urlResetToken = (
    urlParams.get("reset_token")
    || urlParams.get("token")
    || ""
  );

  const [mode, setMode] = useState(
    inviteToken
      ? "student-register"
      : urlResetToken
        ? "reset-password"
        : "login",
  );

  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
  });

  const [confirmPassword, setConfirmPassword] = useState(
    "",
  );

  const [resetToken, setResetToken] = useState(
    urlResetToken,
  );

  const [loginRole, setLoginRole] = useState(
    "coach",
  );

  const [error, setError] = useState(
    "",
  );

  const [message, setMessage] = useState(
    "",
  );

  const [saving, setSaving] = useState(
    false,
  );


  const registeringStudent = (
    mode === "student-register"
  );

  const registeringCoach = (
    mode === "coach-register"
  );

  const registrationComplete = (
    mode === "student-pending"
  );

  const recoveringPassword = (
    mode === "forgot-password"
  );

  const resettingPassword = (
    mode === "reset-password"
  );


  function clearMessages() {
    setError("");
    setMessage("");
  }


  function clearForm() {
    setForm({
      name: "",
      email: "",
      password: "",
    });

    setConfirmPassword("");
  }


  function cleanUrl() {
    const cleanAddress = (
      `${window.location.origin}${window.location.pathname}`
    );

    window.history.replaceState(
      {},
      "",
      cleanAddress,
    );
  }


  function showLogin() {
    setMode(
      "login",
    );

    clearMessages();
    clearForm();
    setResetToken("");
    cleanUrl();
  }


  function showForgotPassword() {
    setMode(
      "forgot-password",
    );

    clearMessages();

    setForm((current) => ({
      ...current,
      name: "",
      password: "",
    }));

    setConfirmPassword("");
  }


  async function handleLogin() {
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
  }


  async function handleRegistration() {
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

      clearForm();

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
  }


  async function handleForgotPassword() {
    const result = await forgotPassword({
      email: form.email,
    });

    setMessage(
  result?.message
  || (
    "Se o e-mail estiver cadastrado, "
    + "você receberá as instruções para redefinir a senha."
  ),
);

  }


  async function handleResetPassword() {
    if (!resetToken) {
      throw new Error(
        "Token de recuperação não informado.",
      );
    }

    if (form.password.length < 8) {
      throw new Error(
        "A nova senha deve ter pelo menos 8 caracteres.",
      );
    }

    if (
      form.password
      !== confirmPassword
    ) {
      throw new Error(
        "As senhas informadas não são iguais.",
      );
    }

    const result = await resetPassword({
      token: resetToken,
      password: form.password,
    });

    setMode(
      "login",
    );

    setResetToken("");
    setConfirmPassword("");

    setForm({
      name: "",
      email: form.email,
      password: "",
    });

    cleanUrl();

    setMessage(
      result.message
      || "Senha alterada com sucesso. Faça o login.",
    );
  }


  async function submit(
    event,
  ) {
    event.preventDefault();

    if (saving) {
      return;
    }

    setSaving(
      true,
    );

    clearMessages();

    try {
      if (mode === "login") {
        await handleLogin();
        return;
      }

      if (recoveringPassword) {
        await handleForgotPassword();
        return;
      }

      if (resettingPassword) {
        await handleResetPassword();
        return;
      }

      await handleRegistration();
    } catch (err) {
      setError(
        err?.message
        || "Não foi possível concluir a solicitação.",
      );
    } finally {
      setSaving(
        false,
      );
    }
  }


  function screenSubtitle() {
    if (registeringStudent) {
      return "Pré-cadastro de aluno";
    }

    if (registeringCoach) {
      return "Cadastro de treinador";
    }

    if (recoveringPassword) {
      return "Recuperar senha";
    }

    if (resettingPassword) {
      return "Definir nova senha";
    }

    return (
      `Entrar como ${
        loginRole === "coach"
          ? "treinador"
          : loginRole === "admin"
            ? "administrativo"
            : "atleta"
      }`
    );
  }


  function submitButtonText() {
    if (saving) {
      return "Aguarde...";
    }

    if (mode === "login") {
      return "Entrar";
    }

    if (recoveringPassword) {
      return "Continuar";
    }

    if (resettingPassword) {
      return "Salvar nova senha";
    }

    if (registeringCoach) {
      return "Criar conta de treinador";
    }

    return "Enviar pré-cadastro";
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
            O acesso será liberado depois que o treinador
            aprovar seu cadastro.
          </p>

          <button
            type="button"
            className="btn-primary"
            onClick={showLogin}
          >
            Voltar para o login
          </button>
        </section>

        <LoginInstitutionalFooter />
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
          {screenSubtitle()}
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

                  clearMessages();
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

                  clearMessages();
                }}
              >
                Sou atleta
              </button>

              <button
                type="button"
                className={
                  loginRole === "admin"
                    ? "active"
                    : ""
                }
                onClick={() => {
                  setLoginRole(
                    "admin",
                  );

                  clearMessages();
                }}
              >
                Administrativo
              </button>
            </div>
          )
        }

        {
          recoveringPassword
          && (
            <p className="muted">
              Informe o e-mail usado no cadastro para
              iniciar a recuperação da senha.
            </p>
          )
        }

        {
          resettingPassword
          && (
            <p className="muted">
              Digite e confirme a nova senha de acesso.
            </p>
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
                Seu cadastro ficará aguardando a aprovação
                do treinador.
              </p>
            )
          }

          {
            registeringCoach
            && (
              <p className="muted">
                Crie sua conta para administrar atletas e
                planejamentos.
              </p>
            )
          }

          {
            !resettingPassword
            && (
              <label>
                E-mail

                <input
                  type="email"
                  required
                  autoComplete="email"
                  value={form.email}
                  onChange={(event) => {
                    setForm({
                      ...form,
                      email: event.target.value,
                    });
                  }}
                />
              </label>
            )
          }

          {
            !recoveringPassword
            && (
              <label>
                {
                  resettingPassword
                    ? "Nova senha"
                    : "Senha"
                }

                <input
                  type="password"
                  required
                  minLength="8"
                  maxLength="128"
                  autoComplete={
                    resettingPassword
                      ? "new-password"
                      : "current-password"
                  }
                  value={form.password}
                  onChange={(event) => {
                    setForm({
                      ...form,
                      password: event.target.value,
                    });
                  }}
                />
              </label>
            )
          }

          {
            resettingPassword
            && (
              <label>
                Confirmar nova senha

                <input
                  type="password"
                  required
                  minLength="8"
                  maxLength="128"
                  autoComplete="new-password"
                  value={confirmPassword}
                  onChange={(event) => {
                    setConfirmPassword(
                      event.target.value,
                    );
                  }}
                />
              </label>
            )
          }

          {
            message
            && (
              <div className="profile-message">
                {message}
              </div>
            )
          }

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
            {submitButtonText()}
          </button>

          {
            mode === "login"
            && (
              <button
                type="button"
                className="auth-switch"
                onClick={showForgotPassword}
              >
                Esqueceu sua senha?
              </button>
            )
          }

          {
            (
              recoveringPassword
              || resettingPassword
            )
            && (
              <button
                type="button"
                className="auth-switch"
                onClick={showLogin}
              >
                Voltar para o login
              </button>
            )
          }
        </form>

        {
          !inviteToken
          && !recoveringPassword
          && !resettingPassword
          && (
            <div className="auth-actions">
              {
                mode === "login"
                  ? null
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
                    ? (
                      "Ainda não possui acesso? "
                      + "Solicite o link de convite ao seu treinador."
                    )
                    : (
                      loginRole === "admin"
                        ? "Contas administrativas são criadas por outro administrador."
                        : "Novos treinadores são cadastrados pelo perfil administrativo."
                    )
                }
              </small>
            </div>
          )
        }
      </section>

      <LoginInstitutionalFooter />
    </main>
  );
}
