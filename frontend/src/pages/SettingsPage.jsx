import "./SettingsPage.css";

export default function SettingsPage({ user }) {
  const panelLabel = user?.role === "student"
    ? "Área do atleta"
    : user?.role === "master"
      ? "Painel Master"
      : user?.role === "admin"
        ? "Painel administrativo"
        : "Painel do treinador";

  return (
    <section className="settings-page">
      <header className="settings-heading">
        <div>
          <p className="eyebrow">CONFIGURAÇÕES</p>
          <h2>Conta e preferências</h2>
          <p className="muted">
            Gerencie as opções da sua conta no RunCore.
          </p>
        </div>

        <span className="settings-role">
          {panelLabel}
        </span>
      </header>

      <section className="settings-card">
        <div className="settings-section-title">
          <div>
            <h3>Configurações da conta</h3>
            <p>
              Notificações, integrações, segurança e
              privacidade serão organizadas nesta área.
            </p>
          </div>
        </div>

        <p className="muted">
          A aparência agora pode ser alternada diretamente
          pela barra superior, sem sair da página atual.
        </p>
      </section>
    </section>
  );
}
