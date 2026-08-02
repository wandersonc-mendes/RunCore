from pathlib import Path
import subprocess

ROOT = Path.cwd()
CSS = ROOT / "frontend/src/App.css"
FRONTEND = ROOT / "frontend"

if not (ROOT / ".git").exists():
    raise RuntimeError("Execute este arquivo na raiz do RunCore.")

if not CSS.exists():
    raise RuntimeError(f"Arquivo não encontrado: {CSS}")

branch = subprocess.check_output(
    ["git", "branch", "--show-current"],
    cwd=ROOT,
    text=True,
).strip()

if branch != "main":
    raise RuntimeError(f"Branch atual: {branch}. Troque para main.")

content = CSS.read_text(encoding="utf-8")
marker = "/* RUNCORE MOBILE ACTIVITIES 68 */"

if marker in content:
    content = content.split(marker)[0].rstrip()

content += '''
/* RUNCORE MOBILE ACTIVITIES 68 */
@media (max-width: 760px) {
  html,
  body,
  #root {
    max-width: 100%;
    overflow-x: hidden;
  }

  .routed-student-page[data-view="activities"],
  .routed-student-page[data-view="activities"] .student-content {
    max-width: 100%;
    min-width: 0;
    width: 100%;
  }

  .routed-student-page[data-view="activities"] .student-content {
    gap: 16px;
    padding-left: 16px;
    padding-right: 16px;
  }

  .routed-student-page[data-view="activities"] .connection-card,
  .routed-student-page[data-view="activities"] .student-stats,
  .routed-student-page[data-view="activities"] .activity-card,
  .routed-student-page[data-view="activities"] .activity-list,
  .routed-student-page[data-view="activities"] .activity-row {
    max-width: 100%;
    min-width: 0;
    width: 100%;
  }

  .routed-student-page[data-view="activities"] .connection-card {
    padding: 18px;
  }

  .routed-student-page[data-view="activities"] .connection-card > div {
    align-items: flex-start;
    min-width: 0;
  }

  .routed-student-page[data-view="activities"] .connection-card > div > div {
    min-width: 0;
  }

  .routed-student-page[data-view="activities"] .connection-card p {
    overflow-wrap: anywhere;
  }

  .routed-student-page[data-view="activities"] .student-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .routed-student-page[data-view="activities"] .student-stats article {
    min-width: 0;
    padding: 15px;
  }

  .routed-student-page[data-view="activities"] .student-stats strong {
    font-size: 20px;
    overflow-wrap: anywhere;
  }

  .routed-student-page[data-view="activities"] .activity-card-heading {
    padding: 16px;
  }

  .routed-student-page[data-view="activities"] .activity-list {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
  }

  .routed-student-page[data-view="activities"] .activity-row {
    display: block;
  }

  .routed-student-page[data-view="activities"] .activity-toggle {
    grid-template-columns: minmax(0, 1fr) auto;
    max-width: 100%;
    min-width: 0;
    padding: 16px;
  }

  .routed-student-page[data-view="activities"] .activity-toggle > div {
    max-width: 100%;
    min-width: 0;
  }

  .routed-student-page[data-view="activities"] .activity-toggle > div > strong,
  .routed-student-page[data-view="activities"] .activity-toggle > div > span {
    max-width: 100%;
    overflow: visible;
    overflow-wrap: anywhere;
    text-overflow: clip;
    white-space: normal;
  }

  .routed-student-page[data-view="activities"] .activity-details {
    grid-template-columns: minmax(0, 1fr);
    max-width: 100%;
    min-width: 0;
    overflow: hidden;
    padding: 14px;
  }

  .routed-student-page[data-view="activities"] .activity-details > *,
  .routed-student-page[data-view="activities"] .training-feedback,
  .routed-student-page[data-view="activities"] .adherence-card,
  .routed-student-page[data-view="activities"] .activity-details .laps {
    grid-column: 1;
    max-width: 100%;
    min-width: 0;
  }

  .routed-student-page[data-view="activities"] .activity-details .lap-main {
    align-items: flex-start;
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    overflow: visible;
  }

  .routed-student-page[data-view="activities"] .activity-details .lap-main strong,
  .routed-student-page[data-view="activities"] .activity-details .lap-main span {
    overflow-wrap: anywhere;
    white-space: normal;
  }

  .routed-student-page[data-view="activities"] .adherence-block {
    align-items: flex-start;
    grid-template-columns: minmax(0, 1fr);
  }

  .routed-student-page[data-view="activities"] .adherence-block em {
    text-align: left;
  }
}

@media (max-width: 390px) {
  .routed-student-page[data-view="activities"] .student-stats {
    grid-template-columns: minmax(0, 1fr);
  }
}
'''

CSS.write_text(content, encoding="utf-8", newline="\n")

build = subprocess.run(
    ["npm.cmd", "run", "build"],
    cwd=FRONTEND,
)

if build.returncode:
    raise SystemExit(build.returncode)

print("\nEtapa 68 concluída.")
print(
    "A página Atividades foi ajustada para celular "
    "sem alterar o layout desktop."
)
print("\nExecute:")
print("git add frontend/src/App.css")
print('git commit -m "fix: corrige responsividade das atividades no celular"')
print("git push origin main")
