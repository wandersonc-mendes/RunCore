from pathlib import Path
import subprocess


ROOT = Path.cwd()
PORTAL = ROOT / "frontend/src/StudentPortal.jsx"
FRONTEND = ROOT / "frontend"

if not (ROOT / ".git").exists():
    raise RuntimeError("Execute este arquivo na raiz do RunCore.")

if not PORTAL.exists():
    raise RuntimeError(f"Arquivo não encontrado: {PORTAL}")

branch = subprocess.check_output(
    ["git", "branch", "--show-current"],
    cwd=ROOT,
    text=True,
).strip()

if branch != "main":
    raise RuntimeError(f"Branch atual: {branch}. Troque para main.")


content = PORTAL.read_text(encoding="utf-8")

old_block = '''  if (showProfile || view === "profile") {
    return (
      <ProfilePanel
        onClose={() => setShowProfile(false)}
      />
    );
  }
'''

new_block = '''  if (showProfile || view === "profile") {
    return (
      <ProfilePanel
        onClose={() => {
          setShowProfile(false);

          if (view === "profile") {
            navigate(
              studentPaths.dashboard,
              { replace: true },
            );
          }
        }}
      />
    );
  }
'''

if old_block in content:
    content = content.replace(
        old_block,
        new_block,
        1,
    )
elif new_block not in content:
    raise RuntimeError(
        "Não encontrei o bloco do ProfilePanel no formato esperado."
    )


PORTAL.write_text(
    content,
    encoding="utf-8",
    newline="\n",
)


build = subprocess.run(
    ["npm.cmd", "run", "build"],
    cwd=FRONTEND,
)

if build.returncode:
    raise SystemExit(build.returncode)


print("\nEtapa 66C concluída.")
print(
    "O botão Voltar agora retorna ao dashboard "
    "quando o perfil estiver aberto pela rota do aluno."
)
print("\nExecute:")
print(
    "git add frontend/src/StudentPortal.jsx"
)
print(
    'git commit -m "fix: corrige retorno da tela de perfil"'
)
print("git push origin main")
