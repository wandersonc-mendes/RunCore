import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTheme } from "../theme/ThemeProvider";

import {
  adminPaths,
  coachPaths,
  studentPaths,
} from "../router/paths";


function initials(name = "") {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("") || "RC";
}


function notificationsFor(role) {
  if (role === "admin" || role === "master") {
    return [
      {
        title: "Gestão de acessos",
        description:
          "Cadastre treinadores e administradores em Usuários e acessos.",
      },
    ];
  }

  if (role === "student") {
    return [
      {
        title: "Planilha de treinamento",
        description:
          "Consulte sua semana atual em Minha planilha.",
      },
      {
        title: "Feedback dos treinos",
        description:
          "Registre como se sentiu após cada atividade.",
      },
    ];
  }

  return [
    {
      title: "Acompanhamento dos atletas",
      description:
        "Consulte avaliações e planejamentos pela tela de atletas.",
    },
    {
      title: "Convites pendentes",
      description:
        "As solicitações de novos alunos aparecem no Dashboard.",
    },
  ];
}


export default function Topbar({
  user,
  title,
  onMenu,
  onLogout,
}) {
  const [openPanel, setOpenPanel] = useState(null);
  const [profilePhoto, setProfilePhoto] = useState("");
  const containerRef = useRef(null);
  const navigate = useNavigate();
  const { resolvedTheme, toggleTheme } = useTheme();

  const isStudent = user?.role === "student";
  const isAdmin = user?.role === "admin";
  const isMaster = user?.role === "master";
  const settingsPath = isStudent
    ? studentPaths.settings
    : isAdmin
      ? adminPaths.settings
      : coachPaths.settings;
  const profilePath = isStudent
    ? studentPaths.profile
    : isAdmin
      ? adminPaths.settings
      : coachPaths.profile;


  useEffect(() => {
    const key = `runcore_profile_photo_${user?.id || user?.email || "coach"}`;

    function loadPhoto() {
      setProfilePhoto(localStorage.getItem(key) || "");
    }

    function handlePhotoChange(event) {
      if (!event.detail || event.detail.key === key) {
        loadPhoto();
      }
    }

    loadPhoto();
    window.addEventListener(
      "runcore-profile-photo-changed",
      handlePhotoChange,
    );

    return () => {
      window.removeEventListener(
        "runcore-profile-photo-changed",
        handlePhotoChange,
      );
    };
  }, [user]);

  useEffect(() => {
    function closeOnOutsideClick(event) {
      if (
        containerRef.current
        && !containerRef.current.contains(event.target)
      ) {
        setOpenPanel(null);
      }
    }

    function closeOnEscape(event) {
      if (event.key === "Escape") {
        setOpenPanel(null);
      }
    }

    document.addEventListener(
      "mousedown",
      closeOnOutsideClick,
    );
    document.addEventListener(
      "keydown",
      closeOnEscape,
    );

    return () => {
      document.removeEventListener(
        "mousedown",
        closeOnOutsideClick,
      );
      document.removeEventListener(
        "keydown",
        closeOnEscape,
      );
    };
  }, []);

  function togglePanel(panel) {
    setOpenPanel((current) =>
      current === panel ? null : panel
    );
  }

  function goTo(path) {
    setOpenPanel(null);
    navigate(path);
  }

  return (
    <header className="app-topbar">
      <div className="app-topbar-heading">
        <button
          type="button"
          className="app-menu-button"
          aria-label="Abrir menu"
          onClick={onMenu}
        >
          ☰
        </button>

        <div>
          <h1>{title}</h1>
          <p>
            {isStudent
              ? "Área do atleta"
              : "Painel do treinador"}
          </p>
        </div>
      </div>

      <div
        className="app-topbar-actions"
        ref={containerRef}
      >
        <button
          type="button"
          className="app-icon-button app-theme-toggle"
          aria-label={
            resolvedTheme === "dark"
              ? "Ativar modo claro"
              : "Ativar modo escuro"
          }
          title={
            resolvedTheme === "dark"
              ? "Ativar modo claro"
              : "Ativar modo escuro"
          }
          onClick={toggleTheme}
        >
          <img
            src={
              resolvedTheme === "dark"
                ? "/icons/modo-claro.png"
                : "/icons/modo-escuro.png"
            }
            alt=""
            aria-hidden="true"
          />
        </button>

        <div className="app-topbar-panel-anchor">
          <button
            type="button"
            className="app-icon-button"
            aria-label="Notificações"
            title="Notificações"
            aria-expanded={openPanel === "notifications"}
            onClick={() => togglePanel("notifications")}
          >
            <span aria-hidden="true">●</span>
            <span className="notification-dot" />
          </button>

          {openPanel === "notifications" && (
            <section
              className="app-floating-panel notification-panel"
              aria-label="Central de notificações"
            >
              <header>
                <div>
                  <strong>Notificações</strong>
                  <span>Informações importantes</span>
                </div>

                <button
                  type="button"
                  aria-label="Fechar notificações"
                  onClick={() => setOpenPanel(null)}
                >
                  ×
                </button>
              </header>

              <div className="notification-list">
                {notificationsFor(user?.role).map(
                  (notification) => (
                    <article key={notification.title}>
                      <span className="notification-marker" />

                      <div>
                        <strong>
                          {notification.title}
                        </strong>
                        <p>
                          {notification.description}
                        </p>
                      </div>
                    </article>
                  ),
                )}
              </div>
            </section>
          )}
        </div>

        <div className="app-topbar-panel-anchor">
          <button
            type="button"
            className="app-icon-button"
            aria-label="Ajuda"
            title="Ajuda"
            aria-expanded={openPanel === "help"}
            onClick={() => togglePanel("help")}
          >
            ?
          </button>

          {openPanel === "help" && (
            <section
              className="app-floating-panel help-panel"
              aria-label="Ajuda do RunCore"
            >
              <header>
                <div>
                  <strong>Ajuda</strong>
                  <span>Orientações rápidas</span>
                </div>

                <button
                  type="button"
                  aria-label="Fechar ajuda"
                  onClick={() => setOpenPanel(null)}
                >
                  ×
                </button>
              </header>

              <div className="help-content">
                <p>
                  Use o menu lateral para acessar cada
                  módulo em uma tela independente.
                </p>

                <button
                  type="button"
                  onClick={() => goTo(settingsPath)}
                >
                  Abrir configurações
                </button>
              </div>
            </section>
          )}
        </div>

        <div className="app-user-menu">
          <button
            type="button"
            className="app-user-trigger"
            aria-expanded={openPanel === "user"}
            onClick={() => togglePanel("user")}
          >
            <span
              className={`app-user-avatar ${
                profilePhoto ? "has-photo" : ""
              }`}
            >
              {profilePhoto ? (
                <img src={profilePhoto} alt="Foto do perfil" />
              ) : (
                initials(user?.name)
              )}
            </span>

            <span className="app-user-name">
              {user?.name || "Usuário"}
            </span>

            <span aria-hidden="true">⌄</span>
          </button>

          {openPanel === "user" && (
            <div className="app-user-dropdown">
              <div className="app-user-summary">
                <span
                  className={`app-user-avatar large ${
                    profilePhoto ? "has-photo" : ""
                  }`}
                >
                  {profilePhoto ? (
                    <img src={profilePhoto} alt="Foto do perfil" />
                  ) : (
                    initials(user?.name)
                  )}
                </span>

                <div>
                  <strong>
                    {user?.name || "Usuário"}
                  </strong>
                  <small>
                    {isStudent
                      ? "Atleta"
                      : isMaster
                        ? "Master"
                      : isAdmin
                        ? "Administrativo"
                        : "Treinador"}
                  </small>
                </div>
              </div>

              <hr />

              <button
                type="button"
                onClick={() => goTo(profilePath)}
              >
                Meu perfil
              </button>

              <button
                type="button"
                onClick={() => goTo(settingsPath)}
              >
                Minha conta
              </button>

              <hr />

              <button
                type="button"
                className="danger"
                onClick={onLogout}
              >
                Sair
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
