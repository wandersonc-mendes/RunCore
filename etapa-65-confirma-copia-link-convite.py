from pathlib import Path
import subprocess


ROOT = Path.cwd()
PAGE = ROOT / "frontend/src/pages/CoachDashboardPage.jsx"
CSS = ROOT / "frontend/src/pages/CoachDashboardPage.css"
FRONTEND = ROOT / "frontend"

if not (ROOT / ".git").exists():
    raise RuntimeError("Execute este arquivo na raiz do RunCore.")

for required in (PAGE, CSS):
    if not required.exists():
        raise RuntimeError(f"Arquivo não encontrado: {required}")

branch = subprocess.check_output(
    ["git", "branch", "--show-current"],
    cwd=ROOT,
    text=True,
).strip()

if branch != "main":
    raise RuntimeError(f"Branch atual: {branch}. Troque para main.")


page = PAGE.read_text(encoding="utf-8")


state_anchor = '''  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
'''

state_replacement = '''  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [inviteCopyStatus, setInviteCopyStatus] = useState("");
'''

if state_replacement not in page:
    if state_anchor not in page:
        raise RuntimeError(
            "Não encontrei o bloco de estados do dashboard."
        )

    page = page.replace(
        state_anchor,
        state_replacement,
        1,
    )


function_anchor = '''  useEffect(() => {
    let active = true;
'''

copy_function = '''  async function copyInvitationLink() {
    setInviteCopyStatus("");

    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(inviteLink);
      } else {
        const temporaryInput = document.createElement("textarea");
        temporaryInput.value = inviteLink;
        temporaryInput.setAttribute("readonly", "");
        temporaryInput.style.position = "fixed";
        temporaryInput.style.opacity = "0";
        document.body.appendChild(temporaryInput);
        temporaryInput.select();

        const copied = document.execCommand("copy");
        document.body.removeChild(temporaryInput);

        if (!copied) {
          throw new Error("Falha ao copiar.");
        }
      }

      setInviteCopyStatus("copied");

      window.setTimeout(() => {
        setInviteCopyStatus("");
      }, 2500);
    } catch {
      setInviteCopyStatus("error");
    }
  }


  useEffect(() => {
    let active = true;
'''

if "async function copyInvitationLink()" not in page:
    if function_anchor not in page:
        raise RuntimeError(
            "Não encontrei o ponto para inserir a função de cópia."
        )

    page = page.replace(
        function_anchor,
        copy_function,
        1,
    )


old_button = '''            <button
              type="button"
              className="btn-ghost"
              onClick={() =>
                navigator.clipboard?.writeText(inviteLink)
              }
            >
              Copiar
            </button>
'''

new_button = '''            <div className="dashboard-copy-feedback">
              <button
                type="button"
                className="btn-ghost"
                onClick={copyInvitationLink}
              >
                {inviteCopyStatus === "copied"
                  ? "Link copiado"
                  : "Copiar"}
              </button>

              {inviteCopyStatus === "copied" && (
                <small role="status">
                  Copiado para a área de transferência.
                </small>
              )}

              {inviteCopyStatus === "error" && (
                <small role="alert" className="is-error">
                  Não foi possível copiar. Selecione o link manualmente.
                </small>
              )}
            </div>
'''

if new_button not in page:
    if old_button not in page:
        raise RuntimeError(
            "Não encontrei o botão Copiar no formato esperado."
        )

    page = page.replace(
        old_button,
        new_button,
        1,
    )


PAGE.write_text(
    page,
    encoding="utf-8",
    newline="\n",
)


css = CSS.read_text(encoding="utf-8")
marker = "/* RUNCORE COPY FEEDBACK 65 */"

if marker in css:
    css = css.split(marker)[0].rstrip()

css += r'''

/* RUNCORE COPY FEEDBACK 65 */
.dashboard-copy-feedback {
  display: grid;
  justify-items: end;
  gap: 6px;
}

.dashboard-copy-feedback small {
  color: var(--shell-accent);
  font-size: 11px;
  font-weight: 700;
  text-align: right;
}

.dashboard-copy-feedback small.is-error {
  color: #d96b5f;
}

@media (max-width: 620px) {
  .dashboard-copy-feedback {
    justify-items: stretch;
  }

  .dashboard-copy-feedback small {
    text-align: left;
  }
}
'''

CSS.write_text(
    css,
    encoding="utf-8",
    newline="\n",
)


build = subprocess.run(
    ["npm.cmd", "run", "build"],
    cwd=FRONTEND,
)

if build.returncode:
    raise SystemExit(build.returncode)


print("\nEtapa 65 concluída.")
print("O botão agora confirma a cópia e possui fallback para celular.")
print("\nExecute:")
print(
    "git add frontend/src/pages/CoachDashboardPage.jsx "
    "frontend/src/pages/CoachDashboardPage.css"
)
print(
    'git commit -m "fix: confirma copia do link de convite"'
)
print("git push origin main")
