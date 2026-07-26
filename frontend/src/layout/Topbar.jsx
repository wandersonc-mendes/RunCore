import { useState } from "react";

function initials(name = "") {
  return name.split(" ").filter(Boolean).slice(0, 2).map((part) => part[0]?.toUpperCase()).join("") || "RC";
}

export default function Topbar({ user, title, onMenu, onLogout }) {
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  return (
    <header className="app-topbar">
      <div className="app-topbar-heading">
        <button type="button" className="app-menu-button" aria-label="Abrir menu" onClick={onMenu}>☰</button>
        <div>
          <h1>{title}</h1>
          <p>{user?.role === "student" ? "Área do atleta" : "Painel do treinador"}</p>
        </div>
      </div>
      <div className="app-topbar-actions">
        <button type="button" className="app-icon-button" aria-label="Notificações" title="Notificações">
          ♧<span className="notification-dot" />
        </button>
        <button type="button" className="app-icon-button" aria-label="Ajuda" title="Ajuda">?</button>
        <div className="app-user-menu">
          <button
            type="button"
            className="app-user-trigger"
            aria-expanded={userMenuOpen}
            onClick={() => setUserMenuOpen((current) => !current)}
          >
            <span className="app-user-avatar">{initials(user?.name)}</span>
            <span className="app-user-name">{user?.name || "Usuário"}</span>
            <span aria-hidden="true">⌄</span>
          </button>
          {userMenuOpen && (
            <div className="app-user-dropdown">
              <button type="button">Meu perfil</button>
              <button type="button">Minha conta</button>
              <button type="button">Aparência</button>
              <button type="button">Alterar senha</button>
              <hr />
              <button type="button" className="danger" onClick={onLogout}>Sair</button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
