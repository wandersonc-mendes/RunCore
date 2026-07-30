import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { studentPaths } from "../router/paths";
import "./SettingsPage.css";


const DEFAULT_NOTIFICATIONS = {
  planChanges: true,
  trainingReminders: true,
  feedbackUpdates: true,
};


function readNotificationPreferences(storageKey) {
  try {
    const saved = window.localStorage.getItem(storageKey);

    return saved
      ? { ...DEFAULT_NOTIFICATIONS, ...JSON.parse(saved) }
      : DEFAULT_NOTIFICATIONS;
  } catch {
    return DEFAULT_NOTIFICATIONS;
  }
}


function SettingsItem({
  title,
  description,
  status = "Disponível em breve",
  tone = "planned",
  actionLabel = "",
  onAction = null,
}) {
  return (
    <article className="settings-item">
      <div>
        <strong>{title}</strong>
        <p>{description}</p>
      </div>

      {onAction ? (
        <button
          type="button"
          className="settings-item-action"
          onClick={onAction}
        >
          {actionLabel || status}
        </button>
      ) : (
        <span className={`settings-status ${tone}`}>
          {status}
        </span>
      )}
    </article>
  );
}


function NotificationToggle({
  title,
  description,
  checked,
  onChange,
}) {
  return (
    <label className="settings-notification-toggle">
      <div>
        <strong>{title}</strong>
        <p>{description}</p>
      </div>

      <input
        type="checkbox"
        checked={checked}
        onChange={(event) => onChange(event.target.checked)}
      />

      <span className="settings-switch" aria-hidden="true">
        <span />
      </span>
    </label>
  );
}


export default function SettingsPage({ user }) {
  const navigate = useNavigate();
  const isStudent = user?.role === "student";
  const accountKey = user?.id || user?.email || "anonymous";
  const notificationStorageKey =
    `runcore.notification-preferences.${accountKey}`;

  const [notifications, setNotifications] = useState(
    () => readNotificationPreferences(notificationStorageKey),
  );

  const panelLabel = isStudent
    ? "Área do atleta"
    : user?.role === "master"
      ? "Painel Master"
      : user?.role === "admin"
        ? "Painel administrativo"
        : "Painel do treinador";

  function changeNotification(field, value) {
    setNotifications((current) => {
      const next = {
        ...current,
        [field]: value,
      };

      window.localStorage.setItem(
        notificationStorageKey,
        JSON.stringify(next),
      );

      return next;
    });
  }

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
                Defina quais avisos devem permanecer ativos neste
                navegador.
              </p>
            </div>
          </header>

          <div className="settings-notification-list">
            <NotificationToggle
              title="Alterações na planilha"
              description={
                isStudent
                  ? "Avisos quando o treinador alterar sessões ou orientações."
                  : "Avisos sobre mudanças importantes nos planejamentos."
              }
              checked={notifications.planChanges}
              onChange={(value) =>
                changeNotification("planChanges", value)
              }
            />

            <NotificationToggle
              title="Lembretes de treino"
              description="Lembretes de sessões próximas e compromissos da agenda."
              checked={notifications.trainingReminders}
              onChange={(value) =>
                changeNotification("trainingReminders", value)
              }
            />

            <NotificationToggle
              title="Feedback e acompanhamento"
              description={
                isStudent
                  ? "Confirmações sobre relatos e retornos do treinador."
                  : "Avisos de novos feedbacks enviados pelos atletas."
              }
              checked={notifications.feedbackUpdates}
              onChange={(value) =>
                changeNotification("feedbackUpdates", value)
              }
            />
          </div>

          <p className="settings-browser-note">
            As preferências são salvas somente neste navegador.
            O envio efetivo de notificações será conectado ao backend
            em uma etapa posterior.
          </p>
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
              actionLabel={isStudent ? "Abrir Atividades" : ""}
              onAction={
                isStudent
                  ? () => navigate(studentPaths.activities)
                  : null
              }
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
