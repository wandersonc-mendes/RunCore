import "./SettingsPage.css";


function SettingsItem({
  title,
  description,
  status = "Disponível em breve",
  tone = "planned",
}) {
  return (
    <article className="settings-item">
      <div>
        <strong>{title}</strong>
        <p>{description}</p>
      </div>

      <span className={`settings-status ${tone}`}>
        {status}
      </span>
    </article>
  );
}


export default function SettingsPage({ user }) {
  const isStudent = user?.role === "student";

  const panelLabel = isStudent
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
          <h2>Conta, integrações e privacidade</h2>
          <p className="muted">
            Consulte o que já está ativo e acompanhe as próximas
            opções previstas para sua conta.
          </p>
        </div>

        <span className="settings-role">
          {panelLabel}
        </span>
      </header>

      <section className="settings-overview">
        <article>
          <span>Conta</span>
          <strong>{user?.email || "E-mail não informado"}</strong>
          <small>
            {user?.active === false ? "Conta inativa" : "Conta ativa"}
          </small>
        </article>

        <article>
          <span>Perfil de acesso</span>
          <strong>{panelLabel}</strong>
          <small>Permissões definidas pelo RunCore</small>
        </article>

        <article>
          <span>Aparência</span>
          <strong>Barra superior</strong>
          <small>Alternância global de tema</small>
        </article>
      </section>

      <section className="settings-grid">
        <section className="settings-card">
          <header className="settings-section-title">
            <div>
              <span>Comunicação</span>
              <h3>Notificações</h3>
              <p>
                Controle como o RunCore informa alterações relevantes.
              </p>
            </div>
          </header>

          <div className="settings-list">
            <SettingsItem
              title="Alterações na planilha"
              description={
                isStudent
                  ? "Avisos quando o treinador alterar sessões ou orientações."
                  : "Avisos sobre mudanças importantes nos planejamentos."
              }
            />

            <SettingsItem
              title="Lembretes de treino"
              description="Lembretes de sessões próximas e compromissos da agenda."
            />

            <SettingsItem
              title="Feedback e acompanhamento"
              description={
                isStudent
                  ? "Confirmações sobre relatos e retornos do treinador."
                  : "Avisos de novos feedbacks enviados pelos atletas."
              }
            />
          </div>
        </section>

        <section className="settings-card">
          <header className="settings-section-title">
            <div>
              <span>Serviços conectados</span>
              <h3>Integrações</h3>
              <p>
                Gerencie plataformas externas vinculadas ao RunCore.
              </p>
            </div>
          </header>

          <div className="settings-list">
            <SettingsItem
              title="Strava"
              description={
                isStudent
                  ? "A conexão e a sincronização permanecem na página Atividades."
                  : "A integração é usada para importar atividades dos atletas."
              }
              status={isStudent ? "Gerenciar em Atividades" : "Integração ativa"}
              tone="available"
            />

            <SettingsItem
              title="Garmin Connect"
              description="Sincronização de treinos estruturados e atividades."
            />

            <SettingsItem
              title="Outras plataformas"
              description="Novos provedores poderão ser adicionados por integração."
            />
          </div>
        </section>

        <section className="settings-card">
          <header className="settings-section-title">
            <div>
              <span>Proteção da conta</span>
              <h3>Segurança</h3>
              <p>
                Recursos relacionados a acesso, senha e sessões.
              </p>
            </div>
          </header>

          <div className="settings-list">
            <SettingsItem
              title="Alterar senha"
              description="Atualização segura da credencial de acesso."
            />

            <SettingsItem
              title="Sessões conectadas"
              description="Visualização e encerramento de acessos ativos."
            />

            <SettingsItem
              title="Autenticação em duas etapas"
              description="Camada adicional de proteção para a conta."
            />
          </div>
        </section>

        <section className="settings-card">
          <header className="settings-section-title">
            <div>
              <span>Dados e controle</span>
              <h3>Privacidade</h3>
              <p>
                Consulte opções relacionadas aos dados armazenados.
              </p>
            </div>
          </header>

          <div className="settings-list">
            <SettingsItem
              title="Exportar meus dados"
              description="Geração de arquivo com informações da conta."
            />

            <SettingsItem
              title="Uso dos dados esportivos"
              description="Informações sobre atividades, avaliações e planejamento."
            />

            <SettingsItem
              title="Desativar conta"
              description="Solicitação controlada de desativação do acesso."
              status="Ação protegida"
              tone="protected"
            />
          </div>
        </section>
      </section>

      <section className="settings-footer-note">
        <div>
          <span>Aparência do sistema</span>
          <h3>O tema não fica nesta página</h3>
          <p>
            A alternância entre modo claro e escuro permanece na barra
            superior e funciona sem sair da tela atual.
          </p>
        </div>
      </section>
    </section>
  );
}
