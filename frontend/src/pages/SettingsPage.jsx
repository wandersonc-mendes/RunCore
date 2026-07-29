import { useTheme } from "../theme/ThemeProvider";
import "./SettingsPage.css";

const options = [
  {
    value: "light",
    title: "Claro",
    description: "Interface clara em todos os dispositivos.",
    preview: "☀",
  },
  {
    value: "dark",
    title: "Escuro",
    description: "Interface escura em todos os dispositivos.",
    preview: "◐",
  },
  {
    value: "system",
    title: "De acordo com o sistema",
    description: "Segue automaticamente a configuração do dispositivo.",
    preview: "◑",
  },
];

export default function SettingsPage({ user }) {
  const {
    preference,
    resolvedTheme,
    changeTheme,
  } = useTheme();

  return (
    <section className="settings-page">
      <header className="settings-heading">
        <div>
          <p className="eyebrow">CONFIGURAÇÕES</p>
          <h2>Aparência</h2>
          <p className="muted">
            Escolha como o RunCore deve ser exibido.
          </p>
        </div>

        <span className="settings-role">
          {user?.role === "student"
            ? "Área do atleta"
            : user?.role === "admin"
              ? "Painel administrativo"
              : "Painel do treinador"}
        </span>
      </header>

      <section className="settings-card">
        <div className="settings-section-title">
          <div>
            <h3>Tema do sistema</h3>
            <p>
              A preferência fica salva neste navegador.
            </p>
          </div>

          <span>
            Tema ativo: {
              resolvedTheme === "dark"
                ? "Escuro"
                : "Claro"
            }
          </span>
        </div>

        <div
          className="theme-options"
          role="radiogroup"
          aria-label="Tema do RunCore"
        >
          {options.map((option) => (
            <button
              key={option.value}
              type="button"
              role="radio"
              aria-checked={preference === option.value}
              className={
                preference === option.value
                  ? "theme-option active"
                  : "theme-option"
              }
              onClick={() => changeTheme(option.value)}
            >
              <span className="theme-preview">
                {option.preview}
              </span>

              <span className="theme-option-copy">
                <strong>{option.title}</strong>
                <small>{option.description}</small>
              </span>

              <span
                className="theme-radio"
                aria-hidden="true"
              />
            </button>
          ))}
        </div>
      </section>
    </section>
  );
}
