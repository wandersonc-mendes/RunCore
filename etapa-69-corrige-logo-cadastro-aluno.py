from pathlib import Path
import subprocess

ROOT = Path.cwd()
PROFILE = ROOT / "frontend/src/ProfilePanel.jsx"
CSS = ROOT / "frontend/src/App.css"
FRONTEND = ROOT / "frontend"

if not (ROOT / ".git").exists():
    raise RuntimeError("Execute este arquivo na raiz do RunCore.")

for required in (PROFILE, CSS):
    if not required.exists():
        raise RuntimeError(f"Arquivo não encontrado: {required}")

branch = subprocess.check_output(
    ["git", "branch", "--show-current"],
    cwd=ROOT,
    text=True,
).strip()

if branch != "main":
    raise RuntimeError(f"Branch atual: {branch}. Troque para main.")

profile = PROFILE.read_text(encoding="utf-8")

old_logo = '<span className="brand-logo"><img src="/logo-horizontal.png?v=2" alt="RunCore" /></span>'
new_logo = '<span className="profile-brand-symbol"><img src="/logo-symbol.png?v=3" alt="RunCore" /></span>'

if old_logo in profile:
    profile = profile.replace(old_logo, new_logo, 1)
elif new_logo not in profile:
    raise RuntimeError(
        "Não encontrei o logo do cabeçalho do perfil."
    )

PROFILE.write_text(profile, encoding="utf-8", newline="\n")

css = CSS.read_text(encoding="utf-8")
marker = "/* RUNCORE PROFILE SYMBOL 69 */"

if marker in css:
    css = css.split(marker)[0].rstrip()

css += '''
/* RUNCORE PROFILE SYMBOL 69 */
.profile-brand-symbol {
  align-items: center;
  background: transparent;
  display: flex;
  flex: 0 0 auto;
  height: 58px;
  justify-content: center;
  overflow: visible;
  width: 78px;
}

.profile-brand-symbol img {
  display: block;
  height: 100%;
  max-height: 58px;
  max-width: 78px;
  object-fit: contain;
  object-position: center;
  width: 100%;
}

@media (max-width: 620px) {
  .profile-brand-symbol {
    height: 48px;
    width: 64px;
  }

  .profile-brand-symbol img {
    max-height: 48px;
    max-width: 64px;
  }
}
'''

CSS.write_text(css, encoding="utf-8", newline="\n")

build = subprocess.run(
    ["npm.cmd", "run", "build"],
    cwd=FRONTEND,
)

if build.returncode:
    raise SystemExit(build.returncode)

print("\nEtapa 69 concluída.")
print(
    "O cabeçalho do perfil agora usa apenas o símbolo RC, "
    "sem comprimir o logo horizontal."
)
print("\nExecute:")
print("git add frontend/src/ProfilePanel.jsx frontend/src/App.css")
print('git commit -m "style: corrige logo do cadastro do aluno"')
print("git push origin main")
